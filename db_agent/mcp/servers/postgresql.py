"""
db_agent/mcp/servers/postgresql.py

PostgreSQL MCP Server

Standalone MCP server for PostgreSQL database operations.

Usage:
    # Start without pre-connection (connect dynamically via connect tool)
    python -m db_agent.mcp.servers.postgresql

    # Start with pre-connection
    python -m db_agent.mcp.servers.postgresql --host localhost --database mydb --user postgres

    # Use environment variables for password
    PGPASSWORD=secret python -m db_agent.mcp.servers.postgresql --host localhost --database mydb

Claude Desktop configuration:
{
  "mcpServers": {
    "postgresql": {
      "command": "python",
      "args": ["-m", "db_agent.mcp.servers.postgresql"]
    }
  }
}

With pre-connection:
{
  "mcpServers": {
    "postgresql": {
      "command": "python",
      "args": [
        "-m", "db_agent.mcp.servers.postgresql",
        "--host", "localhost",
        "--database", "mydb",
        "--user", "postgres"
      ],
      "env": {
        "PGPASSWORD": "your_password"
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
    parser = argparse.ArgumentParser(description='PostgreSQL MCP Server')
    parser.add_argument('--host', default='localhost', help='Database host (default: localhost)')
    parser.add_argument('--port', type=int, default=5432, help='Database port (default: 5432)')
    parser.add_argument('--database', help='Database name')
    parser.add_argument('--user', help='Database user')
    parser.add_argument('--password', help='Database password (prefer PGPASSWORD env var)')
    args = parser.parse_args()

    db_tools = None

    # Pre-connect if database is specified
    if args.database:
        from db_agent.core.database import DatabaseToolsFactory

        config = {
            "host": args.host,
            "port": args.port,
            "database": args.database,
            "user": args.user or os.environ.get("PGUSER", "postgres"),
            "password": args.password or os.environ.get("PGPASSWORD", "")
        }
        try:
            db_tools = DatabaseToolsFactory.create("postgresql", config)
            info = db_tools.get_db_info()
            print(f"Pre-connected to PostgreSQL: {info.get('version', 'unknown')}", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Could not pre-connect: {e}", file=sys.stderr)

    mcp = create_db_mcp_server("postgresql", "postgresql", db_tools)
    mcp.run()


if __name__ == "__main__":
    main()
