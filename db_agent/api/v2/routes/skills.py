"""
Skills management endpoints.
"""
import logging
from typing import List

from fastapi import APIRouter, HTTPException

from ..deps import get_app_state
from ..models import SkillResponse, SkillDetailResponse, SkillExecuteRequest, SuccessResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=List[SkillResponse])
async def list_skills():
    state = get_app_state()
    skills = state.skill_registry.list_all()
    return [
        SkillResponse(
            name=s.name,
            description=s.description or "",
            source=s.source,
            user_invocable=s.is_user_invocable,
            model_invocable=s.is_model_invocable,
        )
        for s in skills
    ]


@router.post("/reload", response_model=SuccessResponse)
async def reload_skills():
    state = get_app_state()
    state.skill_registry.reload()
    return SuccessResponse(message=f"Reloaded {state.skill_registry.count} skills")


@router.get("/{name}", response_model=SkillDetailResponse)
async def get_skill_detail(name: str):
    state = get_app_state()
    skill = state.skill_registry.get(name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{name}' not found")
    return SkillDetailResponse(
        name=skill.name,
        description=skill.description or "",
        source=skill.source,
        user_invocable=skill.is_user_invocable,
        model_invocable=skill.is_model_invocable,
        instructions=skill.instructions,
    )


@router.post("/{name}/execute")
async def execute_skill(name: str, req: SkillExecuteRequest):
    state = get_app_state()
    skill = state.skill_registry.get(name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{name}' not found")

    return {
        "success": True,
        "skill": name,
        "instructions": skill.instructions,
        "message": f"Skill '{name}' instructions loaded. Use in chat to execute.",
    }
