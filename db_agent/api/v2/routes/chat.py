"""
SSE streaming chat endpoint.
"""
import asyncio
import json
import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse

from ..deps import get_app_state
from ..models import ChatMessageRequest, PendingOperation, ConfirmRequest, SuccessResponse, StartMigrationRequest, SubmitFormRequest
from db_agent.storage.models import MigrationTask

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/{session_id}/message")
async def chat_stream(session_id: int, req: ChatMessageRequest):
    """
    Stream a chat response via SSE.

    SSE event types:
    - tool_call: {"name": "...", "input": {...}}
    - tool_result: {"name": "...", "status": "...", "summary": "..."}
    - text_delta: {"content": "..."}
    - pending: {"index": 0, "type": "...", "sql": "..."}
    - done: {"full_text": "...", "has_pending": bool, "pending_count": int}
    - error: {"message": "..."}
    """
    state = get_app_state()

    try:
        agent = state.get_or_create_agent(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    queue: asyncio.Queue = asyncio.Queue()

    def on_thinking(event_type: str, data: Any):
        """Callback invoked from the agent thread to push SSE events."""
        try:
            if event_type == "tool_call":
                # data: {"name": ..., "input": ...}
                queue.put_nowait({"event": "tool_call", "data": data})
            elif event_type == "tool_result":
                # data: {"name": ..., "result": {...}} → transform for frontend
                result = data.get("result", {}) if isinstance(data, dict) else {}
                status = result.get("status", "success") if isinstance(result, dict) else "success"
                # Build a short summary from the result
                summary = ""
                if isinstance(result, dict):
                    if "error" in result:
                        summary = str(result["error"])[:200]
                        status = "error"
                    elif "data" in result:
                        d = result["data"]
                        if isinstance(d, list):
                            summary = f"{len(d)} rows"
                        elif isinstance(d, str):
                            summary = d[:200]
                        else:
                            summary = str(d)[:200]
                    elif "message" in result:
                        summary = str(result["message"])[:200]
                    else:
                        summary = json.dumps(result, ensure_ascii=False, default=str)[:200]
                queue.put_nowait({
                    "event": "tool_result",
                    "data": {"name": data.get("name", ""), "status": status, "summary": summary},
                })
                # Detect migration_setup_requested and send migration_setup SSE event
                if isinstance(result, dict) and result.get("status") == "migration_setup_requested":
                    queue.put_nowait({
                        "event": "migration_setup",
                        "data": {
                            "reason": result.get("reason", ""),
                            "suggested_source_db_type": result.get("suggested_source_db_type"),
                            "suggested_target_db_type": result.get("suggested_target_db_type"),
                        }
                    })
                # Detect form_input_requested and send form_input SSE event
                if isinstance(result, dict) and result.get("status") == "form_input_requested":
                    queue.put_nowait({
                        "event": "form_input",
                        "data": {
                            "title": result.get("title", ""),
                            "description": result.get("description", ""),
                            "fields": result.get("fields", []),
                        }
                    })
            elif event_type == "text":
                # Intermediate text content (LLM text alongside tool calls)
                text = data.get("content", "") if isinstance(data, dict) else ""
                if text:
                    queue.put_nowait({"event": "text_delta", "data": {"content": text}})
            elif event_type == "migration_progress":
                queue.put_nowait({"event": "migration_progress", "data": data})
            # Ignore "thinking" events (no need to stream them)
        except Exception as e:
            logger.warning(f"on_thinking callback error: {e}")
            # Never let callback errors crash the agent thread

    async def generate():
        try:
            # Run the blocking agent.chat() in a thread
            max_iter = 999 if agent.migration_auto_execute else 30
            task = asyncio.create_task(
                asyncio.to_thread(agent.chat, req.message, max_iter, on_thinking)
            )

            # Drain the queue while the task runs
            while not task.done():
                try:
                    ev = await asyncio.wait_for(queue.get(), timeout=0.1)
                    yield f"event: {ev['event']}\ndata: {json.dumps(ev['data'], ensure_ascii=False, default=str)}\n\n"
                except asyncio.TimeoutError:
                    continue

            # Drain any remaining items
            while not queue.empty():
                ev = queue.get_nowait()
                yield f"event: {ev['event']}\ndata: {json.dumps(ev['data'], ensure_ascii=False, default=str)}\n\n"

            # Get the final response
            response = task.result()

            # Send full text response
            if response:
                yield f"event: text_delta\ndata: {json.dumps({'content': response}, ensure_ascii=False)}\n\n"

            # Send pending operations if any
            has_pending = agent.has_pending_operations()
            if has_pending:
                for i, op in enumerate(agent.get_all_pending_operations()):
                    yield f"event: pending\ndata: {json.dumps({'index': i, 'type': op.get('type', 'execute_sql'), 'sql': op.get('sql', ''), 'description': op.get('description', '')}, ensure_ascii=False)}\n\n"

            # Done event
            yield f"event: done\ndata: {json.dumps({'has_pending': has_pending, 'pending_count': agent.get_pending_count() if has_pending else 0}, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"Chat stream error: {e}", exc_info=True)
            yield f"event: error\ndata: {json.dumps({'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{session_id}/interrupt", response_model=SuccessResponse)
