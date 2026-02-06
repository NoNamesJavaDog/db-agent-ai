"""
db_agent/mcp/servers/sqlserver.py

SQL Server MCP Server

Standalone MCP server for Microsoft SQL Server database operations.

Usage:
    # Start without pre-connection (connect dynamically via connect tool)
    python -m db_agent.mcp.servers.sqlserver

    # Start with pre-connection
    python -m db_agent.mcp.servers.sqlserver --host localhost --database master --user sa

    # Use Windows Authentication
    python -m db_agent.mcp.servers.sqlserver --host localhost --database master --trusted-connection

Claude Desktop configuration:
{
  "mcpServers": {
    "sqlserver": {
      "command": "python",
      "args": ["-m", "db_agent.mcp.servers.sqlserver"]
    }
  }
}

With pre-connection:
{
  "mcpServers": {
    "sqlserver": {
      "command": "python",
      "args": [
        "-m", "db_agent.mcp.servers.sqlserver",
        "--host", "localhost",
        "--database", "master",
        "--user", "sa"
      ],
      "env": {
        "MSSQL_PASSWORD": "your_password"
      }
    }
  }
}
"""

import argparse
import os
import sys

from .base import create_db_mcp_server


def main():
    parser = argparse.ArgumentParser(description='SQL Server MCP Server')
    parser.add_argument('--host', default='localhost', help='Database host (default: localhost)')
    parser.add_argument('--port', type=int, default=1433, help='Database port (default: 1433)')
    parser.add_argument('--database', help='Database name')
    parser.add_argument('--user', help='Database user')
    parser.add_argument('--password', help='Database password (prefer MSSQL_PASSWORD env var)')
    parser.add_argument('--trusted-connection', action='store_true',
                        help='Use Windows Authentication instead of SQL authentication')
    args = parser.parse_args()

    db_tools = None

    # Pre-connect if database is specified
    if args.database:
        from db_agent.core.database import DatabaseToolsFactory

        config = {
            "host": args.host,
            "port": args.port,
            "database": args.database,
            "user": args.user or os.environ.get("MSSQL_USER", "sa"),
            "password": args.password or os.environ.get("MSSQL_PASSWORD", ""),
            "trusted_connection": args.trusted_connection
        }
        try:
            db_tools = DatabaseToolsFactory.create("sqlserver", config)
            info = db_tools.get_db_info()
            print(f"Pre-connected to SQL Server: {info.get('version', 'unknown')}", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Could not pre-connect: {e}", file=sys.stderr)

    mcp = create_db_mcp_server("sqlserver", "sqlserver", db_tools)
    mcp.run()


if __name__ == "__main__":
    main()
