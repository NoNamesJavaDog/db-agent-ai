"""
MCP Server Implementation

Exposes db-agent's database tools as an MCP server for Claude Desktop
and other MCP-compatible clients.

Usage:
    # Start as MCP server (stdio mode)
    python -m db_agent.mcp.server --db-type postgresql --host localhost --database mydb

    # Or via CLI
    db-agent --mcp-server --db-type postgresql --host localhost --database mydb

Claude Desktop configuration example:
{
  "mcpServers": {
    "db-agent": {
      "command": "python",
      "args": ["-m", "db_agent.mcp.server", "--db-type", "postgresql", "--host", "localhost", "--database", "mydb"]
    }
  }
}
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Global database tools instance (set during initialization)
_db_tools = None


def get_db_tools():
    """Get the global database tools instance."""
    global _db_tools
    return _db_tools


def create_mcp_server():
    """
    Create and configure the MCP server with database tools.

    Returns:
        FastMCP server instance
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        raise ImportError("MCP SDK not installed. Install with: pip install mcp[cli]")

    mcp = FastMCP("db-agent")

    @mcp.tool()
    async def list_tables(schema: str = "public") -> str:
        """
        List all tables in the database.

        Args:
            schema: Schema name (default: public)

        Returns:
            JSON string with table list
        """
        db_tools = get_db_tools()
        if not db_tools:
            return json.dumps({"status": "error", "error": "Database not connected"})

        try:
            result = db_tools.list_tables(schema)
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e)})

    @mcp.tool()
    async def describe_table(table_name: str, schema: str = "public") -> str:
        """
        Get table structure including columns, indexes, and constraints.

        Args:
            table_name: Name of the table
            schema: Schema name (default: public)

        Returns:
            JSON string with table structure
        """
        db_tools = get_db_tools()
        if not db_tools:
            return json.dumps({"status": "error", "error": "Database not connected"})

        try:
            result = db_tools.describe_table(table_name, schema)
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e)})

    @mcp.tool()
    async def execute_query(sql: str) -> str:
        """
        Execute a SELECT query and return results.

        Only SELECT queries are allowed for safety.

        Args:
            sql: SQL SELECT query to execute

        Returns:
            JSON string with query results
        """
        db_tools = get_db_tools()
        if not db_tools:
            return json.dumps({"status": "error", "error": "Database not connected"})

        # Safety check: only allow SELECT queries
        sql_upper = sql.strip().upper()
        if not sql_upper.startswith("SELECT") and not sql_upper.startswith("WITH"):
            return json.dumps({
                "status": "error",
                "error": "Only SELECT queries are allowed. Use execute_query for read-only operations."
            })

        try:
            result = db_tools.execute_safe_query(sql)
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e)})

    @mcp.tool()
    async def run_explain(sql: str, analyze: bool = False) -> str:
        """
        Run EXPLAIN to analyze query execution plan.

        Args:
            sql: SQL query to analyze
            analyze: Whether to actually execute the query for real statistics (default: False)

        Returns:
            JSON string with execution plan
        """
        db_tools = get_db_tools()
        if not db_tools:
            return json.dumps({"status": "error", "error": "Database not connected"})

        try:
            result = db_tools.run_explain(sql, analyze)
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e)})

    @mcp.tool()
    async def get_sample_data(table_name: str, schema: str = "public", limit: int = 10) -> str:
        """
        Get sample data from a table.

        Args:
            table_name: Name of the table
            schema: Schema name (default: public)
            limit: Number of rows to return (default: 10)

        Returns:
            JSON string with sample data
        """
        db_tools = get_db_tools()
        if not db_tools:
            return json.dumps({"status": "error", "error": "Database not connected"})

        try:
            result = db_tools.get_sample_data(table_name, schema, limit)
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e)})

    @mcp.tool()
    async def identify_slow_queries(min_duration_ms: float = 1000, limit: int = 20) -> str:
        """
        Identify slow queries in the database.

        Args:
            min_duration_ms: Minimum average execution time in milliseconds (default: 1000)
            limit: Maximum number of results to return (default: 20)

        Returns:
            JSON string with slow query information
        """
        db_tools = get_db_tools()
        if not db_tools:
            return json.dumps({"status": "error", "error": "Database not connected"})

        try:
            result = db_tools.identify_slow_queries(min_duration_ms, limit)
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e)})

    @mcp.tool()
    async def get_table_stats(table_name: str, schema: str = "public") -> str:
        """
        Get table statistics including size, row estimates, and index information.

        Args:
            table_name: Name of the table
            schema: Schema name (default: public)

        Returns:
            JSON string with table statistics
        """
        db_tools = get_db_tools()
        if not db_tools:
            return json.dumps({"status": "error", "error": "Database not connected"})

        try:
            result = db_tools.get_table_stats(table_name, schema)
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e)})

    @mcp.tool()
    async def check_index_usage(table_name: str, schema: str = "public") -> str:
        """
        Check index usage for a table.

        Args:
            table_name: Name of the table
            schema: Schema name (default: public)

        Returns:
            JSON string with index usage information
        """
        db_tools = get_db_tools()
        if not db_tools:
            return json.dumps({"status": "error", "error": "Database not connected"})

        try:
            result = db_tools.check_index_usage(table_name, schema)
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e)})

    @mcp.tool()
    async def get_running_queries() -> str:
        """
        Get currently running queries.

        Returns:
            JSON string with running query information
        """
        db_tools = get_db_tools()
        if not db_tools:
            return json.dumps({"status": "error", "error": "Database not connected"})

        try:
            result = db_tools.get_running_queries()
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e)})

    @mcp.tool()
    async def get_db_info() -> str:
        """
        Get database connection information.

        Returns:
            JSON string with database type, version, and connection info
        """
        db_tools = get_db_tools()
        if not db_tools:
            return json.dumps({"status": "error", "error": "Database not connected"})

        try:
            result = db_tools.get_db_info()
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e)})

    return mcp


