"""
V2 API Router factory with startup/shutdown hooks.
"""
import logging
from fastapi import APIRouter

from .routes.connections import router as connections_router
from .routes.providers import router as providers_router
from .routes.sessions import router as sessions_router
from .routes.chat import router as chat_router
from .routes.mcp import router as mcp_router
from .routes.skills import router as skills_router
from .routes.migration import router as migration_router
from .routes.settings import router as settings_router
from .routes.audit import router as audit_router
from .routes.health import router as health_router

logger = logging.getLogger(__name__)


def create_v2_router() -> APIRouter:
    """
    Create the v2 API router with all sub-routers mounted.
    """
    router = APIRouter()

    router.include_router(connections_router, prefix="/connections", tags=["Connections"])
    router.include_router(providers_router, prefix="/providers", tags=["Providers"])
    router.include_router(sessions_router, prefix="/sessions", tags=["Sessions"])
    router.include_router(chat_router, prefix="/chat", tags=["Chat"])
    router.include_router(mcp_router, prefix="/mcp", tags=["MCP"])
    router.include_router(skills_router, prefix="/skills", tags=["Skills"])
    router.include_router(migration_router, prefix="/migration", tags=["Migration"])
    router.include_router(settings_router, prefix="/settings", tags=["Settings"])
    router.include_router(audit_router, prefix="/audit", tags=["Audit"])
    router.include_router(health_router, tags=["Health"])

    logger.info("V2 API router created with all sub-routers")
    return router
