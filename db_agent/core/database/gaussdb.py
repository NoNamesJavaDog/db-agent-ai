"""
GaussDB Database Tools - Centralized and Distributed mode support
GaussDB database tools using pg8000 driver (supports sha256 authentication on Windows)
"""
import pg8000
import pg8000.native
from typing import Dict, Any
import logging
import re
from db_agent.i18n import t
from .base import BaseDatabaseTools

logger = logging.getLogger(__name__)


class GaussDBTools(BaseDatabaseTools):
    """GaussDB database tools implementation (Centralized and Distributed modes)"""

    def __init__(self, db_config: Dict[str, Any]):
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

    def get_connection(self):
        """Get database connection using pg8000 (supports sha256 auth)"""
        return pg8000.connect(
            host=self.db_config.get("host", "localhost"),
            port=int(self.db_config.get("port", 5432)),
            database=self.db_config.get("database"),
            user=self.db_config.get("user"),
            password=self.db_config.get("password")
        )

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

        # Safety check - allow read-only statements
        sql_upper = sql.strip().upper()
        is_safe = (
            sql_upper.startswith("SELECT") or
            sql_upper.startswith("SHOW") or
            sql_upper.startswith("EXPLAIN")
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