def init_database(
    db_type: str,
    host: str,
    port: int,
    database: str,
    user: str,
    password: str
) -> bool:
    """
    Initialize database connection.

    Args:
        db_type: Database type (postgresql, mysql, gaussdb, oracle, sqlserver)
        host: Database host
        port: Database port
        database: Database name
        user: Username
        password: Password

    Returns:
        True if connection successful
    """
    global _db_tools

    try:
        from db_agent.core.database import DatabaseToolsFactory

        db_config = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }

        _db_tools = DatabaseToolsFactory.create(db_type, db_config)

        # Test connection
        info = _db_tools.get_db_info()
        logger.info(f"Connected to {db_type}: {info.get('version', 'unknown')}")
        return True

    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return False


def init_from_config(config_path: str) -> bool:
    """
    Initialize database from a JSON config file.

    Config file format:
    {
        "db_type": "postgresql",
        "host": "localhost",
        "port": 5432,
        "database": "mydb",
        "user": "postgres",
        "password": "secret"
    }

    Args:
        config_path: Path to JSON config file

    Returns:
        True if connection successful
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)

        return init_database(
            db_type=config['db_type'],
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password']
        )

    except Exception as e:
        logger.error(f"Failed to load config from {config_path}: {e}")
        return False


def init_from_storage(connection_name: str = None) -> bool:
    """
    Initialize database from stored connection.

    Args:
        connection_name: Name of stored connection, or None for active connection

    Returns:
        True if connection successful
    """
    try:
        from db_agent.storage import SQLiteStorage
        from db_agent.storage.encryption import decrypt

        storage = SQLiteStorage()

        if connection_name:
            conn = storage.get_connection(connection_name)
        else:
            conn = storage.get_active_connection()

        if not conn:
            logger.error("No database connection found")
            return False

        password = decrypt(conn.password_encrypted)

        return init_database(
            db_type=conn.db_type,
            host=conn.host,
            port=conn.port,
            database=conn.database,
            user=conn.username,
            password=password
        )

    except Exception as e:
        logger.error(f"Failed to load connection from storage: {e}")
        return False


def main():
    """Main entry point for MCP server."""
    parser = argparse.ArgumentParser(
        description='db-agent MCP Server - Expose database tools via MCP protocol'
    )

    # Database connection options
    parser.add_argument('--db-type', choices=['postgresql', 'mysql', 'gaussdb', 'oracle', 'sqlserver'],
                       help='Database type')
    parser.add_argument('--host', default='localhost', help='Database host')
    parser.add_argument('--port', type=int, help='Database port')
    parser.add_argument('--database', help='Database name')
    parser.add_argument('--user', help='Database user')
    parser.add_argument('--password', help='Database password')

    # Alternative: use config file
    parser.add_argument('--db-config', help='Path to database config JSON file')

    # Alternative: use stored connection
    parser.add_argument('--connection', help='Name of stored database connection')
    parser.add_argument('--use-active', action='store_true',
                       help='Use the active database connection from storage')

    args = parser.parse_args()

    # Initialize database connection
    connected = False

    if args.db_config:
        connected = init_from_config(args.db_config)
    elif args.use_active:
        connected = init_from_storage()
    elif args.connection:
        connected = init_from_storage(args.connection)
    elif args.db_type and args.database:
        # Set default ports
        default_ports = {
            'postgresql': 5432,
            'mysql': 3306,
            'gaussdb': 5432,
            'oracle': 1521,
            'sqlserver': 1433
        }
        port = args.port or default_ports.get(args.db_type, 5432)

        # Try to get password from environment if not provided
        password = args.password or os.environ.get('DB_PASSWORD', '')
        user = args.user or os.environ.get('DB_USER', 'postgres')

        connected = init_database(
            db_type=args.db_type,
            host=args.host,
            port=port,
            database=args.database,
            user=user,
            password=password
        )

    if not connected:
        logger.error("Failed to connect to database. MCP server will start but tools will not work.")

    # Create and run MCP server
    mcp = create_mcp_server()
    mcp.run()


if __name__ == "__main__":
    main()
