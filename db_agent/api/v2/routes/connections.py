"""
Connection management endpoints.
"""
import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException

from db_agent.storage.models import DatabaseConnection
from db_agent.storage.encryption import encrypt, decrypt
from db_agent.core.database import DatabaseToolsFactory
from ..deps import get_app_state
from ..models import (
    ConnectionCreate, ConnectionUpdate, ConnectionResponse, ConnectionTestResult,
    SuccessResponse, SwitchDatabaseRequest, DatabaseListResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _conn_to_response(conn: DatabaseConnection) -> ConnectionResponse:
    return ConnectionResponse(
        id=conn.id,
        name=conn.name,
        db_type=conn.db_type,
        host=conn.host,
        port=conn.port,
        database=conn.database,
        username=conn.username,
        is_active=conn.is_active,
        created_at=conn.created_at.isoformat() if conn.created_at else None,
        updated_at=conn.updated_at.isoformat() if conn.updated_at else None,
    )


@router.get("", response_model=List[ConnectionResponse])
async def list_connections():
    state = get_app_state()
    connections = state.storage.list_connections()
    return [_conn_to_response(c) for c in connections]


@router.post("", response_model=ConnectionResponse)
async def create_connection(req: ConnectionCreate):
    state = get_app_state()
    now = datetime.now()
    conn = DatabaseConnection(
        id=None,
        name=req.name,
        db_type=req.db_type,
        host=req.host,
        port=req.port,
        database=req.database,
        username=req.username,
        password_encrypted=encrypt(req.password),
        is_active=False,
        created_at=now,
        updated_at=now,
    )
    try:
        conn_id = state.storage.add_connection(conn)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    conn.id = conn_id
    return _conn_to_response(conn)


@router.put("/{conn_id}", response_model=ConnectionResponse)
async def update_connection(conn_id: int, req: ConnectionUpdate):
    state = get_app_state()
    existing = state.storage.get_connection_by_id(conn_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Connection not found")

    if req.name is not None:
        existing.name = req.name
    if req.db_type is not None:
        existing.db_type = req.db_type
    if req.host is not None:
        existing.host = req.host
    if req.port is not None:
        existing.port = req.port
    if req.database is not None:
        existing.database = req.database
    if req.username is not None:
        existing.username = req.username
    if req.password is not None:
        existing.password_encrypted = encrypt(req.password)
    existing.updated_at = datetime.now()

    if not state.storage.update_connection(existing):
        raise HTTPException(status_code=500, detail="Failed to update connection")

    # Evict cached agents that use this connection
    state.evict_agent(conn_id)
    return _conn_to_response(existing)


@router.delete("/{conn_id}", response_model=SuccessResponse)
async def delete_connection(conn_id: int):
    state = get_app_state()
    existing = state.storage.get_connection_by_id(conn_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Connection not found")

    if not state.storage.delete_connection(existing.name):
        raise HTTPException(status_code=500, detail="Failed to delete connection")
    return SuccessResponse(message=f"Connection '{existing.name}' deleted")


@router.post("/{conn_id}/activate", response_model=SuccessResponse)
async def activate_connection(conn_id: int):
    state = get_app_state()
    existing = state.storage.get_connection_by_id(conn_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Connection not found")

    if not state.storage.set_active_connection(existing.name):
        raise HTTPException(status_code=500, detail="Failed to activate connection")

    # Evict all cached agents so they rebuild with the new connection
    for sid in list(state._agents.keys()):
        state.evict_agent(sid)

    return SuccessResponse(message=f"Connection '{existing.name}' activated")


@router.post("/{conn_id}/test", response_model=ConnectionTestResult)
async def test_connection(conn_id: int):
    state = get_app_state()
    existing = state.storage.get_connection_by_id(conn_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Connection not found")

    db_config = {
        "host": existing.host,
        "port": existing.port,
        "database": existing.database,
        "user": existing.username,
        "password": decrypt(existing.password_encrypted),
    }
    try:
        db_tools = DatabaseToolsFactory.create(existing.db_type, db_config)
        # Actually test the connection by running a query
        conn = db_tools.get_connection()
        conn.close()
        db_info = db_tools.get_db_info()
        return ConnectionTestResult(success=True, message="Connection successful", db_info=db_info)
    except Exception as e:
        return ConnectionTestResult(success=False, message=str(e))


@router.get("/{conn_id}/databases", response_model=DatabaseListResponse)
async def list_databases(conn_id: int):
    """List all databases on the same server instance as this connection."""
    state = get_app_state()
    existing = state.storage.get_connection_by_id(conn_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Connection not found")

    db_config = {
        "host": existing.host,
        "port": existing.port,
        "database": existing.database,
        "user": existing.username,
        "password": decrypt(existing.password_encrypted),
    }
    try:
        db_tools = DatabaseToolsFactory.create(existing.db_type, db_config)
        result = db_tools.list_databases()
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        return DatabaseListResponse(
            databases=result.get("databases", []),
            current_database=result.get("current_database", ""),
            instance=result.get("instance", ""),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conn_id}/switch-db", response_model=ConnectionResponse)
async def switch_database(conn_id: int, req: SwitchDatabaseRequest):
    """Switch to another database on the same server instance.

    If a connection record already exists for the target database, activate it.
    Otherwise, auto-create a new connection record.
    """
    state = get_app_state()
    existing = state.storage.get_connection_by_id(conn_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Connection not found")

    # Check if a connection already exists for this instance + database
    found = state.storage.find_connection_for_instance_db(
        existing.db_type, existing.host, existing.port, existing.username, req.database
    )

    if found:
        state.storage.set_active_connection(found.name)
        found.is_active = True
        # Evict cached agents
        for sid in list(state._agents.keys()):
            state.evict_agent(sid)
        return _conn_to_response(found)

    # Auto-create a new connection
    new_name = f"{existing.name}__{req.database}"
    now = datetime.now()
    new_conn = DatabaseConnection(
        id=None,
        name=new_name,
        db_type=existing.db_type,
        host=existing.host,
        port=existing.port,
        database=req.database,
        username=existing.username,
        password_encrypted=existing.password_encrypted,
        is_active=False,
        created_at=now,
        updated_at=now,
    )
    try:
        new_id = state.storage.add_connection(new_conn)
        new_conn.id = new_id
        state.storage.set_active_connection(new_name)
        new_conn.is_active = True
        # Evict cached agents
        for sid in list(state._agents.keys()):
            state.evict_agent(sid)
        return _conn_to_response(new_conn)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
