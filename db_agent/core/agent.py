"""
SQL Tuning AI Agent - Core Engine
"""
import json
from typing import Dict, List, Any, TYPE_CHECKING
import logging
from db_agent.llm import BaseLLMClient
from db_agent.i18n import i18n, t
from .database import DatabaseToolsFactory
from .migration_rules import get_migration_rules, format_rules_for_prompt, ORACLE_TO_GAUSSDB_RULES
from .token_counter import TokenCounter
from .context_compression import ContextCompressor
from db_agent.storage.models import MigrationTask, MigrationItem

if TYPE_CHECKING:
    from db_agent.storage import SQLiteStorage

logger = logging.getLogger(__name__)


class SQLTuningAgent:
    """SQL调优AI Agent - 智能体核心"""

    def __init__(
        self,
        llm_client: BaseLLMClient,
        db_config: Dict[str, Any],
        language: str = "zh",
        storage: "SQLiteStorage" = None,
        session_id: int = None
    ):
        """
        初始化AI Agent

        Args:
            llm_client: LLM客户端
            db_config: 数据库配置 (包含 type 字段指定数据库类型: postgresql 或 mysql)
            language: 界面语言 (zh/en)
            storage: SQLite storage instance for session persistence
            session_id: Session ID to associate with this agent
        """
        self.llm_client = llm_client
        self.storage = storage
        self.session_id = session_id

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

        # 初始化上下文压缩组件
        self.token_counter = TokenCounter(
            provider=llm_client.get_provider_name(),
            model=llm_client.get_model_name()
        )
        self.context_compressor = ContextCompressor(
            llm_client=llm_client,
            token_counter=self.token_counter
        )

        # 中断控制
        self._interrupt_requested = False
        self._interrupted_state = None  # 保存被打断时的状态

        logger.info(f"AI Agent初始化完成: {llm_client.get_provider_name()} - {llm_client.get_model_name()} (DB: {db_type})")

    def switch_model(self, llm_client: BaseLLMClient):
        """切换LLM模型"""
        self.llm_client = llm_client

        # 重新初始化上下文压缩组件（因为不同模型可能有不同的上下文限制）
        self.token_counter = TokenCounter(
            provider=llm_client.get_provider_name(),
            model=llm_client.get_model_name()
        )
        self.context_compressor = ContextCompressor(
            llm_client=llm_client,
            token_counter=self.token_counter
        )

        logger.info(f"模型已切换: {llm_client.get_provider_name()} - {llm_client.get_model_name()}")

    def reinitialize_db_tools(self, db_config: Dict[str, Any]):
        """
        重新初始化数据库工具（用于切换数据库连接）

        Args:
            db_config: 新的数据库配置
        """
        db_config = db_config.copy()
        db_type = db_config.pop("type", "postgresql")
        self.db_type = db_type

        # 重新创建数据库工具
        self.db_tools = DatabaseToolsFactory.create(db_type, db_config)
        self.db_info = self.db_tools.get_db_info()

        # 重新初始化系统提示
        self._init_system_prompt()

        logger.info(f"数据库工具已重新初始化: {db_type}")

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

        # Database type display name and mode info
        if db_type == "gaussdb":
            db_type_name = "GaussDB"
            is_distributed = self.db_info.get("is_distributed", False)
            mode_info = " (Distributed)" if is_distributed else " (Centralized)"
            db_type_name = f"GaussDB{mode_info}"
        elif db_type == "mysql":
            db_type_name = "MySQL"
        elif db_type == "oracle":
            db_type_name = "Oracle"
        elif db_type == "sqlserver":
            is_azure = self.db_info.get("is_azure", False)
            db_type_name = "Azure SQL Database" if is_azure else "SQL Server"
        else:
            db_type_name = "PostgreSQL"

        # Database-specific notes
        if db_type == "gaussdb":
            is_distributed = self.db_info.get("is_distributed", False)
            if is_distributed:
                db_specific_notes_en = """
GaussDB (Distributed) specific notes:
- Huawei proprietary database, PostgreSQL syntax compatible
- Distributed mode (MPP architecture), suitable for OLAP scenarios
- Use PGXC_STAT_ACTIVITY to view cross-node queries (query_id is same across nodes)
- Use PGXC_THREAD_WAIT_STATUS for cross-node thread wait status
- Use PGXC_LOCKS to check distributed lock information
- Use EXPLAIN ANALYZE to analyze execution plans
- Consider data distribution and skew issues in distributed mode
- Check pgxc_node table for cluster node information

**Oracle to GaussDB Core Migration Rules:**
- Packages: DBMS_LOB→DBE_LOB, DBMS_OUTPUT→DBE_OUTPUT, DBMS_RANDOM→DBE_RANDOM, UTL_RAW→DBE_RAW, DBMS_SQL→DBE_SQL
- Data Types: NUMBER negative scale not supported; VARCHAR2 CHAR unit not supported; DATE→TIMESTAMP(0)
- SQL: != must not have space; CONNECT BY→WITH RECURSIVE; ROWNUM avoid in JOIN ON
- Functions: ROUND(NULL) errors; '.' in REGEXP matches newline; use TO_CHAR before LOWER/UPPER on dates"""
                db_specific_notes_zh = """
GaussDB (分布式) 特定说明:
- 华为自研数据库，兼容 PostgreSQL 语法
- 分布式模式 (MPP 架构)，适合 OLAP 场景
- 使用 PGXC_STAT_ACTIVITY 查看跨节点查询（query_id 跨节点相同）
- 使用 PGXC_THREAD_WAIT_STATUS 查看跨节点线程等待状态
- 使用 PGXC_LOCKS 检查分布式锁信息
- 使用 EXPLAIN ANALYZE 分析执行计划
- 分布式模式注意数据分布和倾斜问题
- 查看 pgxc_node 表获取集群节点信息

**Oracle迁移到GaussDB核心规则：**
- 高级包：DBMS_LOB→DBE_LOB, DBMS_OUTPUT→DBE_OUTPUT, DBMS_RANDOM→DBE_RANDOM, UTL_RAW→DBE_RAW, DBMS_SQL→DBE_SQL
- 数据类型：NUMBER负数标度不支持；VARCHAR2 CHAR单位不支持；DATE→TIMESTAMP(0)
- SQL语法：!=不能有空格；CONNECT BY改用WITH RECURSIVE；ROWNUM避免在JOIN ON中使用
- 函数：ROUND(NULL)会报错；REGEXP中'.'默认匹配换行；日期用LOWER/UPPER前先TO_CHAR"""
            else:
                db_specific_notes_en = """
GaussDB (Centralized) specific notes:
- Huawei proprietary database, PostgreSQL syntax compatible
- Centralized mode (single node/HA cluster), suitable for OLTP scenarios
- Use PG_STAT_ACTIVITY to view active queries
- Use PG_THREAD_WAIT_STATUS for thread wait status
- Use PG_LOCKS to check lock information
- Use EXPLAIN ANALYZE to analyze execution plans
- CREATE INDEX CONCURRENTLY avoids table locks

**Oracle to GaussDB Core Migration Rules:**

1. Package Replacements (MUST change):
   - DBMS_LOB → DBE_LOB (CLOB2FILE not supported)
   - DBMS_OUTPUT → DBE_OUTPUT
   - DBMS_RANDOM → DBE_RANDOM (SEED→SET_SEED, VALUE→GET_VALUE)
   - UTL_RAW → DBE_RAW (CAST_FROM_NUMBER→CAST_FROM_NUMBER_TO_RAW)
   - DBMS_SQL → DBE_SQL (OPEN_CURSOR→REGISTER_CONTEXT)

2. Data Type Differences:
   - NUMBER(p,-s): Negative scale not supported, use ROUND/TRUNC manually
   - VARCHAR2(n CHAR): Only BYTE unit supported, change to VARCHAR2(n*4)
   - DATE: Internally converted to TIMESTAMP(0), watch for precision loss
   - CLOB/BLOB: Oracle's "locator" concept not supported

3. SQL Syntax Key Differences:
   - != operator: Must NOT have space like "! =" (space makes ! factorial)
   - CONNECT BY: Only CONNECT_BY_FILTERING mode, use WITH RECURSIVE for complex hierarchies
   - ROWNUM: Avoid in JOIN ON clause, use in outer WHERE or ROW_NUMBER()

4. Function Differences:
   - ROUND(NULL,...) throws error in GaussDB
   - CHR(0) or CHR(256) truncates at \\0
   - '.' in REGEXP_REPLACE matches newline by default (Oracle doesn't)
   - LOWER/UPPER implicit date conversion format differs, use TO_CHAR first

5. PL/SQL Differences:
   - %TYPE doesn't support record variable attribute references
   - FOR...REVERSE requires lower_bound >= upper_bound
   - Collection comparison is order-strict (Oracle ignores order)"""
                db_specific_notes_zh = """
GaussDB (集中式) 特定说明:
- 华为自研数据库，兼容 PostgreSQL 语法
- 集中式模式（单节点/高可用集群），适合 OLTP 场景
- 使用 PG_STAT_ACTIVITY 查看活跃查询
- 使用 PG_THREAD_WAIT_STATUS 查看线程等待状态
- 使用 PG_LOCKS 检查锁信息
- 使用 EXPLAIN ANALYZE 分析执行计划
- CREATE INDEX CONCURRENTLY 可以避免锁表

**Oracle迁移到GaussDB核心规则：**

1. 高级包替换（必须改）：
   - DBMS_LOB → DBE_LOB（不支持CLOB2FILE）
   - DBMS_OUTPUT → DBE_OUTPUT
   - DBMS_RANDOM → DBE_RANDOM（SEED→SET_SEED, VALUE→GET_VALUE）
   - UTL_RAW → DBE_RAW（CAST_FROM_NUMBER→CAST_FROM_NUMBER_TO_RAW）
   - DBMS_SQL → DBE_SQL（OPEN_CURSOR→REGISTER_CONTEXT）

2. 数据类型差异：
   - NUMBER(p,-s)：GaussDB不支持负数标度，需手动ROUND/TRUNC
   - VARCHAR2(n CHAR)：GaussDB仅支持BYTE，改为VARCHAR2(n*4)
   - DATE：GaussDB内部转为TIMESTAMP(0)，注意精度
   - CLOB/BLOB：不支持Oracle的"定位器"概念

3. SQL语法关键差异：
   - != 运算符：禁止写成 "! ="（有空格会被识别为阶乘）
   - CONNECT BY：仅支持CONNECT_BY_FILTERING，复杂层次查询改用WITH RECURSIVE
   - ROWNUM：避免在JOIN ON中使用，改在外层WHERE或用ROW_NUMBER()

4. 函数差异：
   - ROUND(NULL,...)在GaussDB会报错
   - CHR(0)或CHR(256)会在\\0处截断
   - REGEXP_REPLACE中'.'默认匹配换行符（Oracle不匹配）
   - LOWER/UPPER对日期的隐式转换格式不同，建议先TO_CHAR

5. PL/SQL差异：
   - %TYPE不支持record变量属性引用
   - FOR...REVERSE要求lower_bound >= upper_bound
   - 集合比较严格按顺序，不像Oracle忽略顺序

**补充说明：** 以上为GaussDB专用核心规则。对于核心规则未覆盖的Oracle语法，请参考Oracle→PostgreSQL的通用转换规则：
- ROWNUM → LIMIT/OFFSET 或 ROW_NUMBER()
- (+)外连接 → LEFT/RIGHT JOIN
- MERGE INTO → INSERT ON CONFLICT (UPSERT)
- NVL → COALESCE
- DECODE → CASE WHEN
- 序列: seq.NEXTVAL → nextval('seq')
- LISTAGG → STRING_AGG
- SYS_GUID() → GEN_RANDOM_UUID()
- TO_DATE/TO_CHAR 格式字符串需调整
- PL/SQL → PL/pgSQL 语法调整（PACKAGE不支持，用SCHEMA组织）"""
        elif db_type == "mysql":
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
        elif db_type == "oracle":
            db_type_name = "Oracle"
            db_specific_notes_en = """
Oracle-specific notes:
- Uses oracledb Thin mode driver (no Oracle Client required)
- Supports Oracle 12c and above (12.1, 12.2, 18c, 19c, 21c, 23c)
- Use DBMS_XPLAN.DISPLAY for execution plan analysis
- Use V$SQL and V$SESSION for performance monitoring
- CREATE INDEX ONLINE avoids table locks
- Use DBMS_STATS.GATHER_TABLE_STATS to update statistics
- FETCH FIRST n ROWS ONLY for pagination (12c+)
- DBA_* views require DBA privileges, falls back to ALL_* views"""
            db_specific_notes_zh = """
Oracle特定说明:
- 使用oracledb Thin模式驱动（无需安装Oracle客户端）
- 支持Oracle 12c及以上版本（12.1、12.2、18c、19c、21c、23c）
- 使用DBMS_XPLAN.DISPLAY分析执行计划
- 使用V$SQL和V$SESSION进行性能监控
- CREATE INDEX ONLINE可以避免锁表
- 使用DBMS_STATS.GATHER_TABLE_STATS更新统计信息
- FETCH FIRST n ROWS ONLY用于分页（12c+）
- DBA_*视图需要DBA权限，无权限时降级使用ALL_*视图"""
        elif db_type == "sqlserver":
            db_type_name = "SQL Server"
            is_azure = self.db_info.get("is_azure", False)
            version_major = self.db_info.get("version_major", 0)
            if is_azure:
                db_type_name = "Azure SQL Database"
            db_specific_notes_en = f"""
SQL Server-specific notes:
- Uses pytds (python-tds) driver - pure Python, no ODBC required
- Supports SQL Server 2014+ (12.x, 13.x, 14.x, 15.x, 16.x) and Azure SQL
- Current version: {version_major}.x {"(Azure SQL)" if is_azure else ""}
- Use SET SHOWPLAN_XML ON for execution plan analysis
- Use sys.dm_exec_query_stats for slow query analysis
- Query Store available in SQL Server 2016+ for historical query analysis
- CREATE INDEX ... WITH (ONLINE = ON) for online index creation (Enterprise only)
- Use UPDATE STATISTICS to refresh table statistics
- TOP n for row limiting (or OFFSET-FETCH for pagination)
- sys.dm_exec_requests for monitoring currently running queries

**Permission Requirements:**
- VIEW SERVER STATE (2019 and earlier) or VIEW SERVER PERFORMANCE STATE (2022+) for DMV access
- SHOWPLAN permission for execution plans

**SQL Server → Other Database Migration:**
| SQL Server | PostgreSQL/GaussDB |
|------------|-------------------|
| INT IDENTITY | SERIAL / GENERATED ALWAYS AS IDENTITY |
| NVARCHAR(n) | VARCHAR(n) |
| DATETIME / DATETIME2 | TIMESTAMP |
| BIT | BOOLEAN |
| UNIQUEIDENTIFIER | UUID |
| GETDATE() | CURRENT_TIMESTAMP |
| ISNULL(a,b) | COALESCE(a,b) |
| TOP n | LIMIT n |
| OFFSET n ROWS FETCH NEXT m ROWS ONLY | LIMIT m OFFSET n |
| [bracket] quotes | "double" quotes |"""
            db_specific_notes_zh = f"""
SQL Server特定说明:
- 使用pytds (python-tds)驱动 - 纯Python实现，无需ODBC
- 支持SQL Server 2014+（12.x、13.x、14.x、15.x、16.x）和Azure SQL
- 当前版本: {version_major}.x {"(Azure SQL)" if is_azure else ""}
- 使用SET SHOWPLAN_XML ON分析执行计划
- 使用sys.dm_exec_query_stats进行慢查询分析
- SQL Server 2016+支持Query Store进行历史查询分析
- CREATE INDEX ... WITH (ONLINE = ON)在线创建索引（仅企业版）
- 使用UPDATE STATISTICS更新表统计信息
- TOP n用于限制行数（或OFFSET-FETCH用于分页）
- sys.dm_exec_requests用于监控当前运行的查询

**权限要求:**
- VIEW SERVER STATE（2019及以前）或VIEW SERVER PERFORMANCE STATE（2022+）用于DMV访问
- SHOWPLAN权限用于执行计划

**SQL Server → 其他数据库迁移:**
| SQL Server | PostgreSQL/GaussDB |
|------------|-------------------|
| INT IDENTITY | SERIAL / GENERATED ALWAYS AS IDENTITY |
| NVARCHAR(n) | VARCHAR(n) |
| DATETIME / DATETIME2 | TIMESTAMP |
| BIT | BOOLEAN |
| UNIQUEIDENTIFIER | UUID |
| GETDATE() | CURRENT_TIMESTAMP |
| ISNULL(a,b) | COALESCE(a,b) |
| TOP n | LIMIT n |
| OFFSET n ROWS FETCH NEXT m ROWS ONLY | LIMIT m OFFSET n |
| [方括号]引用 | "双引号"引用 |"""
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
3. **IMPORTANT: Direct tool execution** - When you need to execute non-SELECT operations (INSERT/UPDATE/DELETE/CREATE/DROP etc.), call the execute_sql tool DIRECTLY. Do NOT ask the user for confirmation in your text response. The system will automatically prompt the user for confirmation through the CLI interface.
4. Detailed feedback - Inform the user of execution results after each operation

