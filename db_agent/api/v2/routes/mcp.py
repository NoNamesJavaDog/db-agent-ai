"""
MCP server management endpoints.
"""
import json
import logging
from typing import List

from fastapi import APIRouter, HTTPException

from db_agent.mcp.config import MCPServerConfig
from db_agent.storage.models import MCPServer
from ..deps import get_app_state
from ..models import McpServerCreate, McpServerResponse, McpToolResponse, McpStatusResponse, SuccessResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def _build_server_response(server_dict: dict, state) -> McpServerResponse:
    name = server_dict.get("name", "")
    connected = name in state.mcp_manager.clients
    tool_count = len(state.mcp_manager.get_server_tools(name)) if connected else 0
    args = server_dict.get("args", [])
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except (json.JSONDecodeError, TypeError):
            args = []
    env = server_dict.get("env")
    if isinstance(env, str):
        try:
            env = json.loads(env)
        except (json.JSONDecodeError, TypeError):
            env = None

    return McpServerResponse(
        id=server_dict.get("id"),
        name=name,
        command=server_dict.get("command", ""),
        args=args,
        env=env,
        enabled=server_dict.get("enabled", True),
        connected=connected,
        tool_count=tool_count,
        created_at=server_dict.get("created_at"),
        updated_at=server_dict.get("updated_at"),
    )


@router.get("/servers", response_model=List[McpServerResponse])
async def list_mcp_servers():
    state = get_app_state()
    servers = state.storage.list_mcp_servers(enabled_only=False)
    return [_build_server_response(s, state) for s in servers]


@router.post("/servers", response_model=McpServerResponse)
async def add_mcp_server(req: McpServerCreate):
    state = get_app_state()

    from datetime import datetime
    now = datetime.now()
    server = MCPServer(
        id=None,
        name=req.name,
        command=req.command,
        args=json.dumps(req.args),
        env=json.dumps(req.env) if req.env else None,
        enabled=True,
        created_at=now,
        updated_at=now,
    )
    try:
        server_id = state.storage.add_mcp_server(server)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return McpServerResponse(
        id=server_id,
        name=req.name,
        command=req.command,
        args=req.args,
        env=req.env,
        enabled=True,
        connected=False,
        tool_count=0,
    )


@router.delete("/servers/{name}", response_model=SuccessResponse)
async def delete_mcp_server(name: str):
    state = get_app_state()
    # Disconnect first
    try:
        state.mcp_manager.remove_server_sync(name)
    except Exception:
        pass
    if not state.storage.delete_mcp_server(name):
        raise HTTPException(status_code=404, detail="MCP server not found")
    return SuccessResponse(message=f"MCP server '{name}' deleted")


@router.post("/servers/{name}/enable", response_model=SuccessResponse)
async def enable_mcp_server(name: str):
    state = get_app_state()
    if not state.storage.enable_mcp_server(name, True):
        raise HTTPException(status_code=404, detail="MCP server not found")
    return SuccessResponse(message=f"MCP server '{name}' enabled")


@router.post("/servers/{name}/disable", response_model=SuccessResponse)
async def disable_mcp_server(name: str):
    state = get_app_state()
    # Disconnect if connected
    try:
        state.mcp_manager.remove_server_sync(name)
    except Exception:
        pass
    if not state.storage.enable_mcp_server(name, False):
        raise HTTPException(status_code=404, detail="MCP server not found")
    return SuccessResponse(message=f"MCP server '{name}' disabled")


@router.post("/servers/{name}/connect", response_model=SuccessResponse)
async def connect_mcp_server(name: str):
    state = get_app_state()
    server = state.storage.get_mcp_server(name)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")

    server_dict = server.to_dict() if hasattr(server, 'to_dict') else server
    args = server_dict.get("args", [])
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except (json.JSONDecodeError, TypeError):
            args = []
    env = server_dict.get("env")
    if isinstance(env, str):
        try:
            env = json.loads(env)
        except (json.JSONDecodeError, TypeError):
            env = None

    config = MCPServerConfig(
        name=name,
        command=server_dict.get("command", ""),
        args=args,
        env=env or {},
    )
    try:
        state.mcp_manager.add_server_sync(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect: {e}")
    return SuccessResponse(message=f"Connected to MCP server '{name}'")


@router.get("/servers/{name}/tools", response_model=List[McpToolResponse])
async def get_server_tools(name: str):
    state = get_app_state()
    if name not in state.mcp_manager.clients:
        raise HTTPException(status_code=404, detail="Server not connected")
    tools = state.mcp_manager.get_server_tools(name)
    return [
        McpToolResponse(
            name=t.get("function", {}).get("name", t.get("name", "")),
            description=t.get("function", {}).get("description", t.get("description", "")),
            server_name=name,
            input_schema=t.get("function", {}).get("parameters"),
        )
        for t in tools
    ]


@router.get("/tools", response_model=List[McpToolResponse])
async def get_all_mcp_tools():
    state = get_app_state()
    all_tools = state.mcp_manager.get_all_tools()
    result = []
    for t in all_tools:
        tool_name = t.get("function", {}).get("name", t.get("name", ""))
        server_name = state.mcp_manager._tool_map.get(tool_name, "")
        result.append(McpToolResponse(
            name=tool_name,
            description=t.get("function", {}).get("description", t.get("description", "")),
            server_name=server_name,
            input_schema=t.get("function", {}).get("parameters"),
        ))
    return result


@router.get("/status", response_model=McpStatusResponse)
async def get_mcp_status():
    state = get_app_state()
    servers = state.storage.list_mcp_servers(enabled_only=False)
    server_responses = [_build_server_response(s, state) for s in servers]
    total_tools = len(state.mcp_manager.get_all_tools())
    return McpStatusResponse(servers=server_responses, total_tools=total_tools)


@router.get("/health")
async def mcp_health_check():
    state = get_app_state()
    try:
        health = state.mcp_manager.health_check_all_sync()
    except Exception:
        health = {}
    return {"servers": health}
