"""
PostgreSQL Database Tools - PostgreSQL-specific implementation
"""
import pg8000
from typing import Dict, Any
import logging
from db_agent.i18n import t
from .base import BaseDatabaseTools

logger = logging.getLogger(__name__)


class PostgreSQLTools(BaseDatabaseTools):
    """PostgreSQL database tools implementation"""

    def __init__(self, db_config: Dict[str, Any]):
        super().__init__()
        self.db_config = db_config
        self.db_version = None
        self.db_version_num = None
        self.db_version_full = None
        self._init_db_info()
        logger.info(f"PostgreSQL tools initialized: {db_config['host']}:{db_config['database']} (PostgreSQL {self.db_version})")

    @property
    def db_type(self) -> str:
        return "postgresql"

    def _init_db_info(self):
        """Initialize database information"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()

            # Get version information
            cur.execute("SELECT version();")
            self.db_version_full = cur.fetchone()[0]

            # Get version number (e.g., 150004 means 15.4)
            cur.execute("SHOW server_version_num;")
            self.db_version_num = int(cur.fetchone()[0])

            # Get short version (e.g., "15.4")
            cur.execute("SHOW server_version;")
            self.db_version = cur.fetchone()[0]

            conn.close()
        except Exception as e:
            logger.warning(f"Failed to get database version info: {e}")
            self.db_version = "unknown"
            self.db_version_num = 0
            self.db_version_full = "unknown"

    def get_db_info(self) -> Dict[str, Any]:
        """Get database information"""
        return {
            "type": "postgresql",
            "version": self.db_version,
            "version_num": self.db_version_num,
            "version_full": self.db_version_full,
            "host": self.db_config.get("host"),
            "database": self.db_config.get("database")
        }

    def get_connection(self):
        """Get database connection using pg8000"""
        return pg8000.connect(
            host=self.db_config.get("host", "localhost"),
            port=int(self.db_config.get("port", 5432)),
            database=self.db_config.get("database"),
            user=self.db_config.get("user"),
            password=self.db_config.get("password")
        )

    def identify_slow_queries(self, min_duration_ms: float = 1000, limit: int = 20) -> Dict[str, Any]:
        """
        Identify slow queries

        Args:
            min_duration_ms: Minimum average execution time (milliseconds)
            limit: Number of results to return

        Returns:
            Dictionary containing slow query list
        """
        conn = self.get_connection()
        try:
            cur = conn.cursor()

            # Check if pg_stat_statements is available and properly loaded
            has_pg_stat_statements = False
            pg_stat_version = "new"  # PostgreSQL 13+ uses *_exec_time, older uses *_time
            try:
                # Try new version column names (PostgreSQL 13+)
                cur.execute("SELECT total_exec_time, mean_exec_time FROM pg_stat_statements LIMIT 1;")
                cur.fetchone()
                has_pg_stat_statements = True
                pg_stat_version = "new"
            except Exception:
                conn.rollback()
                try:
                    # Try old version column names (PostgreSQL 12 and earlier)
                    cur.execute("SELECT total_time, mean_time FROM pg_stat_statements LIMIT 1;")
                    cur.fetchone()
                    has_pg_stat_statements = True
                    pg_stat_version = "old"
                except Exception:
                    conn.rollback()
                    pass  # pg_stat_statements not available

            if not has_pg_stat_statements:
                # Use pg_stat_activity as alternative
                # Get a fresh connection since the current one may be in a bad state after rollbacks
                try:
                    conn.close()
                except Exception:
                    pass
                new_conn = self.get_connection()
                try:
                    result = self._get_active_queries(new_conn, limit)
                    return result
                finally:
                    new_conn.close()

            # Select correct column names based on PostgreSQL version
            if pg_stat_version == "new":
                # PostgreSQL 13+
                query = """
                    SELECT
                        query,
                        calls,
                        ROUND(total_exec_time::numeric, 2) as total_time_ms,
                        ROUND(mean_exec_time::numeric, 2) as avg_time_ms,
                        ROUND(max_exec_time::numeric, 2) as max_time_ms,
                        ROUND(stddev_exec_time::numeric, 2) as stddev_time_ms,
                        rows,
                        ROUND(100.0 * shared_blks_hit / NULLIF(shared_blks_hit + shared_blks_read, 0), 2) as cache_hit_ratio
                    FROM pg_stat_statements
                    WHERE mean_exec_time > %s
                    ORDER BY total_exec_time DESC
                    LIMIT %s;
                """
            else:
                # PostgreSQL 12 and earlier
                query = """
                    SELECT
                        query,
                        calls,
                        ROUND(total_time::numeric, 2) as total_time_ms,
                        ROUND(mean_time::numeric, 2) as avg_time_ms,
                        ROUND(max_time::numeric, 2) as max_time_ms,
                        ROUND(stddev_time::numeric, 2) as stddev_time_ms,
                        rows,
                        ROUND(100.0 * shared_blks_hit / NULLIF(shared_blks_hit + shared_blks_read, 0), 2) as cache_hit_ratio
                    FROM pg_stat_statements
                    WHERE mean_time > %s
                    ORDER BY total_time DESC
                    LIMIT %s;
                """

            cur.execute(query, (min_duration_ms, limit))

            if cur.description is None:
                return {
                    "status": "success",
                    "source": "pg_stat_statements",
                    "count": 0,
                    "queries": [],
                    "summary": {"total_slow_queries": 0, "avg_cache_hit_ratio": 0}
                }

            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]

            return {
                "status": "success",
                "source": "pg_stat_statements",
                "count": len(results),
                "queries": results,
                "summary": {
                    "total_slow_queries": len(results),
                    "avg_cache_hit_ratio": sum(q['cache_hit_ratio'] or 0 for q in results) / len(results) if results else 0
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            conn.close()

    def _get_active_queries(self, conn, limit: int = 20) -> Dict[str, Any]:
        """Get current active queries (fallback when pg_stat_statements is not available)"""
        try:
            cur = conn.cursor()
            query = """
                SELECT
                    pid,
                    usename as user,
                    datname as database,
                    state,
                    CASE WHEN query_start IS NOT NULL
                         THEN EXTRACT(EPOCH FROM (now() - query_start))::numeric(10,2)
                         ELSE NULL END as duration_seconds,
                    wait_event_type,
                    wait_event,
                    LEFT(query, 500) as query
                FROM pg_stat_activity
                WHERE state IS NOT NULL
                  AND state != 'idle'
                  AND query NOT LIKE '%%pg_stat_activity%%'
                  AND pid != pg_backend_pid()
                ORDER BY query_start ASC NULLS LAST
                LIMIT %s;
            """
            cur.execute(query, (limit,))

            if cur.description is None:
                return {
                    "status": "success",
                    "source": "pg_stat_activity",
                    "note": t("db_pg_stat_not_enabled"),
                    "count": 0,
                    "queries": []
                }

            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]

            return {
                "status": "success",
                "source": "pg_stat_activity",
                "note": t("db_pg_stat_not_enabled"),
                "count": len(results),
                "queries": results
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def get_running_queries(self) -> Dict[str, Any]:
        """Get currently running queries"""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            query = """
                SELECT
                    pid,
                    usename as user,
                    datname as database,
                    state,
                    CASE WHEN query_start IS NOT NULL
                         THEN EXTRACT(EPOCH FROM (now() - query_start))::numeric(10,2)
                         ELSE NULL END as duration_seconds,
                    wait_event_type,
                    wait_event,
                    LEFT(query, 500) as query
                FROM pg_stat_activity
                WHERE state = 'active'
                  AND query NOT LIKE '%%pg_stat_activity%%'
                  AND pid != pg_backend_pid()
                ORDER BY query_start ASC NULLS LAST;
            """
            cur.execute(query)

            if cur.description is None:
                return {
                    "status": "success",
                    "count": 0,
                    "queries": []
                }

            columns = [desc[0] for desc in cur.description]
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

    def run_explain(self, sql: str, analyze: bool = False) -> Dict[str, Any]:
        """
        Run EXPLAIN to analyze query

        Args:
            sql: SQL statement
            analyze: Whether to actually execute (EXPLAIN ANALYZE)

        Returns:
            EXPLAIN output result
        """
        logger.info(f"Running EXPLAIN analysis: analyze={analyze}")
        logger.debug(f"SQL: {sql[:100]}...")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            # Build EXPLAIN statement
            if analyze:
                explain_sql = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {sql}"
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
        """
        Check index usage for a table

        Args:
            table_name: Table name
            schema: Schema name

        Returns:
            Index usage information
        """
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
        """
        Get table statistics

        Args:
            table_name: Table name
            schema: Schema name

        Returns:
            Table statistics
        """
        logger.info(f"Getting table stats: {schema}.{table_name}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

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
            concurrent: Whether to use CONCURRENTLY (no table lock)

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

        # Add CONCURRENTLY
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
        """
        Update table statistics (ANALYZE)

        Args:
            table_name: Table name
            schema: Schema name

        Returns:
            Execution result
        """
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
        """
        Execute safe read-only query

        Args:
            sql: SQL statement (SELECT, SHOW, EXPLAIN)

        Returns:
            Query result
        """
        logger.info(f"Executing safe query")
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
        # SELECT, SHOW, EXPLAIN are all read-only
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

    def list_tables(self, schema: str = "public") -> Dict[str, Any]:
        """
        List all tables in the database

        Args:
            schema: Schema name

        Returns:
            Table list
        """
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
        """
        Get table structure information

        Args:
            table_name: Table name
            schema: Schema name

        Returns:
            Table structure information
        """
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
        """
        Get sample data from a table

        Args:
            table_name: Table name
            schema: Schema name
            limit: Number of rows to return

        Returns:
            Sample data
        """
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
