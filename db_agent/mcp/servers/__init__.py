"""
Database-specific MCP Servers

Each database type has its own MCP server that can be started independently.

Available servers:
- postgresql: PostgreSQL MCP Server
- mysql: MySQL MCP Server
- oracle: Oracle MCP Server
- sqlserver: SQL Server MCP Server
- gaussdb: GaussDB MCP Server

Usage:
    # Start PostgreSQL MCP server
    python -m db_agent.mcp.servers.postgresql

    # Start with pre-connection
    python -m db_agent.mcp.servers.postgresql --host localhost --database mydb --user postgres
"""

from .base import create_db_mcp_server

__all__ = ['create_db_mcp_server']
