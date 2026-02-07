"""
Session management endpoints.
"""
import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException

from ..deps import get_app_state
from ..models import (
    SessionCreate, SessionRename, SessionResponse,
    MessageResponse, SuccessResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=List[SessionResponse])
async def list_sessions():
    state = get_app_state()
    sessions = state.storage.list_sessions()
    result = []
    for s in sessions:
        # Count only user messages for meaningful display
        all_msgs = state.storage.get_session_messages(s.id)
        msg_count = len([m for m in all_msgs if m.role == 'user'])
        result.append(SessionResponse(
            id=s.id,
            name=s.name,
            connection_id=s.connection_id,
            provider_id=s.provider_id,
            is_current=s.is_current,
            message_count=msg_count,
            created_at=s.created_at.isoformat() if s.created_at else None,
            updated_at=s.updated_at.isoformat() if s.updated_at else None,
        ))
    return result


@router.post("", response_model=SessionResponse)
async def create_session(req: SessionCreate):
    state = get_app_state()

    name = req.name or f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    # Use provided IDs or fall back to active/default
    connection_id = req.connection_id
    provider_id = req.provider_id

    if not connection_id:
        conn = state.storage.get_active_connection()
        connection_id = conn.id if conn else None

    if not provider_id:
        prov = state.storage.get_default_provider()
        provider_id = prov.id if prov else None

    try:
        session_id = state.storage.create_session(name, connection_id, provider_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return SessionResponse(
        id=session_id,
        name=name,
        connection_id=connection_id,
        provider_id=provider_id,
        is_current=False,
        message_count=0,
        created_at=datetime.now().isoformat(),
    )


@router.delete("/{session_id}", response_model=SuccessResponse)
async def delete_session(session_id: int):
    state = get_app_state()
    if not state.storage.delete_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    state.evict_agent(session_id)
    return SuccessResponse(message="Session deleted")


@router.put("/{session_id}/rename", response_model=SuccessResponse)
async def rename_session(session_id: int, req: SessionRename):
    state = get_app_state()
    if not state.storage.rename_session(session_id, req.name):
        raise HTTPException(status_code=404, detail="Session not found")
    return SuccessResponse(message=f"Session renamed to '{req.name}'")


@router.post("/{session_id}/activate", response_model=SuccessResponse)
async def activate_session(session_id: int):
    state = get_app_state()
    if not state.storage.set_current_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return SuccessResponse(message="Session activated")


@router.get("/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(session_id: int):
    state = get_app_state()
    messages = state.storage.get_session_messages(session_id)
    return [
        MessageResponse(
            id=m.id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            tool_calls=m.tool_calls,
            tool_call_id=m.tool_call_id,
            created_at=m.created_at.isoformat() if m.created_at else None,
        )
        for m in messages
    ]


@router.post("/{session_id}/reset", response_model=SuccessResponse)
async def reset_session(session_id: int):
    state = get_app_state()
    try:
        agent = state.get_or_create_agent(session_id)
        agent.reset_conversation()
        state.evict_agent(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return SuccessResponse(message="Session conversation reset")