**How the confirmation mechanism works:**
- When you call execute_sql with a non-SELECT statement, the tool returns "pending_confirmation" status
- The CLI will then display the SQL to the user and ask them to confirm via a menu interface
- You do NOT need to ask "Do you want me to execute this?" - just call the tool directly
- After execution, continue with the workflow

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

Example workflow for inserting test data:
1. Check table structure using describe_table
2. Call execute_sql tool directly with the INSERT statement (system handles confirmation)
3. If error occurs -> Analyze error, modify SQL, call execute_sql again
4. Continue with next step of the task

When communicating with users:
- Use clear English explanations
- Proactively display operation results
- If uncertain, ask the user first

**Heterogeneous Database Migration Capability:**
When users upload SQL files from other database types (Oracle, MySQL, SQL Server, etc.) and ask to convert/migrate to the current database:

1. **Identify source database** - Analyze SQL syntax to detect the source database type
2. **Convert DDL syntax** - Transform data types, functions, and syntax to target database format
3. **Handle object dependencies** - Create objects in correct order (tables before indexes, etc.)
4. **Provide conversion summary** - Show a mapping table of converted syntax

Common syntax mappings (Source → Target {db_type_name}):

**Oracle → PostgreSQL/GaussDB:**
| Oracle | PostgreSQL/GaussDB |
|--------|-------------------|
| NUMBER(n) | INTEGER / BIGINT |
| NUMBER(p,s) | DECIMAL(p,s) / NUMERIC(p,s) |
| VARCHAR2(n) | VARCHAR(n) |
| CLOB | TEXT |
| BLOB | BYTEA |
| DATE | TIMESTAMP |
| SYSDATE | CURRENT_TIMESTAMP |
| NVL(a,b) | COALESCE(a,b) |
| DECODE() | CASE WHEN |
| ROWNUM | LIMIT / ROW_NUMBER() |
| || (concat) | || (same) |
| SEQUENCE.NEXTVAL | nextval('sequence') |

