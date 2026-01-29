"""
SQL Server Database Tools - SQL Server-specific implementation
Supports multiple versions:
- SQL Server 2014 (12.x) - Basic support
- SQL Server 2016 (13.x) - Query Store support
- SQL Server 2017 (14.x)
- SQL Server 2019 (15.x)
- SQL Server 2022 (16.x) - New permission model
- Azure SQL Database
"""
import pytds
from typing import Dict, Any
import logging
from db_agent.i18n import t
from .base import BaseDatabaseTools

logger = logging.getLogger(__name__)


class SQLServerTools(BaseDatabaseTools):
    """SQL Server database tools implementation using pytds (python-tds)"""

    def __init__(self, db_config: Dict[str, Any]):
        super().__init__()
        self.db_config = db_config
        self._default_schema = db_config.get('schema', 'dbo')

        # Version information
        self.db_version = None
        self.db_version_major = 0
        self.db_version_minor = 0
        self.db_version_full = None
        self._edition = None
        self._engine_edition = 0  # 1=Personal, 2=Standard, 3=Enterprise, 5=Azure SQL
        self._is_azure = False

        # Feature flags
        self._has_server_state = False
        self._has_query_store = False
        self._has_showplan = False
        self._has_dm_exec_query_stats = False

        self._init_db_info()
        logger.info(f"SQL Server tools initialized: {db_config.get('host')}:{db_config.get('port', 1433)}/{db_config.get('database')} (SQL Server {self.db_version})")

    @property
    def db_type(self) -> str:
        return "sqlserver"

    def _init_db_info(self):
        """Initialize database information and check available features"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()

            # Get version information using SERVERPROPERTY
            try:
                cur.execute("""
                    SELECT
                        SERVERPROPERTY('ProductMajorVersion'),
                        SERVERPROPERTY('ProductMinorVersion'),
                        SERVERPROPERTY('Edition'),
                        SERVERPROPERTY('EngineEdition'),
                        @@VERSION
                """)
                row = cur.fetchone()
                if row:
                    self.db_version_major = int(row[0]) if row[0] else 0
                    self.db_version_minor = int(row[1]) if row[1] else 0
                    self._edition = row[2]
                    self._engine_edition = int(row[3]) if row[3] else 0
                    self.db_version_full = row[4]
                    self._is_azure = (self._engine_edition == 5)
                    self.db_version = f"{self.db_version_major}.{self.db_version_minor}"
            except Exception as e:
                logger.warning(f"Failed to get version info via SERVERPROPERTY: {e}")
                # Fallback to @@VERSION
                try:
                    cur.execute("SELECT @@VERSION")
                    row = cur.fetchone()
                    if row:
                        self.db_version_full = row[0]
                        self.db_version = "unknown"
                except Exception:
                    self.db_version = "unknown"
                    self.db_version_full = "unknown"

            # Check available features
            self._check_features(cur)

            conn.close()
        except Exception as e:
            logger.warning(f"Failed to get database version info: {e}")
            self.db_version = "unknown"
            self.db_version_major = 0
            self.db_version_full = "unknown"

    def _check_features(self, cur):
        """Check available features based on permissions"""
        # Check VIEW SERVER STATE permission (or VIEW SERVER PERFORMANCE STATE for 2022+)
        self._has_server_state = self._can_access_dmv(cur, "sys.dm_exec_requests")
        self._has_dm_exec_query_stats = self._can_access_dmv(cur, "sys.dm_exec_query_stats")

        # Query Store is available in SQL Server 2016+ (version 13+)
        if self.db_version_major >= 13:
            self._has_query_store = self._can_access_dmv(cur, "sys.query_store_query")

        # Check SHOWPLAN permission
        self._has_showplan = self._check_showplan_permission(cur)

        logger.info(f"SQL Server features: SERVER_STATE={self._has_server_state}, "
                   f"QUERY_STORE={self._has_query_store}, SHOWPLAN={self._has_showplan}, "
                   f"Azure={self._is_azure}")

    def _can_access_dmv(self, cur, view_name: str) -> bool:
        """Check if a DMV is accessible"""
        try:
            cur.execute(f"SELECT TOP 1 1 FROM {view_name}")
            cur.fetchone()
            return True
        except Exception:
            return False

    def _check_showplan_permission(self, cur) -> bool:
        """Check if SHOWPLAN permission is available"""
        try:
            cur.execute("SET SHOWPLAN_TEXT ON")
            cur.execute("SELECT 1")
            cur.fetchall()
            cur.execute("SET SHOWPLAN_TEXT OFF")
            return True
        except Exception:
            return False

    def get_db_info(self) -> Dict[str, Any]:
        """Get database information"""
        return {
            "type": "sqlserver",
            "version": self.db_version,
            "version_major": self.db_version_major,
            "version_minor": self.db_version_minor,
            "version_full": self.db_version_full,
            "edition": self._edition,
            "is_azure": self._is_azure,
            "host": self.db_config.get("host"),
            "database": self.db_config.get("database"),
            "has_server_state": self._has_server_state,
            "has_query_store": self._has_query_store,
            "has_showplan": self._has_showplan
        }

    def get_connection(self):
        """Get database connection using pytds"""
        return pytds.connect(
            server=self.db_config.get("host", "localhost"),
            port=int(self.db_config.get("port", 1433)),
            database=self.db_config.get("database"),
            user=self.db_config.get("user"),
            password=self.db_config.get("password"),
            autocommit=False
        )

    def list_tables(self, schema: str = None) -> Dict[str, Any]:
        """
        List all tables in the database

        Args:
            schema: Schema name (defaults to dbo)

        Returns:
            Table list
        """
        schema = schema or self._default_schema
        logger.info(f"Listing tables: schema={schema}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            query = """
                SELECT
                    t.name AS table_name,
                    s.name AS schema_name,
                    p.rows AS row_count,
                    CAST(ROUND(SUM(a.total_pages) * 8.0 / 1024, 2) AS DECIMAL(18,2)) AS size_mb
                FROM sys.tables t
                INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                INNER JOIN sys.partitions p ON t.object_id = p.object_id AND p.index_id IN (0, 1)
                INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id
                WHERE s.name = @schema AND t.is_ms_shipped = 0
                GROUP BY t.name, s.name, p.rows
                ORDER BY SUM(a.total_pages) DESC
            """

            cur.execute(query, {'schema': schema})

            columns = [desc[0].lower() for desc in cur.description]
            tables = [dict(zip(columns, row)) for row in cur.fetchall()]

            logger.info(f"Found {len(tables)} tables")

            return {
                "status": "success",
                "schema": schema,
                "count": len(tables),
                "tables": tables
            }

        except Exception as e:
            logger.error(f"Failed to list tables: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            conn.close()

    def describe_table(self, table_name: str, schema: str = None) -> Dict[str, Any]:
        """
        Get table structure information

        Args:
            table_name: Table name
            schema: Schema name

        Returns:
            Table structure information
        """
        schema = schema or self._default_schema
        logger.info(f"Getting table structure: {schema}.{table_name}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            # Get column information
            cur.execute("""
                SELECT
                    c.name AS column_name,
                    t.name AS data_type,
                    c.max_length,
                    c.precision,
                    c.scale,
                    c.is_nullable,
                    dc.definition AS default_value,
                    c.is_identity
                FROM sys.columns c
                INNER JOIN sys.types t ON c.user_type_id = t.user_type_id
                INNER JOIN sys.tables tb ON c.object_id = tb.object_id
                INNER JOIN sys.schemas s ON tb.schema_id = s.schema_id
                LEFT JOIN sys.default_constraints dc ON c.default_object_id = dc.object_id
                WHERE tb.name = @table_name AND s.name = @schema
                ORDER BY c.column_id
            """, {"table_name": table_name, "schema": schema})

            columns = [desc[0].lower() for desc in cur.description]
            cols = [dict(zip(columns, row)) for row in cur.fetchall()]

            # Get primary key information
            cur.execute("""
                SELECT col.name AS column_name
                FROM sys.indexes idx
                INNER JOIN sys.index_columns ic ON idx.object_id = ic.object_id AND idx.index_id = ic.index_id
                INNER JOIN sys.columns col ON ic.object_id = col.object_id AND ic.column_id = col.column_id
                INNER JOIN sys.tables t ON idx.object_id = t.object_id
                INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                WHERE idx.is_primary_key = 1
                  AND t.name = @table_name
                  AND s.name = @schema
                ORDER BY ic.key_ordinal
            """, {"table_name": table_name, "schema": schema})
            pk_columns = [row[0] for row in cur.fetchall()]

            # Get foreign key information
            cur.execute("""
                SELECT
                    ccu.column_name,
                    kcu2.table_name AS foreign_table,
                    kcu2.column_name AS foreign_column
                FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
                INNER JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE ccu
                    ON rc.CONSTRAINT_NAME = ccu.CONSTRAINT_NAME
                INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu2
                    ON rc.UNIQUE_CONSTRAINT_NAME = kcu2.CONSTRAINT_NAME
                WHERE ccu.TABLE_NAME = @table_name
                  AND ccu.TABLE_SCHEMA = @schema
            """, {"table_name": table_name, "schema": schema})
            fk_columns = [desc[0].lower() for desc in cur.description]
            fks = [dict(zip(fk_columns, row)) for row in cur.fetchall()]

            logger.info(f"Table structure retrieved: {len(cols)} columns")

            return {
                "status": "success",
                "table": f"{schema}.{table_name}",
                "columns": cols,
                "primary_key": pk_columns,
                "foreign_keys": fks
            }

        except Exception as e:
            logger.error(f"Failed to get table structure: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            conn.close()

    def execute_safe_query(self, sql: str) -> Dict[str, Any]:
        """
        Execute safe read-only query

        Args:
            sql: SQL statement (SELECT, EXPLAIN)

        Returns:
            Query result
        """
        logger.info(f"Executing safe query")
        logger.debug(f"SQL: {sql[:100]}...")

        # Clean up the SQL
        sql = sql.strip()
        sql_upper = sql.upper()

        # Auto-fix: If SQL looks like SELECT columns but missing SELECT keyword
        if not (sql_upper.startswith("SELECT") or
                sql_upper.startswith("WITH") or
                sql_upper.startswith("SET SHOWPLAN")):
            if " AS " in sql_upper or "(" in sql or "," in sql:
                sql = "SELECT " + sql
                sql_upper = sql.upper()
                logger.info(f"Auto-prepended SELECT to query")

        # Safety check - allow read-only statements
        is_safe = (
            sql_upper.startswith("SELECT") or
            sql_upper.startswith("WITH") or
            sql_upper.startswith("SET SHOWPLAN") or
            sql_upper.startswith("SET STATISTICS")
        )
        if not is_safe:
            return {
                "status": "error",
                "error": t("db_only_select")
            }

        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql)

            columns = [desc[0].lower() for desc in cur.description] if cur.description else []
            results = [dict(zip(columns, row)) for row in cur.fetchall()] if columns else []

            logger.info(f"Query successful, returned {len(results)} rows")

            return {
                "status": "success",
                "count": len(results),
                "rows": results
            }

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            conn.close()

    def execute_sql(self, sql: str, confirmed: bool = False) -> Dict[str, Any]:
        """
        Execute any SQL statement (INSERT/UPDATE/DELETE/CREATE/ALTER/DROP etc.)

        Args:
            sql: SQL statement
            confirmed: Whether confirmed to execute

        Returns:
            Execution result
        """
        sql_upper = sql.strip().upper()

        # Read-only queries execute directly without confirmation
        is_readonly = (
            sql_upper.startswith("SELECT") or
            sql_upper.startswith("WITH") or
            sql_upper.startswith("SET SHOWPLAN") or
            sql_upper.startswith("SET STATISTICS")
        )

        if is_readonly:
            conn = self.get_connection()
            try:
                cur = conn.cursor()
                cur.execute(sql)
                columns = [desc[0].lower() for desc in cur.description] if cur.description else []
                results = [dict(zip(columns, row)) for row in cur.fetchall()] if columns else []
                return {
                    "status": "success",
                    "type": "query",
                    "count": len(results),
                    "rows": results
                }
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "sql": sql
                }
            finally:
                conn.close()

        # Non-read-only operations require confirmation
        if not confirmed:
            return {
                "status": "pending_confirmation",
                "sql": sql,
                "message": t("db_need_confirm")
            }

        # Confirmed, execute operation
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql)
            rowcount = cur.rowcount
            conn.commit()
            return {
                "status": "success",
                "type": "execute",
                "affected_rows": rowcount,
                "message": t("db_execute_success", count=rowcount)
            }

        except Exception as e:
            conn.rollback()
            logger.error(f"SQL execution failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "sql": sql
            }
        finally:
            conn.close()

    def run_explain(self, sql: str, analyze: bool = False) -> Dict[str, Any]:
        """
        Run execution plan analysis

        Args:
            sql: SQL statement
            analyze: Whether to gather actual execution statistics

        Returns:
            EXPLAIN output result
        """
        logger.info(f"Running EXPLAIN analysis, analyze={analyze}")
        logger.debug(f"SQL: {sql[:100]}...")

        if not self._has_showplan:
            return {
                "status": "error",
                "error": t("sqlserver_no_showplan"),
                "sql": sql
            }

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            if analyze:
                # Actual execution with statistics
                cur.execute("SET STATISTICS XML ON")
                cur.execute(sql)
                # Consume all result sets to get to the XML plan
                results = []
                while True:
                    try:
                        rows = cur.fetchall()
                        if rows:
                            results.extend(rows)
                        if not cur.nextset():
                            break
                    except Exception:
                        break

                cur.execute("SET STATISTICS XML OFF")

                # The last result should contain the XML plan
                plan_xml = None
                for row in reversed(results):
                    if row and isinstance(row[0], str) and '<ShowPlanXML' in row[0]:
                        plan_xml = row[0]
                        break

                return {
                    "status": "success",
                    "explain_output": [plan_xml] if plan_xml else ["No plan available"],
                    "plan": [plan_xml] if plan_xml else ["No plan available"],
                    "analyzed": True,
                    "sql": sql
                }
            else:
                # Estimated plan only (no execution)
                cur.execute("SET SHOWPLAN_XML ON")
                cur.execute(sql)
                plan_row = cur.fetchone()
                plan_xml = plan_row[0] if plan_row else None
                cur.execute("SET SHOWPLAN_XML OFF")

                plan_lines = [plan_xml] if plan_xml else ["No plan available"]

                logger.info("EXPLAIN analysis completed")

                return {
                    "status": "success",
                    "explain_output": plan_lines,
                    "plan": plan_lines,
                    "analyzed": False,
                    "sql": sql
                }

        except Exception as e:
            logger.error(f"EXPLAIN analysis failed: {e}")
            # Try to reset state
            try:
                cur.execute("SET SHOWPLAN_XML OFF")
            except Exception:
                pass
            try:
                cur.execute("SET STATISTICS XML OFF")
            except Exception:
                pass
            return {
                "status": "error",
                "error": str(e),
                "sql": sql
            }
        finally:
            conn.close()

    def identify_slow_queries(self, min_duration_ms: float = 1000, limit: int = 20) -> Dict[str, Any]:
        """
        Identify slow queries

        Args:
            min_duration_ms: Minimum average execution time (milliseconds)
            limit: Number of results to return

        Returns:
            Dictionary containing slow query list
        """
        logger.info(f"Identifying slow queries: min_duration_ms={min_duration_ms}, limit={limit}")

        # Priority 1: Try Query Store (SQL Server 2016+)
        if self._has_query_store:
            result = self._get_slow_queries_from_query_store(min_duration_ms, limit)
            if result.get("status") == "success" and result.get("count", 0) > 0:
                return result

        # Priority 2: Try dm_exec_query_stats
        if self._has_dm_exec_query_stats:
            result = self._get_slow_queries_from_dmv(min_duration_ms, limit)
            if result.get("status") == "success":
                return result

        # Priority 3: Fallback to running queries
        return self._get_running_queries_fallback(limit)

    def _get_slow_queries_from_query_store(self, min_duration_ms: float, limit: int) -> Dict[str, Any]:
        """Get slow queries from Query Store (SQL Server 2016+)"""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            query = """
                SELECT TOP (@limit)
                    qt.query_sql_text AS sql_text,
                    rs.count_executions AS execution_count,
                    rs.avg_duration / 1000.0 AS avg_duration_ms,
                    rs.avg_cpu_time / 1000.0 AS avg_cpu_ms,
                    rs.avg_logical_io_reads AS avg_logical_reads,
                    rs.avg_physical_io_reads AS avg_physical_reads,
                    rs.last_execution_time
                FROM sys.query_store_query q
                INNER JOIN sys.query_store_query_text qt ON q.query_text_id = qt.query_text_id
                INNER JOIN sys.query_store_plan p ON q.query_id = p.query_id
                INNER JOIN sys.query_store_runtime_stats rs ON p.plan_id = rs.plan_id
                WHERE rs.avg_duration / 1000.0 > @min_ms
                ORDER BY rs.avg_duration DESC
            """
            cur.execute(query, {"limit": limit, "min_ms": min_duration_ms})

            if cur.description is None:
                return {"status": "success", "source": "query_store", "count": 0, "queries": []}

            columns = [desc[0].lower() for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]

            return {
                "status": "success",
                "source": "query_store",
                "count": len(results),
                "queries": results,
                "summary": {"total_slow_queries": len(results)}
            }
        except Exception as e:
            logger.warning(f"Query Store query failed: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            conn.close()

    def _get_slow_queries_from_dmv(self, min_duration_ms: float, limit: int) -> Dict[str, Any]:
        """Get slow queries from dm_exec_query_stats"""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            query = """
                SELECT TOP (@limit)
                    SUBSTRING(qt.text, (qs.statement_start_offset/2)+1,
                        ((CASE qs.statement_end_offset
                            WHEN -1 THEN DATALENGTH(qt.text)
                            ELSE qs.statement_end_offset
                        END - qs.statement_start_offset)/2)+1) AS sql_text,
                    qs.execution_count,
                    qs.total_elapsed_time / 1000.0 AS total_elapsed_ms,
                    (qs.total_elapsed_time / NULLIF(qs.execution_count, 0)) / 1000.0 AS avg_elapsed_ms,
                    qs.total_worker_time / 1000.0 AS total_cpu_ms,
                    qs.total_logical_reads,
                    qs.total_physical_reads,
                    qs.last_execution_time
                FROM sys.dm_exec_query_stats qs
                CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) qt
                WHERE (qs.total_elapsed_time / NULLIF(qs.execution_count, 0)) / 1000.0 > @min_ms
                  AND qs.execution_count > 0
                ORDER BY qs.total_elapsed_time DESC
            """
            cur.execute(query, {"limit": limit, "min_ms": min_duration_ms})

            if cur.description is None:
                return {"status": "success", "source": "dm_exec_query_stats", "count": 0, "queries": []}

            columns = [desc[0].lower() for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]

            return {
                "status": "success",
                "source": "dm_exec_query_stats",
                "count": len(results),
                "queries": results,
                "summary": {"total_slow_queries": len(results)}
            }
        except Exception as e:
            logger.warning(f"DMV query failed: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            conn.close()

    def _get_running_queries_fallback(self, limit: int) -> Dict[str, Any]:
        """Fallback to get currently running queries"""
        result = self.get_running_queries()
        if result.get("status") == "success":
            result["source"] = "dm_exec_requests"
            result["note"] = t("sqlserver_no_server_state")
        return result

    def get_running_queries(self) -> Dict[str, Any]:
        """Get currently running queries"""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            query = """
                SELECT
                    r.session_id,
                    r.status,
                    r.command,
                    r.start_time,
                    DATEDIFF(SECOND, r.start_time, GETDATE()) AS duration_seconds,
                    r.wait_type,
                    r.wait_time,
                    r.cpu_time,
                    r.total_elapsed_time / 1000.0 AS elapsed_ms,
                    r.reads,
                    r.writes,
                    SUBSTRING(qt.text, (r.statement_start_offset/2)+1,
                        ((CASE r.statement_end_offset
                            WHEN -1 THEN DATALENGTH(qt.text)
                            ELSE r.statement_end_offset
                        END - r.statement_start_offset)/2)+1) AS sql_text,
                    s.login_name,
                    DB_NAME(r.database_id) AS database_name
                FROM sys.dm_exec_requests r
                INNER JOIN sys.dm_exec_sessions s ON r.session_id = s.session_id
                CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) qt
                WHERE r.session_id != @@SPID
                  AND s.is_user_process = 1
                ORDER BY r.start_time
            """
            cur.execute(query)

            if cur.description is None:
                return {"status": "success", "count": 0, "queries": []}

            columns = [desc[0].lower() for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]

            return {
                "status": "success",
                "count": len(results),
                "queries": results
            }
        except Exception as e:
            logger.error(f"Failed to get running queries: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            conn.close()

    def check_index_usage(self, table_name: str, schema: str = None) -> Dict[str, Any]:
        """
        Check index usage for a table

        Args:
            table_name: Table name
            schema: Schema name

        Returns:
            Index usage information
        """
        schema = schema or self._default_schema
        logger.info(f"Checking index usage: {schema}.{table_name}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            full_name = f"{schema}.{table_name}"
            query = """
                SELECT
                    i.name AS index_name,
                    i.type_desc,
                    i.is_unique,
                    i.is_primary_key,
                    ius.user_seeks,
                    ius.user_scans,
                    ius.user_lookups,
                    ius.user_updates,
                    ius.last_user_seek,
                    ius.last_user_scan,
                    CAST(ROUND(SUM(ps.used_page_count) * 8.0 / 1024, 2) AS DECIMAL(18,2)) AS size_mb,
                    SUM(ps.used_page_count) * 8 * 1024 AS size_bytes
                FROM sys.indexes i
                INNER JOIN sys.tables t ON i.object_id = t.object_id
                INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                LEFT JOIN sys.dm_db_index_usage_stats ius
                    ON i.object_id = ius.object_id
                    AND i.index_id = ius.index_id
                    AND ius.database_id = DB_ID()
                INNER JOIN sys.dm_db_partition_stats ps
                    ON i.object_id = ps.object_id
                    AND i.index_id = ps.index_id
                WHERE t.name = @table_name
                  AND s.name = @schema
                  AND i.type > 0
                GROUP BY i.name, i.type_desc, i.is_unique, i.is_primary_key,
                         ius.user_seeks, ius.user_scans, ius.user_lookups,
                         ius.user_updates, ius.last_user_seek, ius.last_user_scan
                ORDER BY size_mb DESC
            """

            cur.execute(query, {"table_name": table_name, "schema": schema})
            columns = [desc[0].lower() for desc in cur.description]
            indexes = [dict(zip(columns, row)) for row in cur.fetchall()]

            # Get index columns for each index
            for idx in indexes:
                cur.execute("""
                    SELECT col.name
                    FROM sys.index_columns ic
                    INNER JOIN sys.columns col ON ic.object_id = col.object_id AND ic.column_id = col.column_id
                    INNER JOIN sys.indexes i ON ic.object_id = i.object_id AND ic.index_id = i.index_id
                    INNER JOIN sys.tables t ON i.object_id = t.object_id
                    INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                    WHERE i.name = @index_name
                      AND t.name = @table_name
                      AND s.name = @schema
                    ORDER BY ic.key_ordinal
                """, {"index_name": idx['index_name'], "table_name": table_name, "schema": schema})
                idx['columns'] = [row[0] for row in cur.fetchall()]

            total_size = sum(idx.get('size_bytes') or 0 for idx in indexes)

            logger.info(f"Found {len(indexes)} indexes")

            return {
                "status": "success",
                "table": f"{schema}.{table_name}",
                "total_indexes": len(indexes),
                "total_size": total_size,
                "indexes": indexes,
                "note": t("sqlserver_no_server_state") if not self._has_server_state else None
            }

        except Exception as e:
            logger.error(f"Index check failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            conn.close()

    def get_table_stats(self, table_name: str, schema: str = None) -> Dict[str, Any]:
        """
        Get table statistics

        Args:
            table_name: Table name
            schema: Schema name

        Returns:
            Table statistics
        """
        schema = schema or self._default_schema
        logger.info(f"Getting table stats: {schema}.{table_name}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            query = """
                SELECT
                    s.name AS schemaname,
                    t.name AS tablename,
                    p.rows AS row_count,
                    CAST(ROUND(SUM(a.total_pages) * 8.0 / 1024, 2) AS DECIMAL(18,2)) AS size_mb,
                    CAST(ROUND(SUM(a.used_pages) * 8.0 / 1024, 2) AS DECIMAL(18,2)) AS used_mb,
                    t.create_date,
                    t.modify_date,
                    STATS_DATE(t.object_id, 1) AS stats_date
                FROM sys.tables t
                INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                INNER JOIN sys.partitions p ON t.object_id = p.object_id AND p.index_id IN (0, 1)
                INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id
                WHERE s.name = @schema
                  AND t.name = @table_name
                GROUP BY s.name, t.name, p.rows, t.create_date, t.modify_date, t.object_id
            """

            cur.execute(query, {"schema": schema, "table_name": table_name})
            columns = [desc[0].lower() for desc in cur.description]
            result = cur.fetchone()

            if result:
                stats = dict(zip(columns, result))
                logger.info(f"Table stats retrieved successfully")
                return {
                    "status": "success",
                    "stats": stats
                }
            else:
                return {
                    "status": "error",
                    "error": t("db_table_not_found", schema=schema, table=table_name)
                }

        except Exception as e:
            logger.error(f"Failed to get table stats: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            conn.close()

    def create_index(self, index_sql: str, concurrent: bool = True) -> Dict[str, Any]:
        """
        Create index

        Args:
            index_sql: CREATE INDEX statement
            concurrent: Whether to use ONLINE (SQL Server's equivalent of concurrent)

        Returns:
            Creation result
        """
        logger.info(f"Creating index: concurrent={concurrent}")
        logger.info(f"SQL: {index_sql}")

        # Safety check
        if not index_sql.strip().upper().startswith("CREATE"):
            return {
                "status": "error",
                "error": t("db_only_create_index")
            }

        # Add ONLINE clause for SQL Server (Enterprise edition only)
        if concurrent and "ONLINE" not in index_sql.upper():
            # Check if Enterprise edition
            if self._edition and ("Enterprise" in self._edition or self._is_azure):
                index_sql = index_sql.rstrip().rstrip(';')
                index_sql = f"{index_sql} WITH (ONLINE = ON)"

        conn = self.get_connection()

        try:
            cur = conn.cursor()
            cur.execute(index_sql)
            conn.commit()

            logger.info("Index created successfully")

            return {
                "status": "success",
                "message": t("db_index_created"),
                "sql": index_sql
            }

        except Exception as e:
            logger.error(f"Index creation failed: {e}")
            conn.rollback()
            return {
                "status": "error",
                "error": str(e),
                "sql": index_sql
            }
        finally:
            conn.close()

    def analyze_table(self, table_name: str, schema: str = None) -> Dict[str, Any]:
        """
        Update table statistics using UPDATE STATISTICS

        Args:
            table_name: Table name
            schema: Schema name

        Returns:
            Execution result
        """
        schema = schema or self._default_schema
        logger.info(f"Updating statistics: {schema}.{table_name}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            # Use UPDATE STATISTICS for SQL Server
            sql = f"UPDATE STATISTICS [{schema}].[{table_name}]"
            cur.execute(sql)
            conn.commit()

            logger.info("Statistics updated successfully")

            return {
                "status": "success",
                "message": t("db_stats_updated", schema=schema, table=table_name)
            }

        except Exception as e:
            logger.error(f"Failed to update statistics: {e}")
            conn.rollback()
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            conn.close()

    def get_sample_data(self, table_name: str, schema: str = None, limit: int = 10) -> Dict[str, Any]:
        """
        Get sample data from a table

        Args:
            table_name: Table name
            schema: Schema name
            limit: Number of rows to return

        Returns:
            Sample data
        """
        schema = schema or self._default_schema
        logger.info(f"Getting sample data: {schema}.{table_name}, limit={limit}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            # Use TOP for SQL Server
            sql = f"SELECT TOP (@limit) * FROM [{schema}].[{table_name}]"
            cur.execute(sql, {"limit": limit})

            columns = [desc[0].lower() for desc in cur.description]
            rows = [dict(zip(columns, row)) for row in cur.fetchall()]

            logger.info(f"Sample data retrieved: {len(rows)} rows")

            return {
                "status": "success",
                "table": f"{schema}.{table_name}",
                "columns": columns,
                "count": len(rows),
                "rows": rows
            }

        except Exception as e:
            logger.error(f"Failed to get sample data: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            conn.close()
