"""
Health check endpoint.
"""
from datetime import datetime

from fastapi import APIRouter

from ..deps import get_app_state
from ..models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    state = get_app_state()
    return HealthResponse(
        status="healthy",
        active_sessions=len(state._agents),
        total_connections=len(state.storage.list_connections()),
        total_providers=len(state.storage.list_providers()),
        mcp_servers=len(state.mcp_manager.list_connected_servers()),
        skills_loaded=state.skill_registry.count,
        timestamp=datetime.now().isoformat(),
    )