**MySQL → PostgreSQL/GaussDB:**
| MySQL | PostgreSQL/GaussDB |
|-------|-------------------|
| INT AUTO_INCREMENT | SERIAL / GENERATED ALWAYS AS IDENTITY |
| TINYINT | SMALLINT |
| DATETIME | TIMESTAMP |
| LONGTEXT | TEXT |
| ENUM() | VARCHAR + CHECK |
| IFNULL(a,b) | COALESCE(a,b) |
| NOW() | CURRENT_TIMESTAMP |
| LIMIT n,m | LIMIT m OFFSET n |
| ` (backtick) | " (double quote) |

**Oracle/PostgreSQL → MySQL:**
| Oracle/PostgreSQL | MySQL |
|-------------------|-------|
| SERIAL | INT AUTO_INCREMENT |
| TEXT | LONGTEXT |
| BOOLEAN | TINYINT(1) |
| BYTEA | LONGBLOB |
| CURRENT_TIMESTAMP | NOW() |
| " (double quote) | ` (backtick) |

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
3. **重要：直接调用工具** - 当需要执行非SELECT操作(INSERT/UPDATE/DELETE/CREATE/DROP等)时，直接调用execute_sql工具。不要在回复中询问用户是否确认，系统会通过CLI界面自动向用户显示确认菜单。
4. 详细反馈 - 每次操作后告知用户执行结果

**确认机制的工作方式:**
- 当你调用execute_sql执行非SELECT语句时，工具会返回"pending_confirmation"状态
- CLI会向用户显示SQL并通过菜单界面请求确认
- 你不需要问"是否要执行？" - 直接调用工具即可
- 执行完成后，继续工作流程

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

示例工作流程（插入测试数据）：
1. 使用describe_table查看表结构
2. 直接调用execute_sql工具执行INSERT语句（系统会处理确认）
3. 如果出错 -> 分析错误，修改SQL，再次调用execute_sql
4. 继续执行任务的下一步

与用户交流时:
- 使用清晰的中文解释
- 主动展示操作结果
- 如果不确定,先询问用户

**异构数据库迁移能力:**
当用户上传其他数据库类型的SQL文件（Oracle、MySQL、SQL Server等）并要求转换/迁移到当前数据库时：

1. **识别源数据库** - 分析SQL语法检测源数据库类型
2. **转换DDL语法** - 将数据类型、函数、语法转换为目标数据库格式
3. **处理对象依赖** - 按正确顺序创建对象（先表后索引等）
4. **提供转换摘要** - 显示已转换语法的映射表

常见语法映射（源数据库 → 目标 {db_type_name}）：

**Oracle → PostgreSQL/GaussDB:**
| Oracle | PostgreSQL/GaussDB |
|--------|-------------------|
| NUMBER(n) | INTEGER / BIGINT |
| NUMBER(p,s) | DECIMAL(p,s) / NUMERIC(p,s) |
| VARCHAR2(n) | VARCHAR(n) |
| CLOB | TEXT |
| BLOB | BYTEA |
| DATE | TIMESTAMP |
| SYSDATE | CURRENT_TIMESTAMP |
| NVL(a,b) | COALESCE(a,b) |
| DECODE() | CASE WHEN |
| ROWNUM | LIMIT / ROW_NUMBER() |
| || (连接符) | || (相同) |
| SEQUENCE.NEXTVAL | nextval('sequence') |

