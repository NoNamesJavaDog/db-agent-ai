"""
LLM Provider management endpoints.
"""
import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException

from db_agent.storage.models import LLMProvider
from db_agent.storage.encryption import encrypt
from db_agent.llm import LLMClientFactory
from ..deps import get_app_state
from ..models import (
    ProviderCreate, ProviderUpdate, ProviderResponse,
    AvailableProvider, SuccessResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _provider_to_response(p: LLMProvider) -> ProviderResponse:
    return ProviderResponse(
        id=p.id,
        name=p.name,
        provider=p.provider,
        model=p.model,
        base_url=p.base_url,
        is_default=p.is_default,
        created_at=p.created_at.isoformat() if p.created_at else None,
        updated_at=p.updated_at.isoformat() if p.updated_at else None,
    )


@router.get("", response_model=List[ProviderResponse])
async def list_providers():
    state = get_app_state()
    providers = state.storage.list_providers()
    return [_provider_to_response(p) for p in providers]


@router.post("", response_model=ProviderResponse)
async def create_provider(req: ProviderCreate):
    state = get_app_state()

    # Resolve default model if not provided
    provider_info = LLMClientFactory.PROVIDERS.get(req.provider)
    model = req.model or (provider_info["default_model"] if provider_info else "")

    now = datetime.now()
    provider = LLMProvider(
        id=None,
        name=req.name,
        provider=req.provider,
        api_key_encrypted=encrypt(req.api_key),
        model=model,
        base_url=req.base_url,
        is_default=False,
        created_at=now,
        updated_at=now,
    )
    try:
        pid = state.storage.add_provider(provider)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    provider.id = pid
    return _provider_to_response(provider)


@router.put("/{provider_id}", response_model=ProviderResponse)
async def update_provider(provider_id: int, req: ProviderUpdate):
    state = get_app_state()
    existing = state.storage.get_provider_by_id(provider_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Provider not found")

    if req.name is not None:
        existing.name = req.name
    if req.provider is not None:
        existing.provider = req.provider
    if req.api_key is not None:
        existing.api_key_encrypted = encrypt(req.api_key)
    if req.model is not None:
        existing.model = req.model
    if req.base_url is not None:
        existing.base_url = req.base_url
    existing.updated_at = datetime.now()

    if not state.storage.update_provider(existing):
        raise HTTPException(status_code=500, detail="Failed to update provider")
    return _provider_to_response(existing)


@router.delete("/{provider_id}", response_model=SuccessResponse)
async def delete_provider(provider_id: int):
    state = get_app_state()
    existing = state.storage.get_provider_by_id(provider_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Provider not found")

    if not state.storage.delete_provider(existing.name):
        raise HTTPException(status_code=500, detail="Failed to delete provider")
    return SuccessResponse(message=f"Provider '{existing.name}' deleted")


@router.post("/{provider_id}/activate", response_model=SuccessResponse)
async def activate_provider(provider_id: int):
    state = get_app_state()
    existing = state.storage.get_provider_by_id(provider_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Provider not found")

    if not state.storage.set_default_provider(existing.name):
        raise HTTPException(status_code=500, detail="Failed to activate provider")

    # Evict all cached agents so they rebuild with the new provider
    for sid in list(state._agents.keys()):
        state.evict_agent(sid)

    return SuccessResponse(message=f"Provider '{existing.name}' set as default")


@router.get("/available", response_model=List[AvailableProvider])
async def get_available_providers():
    result = []
    for key, info in LLMClientFactory.PROVIDERS.items():
        result.append(AvailableProvider(
            key=key,
            name=info["name"],
            default_model=info["default_model"],
            base_url=info.get("base_url"),
        ))
    return result
