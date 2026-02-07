"""
db_agent/mcp/servers/mysql.py

MySQL MCP Server

Standalone MCP server for MySQL database operations.

Usage:
    # Start without pre-connection (connect dynamically via connect tool)
    python -m db_agent.mcp.servers.mysql

    # Start with pre-connection
    python -m db_agent.mcp.servers.mysql --host localhost --database mydb --user root

    # Use environment variables for password
    MYSQL_PWD=secret python -m db_agent.mcp.servers.mysql --host localhost --database mydb

Claude Desktop configuration:
{
  "mcpServers": {
    "mysql": {
      "command": "python",
      "args": ["-m", "db_agent.mcp.servers.mysql"]
    }
  }
}

With pre-connection:
{
  "mcpServers": {
    "mysql": {
      "command": "python",
      "args": [
        "-m", "db_agent.mcp.servers.mysql",
        "--host", "localhost",
        "--database", "mydb",
        "--user", "root"
      ],
      "env": {
        "MYSQL_PWD": "your_password"
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
    parser = argparse.ArgumentParser(description='MySQL MCP Server')
    parser.add_argument('--host', default='localhost', help='Database host (default: localhost)')
    parser.add_argument('--port', type=int, default=3306, help='Database port (default: 3306)')
    parser.add_argument('--database', help='Database name')
    parser.add_argument('--user', help='Database user')
    parser.add_argument('--password', help='Database password (prefer MYSQL_PWD env var)')
    args = parser.parse_args()

    db_tools = None

    # Pre-connect if database is specified
    if args.database:
        from db_agent.core.database import DatabaseToolsFactory

        config = {
            "host": args.host,
            "port": args.port,
            "database": args.database,
            "user": args.user or os.environ.get("MYSQL_USER", "root"),
            "password": args.password or os.environ.get("MYSQL_PWD", "")
        }
        try:
            db_tools = DatabaseToolsFactory.create("mysql", config)
            info = db_tools.get_db_info()
            print(f"Pre-connected to MySQL: {info.get('version', 'unknown')}", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Could not pre-connect: {e}", file=sys.stderr)

    mcp = create_db_mcp_server("mysql", "mysql", db_tools)
    mcp.run()


if __name__ == "__main__":
    main()