**MySQL → PostgreSQL/GaussDB:**
| MySQL | PostgreSQL/GaussDB |
|-------|-------------------|
| INT AUTO_INCREMENT | SERIAL / GENERATED ALWAYS AS IDENTITY |
| TINYINT | SMALLINT |
| DATETIME | TIMESTAMP |
| LONGTEXT | TEXT |
| ENUM() | VARCHAR + CHECK |
| IFNULL(a,b) | COALESCE(a,b) |
| NOW() | CURRENT_TIMESTAMP |
| LIMIT n,m | LIMIT m OFFSET n |
| ` (反引号) | " (双引号) |

**Oracle/PostgreSQL → MySQL:**
| Oracle/PostgreSQL | MySQL |
|-------------------|-------|
| SERIAL | INT AUTO_INCREMENT |
| TEXT | LONGTEXT |
| BOOLEAN | TINYINT(1) |
| BYTEA | LONGBLOB |
| CURRENT_TIMESTAMP | NOW() |
| " (双引号) | ` (反引号) |

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
                },
                # Migration tools
                {
                    "type": "function",
                    "function": {
                        "name": "analyze_source_database",
                        "description": "Analyze source database to get all objects (tables, indexes, views, sequences, procedures, etc.) and their dependencies for migration planning.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "source_connection_name": {"type": "string", "description": "Source database connection name"},
                                "schema": {"type": "string", "description": "Schema to analyze (optional)"},
                                "object_types": {"type": "array", "items": {"type": "string"}, "description": "Object types to include: table, view, index, sequence, procedure, function, trigger, constraint"}
                            },
                            "required": ["source_connection_name"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "create_migration_plan",
                        "description": "Create a migration plan with execution order based on object dependencies. Generates converted DDL for target database.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "task_id": {"type": "integer", "description": "Migration task ID"},
                                "source_connection_name": {"type": "string", "description": "Source database connection name"},
                                "target_schema": {"type": "string", "description": "Target schema name (optional)"}
                            },
                            "required": ["task_id", "source_connection_name"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_migration_plan",
                        "description": "Get migration plan details including all items and their status.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "task_id": {"type": "integer", "description": "Migration task ID"}
                            },
                            "required": ["task_id"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_migration_status",
                        "description": "Get migration task status and progress summary.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "task_id": {"type": "integer", "description": "Migration task ID"}
                            },
                            "required": ["task_id"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "execute_migration_item",
                        "description": "Execute a single migration item (create object in target database).",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "item_id": {"type": "integer", "description": "Migration item ID"}
                            },
                            "required": ["item_id"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "execute_migration_batch",
                        "description": "Execute multiple pending migration items in batch.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "task_id": {"type": "integer", "description": "Migration task ID"},
                                "batch_size": {"type": "integer", "description": "Number of items to execute, default 10"}
                            },
                            "required": ["task_id"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "compare_databases",
                        "description": "Compare source and target databases to verify migration results.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "task_id": {"type": "integer", "description": "Migration task ID"}
                            },
                            "required": ["task_id"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "generate_migration_report",
                        "description": "Generate detailed migration report with statistics and any errors.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "task_id": {"type": "integer", "description": "Migration task ID"}
                            },
                            "required": ["task_id"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "skip_migration_item",
                        "description": "Skip a migration item (mark as skipped).",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "item_id": {"type": "integer", "description": "Migration item ID"},
                                "reason": {"type": "string", "description": "Reason for skipping"}
                            },
                            "required": ["item_id"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "retry_failed_items",
                        "description": "Retry all failed migration items.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "task_id": {"type": "integer", "description": "Migration task ID"}
                            },
                            "required": ["task_id"]
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
                },
                # 迁移工具
                {
                    "type": "function",
                    "function": {
                        "name": "analyze_source_database",
                        "description": "分析源数据库，获取所有对象（表、索引、视图、序列、存储过程等）及其依赖关系，用于迁移计划制定。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "source_connection_name": {"type": "string", "description": "源数据库连接名称"},
                                "schema": {"type": "string", "description": "要分析的schema（可选）"},
                                "object_types": {"type": "array", "items": {"type": "string"}, "description": "要包含的对象类型：table、view、index、sequence、procedure、function、trigger、constraint"}
                            },
                            "required": ["source_connection_name"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "create_migration_plan",
                        "description": "根据对象依赖关系创建迁移计划，确定执行顺序，生成转换后的DDL。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "task_id": {"type": "integer", "description": "迁移任务ID"},
                                "source_connection_name": {"type": "string", "description": "源数据库连接名称"},
                                "target_schema": {"type": "string", "description": "目标schema名称（可选）"}
                            },
                            "required": ["task_id", "source_connection_name"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_migration_plan",
                        "description": "获取迁移计划详情，包括所有迁移项及其状态。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "task_id": {"type": "integer", "description": "迁移任务ID"}
                            },
                            "required": ["task_id"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_migration_status",
                        "description": "获取迁移任务状态和进度摘要。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "task_id": {"type": "integer", "description": "迁移任务ID"}
                            },
                            "required": ["task_id"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "execute_migration_item",
                        "description": "执行单个迁移项（在目标数据库中创建对象）。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "item_id": {"type": "integer", "description": "迁移项ID"}
                            },
                            "required": ["item_id"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "execute_migration_batch",
                        "description": "批量执行待处理的迁移项。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "task_id": {"type": "integer", "description": "迁移任务ID"},
                                "batch_size": {"type": "integer", "description": "每批执行数量，默认10"}
                            },
                            "required": ["task_id"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "compare_databases",
                        "description": "比对源库和目标库对象，验证迁移结果。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "task_id": {"type": "integer", "description": "迁移任务ID"}
                            },
                            "required": ["task_id"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "generate_migration_report",
                        "description": "生成详细的迁移报告，包括统计信息和错误详情。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "task_id": {"type": "integer", "description": "迁移任务ID"}
                            },
                            "required": ["task_id"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "skip_migration_item",
                        "description": "跳过某个迁移项（标记为已跳过）。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "item_id": {"type": "integer", "description": "迁移项ID"},
                                "reason": {"type": "string", "description": "跳过原因"}
                            },
                            "required": ["item_id"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "retry_failed_items",
                        "description": "重试所有失败的迁移项。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "task_id": {"type": "integer", "description": "迁移任务ID"}
                            },
                            "required": ["task_id"]
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
                sql = tool_input.get("sql", "")

                # 分析类查询性能检查
                perf_check = self.db_tools.check_query_performance(sql)

                if perf_check.get("should_confirm"):
                    # 发现性能问题，加入待确认队列
                    self.pending_operations.append({
                        "type": "execute_safe_query",
                        "input": tool_input,
                        "performance_check": perf_check
                    })
                    result = {
                        "status": "pending_performance_confirmation",
                        "sql": sql,
                        "performance_summary": perf_check.get("performance_summary"),
                        "issues": perf_check.get("issues"),
                        "message": t("db_performance_issue_need_confirm")
                    }
                else:
                    # 无性能问题，直接执行
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
            # Migration tools
            elif tool_name == "analyze_source_database":
                result = self._execute_analyze_source_database(**tool_input)
            elif tool_name == "create_migration_plan":
                result = self._execute_create_migration_plan(**tool_input)
            elif tool_name == "get_migration_plan":
                result = self._execute_get_migration_plan(**tool_input)
            elif tool_name == "get_migration_status":
                result = self._execute_get_migration_status(**tool_input)
            elif tool_name == "execute_migration_item":
                result = self._execute_migration_item(**tool_input)
            elif tool_name == "execute_migration_batch":
                result = self._execute_migration_batch(**tool_input)
            elif tool_name == "compare_databases":
                result = self._execute_compare_databases(**tool_input)
            elif tool_name == "generate_migration_report":
                result = self._execute_generate_migration_report(**tool_input)
            elif tool_name == "skip_migration_item":
                result = self._execute_skip_migration_item(**tool_input)
            elif tool_name == "retry_failed_items":
                result = self._execute_retry_failed_items(**tool_input)
            else:
                result = {"status": "error", "error": t("db_unknown_tool", tool=tool_name)}

            logger.info(f"工具执行完成: status={result.get('status')}")
            return result

        except Exception as e:
            logger.error(f"工具执行异常: {e}")
            return {"status": "error", "error": str(e)}

    # ==================== Interrupt Control Methods ====================

    def request_interrupt(self):
        """请求中断当前操作"""
        self._interrupt_requested = True

    def clear_interrupt(self):
        """清除中断标志"""
        self._interrupt_requested = False

    def is_interrupt_requested(self) -> bool:
        """检查是否请求了中断"""
        return self._interrupt_requested

    def has_interrupted_task(self) -> bool:
        """检查是否有被打断的任务"""
        return self._interrupted_state is not None

    def get_interrupted_state(self) -> Dict[str, Any]:
        """获取被打断的状态"""
        return self._interrupted_state

    def clear_interrupted_state(self):
        """清除被打断的状态"""
        self._interrupted_state = None

    # ==================== Pending Operations Methods ====================

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
                result.append({"type": op["type"], "sql": sql})
            elif op["type"] == "create_index":
                sql = op["input"].get("index_sql", "")
                result.append({"type": op["type"], "sql": sql})
            elif op["type"] == "execute_safe_query":
                sql = op["input"].get("sql", "")
                perf_check = op.get("performance_check", {})
                result.append({
                    "type": op["type"],
                    "sql": sql,
                    "performance_issues": perf_check.get("issues", []),
                    "performance_summary": perf_check.get("performance_summary", {})
                })
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
        elif pending["type"] == "execute_safe_query":
            # 用户确认后执行查询（跳过性能检查）
            return self.db_tools.execute_safe_query(**pending["input"])

        return {"status": "error", "error": t("db_unknown_pending_type")}

    def clear_pending_operations(self):
        """清空所有待确认的操作"""
        self.pending_operations = []

    def chat(self, user_message: str, max_iterations: int = 30,
             on_thinking: callable = None) -> str:
        """
        与AI Agent对话

        Args:
            user_message: 用户消息
            max_iterations: 最大工具调用迭代次数
            on_thinking: 思考过程回调函数，接收(event_type, data)参数

        Returns:
            Agent的响应，如果被中断返回 None
        """
        def notify(event_type: str, data: Any = None):
            if on_thinking:
                on_thinking(event_type, data)

        # 清除中断标志
        self._interrupt_requested = False

        # 清空待确认操作队列
        self.pending_operations = []

        # 如果有被打断的任务，添加上下文让AI判断用户意图
        if self._interrupted_state:
            state = self._interrupted_state
            self._interrupted_state = None

            # 构建上下文提示
            context_hint = t("interrupted_context_hint")
            full_message = f"[{context_hint}]\n{user_message}"

            self.conversation_history.append({
                "role": "user",
                "content": full_message
            })
            self._save_message("user", content=full_message)
        else:
            # 正常开始新对话
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            self._save_message("user", content=user_message)

        iteration = 0
        original_message = user_message

        while iteration < max_iterations:
            iteration += 1

            # 检查是否请求中断
            if self._interrupt_requested:
                self._interrupted_state = {
                    "iteration": iteration - 1,  # 保存当前迭代位置
                    "original_message": original_message,
                }
                self._interrupt_requested = False
                logger.info("对话被用户中断")
                return None  # 返回 None 表示被中断

            notify("thinking", t("agent_thinking", iteration=iteration))

            # 检查是否需要压缩上下文
            if self.context_compressor.needs_compression(
                self.system_prompt, self.conversation_history
            ):
                self._compress_context()

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
                tool_calls_formatted = [
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
                self.conversation_history.append({
                    "role": "assistant",
                    "content": content,
                    "tool_calls": tool_calls_formatted
                })
                # Save assistant message with tool calls to database
                self._save_message("assistant", content=content, tool_calls=tool_calls_formatted)

                # 执行所有工具调用
                for tc in tool_calls:
                    # 在执行工具前检查中断
                    if self._interrupt_requested:
                        self._interrupted_state = {
                            "iteration": iteration,
                            "original_message": original_message,
                        }
                        self._interrupt_requested = False
                        logger.info("对话在工具执行期间被用户中断")
                        return None

                    tool_name = tc["name"]
                    tool_input = tc["arguments"]

                    # 通知正在调用工具
                    notify("tool_call", {"name": tool_name, "input": tool_input})

                    # 执行工具
                    result = self._execute_tool(tool_name, tool_input)

                    # 通知工具结果
                    notify("tool_result", {"name": tool_name, "result": result})

                    # 添加工具结果到历史
                    tool_result_content = json.dumps(result, ensure_ascii=False, default=str)
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": tool_result_content
                    })
                    # Save tool message to database
                    self._save_message("tool", content=tool_result_content, tool_call_id=tc["id"])

                    # 检查是否有待确认操作，如果有则立即返回，等待用户确认
                    if result.get("status") in ("pending_confirmation", "pending_performance_confirmation"):
                        return content or t("db_pending_confirmation_waiting")

                    # 在工具执行后再次检查中断
                    if self._interrupt_requested:
                        self._interrupted_state = {
                            "iteration": iteration,
                            "original_message": original_message,
                        }
                        self._interrupt_requested = False
                        logger.info("对话在工具执行后被用户中断")
                        return None

            elif finish_reason == "stop":
                # 对话结束
                text_response = content or ""

                # 添加assistant响应到历史
                self.conversation_history.append({
                    "role": "assistant",
                    "content": text_response
                })
                # Save assistant response to database
                self._save_message("assistant", content=text_response)

                return text_response

            elif finish_reason == "error":
                # API 错误，直接返回错误消息
                return content or t("agent_conversation_error", reason=finish_reason)

            else:
                # 其他情况
                return t("agent_conversation_error", reason=finish_reason)

        return t("agent_need_more_time")

    def reset_conversation(self):
        """重置对话历史"""
        logger.info("重置对话历史")
        self.conversation_history = []
        # Also clear from database if session is set
        if self.storage and self.session_id:
            self.storage.clear_session_messages(self.session_id)

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """获取对话历史"""
        return self.conversation_history

    # ==================== Session Management Methods ====================

    def set_session(self, session_id: int, restore_history: bool = True):
        """
        设置当前会话并可选恢复历史

        Args:
            session_id: Session ID
            restore_history: Whether to restore conversation history from database
        """
        self.session_id = session_id
        if restore_history:
            self._restore_conversation_history()

    def _restore_conversation_history(self):
        """从数据库恢复聊天历史"""
        if not self.storage or not self.session_id:
            return

        messages = self.storage.get_session_messages(self.session_id)
        self.conversation_history = []

        for msg in messages:
            history_msg = {
                "role": msg.role,
                "content": msg.content
            }
            # Restore tool_calls for assistant messages
            if msg.tool_calls:
                try:
                    history_msg["tool_calls"] = json.loads(msg.tool_calls)
                except json.JSONDecodeError:
                    pass
            # Restore tool_call_id for tool messages
            if msg.tool_call_id:
                history_msg["tool_call_id"] = msg.tool_call_id

            self.conversation_history.append(history_msg)

        logger.info(f"恢复了 {len(self.conversation_history)} 条历史消息")

    def _save_message(self, role: str, content: str = None,
                      tool_calls: List[Dict] = None, tool_call_id: str = None):
        """
        保存消息到数据库

        Args:
            role: Message role ("user", "assistant", "tool")
            content: Message content
            tool_calls: Tool calls list (for assistant messages)
            tool_call_id: Tool call ID (for tool messages)
        """
        if not self.storage or not self.session_id:
            return

        tool_calls_json = None
        if tool_calls:
            tool_calls_json = json.dumps(tool_calls, ensure_ascii=False)

        self.storage.add_message(
            session_id=self.session_id,
            role=role,
            content=content,
            tool_calls=tool_calls_json,
            tool_call_id=tool_call_id
        )

    def _compress_context(self):
        """压缩对话上下文"""
        logger.info(t("agent_compressing_context"))

        compressed, info = self.context_compressor.compress(
            self.system_prompt,
            self.conversation_history,
            self.language
        )

        if info.get("compressed"):
            # 保存摘要到数据库
            if self.storage and self.session_id:
                summary_msg = compressed[0]  # 第一条是摘要消息
                self.storage.save_context_summary(
                    session_id=self.session_id,
                    summary_text=summary_msg["content"],
                    messages_count=info["messages_compressed"],
                    original_tokens=info["original_tokens"],
                    compressed_tokens=info["compressed_tokens"]
                )
                # 删除已压缩的消息
                self.storage.delete_oldest_messages(
                    self.session_id,
                    info["messages_compressed"]
                )
                # 保存摘要消息到数据库
                self._save_message("assistant", content=summary_msg["content"])

            # 更新内存中的历史
            self.conversation_history = compressed

            logger.info(
                f"上下文已压缩: {info['messages_compressed']} 条消息, "
                f"{info['original_tokens']} -> {info['compressed_tokens']} tokens"
            )

    # ==================== Migration Tool Implementations ====================

    def _execute_analyze_source_database(self, source_connection_name: str,
                                          schema: str = None,
                                          object_types: List[str] = None,
                                          **kwargs) -> Dict[str, Any]:
        """Analyze source database for migration"""
        if not self.storage:
            return {"status": "error", "error": t("migration_storage_required")}

        # Get source connection
        source_conn = self.storage.get_connection(source_connection_name)
        if not source_conn:
            return {"status": "error", "error": t("migration_source_not_found", name=source_connection_name)}

        try:
            # Decrypt password and create source db tools
            from db_agent.storage.encryption import decrypt
            password = decrypt(source_conn.password_encrypted)
            source_config = {
                "type": source_conn.db_type,
                "host": source_conn.host,
                "port": source_conn.port,
                "database": source_conn.database,
                "user": source_conn.username,
                "password": password
            }
            source_tools = DatabaseToolsFactory.create(source_conn.db_type, source_config)

            # Get all objects
            objects_result = source_tools.get_all_objects(schema=schema, object_types=object_types)
            if objects_result.get("status") == "error":
                return objects_result

            # Get FK dependencies for table ordering
            fk_deps = source_tools.get_foreign_key_dependencies(schema=schema)

            # Get object dependencies
            obj_deps = source_tools.get_object_dependencies(schema=schema)

            return {
                "status": "success",
                "source_connection": source_connection_name,
                "source_db_type": source_conn.db_type,
                "schema": schema or objects_result.get("schema"),
                "objects": objects_result.get("objects", {}),
                "total_count": objects_result.get("total_count", 0),
                "table_order": fk_deps.get("table_order", []) if fk_deps.get("status") == "success" else [],
                "foreign_keys": fk_deps.get("foreign_keys", []) if fk_deps.get("status") == "success" else [],
                "dependencies": obj_deps.get("dependencies", []) if obj_deps.get("status") == "success" else []
            }

        except Exception as e:
            logger.error(f"Failed to analyze source database: {e}")
            return {"status": "error", "error": str(e)}

    def _execute_create_migration_plan(self, task_id: int,
                                         source_connection_name: str,
                                         target_schema: str = None,
                                         **kwargs) -> Dict[str, Any]:
        """Create migration plan with converted DDL"""
        if not self.storage:
            return {"status": "error", "error": t("migration_storage_required")}

        # Get task
        task = self.storage.get_migration_task(task_id)
        if not task:
            return {"status": "error", "error": t("migration_task_not_found", id=task_id)}

        # Get source connection
        source_conn = self.storage.get_connection(source_connection_name)
        if not source_conn:
            return {"status": "error", "error": t("migration_source_not_found", name=source_connection_name)}

        try:
            # Create source db tools
            from db_agent.storage.encryption import decrypt
            password = decrypt(source_conn.password_encrypted)
            source_config = {
                "type": source_conn.db_type,
                "host": source_conn.host,
                "port": source_conn.port,
                "database": source_conn.database,
                "user": source_conn.username,
                "password": password
            }
            source_tools = DatabaseToolsFactory.create(source_conn.db_type, source_config)

            # Get objects and dependencies
            objects_result = source_tools.get_all_objects(schema=task.source_schema)
            fk_deps = source_tools.get_foreign_key_dependencies(schema=task.source_schema)

            if objects_result.get("status") == "error":
                return objects_result

            objects = objects_result.get("objects", {})
            table_order = fk_deps.get("table_order", []) if fk_deps.get("status") == "success" else []

            # Build migration items
            items = []
            execution_order = 0

            # 1. Sequences first
            for seq in objects.get("sequences", []):
                execution_order += 1
                ddl_result = source_tools.get_object_ddl("sequence", seq["name"], task.source_schema)
                items.append(MigrationItem(
                    id=None,
                    task_id=task_id,
                    object_type="sequence",
                    object_name=seq["name"],
                    schema_name=task.source_schema,
                    execution_order=execution_order,
                    depends_on=None,
                    status="pending",
                    source_ddl=ddl_result.get("ddl") if ddl_result.get("status") == "success" else None,
                    target_ddl=None,  # Will be converted later
                    conversion_notes=None,
                    execution_result=None,
                    error_message=None,
                    retry_count=0,
                    executed_at=None,
                    created_at=None,
                    updated_at=None
                ))

            # 2. Tables in dependency order
            tables_added = set()
            for table_name in table_order:
                if table_name not in tables_added:
                    execution_order += 1
                    ddl_result = source_tools.get_object_ddl("table", table_name, task.source_schema)
                    deps = ddl_result.get("dependencies", []) if ddl_result.get("status") == "success" else []
                    items.append(MigrationItem(
                        id=None,
                        task_id=task_id,
                        object_type="table",
                        object_name=table_name,
                        schema_name=task.source_schema,
                        execution_order=execution_order,
                        depends_on=json.dumps([d["name"] for d in deps]) if deps else None,
                        status="pending",
                        source_ddl=ddl_result.get("ddl") if ddl_result.get("status") == "success" else None,
                        target_ddl=None,
                        conversion_notes=None,
                        execution_result=None,
                        error_message=None,
                        retry_count=0,
                        executed_at=None,
                        created_at=None,
                        updated_at=None
                    ))
                    tables_added.add(table_name)

            # Add remaining tables not in FK dependency list
            for table in objects.get("tables", []):
                if table["name"] not in tables_added:
                    execution_order += 1
                    ddl_result = source_tools.get_object_ddl("table", table["name"], task.source_schema)
                    items.append(MigrationItem(
                        id=None,
                        task_id=task_id,
                        object_type="table",
                        object_name=table["name"],
                        schema_name=task.source_schema,
                        execution_order=execution_order,
                        depends_on=None,
                        status="pending",
                        source_ddl=ddl_result.get("ddl") if ddl_result.get("status") == "success" else None,
                        target_ddl=None,
                        conversion_notes=None,
                        execution_result=None,
                        error_message=None,
                        retry_count=0,
                        executed_at=None,
                        created_at=None,
                        updated_at=None
                    ))

            # 3. Indexes (excluding primary keys which are created with tables)
            for idx in objects.get("indexes", []):
                if not idx.get("is_primary"):
                    execution_order += 1
                    ddl_result = source_tools.get_object_ddl("index", idx["name"], task.source_schema)
                    items.append(MigrationItem(
                        id=None,
                        task_id=task_id,
                        object_type="index",
                        object_name=idx["name"],
                        schema_name=task.source_schema,
                        execution_order=execution_order,
                        depends_on=json.dumps([idx.get("table_name")]) if idx.get("table_name") else None,
                        status="pending",
                        source_ddl=ddl_result.get("ddl") if ddl_result.get("status") == "success" else None,
                        target_ddl=None,
                        conversion_notes=None,
                        execution_result=None,
                        error_message=None,
                        retry_count=0,
                        executed_at=None,
                        created_at=None,
                        updated_at=None
                    ))

            # 4. Views
            for view in objects.get("views", []):
                execution_order += 1
                ddl_result = source_tools.get_object_ddl("view", view["name"], task.source_schema)
                items.append(MigrationItem(
                    id=None,
                    task_id=task_id,
                    object_type="view",
                    object_name=view["name"],
                    schema_name=task.source_schema,
                    execution_order=execution_order,
                    depends_on=None,
                    status="pending",
                    source_ddl=ddl_result.get("ddl") if ddl_result.get("status") == "success" else None,
                    target_ddl=None,
                    conversion_notes=None,
                    execution_result=None,
                    error_message=None,
                    retry_count=0,
                    executed_at=None,
                    created_at=None,
                    updated_at=None
                ))

            # 5. Functions
            for func in objects.get("functions", []):
                execution_order += 1
                ddl_result = source_tools.get_object_ddl("function", func["name"], task.source_schema)
                items.append(MigrationItem(
                    id=None,
                    task_id=task_id,
                    object_type="function",
                    object_name=func["name"],
                    schema_name=task.source_schema,
                    execution_order=execution_order,
                    depends_on=None,
                    status="pending",
                    source_ddl=ddl_result.get("ddl") if ddl_result.get("status") == "success" else None,
                    target_ddl=None,
                    conversion_notes=None,
                    execution_result=None,
                    error_message=None,
                    retry_count=0,
                    executed_at=None,
                    created_at=None,
                    updated_at=None
                ))

            # 6. Procedures
            for proc in objects.get("procedures", []):
                execution_order += 1
                ddl_result = source_tools.get_object_ddl("procedure", proc["name"], task.source_schema)
                items.append(MigrationItem(
                    id=None,
                    task_id=task_id,
                    object_type="procedure",
                    object_name=proc["name"],
                    schema_name=task.source_schema,
                    execution_order=execution_order,
                    depends_on=None,
                    status="pending",
                    source_ddl=ddl_result.get("ddl") if ddl_result.get("status") == "success" else None,
                    target_ddl=None,
                    conversion_notes=None,
                    execution_result=None,
                    error_message=None,
                    retry_count=0,
                    executed_at=None,
                    created_at=None,
                    updated_at=None
                ))

            # 7. Triggers
            for trigger in objects.get("triggers", []):
                execution_order += 1
                ddl_result = source_tools.get_object_ddl("trigger", trigger["name"], task.source_schema)
                items.append(MigrationItem(
                    id=None,
                    task_id=task_id,
                    object_type="trigger",
                    object_name=trigger["name"],
                    schema_name=task.source_schema,
                    execution_order=execution_order,
                    depends_on=json.dumps([trigger.get("table_name")]) if trigger.get("table_name") else None,
                    status="pending",
                    source_ddl=ddl_result.get("ddl") if ddl_result.get("status") == "success" else None,
                    target_ddl=None,
                    conversion_notes=None,
                    execution_result=None,
                    error_message=None,
                    retry_count=0,
                    executed_at=None,
                    created_at=None,
                    updated_at=None
                ))

            # Save items to database
            if items:
                self.storage.add_migration_items_batch(items)

            # Update task
            self.storage.update_migration_task_status(task_id, "planning")
            self.storage.update_migration_task_analysis(
                task_id,
                json.dumps({"objects": {k: len(v) for k, v in objects.items()}}),
                len(items)
            )

            return {
                "status": "success",
                "task_id": task_id,
                "total_items": len(items),
                "items_by_type": {
                    "sequences": len([i for i in items if i.object_type == "sequence"]),
                    "tables": len([i for i in items if i.object_type == "table"]),
                    "indexes": len([i for i in items if i.object_type == "index"]),
                    "views": len([i for i in items if i.object_type == "view"]),
                    "functions": len([i for i in items if i.object_type == "function"]),
                    "procedures": len([i for i in items if i.object_type == "procedure"]),
                    "triggers": len([i for i in items if i.object_type == "trigger"])
                }
            }

        except Exception as e:
            logger.error(f"Failed to create migration plan: {e}")
            return {"status": "error", "error": str(e)}

    def _execute_get_migration_plan(self, task_id: int, **kwargs) -> Dict[str, Any]:
        """Get migration plan details"""
        if not self.storage:
            return {"status": "error", "error": t("migration_storage_required")}

        task = self.storage.get_migration_task(task_id)
        if not task:
            return {"status": "error", "error": t("migration_task_not_found", id=task_id)}

        items = self.storage.get_migration_items(task_id)

        return {
            "status": "success",
            "task": task.to_dict(),
            "items": [item.to_dict() for item in items],
            "summary": {
                "total": len(items),
                "pending": len([i for i in items if i.status == "pending"]),
                "completed": len([i for i in items if i.status == "completed"]),
                "failed": len([i for i in items if i.status == "failed"]),
                "skipped": len([i for i in items if i.status == "skipped"])
            }
        }

    def _execute_get_migration_status(self, task_id: int, **kwargs) -> Dict[str, Any]:
        """Get migration status summary"""
        if not self.storage:
            return {"status": "error", "error": t("migration_storage_required")}

        summary = self.storage.get_migration_summary(task_id)
        if not summary:
            return {"status": "error", "error": t("migration_task_not_found", id=task_id)}

        return {"status": "success", **summary}

    def _convert_ddl(self, source_ddl: str, source_type: str, target_type: str, object_type: str) -> Dict[str, Any]:
        """
        Convert DDL from source database type to target database type.
        Returns dict with 'ddl' and 'notes' keys.
        """
        if not source_ddl:
            return {"ddl": None, "notes": "No source DDL"}

        if source_type == target_type:
            return {"ddl": source_ddl, "notes": "Same database type, no conversion needed"}

        ddl = source_ddl
        notes = []

        # MySQL to PostgreSQL conversion
        if source_type == "mysql" and target_type == "postgresql":
            import re

            # Data type conversions
            type_mappings = [
                (r'\bINT\s+AUTO_INCREMENT\b', 'SERIAL', 'INT AUTO_INCREMENT → SERIAL'),
                (r'\bBIGINT\s+AUTO_INCREMENT\b', 'BIGSERIAL', 'BIGINT AUTO_INCREMENT → BIGSERIAL'),
                (r'\bSMALLINT\s+AUTO_INCREMENT\b', 'SMALLSERIAL', 'SMALLINT AUTO_INCREMENT → SMALLSERIAL'),
                (r'\bINT\b(?!\s*\()', 'INTEGER', 'INT → INTEGER'),
                (r'\bTINYINT\s*\(\s*1\s*\)', 'BOOLEAN', 'TINYINT(1) → BOOLEAN'),
                (r'\bTINYINT\b', 'SMALLINT', 'TINYINT → SMALLINT'),
                (r'\bMEDIUMINT\b', 'INTEGER', 'MEDIUMINT → INTEGER'),
                (r'\bDOUBLE\b(?!\s+PRECISION)', 'DOUBLE PRECISION', 'DOUBLE → DOUBLE PRECISION'),
                (r'\bFLOAT\b', 'REAL', 'FLOAT → REAL'),
                (r'\bDATETIME\b', 'TIMESTAMP', 'DATETIME → TIMESTAMP'),
                (r'\bTIMESTAMP\s+DEFAULT\s+CURRENT_TIMESTAMP\s+ON\s+UPDATE\s+CURRENT_TIMESTAMP\b',
                 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP', 'Removed ON UPDATE (use trigger in PG)'),
                (r'\bLONGTEXT\b', 'TEXT', 'LONGTEXT → TEXT'),
                (r'\bMEDIUMTEXT\b', 'TEXT', 'MEDIUMTEXT → TEXT'),
                (r'\bTINYTEXT\b', 'TEXT', 'TINYTEXT → TEXT'),
                (r'\bLONGBLOB\b', 'BYTEA', 'LONGBLOB → BYTEA'),
                (r'\bMEDIUMBLOB\b', 'BYTEA', 'MEDIUMBLOB → BYTEA'),
                (r'\bTINYBLOB\b', 'BYTEA', 'TINYBLOB → BYTEA'),
                (r'\bBLOB\b', 'BYTEA', 'BLOB → BYTEA'),
                (r'\bVARBINARY\s*\([^)]+\)', 'BYTEA', 'VARBINARY → BYTEA'),
                (r'\bBINARY\s*\([^)]+\)', 'BYTEA', 'BINARY → BYTEA'),
                (r'\bJSON\b', 'JSONB', 'JSON → JSONB'),
            ]

            for pattern, replacement, note in type_mappings:
                if re.search(pattern, ddl, re.IGNORECASE):
                    ddl = re.sub(pattern, replacement, ddl, flags=re.IGNORECASE)
                    notes.append(note)

            # Remove MySQL-specific clauses
            mysql_clauses = [
                (r'\s+ENGINE\s*=\s*\w+', '', 'Removed ENGINE clause'),
                (r'\s+DEFAULT\s+CHARSET\s*=\s*\w+', '', 'Removed CHARSET clause'),
                (r'\s+COLLATE\s*=?\s*\w+', '', 'Removed COLLATE clause'),
                (r'\s+AUTO_INCREMENT\s*=\s*\d+', '', 'Removed AUTO_INCREMENT value'),
                (r'\s+ROW_FORMAT\s*=\s*\w+', '', 'Removed ROW_FORMAT'),
                (r'\s+COMMENT\s*=?\s*\'[^\']*\'', '', 'Removed table COMMENT'),
                (r'\s+UNSIGNED\b', '', 'Removed UNSIGNED (not in PostgreSQL)'),
                (r'\s+ZEROFILL\b', '', 'Removed ZEROFILL'),
                (r'\bIF\s+NOT\s+EXISTS\s+', '', 'Removed IF NOT EXISTS'),
            ]

            for pattern, replacement, note in mysql_clauses:
                if re.search(pattern, ddl, re.IGNORECASE):
                    ddl = re.sub(pattern, replacement, ddl, flags=re.IGNORECASE)
                    notes.append(note)

            # Handle ENUM - convert to VARCHAR with CHECK constraint (simplified)
            enum_pattern = r"ENUM\s*\(([^)]+)\)"
            if re.search(enum_pattern, ddl, re.IGNORECASE):
                ddl = re.sub(enum_pattern, "VARCHAR(50)", ddl, flags=re.IGNORECASE)
                notes.append("ENUM → VARCHAR(50) (consider adding CHECK constraint)")

            # Handle column comments - remove inline COMMENT
            ddl = re.sub(r"\s+COMMENT\s+'[^']*'", "", ddl, flags=re.IGNORECASE)

            # Handle GENERATED columns (MySQL syntax differs)
            ddl = re.sub(r'\s+GENERATED\s+ALWAYS\s+AS\s+\(([^)]+)\)\s+STORED',
                        r' GENERATED ALWAYS AS (\1) STORED', ddl, flags=re.IGNORECASE)

            # Handle index syntax differences for CREATE INDEX
            if object_type == "index":
                # Remove USING BTREE if present (BTREE is default in PG)
                ddl = re.sub(r'\s+USING\s+BTREE\b', '', ddl, flags=re.IGNORECASE)
                # Handle USING HASH
                if re.search(r'\bUSING\s+HASH\b', ddl, re.IGNORECASE):
                    notes.append("HASH index may behave differently in PostgreSQL")

            # Handle FULLTEXT indexes - not directly supported in PG
            if 'FULLTEXT' in ddl.upper():
                notes.append("FULLTEXT index not supported - consider using GIN/GiST with tsvector")
                return {"ddl": None, "notes": "; ".join(notes), "skip_reason": "FULLTEXT index not supported in PostgreSQL"}

        # MySQL to GaussDB (similar to PostgreSQL with some differences)
        elif source_type == "mysql" and target_type == "gaussdb":
            # GaussDB is PostgreSQL-compatible, use same rules
            result = self._convert_ddl(source_ddl, "mysql", "postgresql", object_type)
            result["notes"] = result.get("notes", "") + " (GaussDB compatibility mode)"
            return result

        # Oracle to PostgreSQL
        elif source_type == "oracle" and target_type == "postgresql":
            import re

            type_mappings = [
                (r'\bNUMBER\s*\(\s*10\s*\)', 'INTEGER', 'NUMBER(10) → INTEGER'),
                (r'\bNUMBER\s*\(\s*19\s*\)', 'BIGINT', 'NUMBER(19) → BIGINT'),
                (r'\bNUMBER\s*\((\d+)\s*,\s*(\d+)\s*\)', r'NUMERIC(\1,\2)', 'NUMBER(p,s) → NUMERIC(p,s)'),
                (r'\bNUMBER\b', 'NUMERIC', 'NUMBER → NUMERIC'),
                (r'\bVARCHAR2\s*\((\d+)\)', r'VARCHAR(\1)', 'VARCHAR2 → VARCHAR'),
                (r'\bNVARCHAR2\s*\((\d+)\)', r'VARCHAR(\1)', 'NVARCHAR2 → VARCHAR'),
                (r'\bCLOB\b', 'TEXT', 'CLOB → TEXT'),
                (r'\bNCLOB\b', 'TEXT', 'NCLOB → TEXT'),
                (r'\bBLOB\b', 'BYTEA', 'BLOB → BYTEA'),
                (r'\bRAW\s*\(\d+\)', 'BYTEA', 'RAW → BYTEA'),
                (r'\bSYSDATE\b', 'CURRENT_TIMESTAMP', 'SYSDATE → CURRENT_TIMESTAMP'),
                (r'\bSYSTIMESTAMP\b', 'CURRENT_TIMESTAMP', 'SYSTIMESTAMP → CURRENT_TIMESTAMP'),
            ]

            for pattern, replacement, note in type_mappings:
                if re.search(pattern, ddl, re.IGNORECASE):
                    ddl = re.sub(pattern, replacement, ddl, flags=re.IGNORECASE)
                    notes.append(note)

        # Other conversions can be added here...

        return {"ddl": ddl.strip(), "notes": "; ".join(notes) if notes else "Basic conversion applied"}

    def _execute_migration_item(self, item_id: int, **kwargs) -> Dict[str, Any]:
        """Execute a single migration item"""
        if not self.storage:
            return {"status": "error", "error": t("migration_storage_required")}

        item = self.storage.get_migration_item(item_id)
        if not item:
            return {"status": "error", "error": t("migration_item_not_found", id=item_id)}

        # Get task to know source/target types
        task = self.storage.get_migration_task(item.task_id)
        if not task:
            return {"status": "error", "error": t("migration_task_not_found", task_id=item.task_id)}

        # Update item status to executing
        self.storage.update_migration_item_status(item_id, "executing")

        try:
            # Convert DDL if needed
            if item.target_ddl:
                ddl = item.target_ddl
            elif item.source_ddl:
                # Convert source DDL to target format
                conversion = self._convert_ddl(
                    item.source_ddl,
                    task.source_db_type,
                    task.target_db_type,
                    item.object_type
                )

                if conversion.get("skip_reason"):
                    # Item should be skipped
                    self.storage.update_migration_item_status(
                        item_id, "skipped",
                        conversion.get("skip_reason")
                    )
                    # Save conversion notes
                    if conversion.get("notes"):
                        self.storage.update_migration_item_ddl(
                            item_id,
                            conversion_notes=conversion.get("notes")
                        )
                    if task:
                        self.storage.update_migration_task_progress(
                            item.task_id,
                            skipped=task.skipped_items + 1
                        )
                    return {
                        "status": "skipped",
                        "item_id": item_id,
                        "object_type": item.object_type,
                        "object_name": item.object_name,
                        "reason": conversion.get("skip_reason"),
                        "notes": conversion.get("notes")
                    }

                ddl = conversion.get("ddl")
                if conversion.get("notes"):
                    self.storage.update_migration_item_ddl(
                        item_id,
                        target_ddl=ddl,
                        conversion_notes=conversion.get("notes")
                    )
            else:
                ddl = None

            if not ddl:
                self.storage.update_migration_item_status(item_id, "failed", "No DDL available")
                return {"status": "error", "error": "No DDL available for this item"}

            # Execute DDL on target database
            result = self.db_tools.execute_sql(ddl, confirmed=True)

            if result.get("status") == "success":
                self.storage.update_migration_item_status(
                    item_id, "completed",
                    execution_result=json.dumps(result)
                )

                # Update task progress
                task = self.storage.get_migration_task(item.task_id)
                if task:
                    self.storage.update_migration_task_progress(
                        item.task_id,
                        completed=task.completed_items + 1
                    )

                return {
                    "status": "success",
                    "item_id": item_id,
                    "object_type": item.object_type,
                    "object_name": item.object_name,
                    "result": result
                }
            else:
                error_msg = result.get("error", "Unknown error")
                self.storage.update_migration_item_status(item_id, "failed", error_msg)

                # Update task progress
                task = self.storage.get_migration_task(item.task_id)
                if task:
                    self.storage.update_migration_task_progress(
                        item.task_id,
                        failed=task.failed_items + 1
                    )

                return {
                    "status": "error",
                    "item_id": item_id,
                    "object_type": item.object_type,
                    "object_name": item.object_name,
                    "error": error_msg
                }

        except Exception as e:
            error_msg = str(e)
            self.storage.update_migration_item_status(item_id, "failed", error_msg)
            return {"status": "error", "error": error_msg}

    def _execute_migration_batch(self, task_id: int, batch_size: int = 10, **kwargs) -> Dict[str, Any]:
        """Execute migration items in batch"""
        if not self.storage:
            return {"status": "error", "error": t("migration_storage_required")}

        results = []
        completed = 0
        failed = 0

        # Update task status to executing
        self.storage.update_migration_task_status(task_id, "executing")

        for _ in range(batch_size):
            item = self.storage.get_next_pending_item(task_id)
            if not item:
                break

            result = self._execute_migration_item(item.id)
            results.append({
                "item_id": item.id,
                "object_type": item.object_type,
                "object_name": item.object_name,
                "status": result.get("status")
            })

            if result.get("status") == "success":
                completed += 1
            else:
                failed += 1

        # Check if all items are done
        summary = self.storage.get_migration_summary(task_id)
        if summary and summary.get("status_counts", {}).get("pending", 0) == 0:
            final_status = "completed" if summary.get("failed_items", 0) == 0 else "completed"
            self.storage.update_migration_task_status(task_id, final_status)

        return {
            "status": "success",
            "task_id": task_id,
            "batch_completed": completed,
            "batch_failed": failed,
            "results": results
        }

    def _execute_compare_databases(self, task_id: int, **kwargs) -> Dict[str, Any]:
        """Compare source and target databases"""
        if not self.storage:
            return {"status": "error", "error": t("migration_storage_required")}

        task = self.storage.get_migration_task(task_id)
        if not task:
            return {"status": "error", "error": t("migration_task_not_found", id=task_id)}

        try:
            # Get source connection
            source_conn = self.storage.get_connection_by_id(task.source_connection_id)
            target_conn = self.storage.get_connection_by_id(task.target_connection_id)

            if not source_conn or not target_conn:
                return {"status": "error", "error": "Connection not found"}

            # Create source tools
            from db_agent.storage.encryption import decrypt
            source_password = decrypt(source_conn.password_encrypted)
            source_config = {
                "type": source_conn.db_type,
                "host": source_conn.host,
                "port": source_conn.port,
                "database": source_conn.database,
                "user": source_conn.username,
                "password": source_password
            }
            source_tools = DatabaseToolsFactory.create(source_conn.db_type, source_config)

            # Get objects from both databases
            source_objects = source_tools.get_all_objects(schema=task.source_schema)
            target_objects = self.db_tools.get_all_objects(schema=task.target_schema)

            # Compare
            comparison = {"matches": [], "missing_in_target": [], "extra_in_target": []}

            source_tables = {t["name"] for t in source_objects.get("objects", {}).get("tables", [])}
            target_tables = {t["name"] for t in target_objects.get("objects", {}).get("tables", [])}

            comparison["matches"] = list(source_tables & target_tables)
            comparison["missing_in_target"] = list(source_tables - target_tables)
            comparison["extra_in_target"] = list(target_tables - source_tables)

            return {
                "status": "success",
                "task_id": task_id,
                "source_db": source_conn.db_type,
                "target_db": target_conn.db_type,
                "comparison": comparison,
                "summary": {
                    "total_source_tables": len(source_tables),
                    "total_target_tables": len(target_tables),
                    "matched": len(comparison["matches"]),
                    "missing": len(comparison["missing_in_target"]),
                    "extra": len(comparison["extra_in_target"])
                }
            }

        except Exception as e:
            logger.error(f"Failed to compare databases: {e}")
            return {"status": "error", "error": str(e)}

    def _execute_generate_migration_report(self, task_id: int, **kwargs) -> Dict[str, Any]:
        """Generate migration report"""
        if not self.storage:
            return {"status": "error", "error": t("migration_storage_required")}

        task = self.storage.get_migration_task(task_id)
        if not task:
            return {"status": "error", "error": t("migration_task_not_found", id=task_id)}

        items = self.storage.get_migration_items(task_id)
        summary = self.storage.get_migration_summary(task_id)

        # Group items by status
        items_by_status = {
            "pending": [],
            "completed": [],
            "failed": [],
            "skipped": []
        }
        for item in items:
            if item.status in items_by_status:
                items_by_status[item.status].append({
                    "id": item.id,
                    "type": item.object_type,
                    "name": item.object_name,
                    "error": item.error_message
                })

        return {
            "status": "success",
            "task_id": task_id,
            "task_name": task.name,
            "source_db_type": task.source_db_type,
            "target_db_type": task.target_db_type,
            "task_status": task.status,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "statistics": {
                "total_items": task.total_items,
                "completed": task.completed_items,
                "failed": task.failed_items,
                "skipped": task.skipped_items,
                "pending": task.total_items - task.completed_items - task.failed_items - task.skipped_items
            },
            "items_by_type": summary.get("type_counts", {}) if summary else {},
            "failed_items": items_by_status["failed"],
            "skipped_items": items_by_status["skipped"]
        }

    def _execute_skip_migration_item(self, item_id: int, reason: str = None, **kwargs) -> Dict[str, Any]:
        """Skip a migration item"""
        if not self.storage:
            return {"status": "error", "error": t("migration_storage_required")}

        item = self.storage.get_migration_item(item_id)
        if not item:
            return {"status": "error", "error": t("migration_item_not_found", id=item_id)}

        self.storage.update_migration_item_status(item_id, "skipped", reason)

        # Update task progress
        task = self.storage.get_migration_task(item.task_id)
        if task:
            self.storage.update_migration_task_progress(
                item.task_id,
                skipped=task.skipped_items + 1
            )

        return {
            "status": "success",
            "item_id": item_id,
            "object_type": item.object_type,
            "object_name": item.object_name,
            "reason": reason
        }

    def _execute_retry_failed_items(self, task_id: int, **kwargs) -> Dict[str, Any]:
        """Retry all failed migration items"""
        if not self.storage:
            return {"status": "error", "error": t("migration_storage_required")}

        failed_items = self.storage.get_migration_items(task_id, status="failed")
        if not failed_items:
            return {"status": "success", "message": "No failed items to retry", "retried": 0}

        retried = 0
        for item in failed_items:
            self.storage.increment_migration_item_retry(item.id)
            retried += 1

        # Reset task failed count
        task = self.storage.get_migration_task(task_id)
        if task:
            self.storage.update_migration_task_progress(task_id, failed=0)
            self.storage.update_migration_task_status(task_id, "executing")

        return {
            "status": "success",
            "task_id": task_id,
            "retried": retried
        }
