"""
Pydantic request/response models for v2 API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ─── Connection Models ────────────────────────────────────────────────────

class ConnectionCreate(BaseModel):
    name: str = Field(..., description="Connection name (unique)")
    db_type: str = Field(..., description="Database type: postgresql, mysql, gaussdb, oracle, sqlserver")
    host: str = Field(default="localhost")
    port: int = Field(..., description="Database port")
    database: str = Field(..., description="Database name")
    username: str = Field(..., description="Database user")
    password: str = Field(..., description="Database password (plaintext, will be encrypted)")


class ConnectionUpdate(BaseModel):
    name: Optional[str] = None
    db_type: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class ConnectionResponse(BaseModel):
    id: int
    name: str
    db_type: str
    host: str
    port: int
    database: str
    username: str
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ConnectionTestResult(BaseModel):
    success: bool
    message: str
    db_info: Optional[Dict[str, Any]] = None


# ─── Provider Models ──────────────────────────────────────────────────────

class ProviderCreate(BaseModel):
    name: str = Field(..., description="Provider name (unique)")
    provider: str = Field(..., description="Provider type: openai, deepseek, claude, gemini, qwen, ollama")
    api_key: str = Field(..., description="API key (plaintext, will be encrypted)")
    model: Optional[str] = Field(default=None, description="Model name (uses default if not provided)")
    base_url: Optional[str] = Field(default=None, description="Custom base URL")


class ProviderUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None


class ProviderResponse(BaseModel):
    id: int
    name: str
    provider: str
    model: str
    base_url: Optional[str] = None
    is_default: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AvailableProvider(BaseModel):
    key: str
    name: str
    default_model: str
    base_url: Optional[str] = None


# ─── Session Models ───────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    name: Optional[str] = Field(default=None, description="Session name (auto-generated if not provided)")
    connection_id: Optional[int] = Field(default=None, description="Database connection ID")
    provider_id: Optional[int] = Field(default=None, description="LLM provider ID")


class SessionRename(BaseModel):
    name: str = Field(..., description="New session name")


class SessionResponse(BaseModel):
    id: int
    name: str
    connection_id: Optional[int] = None
    provider_id: Optional[int] = None
    is_current: bool
    message_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class MessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: Optional[str] = None
    tool_calls: Optional[str] = None
    tool_call_id: Optional[str] = None
    created_at: Optional[str] = None


# ─── Chat Models ──────────────────────────────────────────────────────────

class ChatMessageRequest(BaseModel):
    message: str = Field(..., description="User message")


class PendingOperation(BaseModel):
    index: int
    type: str
    sql: Optional[str] = None
    description: Optional[str] = None


class ConfirmRequest(BaseModel):
    index: int = Field(..., description="Pending operation index to confirm")


class SubmitFormRequest(BaseModel):
    values: Dict[str, Any] = Field(..., description="Form field values submitted by the user")


# ─── MCP Models ───────────────────────────────────────────────────────────

class McpServerCreate(BaseModel):
    name: str = Field(..., description="Server name (unique)")
    command: str = Field(..., description="Command to start server (npx, python, node, etc.)")
    args: List[str] = Field(default_factory=list, description="Command arguments")
    env: Optional[Dict[str, str]] = Field(default=None, description="Environment variables")


class McpServerResponse(BaseModel):
    id: Optional[int] = None
    name: str
    command: str
    args: List[str] = []
    env: Optional[Dict[str, str]] = None
    enabled: bool = True
    connected: bool = False
    tool_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class McpToolResponse(BaseModel):
    name: str
    description: str = ""
    server_name: str = ""
    input_schema: Optional[Dict[str, Any]] = None


class McpStatusResponse(BaseModel):
    servers: List[McpServerResponse]
    total_tools: int = 0


# ─── Skills Models ────────────────────────────────────────────────────────

class SkillResponse(BaseModel):
    name: str
    description: str = ""
    source: str = ""
    user_invocable: bool = True
    model_invocable: bool = True


class SkillDetailResponse(SkillResponse):
    instructions: str = ""


class SkillExecuteRequest(BaseModel):
    parameters: Optional[Dict[str, Any]] = None


# ─── Migration Models ─────────────────────────────────────────────────────

class MigrationTaskCreate(BaseModel):
    name: str = Field(..., description="Task name")
    source_connection_id: int
    target_connection_id: int
    source_schema: Optional[str] = None
    target_schema: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


class MigrationTaskResponse(BaseModel):
    id: int
    name: str
    source_connection_id: int
    target_connection_id: int
    source_db_type: str
    target_db_type: str
    status: str
    total_items: int = 0
    completed_items: int = 0
    failed_items: int = 0
    skipped_items: int = 0
    source_schema: Optional[str] = None
    target_schema: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class MigrationItemResponse(BaseModel):
    id: int
    task_id: int
    object_type: str
    object_name: str
    schema_name: Optional[str] = None
    execution_order: int = 0
    status: str = "pending"
    source_ddl: Optional[str] = None
    target_ddl: Optional[str] = None
    conversion_notes: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    executed_at: Optional[str] = None
    created_at: Optional[str] = None


# ─── Start Migration Request ─────────────────────────────────────────────

class StartMigrationRequest(BaseModel):
    source_connection_id: int = Field(..., description="Source database connection ID")
    target_connection_id: int = Field(..., description="Target database connection ID")
    source_schema: Optional[str] = Field(default=None, description="Source schema name")
    target_schema: Optional[str] = Field(default=None, description="Target schema name")
    auto_execute: bool = Field(default=True, description="Auto-execute SQL without per-statement confirmation")


# ─── Settings Models ──────────────────────────────────────────────────────

class SettingsResponse(BaseModel):
    language: str = "zh"
    theme: str = "light"


class SettingsUpdate(BaseModel):
    language: Optional[str] = None
    theme: Optional[str] = None


# ─── Audit Models ─────────────────────────────────────────────────────────

class AuditLogResponse(BaseModel):
    id: int
    session_id: Optional[int] = None
    connection_id: Optional[int] = None
    category: str
    action: str
    target_type: Optional[str] = None
    target_name: Optional[str] = None
    sql_text: Optional[str] = None
    result_status: str
    result_summary: Optional[str] = None
    affected_rows: Optional[int] = None
    execution_time_ms: Optional[int] = None
    user_confirmed: bool = False
    created_at: Optional[str] = None


# ─── Health Models ────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "healthy"
    active_sessions: int = 0
    total_connections: int = 0
    total_providers: int = 0
    mcp_servers: int = 0
    skills_loaded: int = 0
    timestamp: str


# ─── Generic Models ───────────────────────────────────────────────────────

class SwitchDatabaseRequest(BaseModel):
    database: str = Field(..., description="Target database name to switch to")


class DatabaseListResponse(BaseModel):
    databases: List[Dict[str, Any]]
    current_database: str
    instance: str


class SuccessResponse(BaseModel):
    success: bool = True
    message: str = ""
