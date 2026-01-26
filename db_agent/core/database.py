"""
Database Tools - Agent's "hands and eyes"
"""
import psycopg2
from typing import Dict, Any
import logging
from db_agent.i18n import t

logger = logging.getLogger(__name__)


class DatabaseTools:
    """数据库工具集 - Agent的"手和眼睛"""

    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.db_version = None
        self.db_version_num = None
        self.db_version_full = None
        self._init_db_info()
        logger.info(f"数据库工具初始化: {db_config['host']}:{db_config['database']} (PostgreSQL {self.db_version})")

    def _init_db_info(self):
        """初始化数据库信息"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()

            # 获取版本信息
            cur.execute("SELECT version();")
            self.db_version_full = cur.fetchone()[0]

            # 获取版本号 (如 150004 表示 15.4)
            cur.execute("SHOW server_version_num;")
            self.db_version_num = int(cur.fetchone()[0])

            # 获取简短版本 (如 "15.4")
            cur.execute("SHOW server_version;")
            self.db_version = cur.fetchone()[0]

            conn.close()
        except Exception as e:
            logger.warning(f"获取数据库版本信息失败: {e}")
            self.db_version = "unknown"
            self.db_version_num = 0
            self.db_version_full = "unknown"

    def get_db_info(self) -> Dict[str, Any]:
        """获取数据库信息"""
        return {
            "version": self.db_version,
            "version_num": self.db_version_num,
            "version_full": self.db_version_full,
            "host": self.db_config.get("host"),
            "database": self.db_config.get("database")
        }

    def get_connection(self):
        """获取数据库连接"""
        return psycopg2.connect(**self.db_config)

    def identify_slow_queries(self, min_duration_ms: float = 1000, limit: int = 20) -> Dict[str, Any]:
        """
        识别慢查询

        Args:
            min_duration_ms: 最小平均执行时间(毫秒)
            limit: 返回结果数量

        Returns:
            包含慢查询列表的字典
        """
        conn = self.get_connection()
        try:
            cur = conn.cursor()

            # 先检查pg_stat_statements是否可用且已正确加载
            has_pg_stat_statements = False
            pg_stat_version = "new"  # PostgreSQL 13+ uses *_exec_time, older uses *_time
            try:
                # 尝试使用新版本列名 (PostgreSQL 13+)
                cur.execute("SELECT total_exec_time, mean_exec_time FROM pg_stat_statements LIMIT 1;")
                cur.fetchone()
                has_pg_stat_statements = True
                pg_stat_version = "new"
            except Exception:
                conn.rollback()
                try:
                    # 尝试使用旧版本列名 (PostgreSQL 12 and earlier)
                    cur.execute("SELECT total_time, mean_time FROM pg_stat_statements LIMIT 1;")
                    cur.fetchone()
                    has_pg_stat_statements = True
                    pg_stat_version = "old"
                except Exception:
                    conn.rollback()
                    pass  # pg_stat_statements not available

            if not has_pg_stat_statements:
                # 使用pg_stat_activity作为替代
                result = self._get_active_queries(conn, limit)
                conn.close()
                return result

            # 根据PostgreSQL版本选择正确的列名
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
        """获取当前活动查询（pg_stat_statements不可用时的备选方案）"""
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
        """获取当前正在运行的查询"""
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
        运行EXPLAIN分析查询

        Args:
            sql: SQL语句
            analyze: 是否实际执行(EXPLAIN ANALYZE)

        Returns:
            EXPLAIN输出结果
        """
        logger.info(f"运行EXPLAIN分析: analyze={analyze}")
        logger.debug(f"SQL: {sql[:100]}...")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            # 构建EXPLAIN语句
            if analyze:
                explain_sql = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {sql}"
            else:
                explain_sql = f"EXPLAIN (FORMAT JSON) {sql}"

            cur.execute(explain_sql)
            result = cur.fetchone()[0]

            logger.info("EXPLAIN分析完成")

            return {
                "status": "success",
                "explain_output": result,
                "analyzed": analyze,
                "sql": sql
            }

        except Exception as e:
            logger.error(f"EXPLAIN分析失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "sql": sql
            }
        finally:
            conn.close()

    def check_index_usage(self, table_name: str, schema: str = "public") -> Dict[str, Any]:
        """
        检查表的索引使用情况

        Args:
            table_name: 表名
            schema: 模式名

        Returns:
            索引使用情况
        """
        logger.info(f"检查索引使用: {schema}.{table_name}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            # 获取索引信息
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

            # 分析
            unused_indexes = [idx for idx in indexes if idx['idx_scan'] == 0 or idx['idx_scan'] is None]
            total_size = sum(idx['index_size_bytes'] or 0 for idx in indexes)

            logger.info(f"找到 {len(indexes)} 个索引, {len(unused_indexes)} 个未使用")

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
            logger.error(f"检查索引失败: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            conn.close()

    def get_table_stats(self, table_name: str, schema: str = "public") -> Dict[str, Any]:
        """
        获取表统计信息

        Args:
            table_name: 表名
            schema: 模式名

        Returns:
            表统计信息
        """
        logger.info(f"获取表统计: {schema}.{table_name}")

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
                logger.info(f"表统计获取成功")
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
            logger.error(f"获取表统计失败: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            conn.close()

    def create_index(self, index_sql: str, concurrent: bool = True) -> Dict[str, Any]:
        """
        创建索引

        Args:
            index_sql: CREATE INDEX语句
            concurrent: 是否使用CONCURRENTLY(不锁表)

        Returns:
            创建结果
        """
        logger.info(f"创建索引: concurrent={concurrent}")
        logger.info(f"SQL: {index_sql}")

        # 安全检查
        if not index_sql.strip().upper().startswith("CREATE INDEX"):
            return {
                "status": "error",
                "error": t("db_only_create_index")
            }

        # 添加CONCURRENTLY
        if concurrent and "CONCURRENTLY" not in index_sql.upper():
            index_sql = index_sql.replace("CREATE INDEX", "CREATE INDEX CONCURRENTLY", 1)

        conn = self.get_connection()
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

        try:
            cur = conn.cursor()
            cur.execute(index_sql)

            logger.info("索引创建成功")

            return {
                "status": "success",
                "message": t("db_index_created"),
                "sql": index_sql
            }

        except Exception as e:
            logger.error(f"创建索引失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "sql": index_sql
            }
        finally:
            conn.close()

    def analyze_table(self, table_name: str, schema: str = "public") -> Dict[str, Any]:
        """
        更新表统计信息(ANALYZE)

        Args:
            table_name: 表名
            schema: 模式名

        Returns:
            执行结果
        """
        logger.info(f"更新统计信息: {schema}.{table_name}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(f"ANALYZE {schema}.{table_name};")
            conn.commit()

            logger.info("统计信息更新成功")

            return {
                "status": "success",
                "message": t("db_stats_updated", schema=schema, table=table_name)
            }

        except Exception as e:
            logger.error(f"更新统计信息失败: {e}")
            conn.rollback()
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            conn.close()

    def execute_safe_query(self, sql: str) -> Dict[str, Any]:
        """
        执行安全的只读查询

        Args:
            sql: SQL语句(必须是SELECT)

        Returns:
            查询结果
        """
        logger.info(f"执行安全查询")
        logger.debug(f"SQL: {sql[:100]}...")

        # 安全检查
        sql_upper = sql.strip().upper()
        if not sql_upper.startswith("SELECT"):
            return {
                "status": "error",
                "error": t("db_only_select")
            }

        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql)

            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]

            logger.info(f"查询成功,返回 {len(results)} 行")

            return {
                "status": "success",
                "count": len(results),
                "rows": results
            }

        except Exception as e:
            logger.error(f"查询失败: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            conn.close()

    def execute_sql(self, sql: str, confirmed: bool = False) -> Dict[str, Any]:
        """
        执行任意SQL语句(INSERT/UPDATE/DELETE/CREATE/ALTER/DROP等)

        Args:
            sql: SQL语句
            confirmed: 是否已确认执行

        Returns:
            执行结果
        """
        sql_upper = sql.strip().upper()

        # SELECT 查询直接执行
        if sql_upper.startswith("SELECT"):
            conn = self.get_connection()
            try:
                cur = conn.cursor()
                cur.execute(sql)
                columns = [desc[0] for desc in cur.description]
                results = [dict(zip(columns, row)) for row in cur.fetchall()]
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

        # 非 SELECT 操作需要确认
        if not confirmed:
            return {
                "status": "pending_confirmation",
                "sql": sql,
                "message": t("db_need_confirm")
            }

        # 已确认，执行操作
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
            logger.error(f"SQL执行失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "sql": sql
            }
        finally:
            conn.close()

    def list_tables(self, schema: str = "public") -> Dict[str, Any]:
        """
        列出数据库中的所有表

        Args:
            schema: 模式名

        Returns:
            表列表
        """
        logger.info(f"列出表: schema={schema}")

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

            logger.info(f"找到 {len(tables)} 个表")

            return {
                "status": "success",
                "schema": schema,
                "count": len(tables),
                "tables": tables
            }

        except Exception as e:
            logger.error(f"列出表失败: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            conn.close()

    def describe_table(self, table_name: str, schema: str = "public") -> Dict[str, Any]:
        """
        获取表结构信息

        Args:
            table_name: 表名
            schema: 模式名

        Returns:
            表结构信息
        """
        logger.info(f"获取表结构: {schema}.{table_name}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()

            # 获取列信息
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

            # 获取主键信息
            cur.execute("""
                SELECT a.attname as column_name
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = %s::regclass AND i.indisprimary;
            """, (f"{schema}.{table_name}",))
            pk_columns = [row[0] for row in cur.fetchall()]

            # 获取外键信息
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

            logger.info(f"获取表结构成功: {len(cols)} 列")

            return {
                "status": "success",
                "table": f"{schema}.{table_name}",
                "columns": cols,
                "primary_key": pk_columns,
                "foreign_keys": fks
            }

        except Exception as e:
            logger.error(f"获取表结构失败: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            conn.close()

    def get_sample_data(self, table_name: str, schema: str = "public", limit: int = 10) -> Dict[str, Any]:
        """
        获取表的示例数据

        Args:
            table_name: 表名
            schema: 模式名
            limit: 返回行数

        Returns:
            示例数据
        """
        logger.info(f"获取示例数据: {schema}.{table_name}, limit={limit}")

        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM {schema}.{table_name} LIMIT %s;", (limit,))

            columns = [desc[0] for desc in cur.description]
            rows = [dict(zip(columns, row)) for row in cur.fetchall()]

            logger.info(f"获取示例数据成功: {len(rows)} 行")

            return {
                "status": "success",
                "table": f"{schema}.{table_name}",
                "columns": columns,
                "count": len(rows),
                "rows": rows
            }

        except Exception as e:
            logger.error(f"获取示例数据失败: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            conn.close()
