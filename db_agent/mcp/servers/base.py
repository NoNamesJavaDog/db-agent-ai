"""
db_agent/mcp/servers/base.py

Base MCP Server Factory - Provides common tool definitions and server creation logic
for all database-specific MCP servers.
"""

import json
from typing import Optional

from db_agent.core.database import DatabaseToolsFactory, BaseDatabaseTools


def create_db_mcp_server(
    server_name: str,
    db_type: str,
    db_tools: Optional[BaseDatabaseTools] = None
):
    """
    Create a database MCP server with standard tools.

    Args:
        server_name: Server name (e.g., "postgresql", "mysql")
        db_type: Database type for the factory
        db_tools: Optional pre-connected database tools instance

    Returns:
        Configured FastMCP server instance
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        raise ImportError("MCP SDK not installed. Install with: pip install mcp[cli]")

    mcp = FastMCP(server_name)
    _db_tools = db_tools

    def get_db():
        return _db_tools

    def set_db(tools):
        nonlocal _db_tools
        _db_tools = tools

    # ===== Connection Tools =====

    @mcp.tool()
    async def connect(
        host: str,
        port: int,
        database: str,
        user: str,
        password: str
    ) -> str:
        """
        Connect to the database.

        Args:
            host: Database host address
            port: Database port number
            database: Database name
            user: Username for authentication
            password: Password for authentication

        Returns:
            JSON string with connection status and database info
        """
        config = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password
        }
        try:
            tools = DatabaseToolsFactory.create(db_type, config)
            set_db(tools)
            info = tools.get_db_info()
            return json.dumps({
                "status": "success",
                "message": f"Connected to {db_type}",
                "info": info
            }, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e)})

    @mcp.tool()
    async def disconnect() -> str:
        """
        Disconnect from the database.

        Returns:
            JSON string with disconnection status
        """
        set_db(None)
        return json.dumps({"status": "success", "message": "Disconnected"})

    @mcp.tool()
    async def get_connection_info() -> str:
        """
        Get current database connection information.

        Returns:
            JSON string with database type, version, and connection details
        """
        db = get_db()
        if not db:
            return json.dumps({"status": "error", "error": "Not connected"})
        try:
            return json.dumps(db.get_db_info(), ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e)})

    # ===== Table Tools =====

    @mcp.tool()
    async def list_tables(schema: str = None) -> str:
        """
        List all tables in the database.

        Args:
            schema: Schema name (optional, uses default schema if not specified)

        Returns:
            JSON string with table list
        """
        db = get_db()
        if not db:
            return json.dumps({"status": "error", "error": "Not connected"})
        try:
            result = db.list_tables(schema)
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e)})

    @mcp.tool()
    async def describe_table(table_name: str, schema: str = None) -> str:
        """
        Get table structure including columns, indexes, and constraints.

        Args:
            table_name: Name of the table to describe
            schema: Schema name (optional)

        Returns:
            JSON string with table structure details
        """
        db = get_db()
        if not db:
            return json.dumps({"status": "error", "error": "Not connected"})
        try:
            result = db.describe_table(table_name, schema)
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e)})

    @mcp.tool()
    async def get_sample_data(table_name: str, schema: str = None, limit: int = 10) -> str:
        """
        Get sample data from a table.

        Args:
            table_name: Name of the table
            schema: Schema name (optional)
            limit: Maximum number of rows to return (default: 10)

        Returns:
            JSON string with sample data rows
        """
        db = get_db()
        if not db:
            return json.dumps({"status": "error", "error": "Not connected"})
        try:
            result = db.get_sample_data(table_name, schema, limit)
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e)})

    # ===== Query Tools =====

    @mcp.tool()
    async def execute_query(sql: str) -> str:
        """
        Execute a SELECT query (read-only).

        Only SELECT and WITH queries are allowed for safety.

        Args:
            sql: SQL SELECT query to execute

        Returns:
            JSON string with query results
        """
        db = get_db()
        if not db:
            return json.dumps({"status": "error", "error": "Not connected"})
        sql_upper = sql.strip().upper()
        if not sql_upper.startswith("SELECT") and not sql_upper.startswith("WITH"):
            return json.dumps({"status": "error", "error": "Only SELECT queries allowed"})
        try:
            result = db.execute_safe_query(sql)
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e)})

    @mcp.tool()
    async def run_explain(sql: str, analyze: bool = False) -> str:
        """
        Analyze query execution plan using EXPLAIN.

        Args:
            sql: SQL query to analyze
            analyze: Whether to actually execute the query for real statistics (default: False)

        Returns:
            JSON string with execution plan details
        """
        db = get_db()
        if not db:
            return json.dumps({"status": "error", "error": "Not connected"})
        try:
            result = db.run_explain(sql, analyze)
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e)})

    # ===== Performance Analysis Tools =====

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
        db = get_db()
        if not db:
            return json.dumps({"status": "error", "error": "Not connected"})
        try:
            result = db.identify_slow_queries(min_duration_ms, limit)
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e)})

    @mcp.tool()
    async def get_running_queries() -> str:
        """
        Get currently running queries in the database.

        Returns:
            JSON string with information about active queries
        """
        db = get_db()
        if not db:
            return json.dumps({"status": "error", "error": "Not connected"})
        try:
            result = db.get_running_queries()
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e)})

    @mcp.tool()
    async def get_table_stats(table_name: str, schema: str = None) -> str:
        """
        Get table statistics including size, row estimates, and index information.

        Args:
            table_name: Name of the table
            schema: Schema name (optional)

        Returns:
            JSON string with table statistics
        """
        db = get_db()
        if not db:
            return json.dumps({"status": "error", "error": "Not connected"})
        try:
            result = db.get_table_stats(table_name, schema)
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e)})

    @mcp.tool()
    async def check_index_usage(table_name: str, schema: str = None) -> str:
        """
        Check index usage statistics for a table.

        Args:
            table_name: Name of the table
            schema: Schema name (optional)

        Returns:
            JSON string with index usage information
        """
        db = get_db()
        if not db:
            return json.dumps({"status": "error", "error": "Not connected"})
        try:
            result = db.check_index_usage(table_name, schema)
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e)})

    return mcp
