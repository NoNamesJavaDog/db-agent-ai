"""
Oracle Database Tools - Oracle-specific implementation
Supports Oracle 12c and above (12.1, 12.2, 18c, 19c, 21c, 23c)
Note: Oracle 11g is not supported (requires Oracle Client installation)
"""
import oracledb
from typing import Dict, Any, List
import logging
from db_agent.i18n import t
from .base import BaseDatabaseTools

logger = logging.getLogger(__name__)


class OracleTools(BaseDatabaseTools):
    """Oracle database tools implementation using oracledb Thin mode"""

    def __init__(self, db_config: Dict[str, Any]):
        super().__init__()
        self.db_config = db_config
        self.db_version = None
        self.db_version_num = None
        self.db_version_full = None
        self._has_dba_views = False
        self._has_v_sql = False
        self._has_sql_monitor = False
        self._default_schema = db_config.get('user', '').upper()
        self._init_db_info()
        logger.info(f"Oracle tools initialized: {db_config['host']}:{db_config.get('port', 1521)}/{db_config['database']} (Oracle {self.db_version})")

    @property
    def db_type(self) -> str:
        return "oracle"

    def _init_db_info(self):
        """Initialize database information and check available features"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()

            # Get version information from V$VERSION
            try:
                cur.execute("SELECT banner FROM v$version WHERE ROWNUM = 1")
                row = cur.fetchone()
                if row:
                    self.db_version_full = row[0]
            except Exception:
                self.db_version_full = "unknown"

            # Try to get detailed version (12.2+)
            try:
                cur.execute("SELECT version_full FROM v$instance")
                row = cur.fetchone()
                if row:
                    self.db_version = row[0]
            except Exception:
                # Fallback for older versions
                try:
                    cur.execute("SELECT version FROM v$instance")
                    row = cur.fetchone()
                    if row:
                        self.db_version = row[0]
                except Exception:
                    self.db_version = "unknown"

            # Parse version number (e.g., "19.0.0.0.0" -> 190000)
            if self.db_version and self.db_version != "unknown":
                try:
                    parts = self.db_version.split('.')
                    if len(parts) >= 2:
                        self.db_version_num = int(parts[0]) * 10000 + int(parts[1]) * 100
                    else:
                        self.db_version_num = 0
                except Exception:
                    self.db_version_num = 0
            else:
                self.db_version_num = 0

            # Check available features
            self._check_features(cur)

            conn.close()
        except Exception as e:
            logger.warning(f"Failed to get database version info: {e}")
            self.db_version = "unknown"
            self.db_version_num = 0
            self.db_version_full = "unknown"

    def _check_features(self, cur):
        """Check available features based on permissions"""
        self._has_dba_views = self._can_access(cur, "DBA_TABLES")
        self._has_v_sql = self._can_access(cur, "V$SQL")
        self._has_sql_monitor = self._can_access(cur, "V$SQL_MONITOR")
        logger.info(f"Oracle features: DBA_VIEWS={self._has_dba_views}, V$SQL={self._has_v_sql}, V$SQL_MONITOR={self._has_sql_monitor}")

    def _can_access(self, cur, view_name: str) -> bool:
        """Check if a view is accessible"""
        try:
            cur.execute(f"SELECT 1 FROM {view_name} WHERE ROWNUM = 1")
            cur.fetchone()
            return True
        except Exception:
            return False

    def get_db_info(self) -> Dict[str, Any]:
        """Get database information"""
        return {
            "type": "oracle",
            "version": self.db_version,
            "version_num": self.db_version_num,
            "version_full": self.db_version_full,
            "host": self.db_config.get("host"),
            "database": self.db_config.get("database"),
            "has_dba_views": self._has_dba_views,
            "has_v_sql": self._has_v_sql
        }

    def get_connection(self):
        """Get database connection using oracledb Thin mode"""
        host = self.db_config.get("host", "localhost")
        port = int(self.db_config.get("port", 1521))
        database = self.db_config.get("database")  # Service Name or SID

        # Build DSN in format: host:port/service_name
        dsn = f"{host}:{port}/{database}"

        return oracledb.connect(
            user=self.db_config.get("user"),
            password=self.db_config.get("password"),
            dsn=dsn
        )

    def list_tables(self, schema: str = None) -> Dict[str, Any]:
        """
        List all tables in the database

        Args:
            schema: Schema/owner name (defaults to connection user)

        Returns:
            Table list
        """
        schema = (schema or self._default_schema).upper()
        logger.info(f"Listing tables: schema={schema}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            # Use DBA_TABLES if accessible, otherwise ALL_TABLES
            view = "DBA_TABLES" if self._has_dba_views else "ALL_TABLES"

            query = f"""
                SELECT t.table_name,
                       t.num_rows,
                       ROUND(t.blocks * 8 / 1024, 2) as size_mb
                FROM {view} t
                WHERE t.owner = :schema
                ORDER BY t.num_rows DESC NULLS LAST
            """

            cur.execute(query, {"schema": schema})

            columns = [desc[0].lower() for desc in cur.description]
            tables = [dict(zip(columns, row)) for row in cur.fetchall()]

            logger.info(f"Found {len(tables)} tables")

            return {
                "status": "success",
                "schema": schema,
                "count": len(tables),
                "tables": tables,
                "note": t("oracle_no_dba_access") if not self._has_dba_views else None
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
            schema: Schema/owner name

        Returns:
            Table structure information
        """
        schema = (schema or self._default_schema).upper()
        table_name = table_name.upper()
        logger.info(f"Getting table structure: {schema}.{table_name}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            # Get column information
            cur.execute("""
                SELECT column_name,
                       data_type,
                       data_length,
                       data_precision,
                       data_scale,
                       nullable,
                       data_default
                FROM all_tab_columns
                WHERE owner = :schema AND table_name = :table_name
                ORDER BY column_id
            """, {"schema": schema, "table_name": table_name})

            columns = [desc[0].lower() for desc in cur.description]
            cols = [dict(zip(columns, row)) for row in cur.fetchall()]

            # Get primary key information
            cur.execute("""
                SELECT cols.column_name
                FROM all_constraints cons
                JOIN all_cons_columns cols ON cons.constraint_name = cols.constraint_name
                    AND cons.owner = cols.owner
                WHERE cons.constraint_type = 'P'
                  AND cons.owner = :schema
                  AND cons.table_name = :table_name
                ORDER BY cols.position
            """, {"schema": schema, "table_name": table_name})
            pk_columns = [row[0] for row in cur.fetchall()]

            # Get foreign key information
            cur.execute("""
                SELECT a.column_name,
                       c_pk.table_name AS foreign_table,
                       b.column_name AS foreign_column
                FROM all_cons_columns a
                JOIN all_constraints c ON a.constraint_name = c.constraint_name
                    AND a.owner = c.owner
                JOIN all_constraints c_pk ON c.r_constraint_name = c_pk.constraint_name
                    AND c.r_owner = c_pk.owner
                JOIN all_cons_columns b ON c_pk.constraint_name = b.constraint_name
                    AND c_pk.owner = b.owner
                    AND a.position = b.position
                WHERE c.constraint_type = 'R'
                  AND a.owner = :schema
                  AND a.table_name = :table_name
            """, {"schema": schema, "table_name": table_name})
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
                sql_upper.startswith("EXPLAIN") or
                sql_upper.startswith("WITH")):
            if " AS " in sql_upper or "(" in sql or "," in sql:
                sql = "SELECT " + sql
                sql_upper = sql.upper()
                logger.info(f"Auto-prepended SELECT to query")

        # Safety check - allow read-only statements
        is_safe = (
            sql_upper.startswith("SELECT") or
            sql_upper.startswith("EXPLAIN") or
            sql_upper.startswith("WITH")  # CTE queries
        )
        if not is_safe:
            return {
                "status": "error",
                "error": t("db_only_select")
            }

        func_check = self._check_function_call_in_select(sql_upper)
        if func_check:
            return func_check

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
            sql_upper.startswith("EXPLAIN")
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
        Run EXPLAIN PLAN to analyze query

        Args:
            sql: SQL statement
            analyze: Whether to gather actual execution statistics (not supported in Oracle EXPLAIN PLAN)

        Returns:
            EXPLAIN output result
        """
        logger.info(f"Running EXPLAIN analysis")
        logger.debug(f"SQL: {sql[:100]}...")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            # Use EXPLAIN PLAN FOR to generate plan
            explain_sql = f"EXPLAIN PLAN FOR {sql}"
            cur.execute(explain_sql)

            # Get plan from DBMS_XPLAN.DISPLAY
            cur.execute("""
                SELECT plan_table_output
                FROM TABLE(DBMS_XPLAN.DISPLAY(format => 'ALL'))
            """)

            plan_lines = [row[0] for row in cur.fetchall()]

            logger.info("EXPLAIN analysis completed")

            return {
                "status": "success",
                "explain_output": plan_lines,
                "plan": plan_lines,
                "analyzed": False,  # Oracle EXPLAIN PLAN doesn't execute
                "sql": sql
            }

        except Exception as e:
            logger.error(f"EXPLAIN analysis failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "sql": sql
            }
        finally:
            conn.close()

    def identify_slow_queries(self, min_duration_ms: float = 1000, limit: int = 20) -> Dict[str, Any]:
        """
        Identify slow queries from V$SQL

        Args:
            min_duration_ms: Minimum average execution time (milliseconds)
            limit: Number of results to return

        Returns:
            Dictionary containing slow query list
        """
        logger.info(f"Identifying slow queries: min_duration_ms={min_duration_ms}, limit={limit}")

        if not self._has_v_sql:
            return self._get_active_sessions(limit)

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            # Query V$SQL for slow queries (using Oracle 12c+ FETCH FIRST syntax)
            query = """
                SELECT sql_id,
                       SUBSTR(sql_text, 1, 500) as sql_text,
                       executions,
                       ROUND(elapsed_time/1000000, 2) as elapsed_sec,
                       ROUND(elapsed_time/NULLIF(executions, 0)/1000, 2) as avg_ms,
                       buffer_gets,
                       disk_reads,
                       rows_processed
                FROM v$sql
                WHERE elapsed_time/NULLIF(executions, 0)/1000 > :min_ms
                  AND executions > 0
                ORDER BY elapsed_time DESC
                FETCH FIRST :limit ROWS ONLY
            """

            cur.execute(query, {"min_ms": min_duration_ms, "limit": limit})

            if cur.description is None:
                return {
                    "status": "success",
                    "source": "v$sql",
                    "count": 0,
                    "queries": [],
                    "summary": {"total_slow_queries": 0}
                }

            columns = [desc[0].lower() for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]

            return {
                "status": "success",
                "source": "v$sql",
                "count": len(results),
                "queries": results,
                "summary": {
                    "total_slow_queries": len(results)
                }
            }

        except Exception as e:
            logger.error(f"Failed to identify slow queries: {e}")
            # Fallback to active sessions
            return self._get_active_sessions(limit)
        finally:
            conn.close()

    def _get_active_sessions(self, limit: int = 20) -> Dict[str, Any]:
        """Get current active sessions (fallback when V$SQL is not accessible)"""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            query = """
                SELECT s.sid,
                       s.serial#,
                       s.username,
                       s.status,
                       s.sql_id,
                       ROUND((SYSDATE - s.sql_exec_start) * 24 * 60 * 60, 2) as duration_seconds,
                       s.event,
                       s.wait_class,
                       SUBSTR(q.sql_text, 1, 500) as sql_text
                FROM v$session s
                LEFT JOIN v$sql q ON s.sql_id = q.sql_id AND s.sql_child_number = q.child_number
                WHERE s.type = 'USER'
                  AND s.status = 'ACTIVE'
                  AND s.sid != SYS_CONTEXT('USERENV', 'SID')
                ORDER BY s.sql_exec_start NULLS LAST
                FETCH FIRST :limit ROWS ONLY
            """
            cur.execute(query, {"limit": limit})

            if cur.description is None:
                return {
                    "status": "success",
                    "source": "v$session",
                    "note": t("oracle_no_v_sql_access"),
                    "count": 0,
                    "queries": []
                }

            columns = [desc[0].lower() for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]

            return {
                "status": "success",
                "source": "v$session",
                "note": t("oracle_no_v_sql_access"),
                "count": len(results),
                "queries": results
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            conn.close()

    def get_running_queries(self) -> Dict[str, Any]:
        """Get currently running queries"""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            query = """
                SELECT s.sid,
                       s.serial#,
                       s.username,
                       s.status,
                       s.sql_id,
                       ROUND((SYSDATE - s.sql_exec_start) * 24 * 60 * 60, 2) as duration_seconds,
                       s.event,
                       s.wait_class,
                       SUBSTR(q.sql_text, 1, 500) as sql_text
                FROM v$session s
                LEFT JOIN v$sql q ON s.sql_id = q.sql_id AND s.sql_child_number = q.child_number
                WHERE s.type = 'USER'
                  AND s.status = 'ACTIVE'
                  AND s.sid != SYS_CONTEXT('USERENV', 'SID')
                ORDER BY s.sql_exec_start NULLS LAST
            """
            cur.execute(query)

            if cur.description is None:
                return {
                    "status": "success",
                    "count": 0,
                    "queries": []
                }

            columns = [desc[0].lower() for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]

            return {
                "status": "success",
                "count": len(results),
                "queries": results
            }
        except Exception as e:
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
            schema: Schema/owner name

        Returns:
            Index usage information
        """
        schema = (schema or self._default_schema).upper()
        table_name = table_name.upper()
        logger.info(f"Checking index usage: {schema}.{table_name}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            # Use DBA_INDEXES if accessible, otherwise ALL_INDEXES
            idx_view = "DBA_INDEXES" if self._has_dba_views else "ALL_INDEXES"
            seg_view = "DBA_SEGMENTS" if self._has_dba_views else "USER_SEGMENTS"

            query = f"""
                SELECT i.index_name,
                       i.index_type,
                       i.uniqueness,
                       i.num_rows,
                       i.last_analyzed,
                       i.status,
                       ROUND(s.bytes/1024/1024, 2) as size_mb,
                       s.bytes as size_bytes
                FROM {idx_view} i
                LEFT JOIN {seg_view} s ON i.index_name = s.segment_name
                    AND i.owner = s.owner
                WHERE i.table_name = :table_name
                  AND i.owner = :schema
                ORDER BY s.bytes DESC NULLS LAST
            """

            cur.execute(query, {"table_name": table_name, "schema": schema})
            columns = [desc[0].lower() for desc in cur.description]
            indexes = [dict(zip(columns, row)) for row in cur.fetchall()]

            # Get index columns
            for idx in indexes:
                cur.execute("""
                    SELECT column_name
                    FROM all_ind_columns
                    WHERE index_name = :index_name
                      AND index_owner = :schema
                    ORDER BY column_position
                """, {"index_name": idx['index_name'], "schema": schema})
                idx['columns'] = [row[0] for row in cur.fetchall()]

            total_size = sum(idx.get('size_bytes') or 0 for idx in indexes)

            logger.info(f"Found {len(indexes)} indexes")

            return {
                "status": "success",
                "table": f"{schema}.{table_name}",
                "total_indexes": len(indexes),
                "total_size": total_size,
                "indexes": indexes,
                "note": t("oracle_no_dba_access") if not self._has_dba_views else None
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
            schema: Schema/owner name

        Returns:
            Table statistics
        """
        schema = (schema or self._default_schema).upper()
        table_name = table_name.upper()
        logger.info(f"Getting table stats: {schema}.{table_name}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            # Use DBA views if accessible
            tab_view = "DBA_TABLES" if self._has_dba_views else "ALL_TABLES"
            seg_view = "DBA_SEGMENTS" if self._has_dba_views else "USER_SEGMENTS"

            query = f"""
                SELECT t.owner as schemaname,
                       t.table_name as tablename,
                       t.num_rows,
                       t.blocks,
                       t.avg_row_len,
                       t.last_analyzed,
                       ROUND(s.bytes/1024/1024, 2) as size_mb,
                       t.compression,
                       t.partitioned
                FROM {tab_view} t
                LEFT JOIN {seg_view} s ON t.table_name = s.segment_name
                    AND t.owner = s.owner
                WHERE t.owner = :schema
                  AND t.table_name = :table_name
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
            concurrent: Whether to use ONLINE (Oracle's equivalent of concurrent)

        Returns:
            Creation result
        """
        logger.info(f"Creating index: concurrent={concurrent}")
        logger.info(f"SQL: {index_sql}")

        # Safety check
        if not index_sql.strip().upper().startswith("CREATE INDEX"):
            return {
                "status": "error",
                "error": t("db_only_create_index")
            }

        # Add ONLINE clause for Oracle (equivalent to CONCURRENTLY in PostgreSQL)
        if concurrent and "ONLINE" not in index_sql.upper():
            # Insert ONLINE before the semicolon or at the end
            index_sql = index_sql.rstrip().rstrip(';')
            index_sql = f"{index_sql} ONLINE"

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
        Update table statistics using DBMS_STATS

        Args:
            table_name: Table name
            schema: Schema/owner name

        Returns:
            Execution result
        """
        schema = (schema or self._default_schema).upper()
        table_name = table_name.upper()
        logger.info(f"Updating statistics: {schema}.{table_name}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            # Use DBMS_STATS.GATHER_TABLE_STATS for Oracle
            cur.execute("""
                BEGIN
                    DBMS_STATS.GATHER_TABLE_STATS(
                        ownname => :schema,
                        tabname => :table_name,
                        estimate_percent => DBMS_STATS.AUTO_SAMPLE_SIZE
                    );
                END;
            """, {"schema": schema, "table_name": table_name})
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
            schema: Schema/owner name
            limit: Number of rows to return

        Returns:
            Sample data
        """
        schema = (schema or self._default_schema).upper()
        table_name = table_name.upper()
        logger.info(f"Getting sample data: {schema}.{table_name}, limit={limit}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            # Use FETCH FIRST for Oracle 12c+
            sql = f'SELECT * FROM "{schema}"."{table_name}" FETCH FIRST :limit ROWS ONLY'
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

    def list_databases(self) -> Dict[str, Any]:
        """List all pluggable databases (PDBs) or return current service name for Oracle"""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            databases = []

            # Try to list PDBs (Oracle 12c+ with CDB architecture)
            try:
                cur.execute("""
                    SELECT name,
                           open_mode,
                           ROUND(total_size / 1024 / 1024, 2) AS size_mb
                    FROM v$pdbs
                    ORDER BY name
                """)
                columns = [desc[0].lower() for desc in cur.description]
                for row in cur.fetchall():
                    db = dict(zip(columns, row))
                    db["size"] = f"{db.pop('size_mb', 0)} MB"
                    databases.append(db)
            except Exception:
                pass

            current_db = self.db_config.get("database", "")

            # If no PDBs found, return current service name
            if not databases:
                databases = [{"name": current_db, "is_current": True}]
            else:
                for db in databases:
                    db["is_current"] = (db["name"].upper() == current_db.upper())

            return {
                "status": "success",
                "current_database": current_db,
                "instance": f"{self.db_config.get('host', 'localhost')}:{self.db_config.get('port', 1521)}",
                "count": len(databases),
                "databases": databases
            }
        except Exception as e:
            logger.error(f"Failed to list databases: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            conn.close()

    # ==================== Migration Support Methods ====================

    def get_all_objects(self, schema: str = None, object_types: List[str] = None) -> Dict[str, Any]:
        """Get all database objects for migration"""
        schema = (schema or self._default_schema).upper()
        logger.info(f"Getting all objects from schema: {schema}")

        if object_types is None:
            object_types = ["table", "view", "index", "sequence", "procedure", "function", "trigger", "constraint"]

        result = {
            "status": "success",
            "schema": schema,
            "objects": {}
        }

        # Use DBA views if accessible
        tab_view = "DBA_TABLES" if self._has_dba_views else "ALL_TABLES"
        obj_view = "DBA_OBJECTS" if self._has_dba_views else "ALL_OBJECTS"

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            # Get tables
            if "table" in object_types:
                cur.execute(f"""
                    SELECT table_name as name,
                           owner as schema,
                           num_rows as row_count,
                           blocks * 8192 as size_bytes,
                           tablespace_name,
                           compression,
                           partitioned
                    FROM {tab_view}
                    WHERE owner = :schema
                    ORDER BY table_name
                """, {"schema": schema})
                columns = [desc[0].lower() for desc in cur.description]
                result["objects"]["tables"] = [dict(zip(columns, row)) for row in cur.fetchall()]

            # Get views
            if "view" in object_types:
                view_view = "DBA_VIEWS" if self._has_dba_views else "ALL_VIEWS"
                cur.execute(f"""
                    SELECT view_name as name,
                           owner as schema,
                           text as definition
                    FROM {view_view}
                    WHERE owner = :schema
                    ORDER BY view_name
                """, {"schema": schema})
                columns = [desc[0].lower() for desc in cur.description]
                result["objects"]["views"] = [dict(zip(columns, row)) for row in cur.fetchall()]

            # Get indexes
            if "index" in object_types:
                idx_view = "DBA_INDEXES" if self._has_dba_views else "ALL_INDEXES"
                cur.execute(f"""
                    SELECT i.index_name as name,
                           i.table_name,
                           i.owner as schema,
                           i.index_type,
                           CASE WHEN i.uniqueness = 'UNIQUE' THEN 1 ELSE 0 END as is_unique,
                           CASE WHEN c.constraint_type = 'P' THEN 1 ELSE 0 END as is_primary
                    FROM {idx_view} i
                    LEFT JOIN all_constraints c ON i.index_name = c.index_name AND i.owner = c.owner
                    WHERE i.owner = :schema
                    ORDER BY i.table_name, i.index_name
                """, {"schema": schema})
                columns = [desc[0].lower() for desc in cur.description]
                result["objects"]["indexes"] = [dict(zip(columns, row)) for row in cur.fetchall()]

            # Get sequences
            if "sequence" in object_types:
                seq_view = "DBA_SEQUENCES" if self._has_dba_views else "ALL_SEQUENCES"
                cur.execute(f"""
                    SELECT sequence_name as name,
                           sequence_owner as schema,
                           min_value,
                           max_value,
                           increment_by,
                           CASE WHEN cycle_flag = 'Y' THEN 1 ELSE 0 END as is_cycle,
                           cache_size,
                           last_number
                    FROM {seq_view}
                    WHERE sequence_owner = :schema
                    ORDER BY sequence_name
                """, {"schema": schema})
                columns = [desc[0].lower() for desc in cur.description]
                result["objects"]["sequences"] = [dict(zip(columns, row)) for row in cur.fetchall()]

            # Get procedures
            if "procedure" in object_types:
                cur.execute(f"""
                    SELECT object_name as name,
                           owner as schema,
                           'procedure' as type,
                           status
                    FROM {obj_view}
                    WHERE owner = :schema AND object_type = 'PROCEDURE'
                    ORDER BY object_name
                """, {"schema": schema})
                columns = [desc[0].lower() for desc in cur.description]
                result["objects"]["procedures"] = [dict(zip(columns, row)) for row in cur.fetchall()]

            # Get functions
            if "function" in object_types:
                cur.execute(f"""
                    SELECT object_name as name,
                           owner as schema,
                           'function' as type,
                           status
                    FROM {obj_view}
                    WHERE owner = :schema AND object_type = 'FUNCTION'
                    ORDER BY object_name
                """, {"schema": schema})
                columns = [desc[0].lower() for desc in cur.description]
                result["objects"]["functions"] = [dict(zip(columns, row)) for row in cur.fetchall()]

            # Get triggers
            if "trigger" in object_types:
                trig_view = "DBA_TRIGGERS" if self._has_dba_views else "ALL_TRIGGERS"
                cur.execute(f"""
                    SELECT trigger_name as name,
                           table_name,
                           owner as schema,
                           trigger_type as timing,
                           triggering_event as event,
                           status
                    FROM {trig_view}
                    WHERE owner = :schema
                    ORDER BY table_name, trigger_name
                """, {"schema": schema})
                columns = [desc[0].lower() for desc in cur.description]
                result["objects"]["triggers"] = [dict(zip(columns, row)) for row in cur.fetchall()]

            # Get constraints
            if "constraint" in object_types:
                cur.execute("""
                    SELECT constraint_name as name,
                           table_name,
                           owner as schema,
                           constraint_type,
                           search_condition as definition,
                           r_constraint_name as referenced_constraint,
                           status
                    FROM all_constraints
                    WHERE owner = :schema
                    ORDER BY table_name, constraint_name
                """, {"schema": schema})
                columns = [desc[0].lower() for desc in cur.description]
                result["objects"]["constraints"] = [dict(zip(columns, row)) for row in cur.fetchall()]

            # Calculate totals
            total_count = sum(len(result["objects"].get(k, [])) for k in result["objects"])
            result["total_count"] = total_count

            logger.info(f"Found {total_count} total objects")
            return result

        except Exception as e:
            logger.error(f"Failed to get all objects: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            conn.close()

    def get_object_ddl(self, object_type: str, object_name: str, schema: str = None) -> Dict[str, Any]:
        """Get DDL for a specific database object using DBMS_METADATA"""
        schema = (schema or self._default_schema).upper()
        object_name = object_name.upper()
        logger.info(f"Getting DDL for {object_type}: {schema}.{object_name}")

        # Map object types to Oracle DBMS_METADATA object types
        type_map = {
            "table": "TABLE",
            "view": "VIEW",
            "index": "INDEX",
            "sequence": "SEQUENCE",
            "procedure": "PROCEDURE",
            "function": "FUNCTION",
            "trigger": "TRIGGER"
        }

        oracle_type = type_map.get(object_type.lower())
        if not oracle_type:
            return {"status": "error", "error": f"Unsupported object type: {object_type}"}

        conn = self.get_connection()
        try:
            cur = conn.cursor()
            ddl = None
            dependencies = []

            # Use DBMS_METADATA.GET_DDL to get DDL
            cur.execute("""
                SELECT DBMS_METADATA.GET_DDL(:obj_type, :obj_name, :schema) FROM DUAL
            """, {"obj_type": oracle_type, "obj_name": object_name, "schema": schema})
            result = cur.fetchone()
            if result and result[0]:
                ddl = result[0].read() if hasattr(result[0], 'read') else str(result[0])

            # Get dependencies for tables
            if object_type.lower() == "table":
                cur.execute("""
                    SELECT DISTINCT c_pk.table_name
                    FROM all_constraints c
                    JOIN all_constraints c_pk ON c.r_constraint_name = c_pk.constraint_name
                        AND c.r_owner = c_pk.owner
                    WHERE c.constraint_type = 'R'
                      AND c.owner = :schema
                      AND c.table_name = :table_name
                """, {"schema": schema, "table_name": object_name})
                dependencies = [{"type": "table", "name": row[0]} for row in cur.fetchall()]

            if ddl:
                return {
                    "status": "success",
                    "object_type": object_type,
                    "object_name": object_name,
                    "schema": schema,
                    "ddl": ddl,
                    "dependencies": dependencies
                }
            else:
                return {
                    "status": "error",
                    "error": f"Object not found: {object_type} {schema}.{object_name}"
                }

        except Exception as e:
            logger.error(f"Failed to get DDL: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            conn.close()

    def get_object_dependencies(self, schema: str = None) -> Dict[str, Any]:
        """Get object dependencies in the database"""
        schema = (schema or self._default_schema).upper()
        logger.info(f"Getting object dependencies for schema: {schema}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            # Use ALL_DEPENDENCIES for dependency info
            cur.execute("""
                SELECT name as object_name,
                       type as object_type,
                       referenced_name as depends_on_name,
                       referenced_type as depends_on_type
                FROM all_dependencies
                WHERE owner = :schema
                  AND referenced_owner = :schema
                  AND name != referenced_name
                ORDER BY name
            """, {"schema": schema})

            columns = [desc[0].lower() for desc in cur.description]
            dependencies = [dict(zip(columns, row)) for row in cur.fetchall()]

            # Build dependency graph
            dependency_graph = {}
            for dep in dependencies:
                obj_name = dep["object_name"]
                dep_name = dep["depends_on_name"]
                if obj_name not in dependency_graph:
                    dependency_graph[obj_name] = []
                dependency_graph[obj_name].append(dep_name)

            return {
                "status": "success",
                "schema": schema,
                "dependencies": dependencies,
                "dependency_graph": dependency_graph
            }

        except Exception as e:
            logger.error(f"Failed to get dependencies: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            conn.close()

    def get_foreign_key_dependencies(self, schema: str = None) -> Dict[str, Any]:
        """Get foreign key dependencies between tables"""
        schema = (schema or self._default_schema).upper()
        logger.info(f"Getting FK dependencies for schema: {schema}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            cur.execute("""
                SELECT a.constraint_name,
                       a.table_name,
                       cols.column_name,
                       c_pk.table_name as referenced_table,
                       cols_pk.column_name as referenced_column
                FROM all_constraints a
                JOIN all_constraints c_pk ON a.r_constraint_name = c_pk.constraint_name
                    AND a.r_owner = c_pk.owner
                JOIN all_cons_columns cols ON a.constraint_name = cols.constraint_name
                    AND a.owner = cols.owner
                JOIN all_cons_columns cols_pk ON c_pk.constraint_name = cols_pk.constraint_name
                    AND c_pk.owner = cols_pk.owner
                    AND cols.position = cols_pk.position
                WHERE a.constraint_type = 'R'
                  AND a.owner = :schema
                ORDER BY a.table_name
            """, {"schema": schema})

            columns = [desc[0].lower() for desc in cur.description]
            foreign_keys = [dict(zip(columns, row)) for row in cur.fetchall()]

            # Build dependency graph for topological sort
            tables = set()
            graph = {}
            for fk in foreign_keys:
                tables.add(fk["table_name"])
                tables.add(fk["referenced_table"])
                if fk["table_name"] not in graph:
                    graph[fk["table_name"]] = set()
                graph[fk["table_name"]].add(fk["referenced_table"])

            # Topological sort
            table_order = self._topological_sort(tables, graph)

            return {
                "status": "success",
                "schema": schema,
                "foreign_keys": foreign_keys,
                "table_order": table_order
            }

        except Exception as e:
            logger.error(f"Failed to get FK dependencies: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            conn.close()

    def _topological_sort(self, nodes: set, graph: dict) -> List[str]:
        """Perform topological sort on dependency graph"""
        result = []
        visited = set()
        temp_mark = set()

        def visit(node):
            if node in temp_mark:
                return  # Cycle detected, skip
            if node not in visited:
                temp_mark.add(node)
                for dep in graph.get(node, []):
                    visit(dep)
                temp_mark.remove(node)
                visited.add(node)
                result.append(node)

        for node in nodes:
            if node not in visited:
                visit(node)

        return result
