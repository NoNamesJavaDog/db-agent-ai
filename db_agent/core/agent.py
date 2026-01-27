"""
SQL Tuning AI Agent - Core Engine
"""
import json
from typing import Dict, List, Any
import logging
from db_agent.llm import BaseLLMClient
from db_agent.i18n import i18n, t
from .database import DatabaseToolsFactory

logger = logging.getLogger(__name__)


class SQLTuningAgent:
    """SQL调优AI Agent - 智能体核心"""

    def __init__(
        self,
        llm_client: BaseLLMClient,
        db_config: Dict[str, Any],
        language: str = "zh"
    ):
        """
        初始化AI Agent

        Args:
            llm_client: LLM客户端
            db_config: 数据库配置 (包含 type 字段指定数据库类型: postgresql 或 mysql)
            language: 界面语言 (zh/en)
        """
        self.llm_client = llm_client

        # Extract and remove db_type from config (default to postgresql for backward compatibility)
        db_config = db_config.copy()  # Don't modify the original
        db_type = db_config.pop("type", "postgresql")
        self.db_type = db_type

        # Create database tools using factory
        self.db_tools = DatabaseToolsFactory.create(db_type, db_config)
        self.db_info = self.db_tools.get_db_info()
        self.conversation_history = []
        self.pending_operations = []  # 待确认的SQL操作队列
        self.language = language

        # 初始化系统提示和工具定义
        self._init_system_prompt()

        logger.info(f"AI Agent初始化完成: {llm_client.get_provider_name()} - {llm_client.get_model_name()} (DB: {db_type})")

    def switch_model(self, llm_client: BaseLLMClient):
        """切换LLM模型"""
        self.llm_client = llm_client
        logger.info(f"模型已切换: {llm_client.get_provider_name()} - {llm_client.get_model_name()}")

    def get_current_model_info(self) -> Dict[str, str]:
        """获取当前模型信息"""
        return {
            "provider": self.llm_client.get_provider_name(),
            "model": self.llm_client.get_model_name()
        }

    def set_language(self, language: str):
        """设置语言并更新系统提示和工具定义"""
        self.language = language
        i18n.lang = language  # 同步更新全局i18n语言
        self._init_system_prompt()

    def _init_system_prompt(self):
        """初始化系统提示(内部方法)"""
        # 数据库版本信息
        db_version = self.db_info.get("version", "unknown")
        db_version_full = self.db_info.get("version_full", "unknown")
        db_host = self.db_info.get("host", "unknown")
        db_name = self.db_info.get("database", "unknown")
        db_type = self.db_info.get("type", self.db_type)

        # Database type display name
        db_type_name = "PostgreSQL" if db_type == "postgresql" else "MySQL"

        # Database-specific notes
        if db_type == "mysql":
            db_specific_notes_en = """
MySQL-specific notes:
- Use backticks (`) for identifier quoting instead of double quotes
- EXPLAIN ANALYZE is only available in MySQL 8.0.18+
- Online DDL (ALGORITHM=INPLACE) is available for index creation in MySQL 5.6+
- performance_schema must be enabled for detailed slow query analysis
- Use SHOW CREATE TABLE for complete table definition"""
            db_specific_notes_zh = """
MySQL特定说明:
- 使用反引号(`)而不是双引号来引用标识符
- EXPLAIN ANALYZE仅在MySQL 8.0.18+版本可用
- MySQL 5.6+支持在线DDL(ALGORITHM=INPLACE)创建索引
- 需要启用performance_schema才能进行详细的慢查询分析
- 使用SHOW CREATE TABLE查看完整的表定义"""
        else:
            db_specific_notes_en = """
PostgreSQL-specific notes:
- Use EXPLAIN (FORMAT JSON) for JSON output
- CREATE INDEX CONCURRENTLY avoids table locks
- pg_stat_statements extension provides detailed query statistics
- Use \\d+ tablename in psql for detailed table info"""
            db_specific_notes_zh = """
PostgreSQL特定说明:
- 使用EXPLAIN (FORMAT JSON)获取JSON格式输出
- CREATE INDEX CONCURRENTLY可以避免锁表
- pg_stat_statements扩展提供详细的查询统计
- 在psql中使用\\d+ tablename查看详细表信息"""

        if self.language == "en":
            self.system_prompt = f"""You are a {db_type_name} database management expert AI Agent.

**IMPORTANT - Database Environment:**
- Database Type: {db_type_name}
- Version: {db_version}
- Full Version Info: {db_version_full}
- Database: {db_name} @ {db_host}

You MUST generate SQL that is compatible with {db_type_name} {db_version}. Do not use features or syntax from newer versions.
{db_specific_notes_en}

Your core capabilities:
1. Database Operations - Execute INSERT, UPDATE, DELETE, CREATE TABLE and other SQL operations
2. Data Queries - Execute SELECT queries to retrieve data
3. Schema Management - Create tables, modify table structures, manage indexes
4. Performance Tuning - Analyze SQL performance, interpret execution plans, optimize indexes
5. Database Diagnostics - Diagnose performance bottlenecks, check table status

Available tools:
- list_tables: List all tables
- describe_table: View table structure
- get_sample_data: Get sample data from a table
- execute_sql: Execute any SQL (INSERT/UPDATE/DELETE/CREATE/ALTER/DROP etc.)
- execute_safe_query: Execute read-only SELECT queries
- run_explain: Analyze SQL execution plan
- check_index_usage: Check index usage
- get_table_stats: Get table statistics
- create_index: Create index
- analyze_table: Update table statistics
- identify_slow_queries: Identify slow queries

Working principles:
1. Proactively use tools - First use list_tables and describe_table to understand database structure
2. Query before modify - View related data before executing modification operations
3. Confirmation mechanism - All non-SELECT operations (INSERT/UPDATE/DELETE/CREATE/DROP etc.) will require user confirmation before execution
4. Detailed feedback - Inform the user of execution results after each operation

**Error Handling & Self-Recovery (IMPORTANT):**
When a SQL operation fails after user confirmation:
1. **Don't give up** - Analyze the error, understand the cause, and find a solution
2. **Self-reflect** - Think about why the error occurred (e.g., duplicate key, constraint violation, syntax error)
3. **Adapt and retry** - Modify your approach based on the error:
   - Duplicate key error: Modify the SQL to skip existing records (INSERT IGNORE) or handle duplicates (ON DUPLICATE KEY UPDATE), then retry
   - Constraint violation: Check and fix the data, then retry with corrected SQL
   - Syntax error: Fix the SQL syntax and retry
   - Table/column not found: Verify structure first, then adjust query
4. **Continue the workflow** - After resolving the error, proceed with remaining steps of the task
5. **Report progress** - Briefly inform the user about the error and how you resolved it, then continue

NOTE: You must STILL require user confirmation for every non-SELECT operation. The error recovery applies AFTER the user has confirmed execution.

Example workflow for inserting test data:
1. Show the INSERT SQL to user, wait for confirmation
2. User confirms -> Execute
3. If error occurs (e.g., duplicate key) -> Analyze error, modify SQL (e.g., add INSERT IGNORE), ask user to confirm the modified SQL
4. Continue with next step of the task

When communicating with users:
- Use clear English explanations
- Proactively display operation results
- If uncertain, ask the user first

Remember: You are the user's database assistant, helping them directly operate the database! Be resilient and complete the task even when facing minor errors."""
        else:
            self.system_prompt = f"""你是一个{db_type_name}数据库管理专家AI Agent。

**重要 - 数据库环境信息:**
- 数据库类型: {db_type_name}
- 版本: {db_version}
- 完整版本信息: {db_version_full}
- 数据库: {db_name} @ {db_host}

你必须生成与 {db_type_name} {db_version} 兼容的SQL语句。不要使用更高版本才支持的特性或语法。
{db_specific_notes_zh}

你的核心能力:
1. 数据库操作 - 执行INSERT、UPDATE、DELETE、CREATE TABLE等SQL操作
2. 数据查询 - 执行SELECT查询获取数据
3. 结构管理 - 创建表、修改表结构、管理索引
4. 性能调优 - 分析SQL性能、解读执行计划、优化索引
5. 数据库诊断 - 诊断性能瓶颈、检查表状态

可用工具:
- list_tables: 列出所有表
- describe_table: 查看表结构
- get_sample_data: 获取表的示例数据
- execute_sql: 执行任意SQL(INSERT/UPDATE/DELETE/CREATE/ALTER/DROP等)
- execute_safe_query: 执行只读SELECT查询
- run_explain: 分析SQL执行计划
- check_index_usage: 检查索引使用情况
- get_table_stats: 获取表统计信息
- create_index: 创建索引
- analyze_table: 更新表统计信息
- identify_slow_queries: 识别慢查询

工作原则:
1. 主动使用工具 - 先用list_tables和describe_table了解数据库结构
2. 先查后改 - 执行修改操作前先查看相关数据
3. 确认机制 - 所有非SELECT操作(INSERT/UPDATE/DELETE/CREATE/DROP等)都会要求用户确认后才执行
4. 详细反馈 - 每次操作后告知用户执行结果

**错误处理与自我修复（重要）:**
当用户确认执行后SQL操作失败时：
1. **不要放弃** - 分析错误原因，理解问题，寻找解决方案
2. **自我反思** - 思考错误发生的原因（如：重复键、约束违反、语法错误）
3. **调整并重试** - 根据错误调整策略：
   - 重复键错误：修改SQL使用 INSERT IGNORE 或 ON DUPLICATE KEY UPDATE，然后重试
   - 约束违反：检查并修正数据，使用修正后的SQL重试
   - 语法错误：修正SQL语法后重试
   - 表/列不存在：先确认结构，再调整查询
4. **继续工作流程** - 解决错误后，继续执行任务的剩余步骤
5. **报告进度** - 简要告知用户遇到的错误及处理方式，然后继续执行

注意：你仍然必须对每个非SELECT操作要求用户确认！错误恢复机制是在用户确认执行之后才适用的。

示例工作流程（插入测试数据）：
1. 向用户展示 INSERT SQL，等待确认
2. 用户确认 -> 执行
3. 如果出错（如重复键）-> 分析错误，修改SQL（如添加 INSERT IGNORE），请求用户确认修改后的SQL
4. 继续执行任务的下一步

与用户交流时:
- 使用清晰的中文解释
- 主动展示操作结果
- 如果不确定,先询问用户

记住:你是用户的数据库助手,可以帮助他们直接操作数据库！遇到小错误时要有韧性，坚持完成任务！"""

        # 初始化工具定义
        self._init_tools()

    def _init_tools(self):
        """初始化工具定义(根据语言)"""
        if self.language == "en":
            self.tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "identify_slow_queries",
                        "description": "Identify slow queries in the database. For PostgreSQL uses pg_stat_statements, for MySQL uses performance_schema. Falls back to active queries if statistics are not available.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "min_duration_ms": {
                                    "type": "number",
                                    "description": "Minimum average execution time in milliseconds, default 1000ms"
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Number of results to return, default 20"
                                }
                            }
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_running_queries",
                        "description": "Get currently running queries. Shows PID, user, database, state, duration, etc.",
                        "parameters": {"type": "object", "properties": {}}
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "run_explain",
                        "description": "Run EXPLAIN to analyze SQL query execution plan. Shows index usage, full table scans, JOIN strategies, etc. analyze=true executes the query to get actual timing.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "sql": {"type": "string", "description": "SQL statement to analyze"},
                                "analyze": {"type": "boolean", "description": "Whether to actually execute (EXPLAIN ANALYZE), default false. True gets real execution time but runs the query."}
                            },
                            "required": ["sql"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "check_index_usage",
                        "description": "Check index usage for a table. Find unused indexes, scan counts, index sizes. For index optimization.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "table_name": {"type": "string", "description": "Table name"},
                                "schema": {"type": "string", "description": "Schema name, default public"}
                            },
                            "required": ["table_name"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_table_stats",
                        "description": "Get table statistics. Includes size, dead tuple ratio, last VACUUM/ANALYZE time, sequential scan count. For diagnosing table health.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "table_name": {"type": "string", "description": "Table name"},
                                "schema": {"type": "string", "description": "Schema name, default public"}
                            },
                            "required": ["table_name"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "create_index",
                        "description": "Create an index. Requires user confirmation. Uses online DDL when possible to minimize table locks (CONCURRENTLY for PostgreSQL, ALGORITHM=INPLACE for MySQL 5.6+).",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "index_sql": {"type": "string", "description": "CREATE INDEX statement"},
                                "concurrent": {"type": "boolean", "description": "Use online DDL (no/minimal table lock), default true"}
                            },
                            "required": ["index_sql"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "analyze_table",
                        "description": "Update table statistics (ANALYZE). Outdated statistics cause query optimizer to choose wrong execution plans. Safe operation, no table lock.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "table_name": {"type": "string", "description": "Table name"},
                                "schema": {"type": "string", "description": "Schema name, default public"}
                            },
                            "required": ["table_name"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "execute_safe_query",
                        "description": "Execute safe SELECT query. Only allows SELECT, no data modification. For getting additional database information.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "sql": {"type": "string", "description": "SELECT query statement"}
                            },
                            "required": ["sql"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "execute_sql",
                        "description": "Execute any SQL statement including INSERT, UPDATE, DELETE, CREATE TABLE, ALTER TABLE, DROP TABLE, etc. For direct database operations. Returns affected rows or query results.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "sql": {"type": "string", "description": "SQL statement to execute"}
                            },
                            "required": ["sql"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "list_tables",
                        "description": "List all tables in the database with name and size information. For understanding database structure.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "schema": {"type": "string", "description": "Schema name, default public"}
                            }
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "describe_table",
                        "description": "Get detailed table structure including column names, data types, nullability, defaults, primary keys and foreign keys.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "table_name": {"type": "string", "description": "Table name"},
                                "schema": {"type": "string", "description": "Schema name, default public"}
                            },
                            "required": ["table_name"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_sample_data",
                        "description": "Get sample data from a table to understand the data content and format.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "table_name": {"type": "string", "description": "Table name"},
                                "schema": {"type": "string", "description": "Schema name, default public"},
                                "limit": {"type": "integer", "description": "Number of rows to return, default 10"}
                            },
                            "required": ["table_name"]
                        }
                    }
                }
            ]
        else:
            # Chinese tools
            self.tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "identify_slow_queries",
                        "description": "识别数据库中的慢查询。PostgreSQL使用pg_stat_statements，MySQL使用performance_schema。如不可用则显示当前活动查询。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "min_duration_ms": {"type": "number", "description": "最小平均执行时间(毫秒),默认1000ms"},
                                "limit": {"type": "integer", "description": "返回结果数量,默认20"}
                            }
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_running_queries",
                        "description": "获取当前正在运行的查询。显示查询的PID、用户、数据库、状态、运行时间等信息。",
                        "parameters": {"type": "object", "properties": {}}
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "run_explain",
                        "description": "运行EXPLAIN分析SQL查询的执行计划。可以看到是否使用索引、是否全表扫描、JOIN策略等。analyze=true会实际执行查询获取真实时间。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "sql": {"type": "string", "description": "要分析的SQL语句"},
                                "analyze": {"type": "boolean", "description": "是否实际执行查询(EXPLAIN ANALYZE),默认false。true会获取真实执行时间,但会实际执行查询。"}
                            },
                            "required": ["sql"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "check_index_usage",
                        "description": "检查表的索引使用情况。可以发现未使用的索引、索引扫描次数、索引大小等。用于索引优化。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "table_name": {"type": "string", "description": "表名"},
                                "schema": {"type": "string", "description": "模式名,默认public"}
                            },
                            "required": ["table_name"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_table_stats",
                        "description": "获取表的统计信息。包括表大小、死元组比例、最后VACUUM/ANALYZE时间、顺序扫描次数等。用于诊断表的健康状况。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "table_name": {"type": "string", "description": "表名"},
                                "schema": {"type": "string", "description": "模式名,默认public"}
                            },
                            "required": ["table_name"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "create_index",
                        "description": "创建索引。需要用户确认后才能执行。默认使用在线DDL避免锁表(PostgreSQL使用CONCURRENTLY，MySQL 5.6+使用ALGORITHM=INPLACE)。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "index_sql": {"type": "string", "description": "CREATE INDEX语句"},
                                "concurrent": {"type": "boolean", "description": "是否使用在线DDL(不锁表/少锁表),默认true"}
                            },
                            "required": ["index_sql"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "analyze_table",
                        "description": "更新表的统计信息(ANALYZE)。统计信息过期会导致查询优化器选择错误的执行计划。这个操作很安全,不会锁表。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "table_name": {"type": "string", "description": "表名"},
                                "schema": {"type": "string", "description": "模式名,默认public"}
                            },
                            "required": ["table_name"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "execute_safe_query",
                        "description": "执行安全的SELECT查询。只允许SELECT,不允许修改数据。用于获取额外的数据库信息。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "sql": {"type": "string", "description": "SELECT查询语句"}
                            },
                            "required": ["sql"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "execute_sql",
                        "description": "执行任意SQL语句，包括INSERT、UPDATE、DELETE、CREATE TABLE、ALTER TABLE、DROP TABLE等。用于直接操作数据库。返回影响的行数或查询结果。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "sql": {"type": "string", "description": "要执行的SQL语句"}
                            },
                            "required": ["sql"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "list_tables",
                        "description": "列出数据库中的所有表，包括表名和大小信息。用于了解数据库结构。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "schema": {"type": "string", "description": "模式名,默认public"}
                            }
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "describe_table",
                        "description": "获取表的详细结构信息，包括列名、数据类型、是否可空、默认值、主键和外键信息。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "table_name": {"type": "string", "description": "表名"},
                                "schema": {"type": "string", "description": "模式名,默认public"}
                            },
                            "required": ["table_name"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_sample_data",
                        "description": "获取表的示例数据，用于了解表中的数据内容和格式。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "table_name": {"type": "string", "description": "表名"},
                                "schema": {"type": "string", "description": "模式名,默认public"},
                                "limit": {"type": "integer", "description": "返回的行数,默认10"}
                            },
                            "required": ["table_name"]
                        }
                    }
                }
            ]

    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具调用"""
        logger.info(f"执行工具: {tool_name}")
        logger.debug(f"输入参数: {tool_input}")

        try:
            if tool_name == "identify_slow_queries":
                result = self.db_tools.identify_slow_queries(**tool_input)
            elif tool_name == "run_explain":
                result = self.db_tools.run_explain(**tool_input)
            elif tool_name == "check_index_usage":
                result = self.db_tools.check_index_usage(**tool_input)
            elif tool_name == "get_table_stats":
                result = self.db_tools.get_table_stats(**tool_input)
            elif tool_name == "create_index":
                # 创建索引需要确认，加入队列
                self.pending_operations.append({"type": "create_index", "input": tool_input})
                result = {
                    "status": "pending_confirmation",
                    "sql": tool_input.get("index_sql", ""),
                    "message": t("db_create_index_need_confirm")
                }
            elif tool_name == "analyze_table":
                result = self.db_tools.analyze_table(**tool_input)
            elif tool_name == "execute_safe_query":
                result = self.db_tools.execute_safe_query(**tool_input)
            elif tool_name == "execute_sql":
                result = self.db_tools.execute_sql(**tool_input)
                # 如果需要确认，加入待确认队列
                if result.get("status") == "pending_confirmation":
                    self.pending_operations.append({"type": "execute_sql", "input": tool_input})
            elif tool_name == "list_tables":
                result = self.db_tools.list_tables(**tool_input)
            elif tool_name == "describe_table":
                result = self.db_tools.describe_table(**tool_input)
            elif tool_name == "get_sample_data":
                result = self.db_tools.get_sample_data(**tool_input)
            elif tool_name == "get_running_queries":
                result = self.db_tools.get_running_queries()
            else:
                result = {"status": "error", "error": t("db_unknown_tool", tool=tool_name)}

            logger.info(f"工具执行完成: status={result.get('status')}")
            return result

        except Exception as e:
            logger.error(f"工具执行异常: {e}")
            return {"status": "error", "error": str(e)}

    def has_pending_operations(self) -> bool:
        """检查是否有待确认的操作"""
        return len(self.pending_operations) > 0

    def get_pending_count(self) -> int:
        """获取待确认操作的数量"""
        return len(self.pending_operations)

    def get_all_pending_operations(self) -> List[Dict[str, Any]]:
        """获取所有待确认的操作"""
        result = []
        for op in self.pending_operations:
            if op["type"] == "execute_sql":
                sql = op["input"].get("sql", "")
            elif op["type"] == "create_index":
                sql = op["input"].get("index_sql", "")
            else:
                sql = ""
            result.append({"type": op["type"], "sql": sql})
        return result

    def confirm_operation(self, index: int) -> Dict[str, Any]:
        """确认并执行指定索引的操作"""
        if index < 0 or index >= len(self.pending_operations):
            return {"status": "error", "error": t("db_invalid_operation_index")}

        pending = self.pending_operations[index]

        if pending["type"] == "execute_sql":
            return self.db_tools.execute_sql(pending["input"]["sql"], confirmed=True)
        elif pending["type"] == "create_index":
            return self.db_tools.create_index(**pending["input"])

        return {"status": "error", "error": t("db_unknown_pending_type")}

    def clear_pending_operations(self):
        """清空所有待确认的操作"""
        self.pending_operations = []

    def chat(self, user_message: str, max_iterations: int = 30, on_thinking: callable = None) -> str:
        """
        与AI Agent对话

        Args:
            user_message: 用户消息
            max_iterations: 最大工具调用迭代次数
            on_thinking: 思考过程回调函数，接收(event_type, data)参数

        Returns:
            Agent的响应
        """
        def notify(event_type: str, data: Any = None):
            if on_thinking:
                on_thinking(event_type, data)

        # 清空待确认操作队列
        self.pending_operations = []

        # 添加用户消息到历史
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            notify("thinking", t("agent_thinking", iteration=iteration))

            # 构建消息列表(包含system消息)
            messages = [{"role": "system", "content": self.system_prompt}] + self.conversation_history

            # 调用LLM API (统一接口)
            response = self.llm_client.chat(messages=messages, tools=self.tools)

            finish_reason = response["finish_reason"]
            content = response["content"]
            tool_calls = response["tool_calls"]

            # 检查是否需要调用工具
            if finish_reason == "tool_calls" and tool_calls:
                # 添加assistant消息(包含tool_calls)
                self.conversation_history.append({
                    "role": "assistant",
                    "content": content,
                    "tool_calls": [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc["name"],
                                "arguments": json.dumps(tc["arguments"], ensure_ascii=False)
                            }
                        }
                        for tc in tool_calls
                    ]
                })

                # 执行所有工具调用
                for tc in tool_calls:
                    tool_name = tc["name"]
                    tool_input = tc["arguments"]

                    # 通知正在调用工具
                    notify("tool_call", {"name": tool_name, "input": tool_input})

                    # 执行工具
                    result = self._execute_tool(tool_name, tool_input)

                    # 通知工具结果
                    notify("tool_result", {"name": tool_name, "result": result})

                    # 添加工具结果到历史
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps(result, ensure_ascii=False, default=str)
                    })

            elif finish_reason == "stop":
                # 对话结束
                text_response = content or ""

                # 添加assistant响应到历史
                self.conversation_history.append({
                    "role": "assistant",
                    "content": text_response
                })

                return text_response

            else:
                # 其他情况
                return t("agent_conversation_error", reason=finish_reason)

        return t("agent_need_more_time")

    def reset_conversation(self):
        """重置对话历史"""
        logger.info("重置对话历史")
        self.conversation_history = []

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """获取对话历史"""
        return self.conversation_history
