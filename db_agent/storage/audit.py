"""
Audit logging service for tracking database operations and changes
"""
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, TYPE_CHECKING

from .models import AuditLog

if TYPE_CHECKING:
    from .sqlite_storage import SQLiteStorage


class AuditService:
    """
    Audit logging service that provides high-level methods for logging
    SQL executions, tool calls, and configuration changes.
    """

    # Audit categories
    CATEGORY_SQL_EXECUTE = "sql_execute"
    CATEGORY_TOOL_CALL = "tool_call"
    CATEGORY_CONFIG_CHANGE = "config_change"

    def __init__(self, storage: "SQLiteStorage"):
        """
        Initialize the audit service.

        Args:
            storage: SQLiteStorage instance for persisting logs
        """
        self.storage = storage

    def log_sql_execution(
        self,
        session_id: Optional[int],
        connection_id: Optional[int],
        sql: str,
        action: str,
        result_status: str,
        affected_rows: int = None,
        error_message: str = None,
        execution_time_ms: int = None,
        user_confirmed: bool = False
    ) -> int:
        """
        Log a SQL execution event.

        Args:
            session_id: Session ID (optional)
            connection_id: Database connection ID (optional)
            sql: The SQL statement executed
            action: Action type (execute_sql, execute_safe_query, run_explain)
            result_status: Result status (success, error, pending)
            affected_rows: Number of rows affected (optional)
            error_message: Error message if failed (optional)
            execution_time_ms: Execution time in milliseconds (optional)
            user_confirmed: Whether the operation was confirmed by user

        Returns:
            The ID of the created audit log entry
        """
        # Build result summary
        result_summary = {}
        if affected_rows is not None:
            result_summary["affected_rows"] = affected_rows
        if error_message:
            result_summary["error"] = error_message

        # Extract target info from SQL
        target_type, target_name = self._extract_sql_target(sql)

        log = AuditLog(
            id=None,
            session_id=session_id,
            connection_id=connection_id,
            category=self.CATEGORY_SQL_EXECUTE,
            action=action,
            target_type=target_type,
            target_name=target_name,
            sql_text=sql,
            parameters=None,
            result_status=result_status,
            result_summary=json.dumps(result_summary) if result_summary else None,
            affected_rows=affected_rows,
            execution_time_ms=execution_time_ms,
            user_confirmed=user_confirmed,
            created_at=datetime.now()
        )

        return self.storage.add_audit_log(log)

    def log_tool_call(
        self,
        session_id: Optional[int],
        connection_id: Optional[int],
        tool_name: str,
        parameters: Dict[str, Any],
        result_status: str,
        result_summary: str = None,
        execution_time_ms: int = None
    ) -> int:
        """
        Log a tool call event.

        Args:
            session_id: Session ID (optional)
            connection_id: Database connection ID (optional)
            tool_name: Name of the tool called
            parameters: Tool parameters
            result_status: Result status (success, error)
            result_summary: Summary of the result (optional)
            execution_time_ms: Execution time in milliseconds (optional)

        Returns:
            The ID of the created audit log entry
        """
        # Extract target info from tool parameters
        target_type, target_name = self._extract_tool_target(tool_name, parameters)

        # Sanitize parameters (remove sensitive data)
        safe_params = self._sanitize_parameters(parameters)

        log = AuditLog(
            id=None,
            session_id=session_id,
            connection_id=connection_id,
            category=self.CATEGORY_TOOL_CALL,
            action=tool_name,
            target_type=target_type,
            target_name=target_name,
            sql_text=parameters.get("sql") if "sql" in parameters else None,
            parameters=json.dumps(safe_params, ensure_ascii=False) if safe_params else None,
            result_status=result_status,
            result_summary=result_summary,
            affected_rows=None,
            execution_time_ms=execution_time_ms,
            user_confirmed=False,
            created_at=datetime.now()
        )

        return self.storage.add_audit_log(log)

    def log_config_change(
        self,
        action: str,
        target_type: str,
        target_name: str,
        parameters: Dict[str, Any] = None,
        result_status: str = "success",
        session_id: Optional[int] = None
    ) -> int:
        """
        Log a configuration change event.

        Args:
            action: Action type (add_connection, update_connection, delete_connection, etc.)
            target_type: Type of configuration (connection, provider, session, mcp_server)
            target_name: Name of the configuration item
            parameters: Change parameters (optional)
            result_status: Result status (success, error)
            session_id: Session ID (optional)

        Returns:
            The ID of the created audit log entry
        """
        # Sanitize parameters
        safe_params = self._sanitize_parameters(parameters) if parameters else None

        log = AuditLog(
            id=None,
            session_id=session_id,
            connection_id=None,
            category=self.CATEGORY_CONFIG_CHANGE,
            action=action,
            target_type=target_type,
            target_name=target_name,
            sql_text=None,
            parameters=json.dumps(safe_params, ensure_ascii=False) if safe_params else None,
            result_status=result_status,
            result_summary=None,
            affected_rows=None,
            execution_time_ms=None,
            user_confirmed=False,
            created_at=datetime.now()
        )

        return self.storage.add_audit_log(log)

    # ==================== Query Methods ====================

    def get_logs_by_session(self, session_id: int, limit: int = 100) -> List[AuditLog]:
        """
        Get audit logs for a specific session.

        Args:
            session_id: Session ID
            limit: Maximum number of logs to return

        Returns:
            List of AuditLog objects
        """
        return self.storage.get_audit_logs_by_session(session_id, limit)

    def get_logs_by_time_range(
        self,
        start: datetime,
        end: datetime,
        limit: int = 1000
    ) -> List[AuditLog]:
        """
        Get audit logs within a time range.

        Args:
            start: Start of time range
            end: End of time range
            limit: Maximum number of logs to return

        Returns:
            List of AuditLog objects
        """
        return self.storage.get_audit_logs_by_time_range(start, end, limit)

    def get_logs_by_category(self, category: str, limit: int = 100) -> List[AuditLog]:
        """
        Get audit logs by category.

        Args:
            category: Log category (sql_execute, tool_call, config_change)
            limit: Maximum number of logs to return

        Returns:
            List of AuditLog objects
        """
        return self.storage.get_audit_logs_by_category(category, limit)

    def get_recent_sql_executions(self, limit: int = 50) -> List[AuditLog]:
        """
        Get recent SQL execution logs.

        Args:
            limit: Maximum number of logs to return

        Returns:
            List of AuditLog objects
        """
        return self.storage.get_recent_sql_executions(limit)

    def get_today_logs(self, limit: int = 500) -> List[AuditLog]:
        """
        Get today's audit logs.

        Args:
            limit: Maximum number of logs to return

        Returns:
            List of AuditLog objects
        """
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = datetime.now()
        return self.get_logs_by_time_range(today_start, today_end, limit)

    def get_recent_logs(self, limit: int = 100) -> List[AuditLog]:
        """
        Get the most recent audit logs.

        Args:
            limit: Maximum number of logs to return

        Returns:
            List of AuditLog objects
        """
        return self.storage.get_audit_logs(limit)

    # ==================== Cleanup Methods ====================

    def cleanup_old_logs(self, days: int = 30) -> int:
        """
        Delete audit logs older than specified days.

        Args:
            days: Number of days to keep logs

        Returns:
            Number of deleted logs
        """
        return self.storage.cleanup_old_audit_logs(days)

    # ==================== Helper Methods ====================

    def _extract_sql_target(self, sql: str) -> tuple:
        """
        Extract target type and name from SQL statement.

        Args:
            sql: SQL statement

        Returns:
            Tuple of (target_type, target_name)
        """
        if not sql:
            return None, None

        sql_upper = sql.upper().strip()
        sql_parts = sql.split()

        # SELECT queries
        if sql_upper.startswith("SELECT"):
            # Try to find FROM clause
            try:
                from_idx = sql_upper.index("FROM")
                # Get table name after FROM
                remaining = sql[from_idx + 4:].strip().split()
                if remaining:
                    table_name = remaining[0].strip(",;")
                    return "table", table_name
            except ValueError:
                pass
            return "query", None

        # INSERT
        if sql_upper.startswith("INSERT"):
            try:
                into_idx = sql_upper.index("INTO")
                remaining = sql[into_idx + 4:].strip().split()
                if remaining:
                    table_name = remaining[0].strip("(,;")
                    return "table", table_name
            except ValueError:
                pass
            return "table", None

        # UPDATE
        if sql_upper.startswith("UPDATE"):
            if len(sql_parts) > 1:
                table_name = sql_parts[1].strip(",;")
                return "table", table_name

        # DELETE
        if sql_upper.startswith("DELETE"):
            try:
                from_idx = sql_upper.index("FROM")
                remaining = sql[from_idx + 4:].strip().split()
                if remaining:
                    table_name = remaining[0].strip(",;")
                    return "table", table_name
            except ValueError:
                pass

        # CREATE TABLE
        if sql_upper.startswith("CREATE TABLE"):
            if len(sql_parts) > 2:
                table_name = sql_parts[2].strip("(,;")
                if table_name.upper() == "IF":
                    # CREATE TABLE IF NOT EXISTS
                    if len(sql_parts) > 5:
                        table_name = sql_parts[5].strip("(,;")
                return "table", table_name

        # CREATE INDEX
        if sql_upper.startswith("CREATE INDEX") or sql_upper.startswith("CREATE UNIQUE INDEX"):
            idx_offset = 2 if "UNIQUE" not in sql_upper else 3
            if len(sql_parts) > idx_offset:
                index_name = sql_parts[idx_offset].strip("(,;")
                if index_name.upper() == "IF":
                    idx_offset += 3  # Skip IF NOT EXISTS
                    if len(sql_parts) > idx_offset:
                        index_name = sql_parts[idx_offset].strip("(,;")
                return "index", index_name

        # DROP TABLE
        if sql_upper.startswith("DROP TABLE"):
            if len(sql_parts) > 2:
                table_name = sql_parts[2].strip(",;")
                if table_name.upper() == "IF":
                    if len(sql_parts) > 4:
                        table_name = sql_parts[4].strip(",;")
                return "table", table_name

        # ALTER TABLE
        if sql_upper.startswith("ALTER TABLE"):
            if len(sql_parts) > 2:
                table_name = sql_parts[2].strip(",;")
                return "table", table_name

        # EXPLAIN
        if sql_upper.startswith("EXPLAIN"):
            return "query", None

        return None, None

    def _extract_tool_target(self, tool_name: str, parameters: Dict[str, Any]) -> tuple:
        """
        Extract target type and name from tool call.

        Args:
            tool_name: Tool name
            parameters: Tool parameters

        Returns:
            Tuple of (target_type, target_name)
        """
        if tool_name in ("describe_table", "get_sample_data", "get_table_stats", "analyze_table"):
            return "table", parameters.get("table_name") or parameters.get("table")

        if tool_name == "check_index_usage":
            return "table", parameters.get("table_name")

        if tool_name == "create_index":
            return "index", parameters.get("index_name")

        if tool_name == "list_tables":
            return "schema", parameters.get("schema")

        return None, None

    def _sanitize_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove sensitive data from parameters.

        Args:
            params: Original parameters

        Returns:
            Sanitized parameters
        """
        if not params:
            return {}

        # Keys that should be masked
        sensitive_keys = {
            "password", "api_key", "secret", "token", "credential",
            "password_encrypted", "api_key_encrypted"
        }

        sanitized = {}
        for key, value in params.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                sanitized[key] = "***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_parameters(value)
            else:
                sanitized[key] = value

        return sanitized


class AuditContext:
    """
    Context manager for timing and logging operations.

    Usage:
        with AuditContext(audit_service, session_id, connection_id, "execute_sql") as ctx:
            result = do_operation()
            ctx.set_result("success", affected_rows=result.rows)
    """

    def __init__(
        self,
        audit_service: AuditService,
        session_id: Optional[int],
        connection_id: Optional[int],
        action: str,
        sql: str = None
    ):
        self.audit_service = audit_service
        self.session_id = session_id
        self.connection_id = connection_id
        self.action = action
        self.sql = sql
        self.start_time = None
        self.result_status = "pending"
        self.affected_rows = None
        self.error_message = None
        self.user_confirmed = False

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        execution_time = int((time.time() - self.start_time) * 1000)

        if exc_type is not None:
            self.result_status = "error"
            self.error_message = str(exc_val)

        if self.sql:
            self.audit_service.log_sql_execution(
                session_id=self.session_id,
                connection_id=self.connection_id,
                sql=self.sql,
                action=self.action,
                result_status=self.result_status,
                affected_rows=self.affected_rows,
                error_message=self.error_message,
                execution_time_ms=execution_time,
                user_confirmed=self.user_confirmed
            )

        return False  # Don't suppress exceptions

    def set_result(
        self,
        status: str,
        affected_rows: int = None,
        error_message: str = None,
        user_confirmed: bool = False
    ):
        """Set the result of the operation."""
        self.result_status = status
        self.affected_rows = affected_rows
        self.error_message = error_message
        self.user_confirmed = user_confirmed
