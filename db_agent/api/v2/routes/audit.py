"""
Audit log endpoints.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Query

from ..deps import get_app_state
from ..models import AuditLogResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    category: Optional[str] = Query(default=None),
    session_id: Optional[int] = Query(default=None),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0),
):
    state = get_app_state()

    if session_id is not None:
        logs = state.audit_service.get_logs_by_session(session_id, limit=limit)
    elif category is not None:
        logs = state.audit_service.get_logs_by_category(category, limit=limit)
    else:
        logs = state.audit_service.get_recent_logs(limit=limit)

    return [
        AuditLogResponse(
            id=log.id,
            session_id=log.session_id,
            connection_id=log.connection_id,
            category=log.category,
            action=log.action,
            target_type=log.target_type,
            target_name=log.target_name,
            sql_text=log.sql_text,
            result_status=log.result_status,
            result_summary=log.result_summary,
            affected_rows=log.affected_rows,
            execution_time_ms=log.execution_time_ms,
            user_confirmed=log.user_confirmed,
            created_at=log.created_at.isoformat() if log.created_at else None,
        )
        for log in logs
    ]
