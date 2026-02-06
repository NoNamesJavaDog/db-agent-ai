"""
Data models for storage
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class DatabaseConnection:
    """Database connection configuration"""
    id: Optional[int]
    name: str                    # Connection name (unique identifier)
    db_type: str                 # postgresql, mysql, gaussdb, oracle, sqlserver
    host: str
    port: int
    database: str
    username: str
    password_encrypted: str      # Encrypted password
    is_active: bool              # Current active connection
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary for display (without password)"""
        return {
            'id': self.id,
            'name': self.name,
            'db_type': self.db_type,
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'username': self.username,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class LLMProvider:
    """LLM provider configuration"""
    id: Optional[int]
    name: str                    # Provider name (unique identifier)
    provider: str                # deepseek, openai, claude, gemini, qwen, ollama
    api_key_encrypted: str       # Encrypted API key
    model: str
    base_url: Optional[str]
    is_default: bool             # Default provider
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary for display (without API key)"""
        return {
            'id': self.id,
            'name': self.name,
            'provider': self.provider,
            'model': self.model,
            'base_url': self.base_url,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class Preference:
    """User preference setting"""
    key: str
    value: str


@dataclass
class Session:
    """Chat session"""
    id: Optional[int]
    name: str                      # Session name (e.g., "Session 2024-02-04 10:30")
    connection_id: Optional[int]   # Associated database connection ID
    provider_id: Optional[int]     # Associated LLM provider ID
    is_current: bool               # Whether this is the current active session
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary for display"""
        return {
            'id': self.id,
            'name': self.name,
            'connection_id': self.connection_id,
            'provider_id': self.provider_id,
            'is_current': self.is_current,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class ChatMessage:
    """Chat message in a session"""
    id: Optional[int]
    session_id: int                # Foreign key to sessions.id
    role: str                      # "user", "assistant", "tool"
    content: Optional[str]         # Message content
    tool_calls: Optional[str]      # JSON formatted tool calls (for assistant messages)
    tool_call_id: Optional[str]    # Tool call ID (for tool messages)
    created_at: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'tool_calls': self.tool_calls,
            'tool_call_id': self.tool_call_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class MigrationTask:
    """Database migration task"""
    id: Optional[int]
    name: str                          # Task name
    source_connection_id: int          # Source database connection ID
    target_connection_id: int          # Target database connection ID
    source_db_type: str                # Source database type
    target_db_type: str                # Target database type
    status: str                        # pending/analyzing/planning/confirmed/executing/completed/failed
    total_items: int                   # Total migration items
    completed_items: int               # Completed items count
    failed_items: int                  # Failed items count
    skipped_items: int                 # Skipped items count
    source_schema: Optional[str]       # Source schema
    target_schema: Optional[str]       # Target schema
    options: Optional[str]             # JSON: migration options
    analysis_result: Optional[str]     # JSON: analysis result
    error_message: Optional[str]       # Error message if failed
    started_at: Optional[datetime]     # Migration start time
    completed_at: Optional[datetime]   # Migration completion time
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary for display"""
        return {
            'id': self.id,
            'name': self.name,
            'source_connection_id': self.source_connection_id,
            'target_connection_id': self.target_connection_id,
            'source_db_type': self.source_db_type,
            'target_db_type': self.target_db_type,
            'status': self.status,
            'total_items': self.total_items,
            'completed_items': self.completed_items,
            'failed_items': self.failed_items,
            'skipped_items': self.skipped_items,
            'source_schema': self.source_schema,
            'target_schema': self.target_schema,
            'options': self.options,
            'analysis_result': self.analysis_result,
            'error_message': self.error_message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class MigrationItem:
    """Migration item (single database object)"""
    id: Optional[int]
    task_id: int                       # Foreign key to migration_tasks.id
    object_type: str                   # table/index/view/sequence/procedure/function/trigger
    object_name: str                   # Object name
    schema_name: Optional[str]         # Schema name
    execution_order: int               # Execution order
    depends_on: Optional[str]          # JSON: dependent objects
    status: str                        # pending/executing/completed/failed/skipped
    source_ddl: Optional[str]          # Source DDL
    target_ddl: Optional[str]          # Converted DDL for target
    conversion_notes: Optional[str]    # JSON: conversion notes
    execution_result: Optional[str]    # JSON: execution result
    error_message: Optional[str]       # Error message if failed
    retry_count: int                   # Retry count
    executed_at: Optional[datetime]    # Execution time
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary for display"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'object_type': self.object_type,
            'object_name': self.object_name,
            'schema_name': self.schema_name,
            'execution_order': self.execution_order,
            'depends_on': self.depends_on,
            'status': self.status,
            'source_ddl': self.source_ddl,
            'target_ddl': self.target_ddl,
            'conversion_notes': self.conversion_notes,
            'execution_result': self.execution_result,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class MCPServer:
    """MCP Server configuration"""
    id: Optional[int]
    name: str                          # Server name (unique identifier)
    command: str                       # Command to start server (npx, python, node, etc.)
    args: str                          # JSON serialized argument list
    env: Optional[str]                 # JSON serialized environment variables
    enabled: bool                      # Whether this server is enabled
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary for display"""
        import json
        return {
            'id': self.id,
            'name': self.name,
            'command': self.command,
            'args': json.loads(self.args) if self.args else [],
            'env': json.loads(self.env) if self.env else None,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class AuditLog:
    """Audit log record for tracking database operations and changes"""
    id: Optional[int]
    session_id: Optional[int]          # Associated session ID
    connection_id: Optional[int]       # Associated database connection ID
    category: str                      # sql_execute / tool_call / config_change
    action: str                        # Specific action (execute_sql, list_tables, add_connection, etc.)
    target_type: Optional[str]         # Target object type (table, index, connection, provider, etc.)
    target_name: Optional[str]         # Target object name
    sql_text: Optional[str]            # SQL statement (if applicable)
    parameters: Optional[str]          # JSON: operation parameters
    result_status: str                 # success / error / pending
    result_summary: Optional[str]      # Result summary (affected_rows, error_message, etc.)
    affected_rows: Optional[int]       # Number of affected rows
    execution_time_ms: Optional[int]   # Execution time in milliseconds
    user_confirmed: bool               # Whether user confirmed the operation
    created_at: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary for display"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'connection_id': self.connection_id,
            'category': self.category,
            'action': self.action,
            'target_type': self.target_type,
            'target_name': self.target_name,
            'sql_text': self.sql_text,
            'parameters': self.parameters,
            'result_status': self.result_status,
            'result_summary': self.result_summary,
            'affected_rows': self.affected_rows,
            'execution_time_ms': self.execution_time_ms,
            'user_confirmed': self.user_confirmed,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
