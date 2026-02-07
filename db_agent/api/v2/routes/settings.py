"""
Settings management endpoints.
"""
import logging

from fastapi import APIRouter

from ..deps import get_app_state
from ..models import SettingsResponse, SettingsUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=SettingsResponse)
async def get_settings():
    state = get_app_state()
    language = state.storage.get_preference("language") or "zh"
    theme = state.storage.get_preference("theme") or "light"
    return SettingsResponse(language=language, theme=theme)


@router.put("", response_model=SettingsResponse)
async def update_settings(req: SettingsUpdate):
    state = get_app_state()
    if req.language is not None:
        state.storage.set_preference("language", req.language)
    if req.theme is not None:
        state.storage.set_preference("theme", req.theme)

    language = state.storage.get_preference("language") or "zh"
    theme = state.storage.get_preference("theme") or "light"
    return SettingsResponse(language=language, theme=theme)
