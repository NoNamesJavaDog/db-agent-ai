"""
MCP Error Types

Provides structured error handling for MCP operations.
"""


class MCPError(Exception):
    """Base exception for MCP operations."""
    pass


class MCPConnectionError(MCPError):
    """Connection-related errors (retryable)."""

    def __init__(self, message: str, server_name: str = None, cause: Exception = None):
        self.server_name = server_name
        self.cause = cause
        super().__init__(message)


class MCPTimeoutError(MCPError):
    """Timeout errors (retryable)."""

    def __init__(self, message: str, server_name: str = None, timeout_seconds: float = None):
        self.server_name = server_name
        self.timeout_seconds = timeout_seconds
        super().__init__(message)


class MCPToolError(MCPError):
    """Tool execution errors (not retryable)."""

    def __init__(self, message: str, tool_name: str = None, server_name: str = None):
        self.tool_name = tool_name
        self.server_name = server_name
        super().__init__(message)
