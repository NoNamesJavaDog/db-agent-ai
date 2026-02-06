"""
MCP (Model Context Protocol) Module for db-agent-ai

This module provides:
1. MCP Client - Connect to external MCP servers to extend agent's toolset
2. MCP Server - Expose db-agent's database tools as MCP service for Claude Desktop

Architecture:
- MCPClient: Wraps MCP SDK to communicate with external MCP servers
- MCPManager: Manages multiple MCP client connections
- MCPServerConfig: Configuration dataclass for MCP server connections
- server.py: FastMCP-based server exposing database tools
"""

from .config import MCPServerConfig
from .client import MCPClient
from .manager import MCPManager

__all__ = [
    'MCPServerConfig',
    'MCPClient',
    'MCPManager',
]
