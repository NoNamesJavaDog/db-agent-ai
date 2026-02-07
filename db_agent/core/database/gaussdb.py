"""
GaussDB Database Tools - Centralized and Distributed mode support
GaussDB database tools using pg8000 driver (supports sha256 authentication on Windows)
"""
import pg8000
import pg8000.native
from typing import Dict, Any, List
import logging
import re
from db_agent.i18n import t
from .base import BaseDatabaseTools

logger = logging.getLogger(__name__)


class GaussDBTools(BaseDatabaseTools):
    """GaussDB database tools implementation (Centralized and Distributed modes)"""

    def __init__(self, db_config: Dict[str, Any]):
        super().__init__()
        self.db_config = db_config
        self.db_version = None
        self.db_version_num = None
        self.db_version_full = None
        self._is_distributed = False
        self._init_db_info()
        mode_str = 'Distributed' if self._is_distributed else 'Centralized'
        logger.info(f"GaussDB tools initialized: {db_config['host']}:{db_config['database']} "
                    f"(GaussDB {self.db_version}, {mode_str})")

    @property
    def db_type(self) -> str:
        return "gaussdb"

    def get_connection(self, retries: int = 3):
        """Get database connection using pg8000 (supports sha256 auth)

        Args:
            retries: Number of retry attempts for transient failures
        """
        import time
        last_error = None
        for attempt in range(retries):
            try:
                return pg8000.connect(
                    host=self.db_config.get("host", "localhost"),
                    port=int(self.db_config.get("port", 5432)),
                    database=self.db_config.get("database"),
                    user=self.db_config.get("user"),
                    password=self.db_config.get("password")
                )
            except Exception as e:
                last_error = e
                error_msg = str(e).lower()
                # Retry on transient connection errors
                if attempt < retries - 1 and (
                    "connection" in error_msg or
                    "timeout" in error_msg or
                    "refused" in error_msg
                ):
                    logger.warning(f"Connection attempt {attempt + 1} failed: {e}, retrying...")
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                else:
                    raise
        raise last_error

    def _init_db_info(self):
        """Initialize database information, detect Centralized/Distributed mode"""
        conn = self.get_connection()
        try:
            cur = conn.cursor()

            # Get version information
            cur.execute("SELECT version()")
            self.db_version_full = cur.fetchone()[0]

            # Parse version number (e.g., "GaussDB Kernel V500R002C10" or "(GaussDB 8.1.3)")
            match = re.search(r'V(\d+)R(\d+)C(\d+)|(\d+)\.(\d+)\.(\d+)', self.db_version_full)
            if match:
                groups = [g for g in match.groups() if g]
                if len(groups) >= 3:
                    self.db_version = f"{groups[0]}.{groups[1]}.{groups[2]}"
                    try:
                        self.db_version_num = int(groups[0]) * 10000 + int(groups[1]) * 100 + int(groups[2])
                    except ValueError:
                        self.db_version_num = 0
                else:
                    self.db_version = "unknown"
                    self.db_version_num = 0
            else:
                self.db_version = "unknown"
                self.db_version_num = 0

            # Detect distributed mode (check pgxc_node table)
            try:
                cur.execute("SELECT count(*) FROM pgxc_node WHERE node_type IN ('C', 'D')")
                node_count = cur.fetchone()[0]
                self._is_distributed = node_count > 1
            except Exception:
                conn.rollback()
                self._is_distributed = False

        except Exception as e:
            logger.warning(f"Failed to get GaussDB version info: {e}")
            self.db_version = "unknown"
            self.db_version_num = 0
            self.db_version_full = "unknown"
        finally:
            conn.close()

    def get_db_info(self) -> Dict[str, Any]:
        """Get database information"""
        mode = "distributed" if self._is_distributed else "centralized"
        return {
            "type": "gaussdb",
            "mode": mode,
            "version": self.db_version,
            "version_num": self.db_version_num,
            "version_full": self.db_version_full,
            "host": self.db_config.get("host"),
            "database": self.db_config.get("database"),
            "is_distributed": self._is_distributed
        }

    def get_running_queries(self, limit: int = 20) -> Dict[str, Any]:
        """Get currently running queries"""
        conn = self.get_connection()
        try:
            cur = conn.cursor()

            if self._is_distributed:
                # Distributed mode uses PGXC_STAT_ACTIVITY
                query = """
                    SELECT
                        coorname,
                        pid,
                        usename,
                        datname,
                        application_name,
                        client_addr,
                        state,
                        waiting,
                        query_start,
                        now() - query_start AS duration,
                        query_id,
                        LEFT(query, 500) as query
                    FROM pgxc_stat_activity
                    WHERE state = 'active'
                      AND query NOT LIKE '%%pgxc_stat_activity%%'
                    ORDER BY query_start
                    LIMIT %s
                """
            else:
                # Centralized mode uses PG_STAT_ACTIVITY
                query = """
                    SELECT
                        pid,
                        usename,
                        datname,
                        application_name,
                        client_addr,
                        state,
                        waiting,
                        query_start,
                        now() - query_start AS duration,
                        query_id,
                        LEFT(query, 500) as query
                    FROM pg_stat_activity
                    WHERE state = 'active'
                      AND pid != pg_backend_pid()
                    ORDER BY query_start
                    LIMIT %s
                """

            cur.execute(query, (limit,))

            if cur.description is None:
                return {
                    "status": "success",
                    "mode": "distributed" if self._is_distributed else "centralized",
                    "count": 0,
                    "queries": []
                }

            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]

            return {
                "status": "success",
                "mode": "distributed" if self._is_distributed else "centralized",
                "count": len(results),
                "queries": results
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}
        finally:
            conn.close()

    def identify_slow_queries(self, min_duration_ms: float = 1000, limit: int = 20) -> Dict[str, Any]:
        """Identify slow queries"""
        conn = self.get_connection()
        try:
            cur = conn.cursor()

            if self._is_distributed:
                # Distributed: Use PGXC_STAT_ACTIVITY for current slow queries
                query = """
                    SELECT
                        coorname,
                        pid,
                        usename,
                        datname,
                        state,
                        query_start,
                        EXTRACT(EPOCH FROM (now() - query_start)) * 1000 AS duration_ms,
                        query_id,
                        LEFT(query, 500) as query
                    FROM pgxc_stat_activity
                    WHERE state = 'active'
                      AND query_start < now() - interval '%s milliseconds'
                    ORDER BY query_start
                    LIMIT %s
                """
            else:
                # Centralized: Use PG_STAT_ACTIVITY
                query = """
                    SELECT
                        pid,
                        usename,
                        datname,
                        state,
                        query_start,
                        EXTRACT(EPOCH FROM (now() - query_start)) * 1000 AS duration_ms,
                        query_id,
                        LEFT(query, 500) as query
                    FROM pg_stat_activity
                    WHERE state = 'active'
                      AND query_start < now() - interval '%s milliseconds'
                      AND pid != pg_backend_pid()
                    ORDER BY query_start
                    LIMIT %s
                """

            cur.execute(query, (min_duration_ms, limit))

            if cur.description is None:
                return {
                    "status": "success",
                    "source": "pgxc_stat_activity" if self._is_distributed else "pg_stat_activity",
                    "count": 0,
                    "queries": []
                }

            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]

            return {
                "status": "success",
                "source": "pgxc_stat_activity" if self._is_distributed else "pg_stat_activity",
                "count": len(results),
                "queries": results
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}
        finally:
            conn.close()

    def run_explain(self, sql: str, analyze: bool = False) -> Dict[str, Any]:
        """Analyze SQL execution plan"""
        logger.info(f"Running EXPLAIN analysis: analyze={analyze}")
        logger.debug(f"SQL: {sql[:100]}...")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            if analyze:
                explain_sql = f"EXPLAIN ANALYZE {sql}"
                cur.execute(explain_sql)
                results = cur.fetchall()
                result = "\n".join([row[0] for row in results])
            else:
                explain_sql = f"EXPLAIN (FORMAT JSON) {sql}"
                cur.execute(explain_sql)
                result = cur.fetchone()[0]

            logger.info("EXPLAIN analysis completed")

            return {
                "status": "success",
                "explain_output": result,
                "analyzed": analyze,
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

    def check_index_usage(self, table_name: str, schema: str = "public") -> Dict[str, Any]:
        """Check index usage for a table"""
        logger.info(f"Checking index usage: {schema}.{table_name}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            # Get index information
            query = """
                SELECT
                    i.indexname,
                    i.indexdef,
                    s.idx_scan,
                    s.idx_tup_read,
                    s.idx_tup_fetch,
                    pg_size_pretty(pg_relation_size(i.schemaname||'.'||i.indexname)) as index_size,
                    pg_relation_size(i.schemaname||'.'||i.indexname) as index_size_bytes
                FROM pg_indexes i
                LEFT JOIN pg_stat_user_indexes s
                    ON i.schemaname = s.schemaname
                    AND i.indexname = s.indexrelname
                WHERE i.schemaname = %s AND i.tablename = %s
                ORDER BY s.idx_scan DESC NULLS LAST;
            """

            cur.execute(query, (schema, table_name))
            columns = [desc[0] for desc in cur.description]
            indexes = [dict(zip(columns, row)) for row in cur.fetchall()]

            # Analysis
            unused_indexes = [idx for idx in indexes if idx['idx_scan'] == 0 or idx['idx_scan'] is None]
            total_size = sum(idx['index_size_bytes'] or 0 for idx in indexes)

            logger.info(f"Found {len(indexes)} indexes, {len(unused_indexes)} unused")

            return {
                "status": "success",
                "table": f"{schema}.{table_name}",
                "total_indexes": len(indexes),
                "unused_count": len(unused_indexes),
                "total_size": total_size,
                "indexes": indexes,
                "analysis": {
                    "has_unused_indexes": len(unused_indexes) > 0,
                    "unused_indexes": unused_indexes
                }
            }

        except Exception as e:
            logger.error(f"Index check failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            conn.close()

    def get_table_stats(self, table_name: str, schema: str = "public") -> Dict[str, Any]:
        """Get table statistics"""
        logger.info(f"Getting table stats: {schema}.{table_name}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            if self._is_distributed:
                # Distributed mode: use PGXC_STAT_TABLE if available
                query = """
                    SELECT
                        schemaname,
                        relname as tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname)) as total_size,
                        pg_size_pretty(pg_relation_size(schemaname||'.'||relname)) as table_size,
                        pg_size_pretty(pg_indexes_size(schemaname||'.'||relname)) as indexes_size,
                        n_live_tup,
                        n_dead_tup,
                        ROUND(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) as dead_ratio,
                        last_vacuum,
                        last_autovacuum,
                        last_analyze,
                        last_autoanalyze,
                        seq_scan,
                        seq_tup_read,
                        idx_scan,
                        idx_tup_fetch
                    FROM pg_stat_user_tables
                    WHERE schemaname = %s AND relname = %s;
                """
            else:
                query = """
                    SELECT
                        schemaname,
                        relname as tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname)) as total_size,
                        pg_size_pretty(pg_relation_size(schemaname||'.'||relname)) as table_size,
                        pg_size_pretty(pg_indexes_size(schemaname||'.'||relname)) as indexes_size,
                        n_live_tup,
                        n_dead_tup,
                        ROUND(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) as dead_ratio,
                        last_vacuum,
                        last_autovacuum,
                        last_analyze,
                        last_autoanalyze,
                        seq_scan,
                        seq_tup_read,
                        idx_scan,
                        idx_tup_fetch
                    FROM pg_stat_user_tables
                    WHERE schemaname = %s AND relname = %s;
                """

            cur.execute(query, (schema, table_name))
            columns = [desc[0] for desc in cur.description]
            result = cur.fetchone()

            if result:
                stats = dict(zip(columns, result))
                logger.info("Table stats retrieved successfully")
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
        """Create index"""
        logger.info(f"Creating index: concurrent={concurrent}")
        logger.info(f"SQL: {index_sql}")

        # Safety check
        if not index_sql.strip().upper().startswith("CREATE INDEX"):
            return {
                "status": "error",
                "error": t("db_only_create_index")
            }

        # Add CONCURRENTLY (GaussDB supports this like PostgreSQL)
        if concurrent and "CONCURRENTLY" not in index_sql.upper():
            index_sql = index_sql.replace("CREATE INDEX", "CREATE INDEX CONCURRENTLY", 1)

        conn = self.get_connection()
        conn.autocommit = True

        try:
            cur = conn.cursor()
            cur.execute(index_sql)

            logger.info("Index created successfully")

            return {
                "status": "success",
                "message": t("db_index_created"),
                "sql": index_sql
            }

        except Exception as e:
            logger.error(f"Index creation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "sql": index_sql
            }
        finally:
            conn.close()

    def analyze_table(self, table_name: str, schema: str = "public") -> Dict[str, Any]:
        """Update table statistics (ANALYZE)"""
        logger.info(f"Updating statistics: {schema}.{table_name}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(f"ANALYZE {schema}.{table_name};")
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

    def execute_safe_query(self, sql: str) -> Dict[str, Any]:
        """Execute safe read-only query"""
        logger.info("Executing safe query")
        logger.debug(f"SQL: {sql[:100]}...")

        # Clean up the SQL
        sql = sql.strip()
        sql_upper = sql.upper()

        # Auto-fix: If SQL looks like SELECT columns but missing SELECT keyword, prepend it
        if not (sql_upper.startswith("SELECT") or
                sql_upper.startswith("SHOW") or
                sql_upper.startswith("EXPLAIN") or
                sql_upper.startswith("WITH")):
            # Check if it looks like a SELECT expression (contains AS, column aliases, or functions)
            if " AS " in sql_upper or "(" in sql or "," in sql:
                sql = "SELECT " + sql
                sql_upper = sql.upper()
                logger.info(f"Auto-prepended SELECT to query")

        # Safety check - allow read-only statements
        is_safe = (
            sql_upper.startswith("SELECT") or
            sql_upper.startswith("SHOW") or
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

            columns = [desc[0] for desc in cur.description] if cur.description else []
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
        """Execute any SQL statement (INSERT/UPDATE/DELETE/CREATE/ALTER/DROP etc.)"""
        sql_upper = sql.strip().upper()

        # Read-only queries execute directly without confirmation
        is_readonly = (
            sql_upper.startswith("SELECT") or
            sql_upper.startswith("SHOW") or
            sql_upper.startswith("EXPLAIN")
        )

        if is_readonly:
            conn = self.get_connection()
            try:
                cur = conn.cursor()
                cur.execute(sql)
                columns = [desc[0] for desc in cur.description] if cur.description else []
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

        # Check if SQL requires autocommit (cannot run inside transaction block)
        needs_autocommit = (
            sql_upper.startswith("CREATE DATABASE") or
            sql_upper.startswith("DROP DATABASE") or
            sql_upper.startswith("VACUUM")
        )

        # Confirmed, execute operation
        conn = self.get_connection()
        if needs_autocommit:
            conn.autocommit = True
        try:
            cur = conn.cursor()
            cur.execute(sql)
            rowcount = cur.rowcount
            if not needs_autocommit:
                conn.commit()
            return {
                "status": "success",
                "type": "execute",
                "affected_rows": rowcount,
                "message": t("db_execute_success", count=rowcount)
            }

        except Exception as e:
            if not needs_autocommit:
                conn.rollback()
            logger.error(f"SQL execution failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "sql": sql
            }
        finally:
            conn.close()

    def list_tables(self, schema: str = "public") -> Dict[str, Any]:
        """List all tables in the database"""
        logger.info(f"Listing tables: schema={schema}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables
                WHERE schemaname = %s
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
            """, (schema,))

            columns = [desc[0] for desc in cur.description]
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

    def describe_table(self, table_name: str, schema: str = "public") -> Dict[str, Any]:
        """Get table structure information"""
        logger.info(f"Getting table structure: {schema}.{table_name}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            # Get column information
            cur.execute("""
                SELECT
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position;
            """, (schema, table_name))

            columns = [desc[0] for desc in cur.description]
            cols = [dict(zip(columns, row)) for row in cur.fetchall()]

            # Get primary key information
            cur.execute("""
                SELECT a.attname as column_name
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = %s::regclass AND i.indisprimary;
            """, (f"{schema}.{table_name}",))
            pk_columns = [row[0] for row in cur.fetchall()]

            # Get foreign key information
            cur.execute("""
                SELECT
                    kcu.column_name,
                    ccu.table_name AS foreign_table,
                    ccu.column_name AS foreign_column
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = %s
                    AND tc.table_name = %s;
            """, (schema, table_name))
            fk_columns = [desc[0] for desc in cur.description]
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

    def get_sample_data(self, table_name: str, schema: str = "public", limit: int = 10) -> Dict[str, Any]:
        """Get sample data from a table"""
        logger.info(f"Getting sample data: {schema}.{table_name}, limit={limit}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM {schema}.{table_name} LIMIT %s;", (limit,))

            columns = [desc[0] for desc in cur.description]
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

    def get_node_info(self) -> Dict[str, Any]:
        """Get GaussDB cluster node information (distributed mode only)"""
        if not self._is_distributed:
            return {
                "status": "success",
                "mode": "centralized",
                "message": "This is a centralized GaussDB instance, no cluster nodes.",
                "nodes": []
            }

        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    node_name,
                    node_type,
                    node_host,
                    node_port,
                    CASE node_type
                        WHEN 'C' THEN 'Coordinator'
                        WHEN 'D' THEN 'Datanode'
                        ELSE node_type
                    END as node_type_name
                FROM pgxc_node
                ORDER BY node_type, node_name;
            """)

            columns = [desc[0] for desc in cur.description]
            nodes = [dict(zip(columns, row)) for row in cur.fetchall()]

            coordinators = [n for n in nodes if n['node_type'] == 'C']
            datanodes = [n for n in nodes if n['node_type'] == 'D']

            return {
                "status": "success",
                "mode": "distributed",
                "total_nodes": len(nodes),
                "coordinators": len(coordinators),
                "datanodes": len(datanodes),
                "nodes": nodes
            }

        except Exception as e:
            logger.error(f"Failed to get node info: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            conn.close()

    def get_thread_wait_status(self, limit: int = 50) -> Dict[str, Any]:
        """Get thread wait status (useful for diagnosing lock contention)"""
        conn = self.get_connection()
        try:
            cur = conn.cursor()

            if self._is_distributed:
                query = """
                    SELECT
                        node_name,
                        db_name,
                        thread_name,
                        query_id,
                        tid,
                        lwtid,
                        ptid,
                        tlevel,
                        smpid,
                        wait_status,
                        wait_event,
                        LEFT(query, 200) as query
                    FROM pgxc_thread_wait_status
                    WHERE wait_status != 'wait cmd'
                    ORDER BY wait_status
                    LIMIT %s;
                """
            else:
                query = """
                    SELECT
                        db_name,
                        thread_name,
                        query_id,
                        tid,
                        lwtid,
                        ptid,
                        tlevel,
                        smpid,
                        wait_status,
                        wait_event,
                        LEFT(query, 200) as query
                    FROM pg_thread_wait_status
                    WHERE wait_status != 'wait cmd'
                    ORDER BY wait_status
                    LIMIT %s;
                """

            cur.execute(query, (limit,))

            if cur.description is None:
                return {
                    "status": "success",
                    "count": 0,
                    "threads": []
                }

            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]

            return {
                "status": "success",
                "mode": "distributed" if self._is_distributed else "centralized",
                "count": len(results),
                "threads": results
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}
        finally:
            conn.close()

    def get_locks_info(self, limit: int = 50) -> Dict[str, Any]:
        """Get lock information"""
        conn = self.get_connection()
        try:
            cur = conn.cursor()

            if self._is_distributed:
                query = """
                    SELECT
                        locktype,
                        database,
                        relation,
                        page,
                        tuple,
                        virtualxid,
                        transactionid,
                        classid,
                        objid,
                        objsubid,
                        virtualtransaction,
                        pid,
                        mode,
                        granted,
                        fastpath
                    FROM pgxc_locks
                    WHERE NOT granted
                    LIMIT %s;
                """
            else:
                query = """
                    SELECT
                        locktype,
                        database,
                        relation,
                        page,
                        tuple,
                        virtualxid,
                        transactionid,
                        classid,
                        objid,
                        objsubid,
                        virtualtransaction,
                        pid,
                        mode,
                        granted,
                        fastpath
                    FROM pg_locks
                    WHERE NOT granted
                    LIMIT %s;
                """

            cur.execute(query, (limit,))

            if cur.description is None:
                return {
                    "status": "success",
                    "count": 0,
                    "locks": [],
                    "message": "No waiting locks found"
                }

            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]

            return {
                "status": "success",
                "mode": "distributed" if self._is_distributed else "centralized",
                "count": len(results),
                "locks": results
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}
        finally:
            conn.close()

    def list_databases(self) -> Dict[str, Any]:
        """List all databases on the GaussDB server instance"""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT datname AS name,
                       pg_size_pretty(pg_database_size(datname)) AS size,
                       pg_catalog.pg_get_userbyid(datdba) AS owner
                FROM pg_database
                WHERE datistemplate = false
                ORDER BY datname
            """)
            columns = [desc[0] for desc in cur.description]
            databases = [dict(zip(columns, row)) for row in cur.fetchall()]
            current_db = self.db_config.get("database", "")
            for db in databases:
                db["is_current"] = (db["name"] == current_db)
            return {
                "status": "success",
                "current_database": current_db,
                "instance": f"{self.db_config.get('host', 'localhost')}:{self.db_config.get('port', 5432)}",
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
        schema = schema or "public"
        logger.info(f"Getting all objects from schema: {schema}")

        if object_types is None:
            object_types = ["table", "view", "index", "sequence", "procedure", "function", "trigger", "constraint"]

        result = {
            "status": "success",
            "schema": schema,
            "mode": "distributed" if self._is_distributed else "centralized",
            "objects": {}
        }

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            # Get tables (GaussDB uses pg_tables like PostgreSQL)
            if "table" in object_types:
                cur.execute("""
                    SELECT
                        t.tablename as name,
                        t.schemaname as schema,
                        COALESCE(s.n_live_tup, 0) as row_count,
                        pg_total_relation_size(t.schemaname||'.'||t.tablename) as size_bytes
                    FROM pg_tables t
                    LEFT JOIN pg_stat_user_tables s ON t.schemaname = s.schemaname AND t.tablename = s.relname
                    WHERE t.schemaname = %s
                    ORDER BY t.tablename
                """, (schema,))
                columns = [desc[0] for desc in cur.description]
                result["objects"]["tables"] = [dict(zip(columns, row)) for row in cur.fetchall()]

            # Get views
            if "view" in object_types:
                cur.execute("""
                    SELECT
                        viewname as name,
                        schemaname as schema,
                        definition
                    FROM pg_views
                    WHERE schemaname = %s
                    ORDER BY viewname
                """, (schema,))
                columns = [desc[0] for desc in cur.description]
                result["objects"]["views"] = [dict(zip(columns, row)) for row in cur.fetchall()]

            # Get indexes
            if "index" in object_types:
                cur.execute("""
                    SELECT
                        i.indexname as name,
                        i.tablename as table_name,
                        i.schemaname as schema,
                        i.indexdef as definition,
                        idx.indisunique as is_unique,
                        idx.indisprimary as is_primary
                    FROM pg_indexes i
                    JOIN pg_class c ON c.relname = i.indexname
                    JOIN pg_index idx ON idx.indexrelid = c.oid
                    WHERE i.schemaname = %s
                    ORDER BY i.tablename, i.indexname
                """, (schema,))
                columns = [desc[0] for desc in cur.description]
                result["objects"]["indexes"] = [dict(zip(columns, row)) for row in cur.fetchall()]

            # Get sequences
            if "sequence" in object_types:
                cur.execute("""
                    SELECT
                        sequencename as name,
                        schemaname as schema,
                        start_value,
                        min_value,
                        max_value,
                        increment_by,
                        cycle as is_cycle,
                        cache_size
                    FROM pg_sequences
                    WHERE schemaname = %s
                    ORDER BY sequencename
                """, (schema,))
                columns = [desc[0] for desc in cur.description]
                result["objects"]["sequences"] = [dict(zip(columns, row)) for row in cur.fetchall()]

            # Get functions/procedures
            if "function" in object_types or "procedure" in object_types:
                cur.execute("""
                    SELECT
                        p.proname as name,
                        n.nspname as schema,
                        CASE p.prokind
                            WHEN 'f' THEN 'function'
                            WHEN 'p' THEN 'procedure'
                            WHEN 'a' THEN 'aggregate'
                            WHEN 'w' THEN 'window'
                            ELSE 'function'
                        END as type,
                        pg_get_function_arguments(p.oid) as parameters,
                        pg_get_function_result(p.oid) as return_type,
                        l.lanname as language
                    FROM pg_proc p
                    JOIN pg_namespace n ON p.pronamespace = n.oid
                    JOIN pg_language l ON p.prolang = l.oid
                    WHERE n.nspname = %s
                    ORDER BY p.proname
                """, (schema,))
                columns = [desc[0] for desc in cur.description]
                all_routines = [dict(zip(columns, row)) for row in cur.fetchall()]

                if "function" in object_types:
                    result["objects"]["functions"] = [r for r in all_routines if r["type"] == "function"]
                if "procedure" in object_types:
                    result["objects"]["procedures"] = [r for r in all_routines if r["type"] == "procedure"]

            # Get triggers
            if "trigger" in object_types:
                cur.execute("""
                    SELECT
                        t.tgname as name,
                        c.relname as table_name,
                        n.nspname as schema,
                        pg_get_triggerdef(t.oid) as definition
                    FROM pg_trigger t
                    JOIN pg_class c ON t.tgrelid = c.oid
                    JOIN pg_namespace n ON c.relnamespace = n.oid
                    WHERE n.nspname = %s
                      AND NOT t.tgisinternal
                    ORDER BY c.relname, t.tgname
                """, (schema,))
                columns = [desc[0] for desc in cur.description]
                result["objects"]["triggers"] = [dict(zip(columns, row)) for row in cur.fetchall()]

            # Get constraints
            if "constraint" in object_types:
                cur.execute("""
                    SELECT
                        con.conname as name,
                        c.relname as table_name,
                        n.nspname as schema,
                        CASE con.contype
                            WHEN 'p' THEN 'PRIMARY KEY'
                            WHEN 'f' THEN 'FOREIGN KEY'
                            WHEN 'u' THEN 'UNIQUE'
                            WHEN 'c' THEN 'CHECK'
                        END as constraint_type,
                        pg_get_constraintdef(con.oid) as definition
                    FROM pg_constraint con
                    JOIN pg_class c ON con.conrelid = c.oid
                    JOIN pg_namespace n ON c.relnamespace = n.oid
                    WHERE n.nspname = %s
                    ORDER BY c.relname, con.conname
                """, (schema,))
                columns = [desc[0] for desc in cur.description]
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
        """Get DDL for a specific database object"""
        schema = schema or "public"
        logger.info(f"Getting DDL for {object_type}: {schema}.{object_name}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()
            ddl = None
            dependencies = []

            if object_type == "table":
                # Build table DDL manually
                cur.execute("""
                    SELECT
                        'CREATE TABLE ' || quote_ident(%s) || '.' || quote_ident(%s) || ' (' ||
                        string_agg(
                            quote_ident(column_name) || ' ' ||
                            data_type ||
                            CASE
                                WHEN character_maximum_length IS NOT NULL
                                THEN '(' || character_maximum_length || ')'
                                ELSE ''
                            END ||
                            CASE WHEN is_nullable = 'NO' THEN ' NOT NULL' ELSE '' END ||
                            CASE WHEN column_default IS NOT NULL THEN ' DEFAULT ' || column_default ELSE '' END,
                            ', ' ORDER BY ordinal_position
                        ) || ');'
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                """, (schema, object_name, schema, object_name))
                result = cur.fetchone()
                ddl = result[0] if result else None

                # Get FK dependencies
                cur.execute("""
                    SELECT DISTINCT ccu.table_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.constraint_column_usage ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_schema = %s
                        AND tc.table_name = %s
                """, (schema, object_name))
                dependencies = [{"type": "table", "name": row[0]} for row in cur.fetchall()]

            elif object_type == "view":
                cur.execute("""
                    SELECT 'CREATE OR REPLACE VIEW ' || quote_ident(%s) || '.' || quote_ident(viewname) || ' AS ' || definition
                    FROM pg_views
                    WHERE schemaname = %s AND viewname = %s
                """, (schema, schema, object_name))
                result = cur.fetchone()
                ddl = result[0] if result else None

            elif object_type == "index":
                cur.execute("""
                    SELECT indexdef
                    FROM pg_indexes
                    WHERE schemaname = %s AND indexname = %s
                """, (schema, object_name))
                result = cur.fetchone()
                ddl = result[0] if result else None

            elif object_type == "sequence":
                cur.execute("""
                    SELECT 'CREATE SEQUENCE ' || quote_ident(%s) || '.' || quote_ident(sequencename) ||
                           ' START ' || start_value ||
                           ' INCREMENT ' || increment_by ||
                           ' MINVALUE ' || min_value ||
                           ' MAXVALUE ' || max_value ||
                           CASE WHEN cycle THEN ' CYCLE' ELSE ' NO CYCLE' END ||
                           ' CACHE ' || cache_size || ';'
                    FROM pg_sequences
                    WHERE schemaname = %s AND sequencename = %s
                """, (schema, schema, object_name))
                result = cur.fetchone()
                ddl = result[0] if result else None

            elif object_type in ("function", "procedure"):
                cur.execute("""
                    SELECT pg_get_functiondef(p.oid)
                    FROM pg_proc p
                    JOIN pg_namespace n ON p.pronamespace = n.oid
                    WHERE n.nspname = %s AND p.proname = %s
                """, (schema, object_name))
                result = cur.fetchone()
                ddl = result[0] if result else None

            elif object_type == "trigger":
                cur.execute("""
                    SELECT pg_get_triggerdef(t.oid, true)
                    FROM pg_trigger t
                    JOIN pg_class c ON t.tgrelid = c.oid
                    JOIN pg_namespace n ON c.relnamespace = n.oid
                    WHERE n.nspname = %s AND t.tgname = %s
                """, (schema, object_name))
                result = cur.fetchone()
                ddl = result[0] if result else None

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
        schema = schema or "public"
        logger.info(f"Getting object dependencies for schema: {schema}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            # Get dependencies from pg_depend (similar to PostgreSQL)
            cur.execute("""
                SELECT DISTINCT
                    CASE dc.relkind
                        WHEN 'r' THEN 'table'
                        WHEN 'v' THEN 'view'
                        WHEN 'i' THEN 'index'
                        WHEN 'S' THEN 'sequence'
                        ELSE 'other'
                    END as object_type,
                    dc.relname as object_name,
                    CASE rc.relkind
                        WHEN 'r' THEN 'table'
                        WHEN 'v' THEN 'view'
                        WHEN 'i' THEN 'index'
                        WHEN 'S' THEN 'sequence'
                        ELSE 'other'
                    END as depends_on_type,
                    rc.relname as depends_on_name
                FROM pg_depend d
                JOIN pg_class dc ON d.classid = 'pg_class'::regclass AND d.objid = dc.oid
                JOIN pg_class rc ON d.refclassid = 'pg_class'::regclass AND d.refobjid = rc.oid
                JOIN pg_namespace dn ON dc.relnamespace = dn.oid
                JOIN pg_namespace rn ON rc.relnamespace = rn.oid
                WHERE dn.nspname = %s
                  AND rn.nspname = %s
                  AND d.deptype IN ('n', 'a')
                  AND dc.relname != rc.relname
                ORDER BY dc.relname
            """, (schema, schema))

            columns = [desc[0] for desc in cur.description]
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
        schema = schema or "public"
        logger.info(f"Getting FK dependencies for schema: {schema}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            cur.execute("""
                SELECT
                    tc.constraint_name,
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS referenced_table,
                    ccu.column_name AS referenced_column
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = %s
                ORDER BY tc.table_name
            """, (schema,))

            columns = [desc[0] for desc in cur.description]
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
