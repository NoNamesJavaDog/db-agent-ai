"""
Migration task management endpoints.
"""
import json
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from db_agent.storage.models import MigrationTask
from ..deps import get_app_state
from ..models import MigrationTaskCreate, MigrationTaskResponse, MigrationItemResponse, SuccessResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def _task_to_response(task: MigrationTask) -> MigrationTaskResponse:
    return MigrationTaskResponse(
        id=task.id,
        name=task.name,
        source_connection_id=task.source_connection_id,
        target_connection_id=task.target_connection_id,
        source_db_type=task.source_db_type,
        target_db_type=task.target_db_type,
        status=task.status,
        total_items=task.total_items,
        completed_items=task.completed_items,
        failed_items=task.failed_items,
        skipped_items=task.skipped_items,
        source_schema=task.source_schema,
        target_schema=task.target_schema,
        error_message=task.error_message,
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        created_at=task.created_at.isoformat() if task.created_at else None,
        updated_at=task.updated_at.isoformat() if task.updated_at else None,
    )


@router.get("/tasks", response_model=List[MigrationTaskResponse])
async def list_migration_tasks(
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=50),
):
    state = get_app_state()
    tasks = state.storage.list_migration_tasks(status=status, limit=limit)
    return [_task_to_response(t) for t in tasks]


@router.post("/tasks", response_model=MigrationTaskResponse)
async def create_migration_task(req: MigrationTaskCreate):
    state = get_app_state()

    # Resolve source and target db types
    source_conn = state.storage.get_connection_by_id(req.source_connection_id)
    target_conn = state.storage.get_connection_by_id(req.target_connection_id)

    if not source_conn:
        raise HTTPException(status_code=400, detail="Source connection not found")
    if not target_conn:
        raise HTTPException(status_code=400, detail="Target connection not found")

    now = datetime.now()
    task = MigrationTask(
        id=None,
        name=req.name,
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
        options=json.dumps(req.options) if req.options else None,
        analysis_result=None,
        error_message=None,
        started_at=None,
        completed_at=None,
        created_at=now,
        updated_at=now,
    )

    try:
        task_id = state.storage.create_migration_task(task)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    task.id = task_id
    return _task_to_response(task)


@router.get("/tasks/{task_id}", response_model=MigrationTaskResponse)
async def get_migration_task(task_id: int):
    state = get_app_state()
    task = state.storage.get_migration_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Migration task not found")
    return _task_to_response(task)


@router.delete("/tasks/{task_id}", response_model=SuccessResponse)
async def delete_migration_task(task_id: int):
    state = get_app_state()
    if not state.storage.delete_migration_task(task_id):
        raise HTTPException(status_code=404, detail="Migration task not found")
    return SuccessResponse(message="Migration task deleted")


@router.get("/tasks/{task_id}/items", response_model=List[MigrationItemResponse])
async def get_migration_items(
    task_id: int,
    status: Optional[str] = Query(default=None),
):
    state = get_app_state()
    items = state.storage.get_migration_items(task_id, status=status)
    return [
        MigrationItemResponse(
            id=item.id,
            task_id=item.task_id,
            object_type=item.object_type,
            object_name=item.object_name,
            schema_name=item.schema_name,
            execution_order=item.execution_order,
            status=item.status,
            source_ddl=item.source_ddl,
            target_ddl=item.target_ddl,
            conversion_notes=item.conversion_notes,
            error_message=item.error_message,
            retry_count=item.retry_count,
            executed_at=item.executed_at.isoformat() if item.executed_at else None,
            created_at=item.created_at.isoformat() if item.created_at else None,
        )
        for item in items
    ]