async def interrupt_chat(session_id: int):
    state = get_app_state()
    try:
        agent = state.get_or_create_agent(session_id)
        agent.request_interrupt()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return SuccessResponse(message="Interrupt requested")


@router.get("/{session_id}/pending")
async def get_pending_operations(session_id: int):
    state = get_app_state()
    try:
        agent = state.get_or_create_agent(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    ops = agent.get_all_pending_operations()
    return {
        "has_pending": agent.has_pending_operations(),
        "pending_count": len(ops),
        "operations": [
            PendingOperation(
                index=i,
                type=op.get("type", "execute_sql"),
                sql=op.get("sql", ""),
                description=op.get("description", ""),
            ).model_dump()
            for i, op in enumerate(ops)
        ],
    }


def _update_last_tool_result(agent, result_content: str):
    """Update the last tool message in conversation history with actual execution result."""
    # Find the last tool message with pending_confirmation or form_input_requested and update it
    for i in range(len(agent.conversation_history) - 1, -1, -1):
        msg = agent.conversation_history[i]
        content = msg.get("content", "")
        if msg.get("role") == "tool" and ("pending_confirmation" in content or "form_input_requested" in content):
            agent.conversation_history[i]["content"] = result_content
            return
    # Fallback: append as user context if no pending tool message found
    agent.conversation_history.append({
        "role": "user",
        "content": f"[System: SQL execution result] {result_content}",
    })


@router.post("/{session_id}/confirm")
async def confirm_operation(session_id: int, req: ConfirmRequest):
    state = get_app_state()
    try:
        agent = state.get_or_create_agent(session_id)
        result = agent.confirm_operation(req.index)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except IndexError:
        raise HTTPException(status_code=400, detail="Invalid operation index")

    # Update the pending tool result in conversation history with actual result
    result_content = json.dumps(result, ensure_ascii=False, default=str)
    _update_last_tool_result(agent, result_content)

    return {"success": True, "result": result}


@router.post("/{session_id}/confirm-all")
async def confirm_all_operations(session_id: int):
    state = get_app_state()
    try:
        agent = state.get_or_create_agent(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    results = []
    count = len(agent.get_all_pending_operations())
    for i in range(count):
        try:
            result = agent.confirm_operation(0)  # Always confirm index 0 as list shrinks
            results.append(result)
        except Exception as e:
            results.append({"error": str(e)})

    # Update the pending tool result with all execution results
    result_content = json.dumps(results, ensure_ascii=False, default=str)
    _update_last_tool_result(agent, result_content)

    return {"success": True, "results": results}


@router.post("/{session_id}/skip-all", response_model=SuccessResponse)
async def skip_all_operations(session_id: int):
    state = get_app_state()
    try:
        agent = state.get_or_create_agent(session_id)
        agent.clear_pending_operations()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Update the pending tool result to indicate skip
    _update_last_tool_result(agent, json.dumps({"status": "skipped", "message": "Operation skipped by user"}))

    return SuccessResponse(message="All pending operations skipped")


@router.post("/{session_id}/upload")
async def upload_file(session_id: int, file: UploadFile = File(...)):
    state = get_app_state()
    try:
        agent = state.get_or_create_agent(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    content = await file.read()
    text_content = content.decode("utf-8", errors="replace")

    # Add file content to conversation as context
    context_message = f"[File uploaded: {file.filename}]\n\n{text_content}"
    agent.conversation_history.append({
        "role": "user",
        "content": context_message,
    })
    if agent.storage and agent.session_id:
        agent._save_message("user", context_message, None, None)

    return {
        "success": True,
        "filename": file.filename,
        "size": len(content),
        "message": f"File '{file.filename}' loaded into conversation context",
    }


@router.post("/{session_id}/start-migration")
async def start_migration(session_id: int, req: StartMigrationRequest):
    """
    Start a migration task from the inline MigrationCard.

    Creates a MigrationTask, sets auto_execute flag on the agent,
    and returns the instruction text for the AI to proceed.
    """
    state = get_app_state()

    try:
        agent = state.get_or_create_agent(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    storage = state.storage

    # Validate connections
    source_conn = storage.get_connection_by_id(req.source_connection_id)
    target_conn = storage.get_connection_by_id(req.target_connection_id)
    if not source_conn:
        raise HTTPException(status_code=400, detail="Source connection not found")
    if not target_conn:
        raise HTTPException(status_code=400, detail="Target connection not found")

    # Create migration task
    from datetime import datetime
    now = datetime.now()
    task_name = f"{source_conn.db_type}→{target_conn.db_type} {now.strftime('%Y%m%d_%H%M%S')}"
    task = MigrationTask(
        id=None,
        name=task_name,
        source_connection_id=req.source_connection_id,
        target_connection_id=req.target_connection_id,
        source_db_type=source_conn.db_type,
        target_db_type=target_conn.db_type,
        status="pending",
        total_items=0,
        completed_items=0,
        failed_items=0,
        skipped_items=0,
        source_schema=req.source_schema,
        target_schema=req.target_schema,
        options=None,
        analysis_result=None,
        error_message=None,
        started_at=None,
        completed_at=None,
        created_at=now,
        updated_at=now,
    )
    task_id = storage.create_migration_task(task)

    # Set auto-execute mode if requested
    if req.auto_execute:
        agent.migration_auto_execute = True

    # Build instruction for the AI
    source_schema = req.source_schema or "default"
    from db_agent.i18n import t
    instruction = t(
        "migrate_online_instruction",
        task_id=task_id,
        source_name=source_conn.name,
        source_type=source_conn.db_type,
        target_name=target_conn.name,
        target_type=target_conn.db_type,
        source_schema=source_schema,
    )

    return {
        "success": True,
        "task_id": task_id,
        "instruction": instruction,
    }


@router.post("/{session_id}/submit-form")
async def submit_form_input(session_id: int, req: SubmitFormRequest):
    """
    Submit user-filled form data back to the AI conversation.

    Updates the last tool result in conversation history with the form data,
    so the AI can continue processing.
    """
    state = get_app_state()

    try:
        agent = state.get_or_create_agent(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Update the last tool result (form_input_requested) with the submitted values
    result_content = json.dumps({"status": "success", "form_data": req.values}, ensure_ascii=False)
    _update_last_tool_result(agent, result_content)

    return {
        "success": True,
        "instruction": f"User submitted form: {json.dumps(req.values, ensure_ascii=False)}",
    }
