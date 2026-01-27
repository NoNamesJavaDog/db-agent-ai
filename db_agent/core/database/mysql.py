"""
MySQL Database Tools - MySQL 5.7/8.0 specific implementation
"""
import pymysql
from typing import Dict, Any
import logging
import re
from db_agent.i18n import t
from .base import BaseDatabaseTools

logger = logging.getLogger(__name__)


class MySQLTools(BaseDatabaseTools):
    """MySQL database tools implementation (supports MySQL 5.7 and 8.0)"""

    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.db_version = None
        self.db_version_num = None
        self.db_version_full = None
        self._has_performance_schema = False
        self._init_db_info()
        logger.info(f"MySQL tools initialized: {db_config['host']}:{db_config['database']} (MySQL {self.db_version})")

    @property
    def db_type(self) -> str:
        return "mysql"

    def _parse_version(self, version_str: str) -> int:
        """Parse MySQL version string to numeric format (e.g., '8.0.32' -> 80032)"""
        try:
            # Extract version number from string like "8.0.32-mysql" or "5.7.42"
            match = re.search(r'(\d+)\.(\d+)\.(\d+)', version_str)
            if match:
                major, minor, patch = match.groups()
                return int(major) * 10000 + int(minor) * 100 + int(patch)
        except Exception:
            pass
        return 0

    def _init_db_info(self):
        """Initialize database information"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()

            # Get version information (DictCursor returns dict)
            cur.execute("SELECT VERSION() as version")
            result = cur.fetchone()
            self.db_version_full = result['version']
            self.db_version = self.db_version_full.split('-')[0]
            self.db_version_num = self._parse_version(self.db_version_full)

            # Check if performance_schema is enabled
            try:
                cur.execute("SELECT COUNT(*) as cnt FROM performance_schema.events_statements_summary_by_digest LIMIT 1")
                self._has_performance_schema = True
            except Exception:
                self._has_performance_schema = False

            conn.close()
        except Exception as e:
            logger.warning(f"Failed to get database version info: {e}")
            self.db_version = "unknown"
            self.db_version_num = 0
            self.db_version_full = "unknown"

    def get_db_info(self) -> Dict[str, Any]:
        """Get database information"""
        return {
            "type": "mysql",
            "version": self.db_version,
            "version_num": self.db_version_num,
            "version_full": self.db_version_full,
            "host": self.db_config.get("host"),
            "database": self.db_config.get("database"),
            "has_performance_schema": self._has_performance_schema
        }

    def get_connection(self):
        """Get database connection"""
        # Map config keys to pymysql parameter names
        conn_config = {
            "host": self.db_config.get("host", "localhost"),
            "port": self.db_config.get("port", 3306),
            "user": self.db_config.get("user"),
            "password": self.db_config.get("password"),
            "database": self.db_config.get("database"),
            "charset": "utf8mb4",
            "cursorclass": pymysql.cursors.DictCursor
        }
        return pymysql.connect(**conn_config)

    def identify_slow_queries(self, min_duration_ms: float = 1000, limit: int = 20) -> Dict[str, Any]:
        """
        Identify slow queries using performance_schema

        Args:
            min_duration_ms: Minimum average execution time (milliseconds)
            limit: Number of results to return

        Returns:
            Dictionary containing slow query list
        """
        conn = self.get_connection()
        try:
            cur = conn.cursor()

            if not self._has_performance_schema:
                # Fallback to PROCESSLIST
                return self._get_active_queries(conn, limit)

            # Use performance_schema for slow query analysis
            # Timer values are in picoseconds, convert to milliseconds
            query = """
                SELECT
                    DIGEST_TEXT as query,
                    COUNT_STAR as calls,
                    ROUND(SUM_TIMER_WAIT / 1000000000000, 2) as total_time_sec,
                    ROUND(AVG_TIMER_WAIT / 1000000000, 2) as avg_time_ms,
                    ROUND(MAX_TIMER_WAIT / 1000000000, 2) as max_time_ms,
                    SUM_ROWS_EXAMINED as rows_examined,
                    SUM_ROWS_SENT as rows_sent,
                    FIRST_SEEN,
                    LAST_SEEN
                FROM performance_schema.events_statements_summary_by_digest
                WHERE DIGEST_TEXT IS NOT NULL
                  AND AVG_TIMER_WAIT / 1000000000 > %s
                ORDER BY SUM_TIMER_WAIT DESC
                LIMIT %s
            """

            cur.execute(query, (min_duration_ms, limit))
            results = cur.fetchall()

            return {
                "status": "success",
                "source": "performance_schema",
                "count": len(results),
                "queries": results,
                "summary": {
                    "total_slow_queries": len(results),
                    "avg_time_ms": sum(q['avg_time_ms'] or 0 for q in results) / len(results) if results else 0
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
        """Get current active queries from PROCESSLIST"""
        try:
            cur = conn.cursor()
            query = """
                SELECT
                    ID as pid,
                    USER as user,
                    DB as `database`,
                    COMMAND as state,
                    TIME as duration_seconds,
                    STATE as wait_event,
                    LEFT(INFO, 500) as query
                FROM information_schema.PROCESSLIST
                WHERE COMMAND != 'Sleep'
                  AND ID != CONNECTION_ID()
                ORDER BY TIME DESC
                LIMIT %s
            """
            cur.execute(query, (limit,))
            results = cur.fetchall()

            return {
                "status": "success",
                "source": "information_schema.PROCESSLIST",
                "note": t("db_performance_schema_required"),
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
                    ID as pid,
                    USER as user,
                    DB as `database`,
                    COMMAND as state,
                    TIME as duration_seconds,
                    STATE as wait_event,
                    LEFT(INFO, 500) as query
                FROM information_schema.PROCESSLIST
                WHERE COMMAND != 'Sleep'
                  AND INFO IS NOT NULL
                  AND ID != CONNECTION_ID()
                ORDER BY TIME DESC
            """
            cur.execute(query)
            results = cur.fetchall()

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
            analyze: Whether to actually execute (EXPLAIN ANALYZE - MySQL 8.0.18+)

        Returns:
            EXPLAIN output result
        """
        logger.info(f"Running EXPLAIN analysis: analyze={analyze}")
        logger.debug(f"SQL: {sql[:100]}...")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            # MySQL 8.0.18+ supports EXPLAIN ANALYZE
            if analyze and self.db_version_num >= 80018:
                explain_sql = f"EXPLAIN ANALYZE {sql}"
                cur.execute(explain_sql)
                # EXPLAIN ANALYZE returns text format
                results = cur.fetchall()
                result = "\n".join([list(r.values())[0] for r in results])
            else:
                # Use JSON format for regular EXPLAIN
                explain_sql = f"EXPLAIN FORMAT=JSON {sql}"
                cur.execute(explain_sql)
                result = cur.fetchone()
                # Get the first (and only) value from the dict
                result = list(result.values())[0] if result else None

            logger.info("EXPLAIN analysis completed")

            return {
                "status": "success",
                "explain_output": result,
                "analyzed": analyze and self.db_version_num >= 80018,
                "sql": sql,
                "note": "EXPLAIN ANALYZE requires MySQL 8.0.18+" if analyze and self.db_version_num < 80018 else None
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

    def check_index_usage(self, table_name: str, schema: str = None) -> Dict[str, Any]:
        """
        Check index usage for a table

        Args:
            table_name: Table name
            schema: Schema/database name (uses current database if None)

        Returns:
            Index usage information
        """
        schema = schema or self.db_config.get("database")
        logger.info(f"Checking index usage: {schema}.{table_name}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            # Get index information from information_schema
            query = """
                SELECT
                    INDEX_NAME as indexname,
                    GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) as columns,
                    NON_UNIQUE,
                    INDEX_TYPE,
                    CARDINALITY
                FROM information_schema.STATISTICS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                GROUP BY INDEX_NAME, NON_UNIQUE, INDEX_TYPE, CARDINALITY
                ORDER BY INDEX_NAME
            """

            cur.execute(query, (schema, table_name))
            indexes = cur.fetchall()

            # Try to get index usage stats from performance_schema (MySQL 8.0+)
            index_stats = {}
            if self._has_performance_schema and self.db_version_num >= 80000:
                try:
                    cur.execute("""
                        SELECT
                            INDEX_NAME,
                            COUNT_READ,
                            COUNT_WRITE
                        FROM performance_schema.table_io_waits_summary_by_index_usage
                        WHERE OBJECT_SCHEMA = %s AND OBJECT_NAME = %s
                    """, (schema, table_name))
                    for row in cur.fetchall():
                        index_stats[row['INDEX_NAME']] = {
                            'read_count': row['COUNT_READ'],
                            'write_count': row['COUNT_WRITE']
                        }
                except Exception:
                    pass

            # Enrich indexes with usage stats
            for idx in indexes:
                idx_name = idx['indexname']
                if idx_name in index_stats:
                    idx['read_count'] = index_stats[idx_name]['read_count']
                    idx['write_count'] = index_stats[idx_name]['write_count']
                else:
                    idx['read_count'] = None
                    idx['write_count'] = None

            # Identify unused indexes (only if we have stats)
            unused_indexes = []
            if index_stats:
                unused_indexes = [idx for idx in indexes
                                  if idx['read_count'] == 0 and idx['indexname'] != 'PRIMARY']

            logger.info(f"Found {len(indexes)} indexes")

            return {
                "status": "success",
                "table": f"{schema}.{table_name}",
                "total_indexes": len(indexes),
                "unused_count": len(unused_indexes),
                "indexes": indexes,
                "analysis": {
                    "has_unused_indexes": len(unused_indexes) > 0,
                    "unused_indexes": unused_indexes,
                    "note": "Index usage stats require MySQL 8.0+ with performance_schema enabled" if not index_stats else None
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

    def get_table_stats(self, table_name: str, schema: str = None) -> Dict[str, Any]:
        """
        Get table statistics

        Args:
            table_name: Table name
            schema: Schema/database name

        Returns:
            Table statistics
        """
        schema = schema or self.db_config.get("database")
        logger.info(f"Getting table stats: {schema}.{table_name}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            query = """
                SELECT
                    TABLE_NAME as tablename,
                    ENGINE,
                    TABLE_ROWS as row_count,
                    ROUND(DATA_LENGTH / 1024 / 1024, 2) as data_size_mb,
                    ROUND(INDEX_LENGTH / 1024 / 1024, 2) as index_size_mb,
                    ROUND((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) as total_size_mb,
                    DATA_LENGTH as data_size_bytes,
                    INDEX_LENGTH as index_size_bytes,
                    AUTO_INCREMENT,
                    CREATE_TIME,
                    UPDATE_TIME,
                    TABLE_COLLATION
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            """

            cur.execute(query, (schema, table_name))
            result = cur.fetchone()

            if result:
                logger.info(f"Table stats retrieved successfully")
                return {
                    "status": "success",
                    "stats": result
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
            concurrent: Whether to use online DDL (MySQL 5.6+)

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

        # For MySQL 5.6+, convert to online DDL using ALTER TABLE with ALGORITHM=INPLACE
        final_sql = index_sql
        if concurrent and self.db_version_num >= 50600:
            # Try to convert CREATE INDEX to ALTER TABLE for online DDL
            # CREATE INDEX idx_name ON table_name (columns) -> ALTER TABLE table_name ADD INDEX idx_name (columns)
            match = re.match(
                r'CREATE\s+INDEX\s+(\w+)\s+ON\s+(\w+)\s*\(([^)]+)\)',
                index_sql.strip(),
                re.IGNORECASE
            )
            if match:
                idx_name, table_name, columns = match.groups()
                final_sql = f"ALTER TABLE {table_name} ADD INDEX {idx_name} ({columns}), ALGORITHM=INPLACE, LOCK=NONE"

        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(final_sql)
            conn.commit()

            logger.info("Index created successfully")

            return {
                "status": "success",
                "message": t("db_index_created"),
                "sql": final_sql,
                "original_sql": index_sql if final_sql != index_sql else None
            }

        except Exception as e:
            logger.error(f"Index creation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "sql": final_sql
            }
        finally:
            conn.close()

    def analyze_table(self, table_name: str, schema: str = None) -> Dict[str, Any]:
        """
        Update table statistics (ANALYZE TABLE)

        Args:
            table_name: Table name
            schema: Schema/database name

        Returns:
            Execution result
        """
        schema = schema or self.db_config.get("database")
        logger.info(f"Updating statistics: {schema}.{table_name}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(f"ANALYZE TABLE `{schema}`.`{table_name}`")
            result = cur.fetchone()

            logger.info("Statistics updated successfully")

            return {
                "status": "success",
                "message": t("db_stats_updated", schema=schema, table=table_name),
                "details": result
            }

        except Exception as e:
            logger.error(f"Failed to update statistics: {e}")
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
            sql: SQL statement (SELECT, SHOW, DESCRIBE, EXPLAIN)

        Returns:
            Query result
        """
        logger.info(f"Executing safe query")
        logger.debug(f"SQL: {sql[:100]}...")

        # Safety check - allow read-only statements
        sql_upper = sql.strip().upper()
        is_safe = (
            sql_upper.startswith("SELECT") or
            sql_upper.startswith("SHOW") or
            sql_upper.startswith("DESCRIBE") or
            sql_upper.startswith("DESC ") or
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
            results = cur.fetchall()

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
        # SELECT, SHOW, DESCRIBE, DESC, EXPLAIN are all read-only
        is_readonly = (
            sql_upper.startswith("SELECT") or
            sql_upper.startswith("SHOW") or
            sql_upper.startswith("DESCRIBE") or
            sql_upper.startswith("DESC ") or
            sql_upper.startswith("EXPLAIN")
        )

        if is_readonly:
            conn = self.get_connection()
            try:
                cur = conn.cursor()
                cur.execute(sql)
                results = cur.fetchall()
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

    def list_tables(self, schema: str = None) -> Dict[str, Any]:
        """
        List all tables in the database

        Args:
            schema: Schema/database name

        Returns:
            Table list
        """
        schema = schema or self.db_config.get("database")
        logger.info(f"Listing tables: schema={schema}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    TABLE_NAME as tablename,
                    CONCAT(ROUND((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2), ' MB') as total_size,
                    (DATA_LENGTH + INDEX_LENGTH) as size_bytes
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s
                  AND TABLE_TYPE = 'BASE TABLE'
                ORDER BY (DATA_LENGTH + INDEX_LENGTH) DESC
            """, (schema,))

            tables = cur.fetchall()

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
            schema: Schema/database name

        Returns:
            Table structure information
        """
        schema = schema or self.db_config.get("database")
        logger.info(f"Getting table structure: {schema}.{table_name}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            # Get column information
            cur.execute("""
                SELECT
                    COLUMN_NAME as column_name,
                    DATA_TYPE as data_type,
                    CHARACTER_MAXIMUM_LENGTH as character_maximum_length,
                    IS_NULLABLE as is_nullable,
                    COLUMN_DEFAULT as column_default,
                    COLUMN_TYPE as column_type,
                    EXTRA
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
            """, (schema, table_name))

            cols = cur.fetchall()

            # Get primary key information
            cur.execute("""
                SELECT COLUMN_NAME
                FROM information_schema.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = %s
                  AND TABLE_NAME = %s
                  AND CONSTRAINT_NAME = 'PRIMARY'
                ORDER BY ORDINAL_POSITION
            """, (schema, table_name))
            pk_columns = [row['COLUMN_NAME'] for row in cur.fetchall()]

            # Get foreign key information
            cur.execute("""
                SELECT
                    kcu.COLUMN_NAME as column_name,
                    kcu.REFERENCED_TABLE_NAME AS foreign_table,
                    kcu.REFERENCED_COLUMN_NAME AS foreign_column
                FROM information_schema.KEY_COLUMN_USAGE kcu
                WHERE kcu.TABLE_SCHEMA = %s
                  AND kcu.TABLE_NAME = %s
                  AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
            """, (schema, table_name))
            fks = cur.fetchall()

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

    def get_sample_data(self, table_name: str, schema: str = None, limit: int = 10) -> Dict[str, Any]:
        """
        Get sample data from a table

        Args:
            table_name: Table name
            schema: Schema/database name
            limit: Number of rows to return

        Returns:
            Sample data
        """
        schema = schema or self.db_config.get("database")
        logger.info(f"Getting sample data: {schema}.{table_name}, limit={limit}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM `{schema}`.`{table_name}` LIMIT %s", (limit,))

            rows = cur.fetchall()
            columns = list(rows[0].keys()) if rows else []

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
