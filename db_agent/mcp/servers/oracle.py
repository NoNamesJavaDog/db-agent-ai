"""
db_agent/mcp/servers/oracle.py

Oracle MCP Server

Standalone MCP server for Oracle database operations.

Usage:
    # Start without pre-connection (connect dynamically via connect tool)
    python -m db_agent.mcp.servers.oracle

    # Start with pre-connection (using service name)
    python -m db_agent.mcp.servers.oracle --host localhost --service-name ORCL --user system

    # Start with pre-connection (using SID)
    python -m db_agent.mcp.servers.oracle --host localhost --database ORCL --user system

Claude Desktop configuration:
{
  "mcpServers": {
    "oracle": {
      "command": "python",
      "args": ["-m", "db_agent.mcp.servers.oracle"]
    }
  }
}

With pre-connection:
{
  "mcpServers": {
    "oracle": {
      "command": "python",
      "args": [
        "-m", "db_agent.mcp.servers.oracle",
        "--host", "localhost",
        "--service-name", "ORCL",
        "--user", "system"
      ],
      "env": {
        "ORACLE_PASSWORD": "your_password"
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
    parser = argparse.ArgumentParser(description='Oracle MCP Server')
    parser.add_argument('--host', default='localhost', help='Database host (default: localhost)')
    parser.add_argument('--port', type=int, default=1521, help='Database port (default: 1521)')
    parser.add_argument('--database', help='Database SID')
    parser.add_argument('--service-name', help='Oracle service name (preferred over SID)')
    parser.add_argument('--user', help='Database user')
    parser.add_argument('--password', help='Database password (prefer ORACLE_PASSWORD env var)')
    args = parser.parse_args()

    db_tools = None

    # Pre-connect if database or service-name is specified
    database = args.service_name or args.database
    if database:
        from db_agent.core.database import DatabaseToolsFactory

        config = {
            "host": args.host,
            "port": args.port,
            "database": database,
            "user": args.user or os.environ.get("ORACLE_USER", "system"),
            "password": args.password or os.environ.get("ORACLE_PASSWORD", ""),
            "service_name": args.service_name  # Pass service_name if specified
        }
        try:
            db_tools = DatabaseToolsFactory.create("oracle", config)
            info = db_tools.get_db_info()
            print(f"Pre-connected to Oracle: {info.get('version', 'unknown')}", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Could not pre-connect: {e}", file=sys.stderr)

    mcp = create_db_mcp_server("oracle", "oracle", db_tools)
    mcp.run()


if __name__ == "__main__":
    main()
