"""
国际化支持 - Internationalization Support
"""
import locale
import os

# 语言包
TRANSLATIONS = {
    "zh": {
        # 通用
        "app_name": "数据库智能助手",
        "welcome": "欢迎使用",
        "goodbye": "再见！",
        "error": "错误",
        "success": "成功",
        "failed": "失败",
        "cancelled": "已取消",
        "skipped": "已跳过",
        "yes": "是",
        "no": "否",
        "confirm": "确认",
        "cancel": "取消",
        "loading": "加载中...",
        "thinking": "思考中...",
        "connecting": "正在连接数据库...",
        "initializing": "正在初始化...",

        # 连接状态
        "connected": "已连接",
        "connection_warning": "连接警告",
        "connection_failed": "连接失败",

        # 命令
        "cmd_help": "显示帮助信息",
        "cmd_model": "切换AI模型",
        "cmd_language": "切换语言 (中文/English)",
        "cmd_reset": "重置对话历史",
        "cmd_history": "查看对话历史",
        "cmd_clear": "清屏",
        "cmd_exit": "退出程序",

        # 帮助
        "help_title": "命令帮助",
        "examples_title": "使用示例",
        "example_list_tables": "列出所有表",
        "example_describe_table": "查看 users 表的结构",
        "example_sample_data": "显示 orders 表的前10条数据",
        "example_create_table": "创建一个 products 表",
        "example_insert": "插入一条数据到 users 表",
        "example_optimize": "帮我优化这个查询的性能",

        # 模型
        "current_model": "当前模型",
        "available_models": "可用模型",
        "select_model": "选择模型序号 (留空取消)",
        "model_configured": "已配置",
        "model_not_configured": "未配置",
        "model_switched": "已切换到",
        "model_switch_failed": "切换失败",
        "model_not_configured_error": "未配置 API Key",
        "model_config_hint": "请在 config.ini 的 [{provider}] 部分配置 api_key",
        "invalid_choice": "无效的选择",
        "enter_valid_number": "请输入有效的数字",

        # 语言
        "language_switched": "语言已切换为中文",
        "select_language": "选择语言",
        "language_chinese": "中文",
        "language_english": "English",

        # 对话
        "conversation_reset": "对话已重置，开始新会话",
        "no_history": "暂无对话历史",
        "confirm_exit": "确定要退出吗?",

        # 工具
        "tool_list_tables": "列出表",
        "tool_describe_table": "查看表结构",
        "tool_sample_data": "获取示例数据",
        "tool_execute_sql": "执行SQL",
        "tool_safe_query": "查询数据",
        "tool_explain": "分析执行计划",
        "tool_check_index": "检查索引",
        "tool_table_stats": "获取表统计",
        "tool_create_index": "创建索引",
        "tool_analyze": "更新统计信息",
        "tool_slow_queries": "识别慢查询",
        "tool_running_queries": "查看运行中的查询",

        # 结果
        "returned_records": "返回 {count} 条记录",
        "affected_rows": "影响 {count} 行",
        "waiting_confirm": "等待确认",
        "execute_success": "执行成功",
        "execute_failed": "执行失败",

        # SQL确认
        "pending_operations": "共有 {count} 个操作需要确认",
        "pending_sql_title": "待确认的SQL操作",
        "confirm_execute": "确认执行?",

        # 提示
        "input_hint": "输入 {help} 查看帮助，{model} 切换模型，{lang} 切换语言，{exit} 退出",
        "autocomplete_hint": "输入 / 显示命令菜单，或直接输入 /命令 (支持自动补全)",

        # 配置
        "config_not_found": "配置文件 config.ini 不存在",
        "api_key_not_configured": "默认提供商 {provider} 未配置 API Key",
        "init_llm_failed": "初始化LLM客户端失败",

        # Agent/数据库工具消息
        "db_pg_stat_not_enabled": "pg_stat_statements未启用，显示当前活动查询",
        "db_performance_schema_required": "需要启用performance_schema才能查看详细慢查询统计，显示当前活动查询",
        "db_type_postgresql": "PostgreSQL",
        "db_type_mysql": "MySQL",
        "db_type_gaussdb": "GaussDB",
        "db_gaussdb_centralized": "GaussDB 集中式",
        "db_gaussdb_distributed": "GaussDB 分布式",
        "db_gaussdb_mode_detected": "检测到 {mode} 模式",
        "db_gaussdb_driver_note": "请确保已安装 GaussDB 专用 psycopg2 驱动（不是标准 PostgreSQL psycopg2）",
        "execution_feedback_header": "用户已确认执行，结果如下：",
        "execution_feedback_continue": "请继续执行后续任务。",
        "execution_feedback_has_errors": "注意：有些操作执行失败了。请分析错误原因，调整策略（例如：使用INSERT IGNORE或ON DUPLICATE KEY UPDATE处理重复键错误），然后用修改后的SQL重新请求确认执行，继续完成任务。",
        "execution_feedback_all_success": "所有操作执行成功，请继续执行后续任务。",
        "execution_result_success": "SQL {index}: 执行成功, {message}",
        "execution_result_failed": "SQL {index}: 执行失败 - {error}",
        "execution_result_skipped": "SQL {index}: 用户跳过",
        "db_table_not_found": "表 {schema}.{table} 不存在",
        "db_only_create_index": "只允许CREATE INDEX语句",
        "db_index_created": "索引创建成功",
        "db_stats_updated": "已更新 {schema}.{table} 的统计信息",
        "db_only_select": "只允许SELECT查询",
        "db_need_confirm": "此操作需要用户确认后才能执行",
        "db_execute_success": "执行成功，影响 {count} 行",
        "db_create_index_need_confirm": "创建索引操作需要用户确认后才能执行",
        "db_unknown_tool": "未知工具: {tool}",
        "db_invalid_operation_index": "无效的操作索引",
        "db_unknown_pending_type": "未知的待确认操作类型",
        "agent_thinking": "思考中... (迭代 {iteration})",
        "agent_conversation_error": "对话异常结束: {reason}",
        "agent_need_more_time": "抱歉，我需要更多时间来分析这个问题。请尝试简化你的问题或分步骤询问。",
        "db_unsupported_provider": "不支持的提供商: {provider}",

        # 性能检查
        "db_performance_issue_need_confirm": "检测到性能问题，此查询需要用户确认后才能执行",
        "db_performance_check_passed": "性能检查通过",

        # API Server
        "api_no_api_key": "未提供Anthropic API Key",
        "api_db_connection_failed": "数据库连接测试失败: {error}",
        "api_session_not_found": "会话不存在: {session_id}",
        "api_session_deleted": "会话已删除",
        "api_session_reset": "会话已重置",

        # LLM API 错误码
        "llm_error_400": "请求格式错误，请检查请求参数",
        "llm_error_401": "API Key 错误或认证失败，请检查您的 API Key 是否正确",
        "llm_error_402": "账户余额不足，请前往充值",
        "llm_error_422": "请求参数错误: {detail}",
        "llm_error_429": "请求速率达到上限，请稍后重试",
        "llm_error_500": "服务器内部故障，请稍后重试",
        "llm_error_503": "服务器繁忙，请稍后重试",
        "llm_error_unknown": "API 请求失败 (状态码 {code}): {message}",
        "llm_error_connection": "无法连接到 API 服务器: {error}",
        "llm_error_timeout": "API 请求超时，请稍后重试",
    },

    "en": {
        # General
        "app_name": "Database Agent",
        "welcome": "Welcome to",
        "goodbye": "Goodbye!",
        "error": "Error",
        "success": "Success",
        "failed": "Failed",
        "cancelled": "Cancelled",
        "skipped": "Skipped",
        "yes": "Yes",
        "no": "No",
        "confirm": "Confirm",
        "cancel": "Cancel",
        "loading": "Loading...",
        "thinking": "Thinking...",
        "connecting": "Connecting to database...",
        "initializing": "Initializing...",

        # Connection
        "connected": "Connected",
        "connection_warning": "Connection warning",
        "connection_failed": "Connection failed",

        # Commands
        "cmd_help": "Show help",
        "cmd_model": "Switch AI model",
        "cmd_language": "Switch language (中文/English)",
        "cmd_reset": "Reset conversation",
        "cmd_history": "View history",
        "cmd_clear": "Clear screen",
        "cmd_exit": "Exit",

        # Help
        "help_title": "Commands",
        "examples_title": "Examples",
        "example_list_tables": "List all tables",
        "example_describe_table": "Describe the users table",
        "example_sample_data": "Show first 10 rows of orders table",
        "example_create_table": "Create a products table",
        "example_insert": "Insert a record into users table",
        "example_optimize": "Help me optimize this query",

        # Model
        "current_model": "Current model",
        "available_models": "Available Models",
        "select_model": "Select model number (empty to cancel)",
        "model_configured": "Configured",
        "model_not_configured": "Not configured",
        "model_switched": "Switched to",
        "model_switch_failed": "Switch failed",
        "model_not_configured_error": "API Key not configured",
        "model_config_hint": "Please configure api_key in [{provider}] section of config.ini",
        "invalid_choice": "Invalid choice",
        "enter_valid_number": "Please enter a valid number",

        # Language
        "language_switched": "Language switched to English",
        "select_language": "Select language",
        "language_chinese": "中文",
        "language_english": "English",

        # Conversation
        "conversation_reset": "Conversation reset, starting new session",
        "no_history": "No conversation history",
        "confirm_exit": "Are you sure you want to exit?",

        # Tools
        "tool_list_tables": "List tables",
        "tool_describe_table": "Describe table",
        "tool_sample_data": "Get sample data",
        "tool_execute_sql": "Execute SQL",
        "tool_safe_query": "Query data",
        "tool_explain": "Analyze execution plan",
        "tool_check_index": "Check indexes",
        "tool_table_stats": "Get table stats",
        "tool_create_index": "Create index",
        "tool_analyze": "Update statistics",
        "tool_slow_queries": "Identify slow queries",
        "tool_running_queries": "View running queries",

        # Results
        "returned_records": "Returned {count} records",
        "affected_rows": "Affected {count} rows",
        "waiting_confirm": "Waiting for confirmation",
        "execute_success": "Executed successfully",
        "execute_failed": "Execution failed",

        # SQL Confirmation
        "pending_operations": "{count} operations need confirmation",
        "pending_sql_title": "Pending SQL Operation",
        "confirm_execute": "Confirm execution?",

        # Hints
        "input_hint": "Type {help} for help, {model} to switch model, {lang} to switch language, {exit} to quit",
        "autocomplete_hint": "Type / to show command menu, or type /command (with autocomplete)",

        # Config
        "config_not_found": "Config file config.ini not found",
        "api_key_not_configured": "API Key not configured for default provider {provider}",
        "init_llm_failed": "Failed to initialize LLM client",

        # Agent/Database tool messages
        "db_pg_stat_not_enabled": "pg_stat_statements not enabled, showing current active queries",
        "db_performance_schema_required": "performance_schema must be enabled to view detailed slow query statistics, showing current active queries",
        "db_type_postgresql": "PostgreSQL",
        "db_type_mysql": "MySQL",
        "db_type_gaussdb": "GaussDB",
        "db_gaussdb_centralized": "GaussDB Centralized",
        "db_gaussdb_distributed": "GaussDB Distributed",
        "db_gaussdb_mode_detected": "Detected {mode} mode",
        "db_gaussdb_driver_note": "Please ensure GaussDB-specific psycopg2 driver is installed (NOT standard PostgreSQL psycopg2)",
        "execution_feedback_header": "User confirmed execution, results:",
        "execution_feedback_continue": "Please continue with the remaining tasks.",
        "execution_feedback_has_errors": "Note: Some operations failed. Please analyze the errors, adjust your strategy (e.g., use INSERT IGNORE or ON DUPLICATE KEY UPDATE to handle duplicate key errors), then request confirmation again with the modified SQL, and continue completing the task.",
        "execution_feedback_all_success": "All operations executed successfully, please continue with the remaining tasks.",
        "execution_result_success": "SQL {index}: Success, {message}",
        "execution_result_failed": "SQL {index}: Failed - {error}",
        "execution_result_skipped": "SQL {index}: Skipped by user",
        "db_table_not_found": "Table {schema}.{table} does not exist",
        "db_only_create_index": "Only CREATE INDEX statements are allowed",
        "db_index_created": "Index created successfully",
        "db_stats_updated": "Statistics updated for {schema}.{table}",
        "db_only_select": "Only SELECT queries are allowed",
        "db_need_confirm": "This operation requires user confirmation before execution",
        "db_execute_success": "Executed successfully, {count} rows affected",
        "db_create_index_need_confirm": "Create index operation requires user confirmation",
        "db_unknown_tool": "Unknown tool: {tool}",
        "db_invalid_operation_index": "Invalid operation index",
        "db_unknown_pending_type": "Unknown pending operation type",
        "agent_thinking": "Thinking... (iteration {iteration})",
        "agent_conversation_error": "Conversation ended abnormally: {reason}",
        "agent_need_more_time": "Sorry, I need more time to analyze this problem. Please try simplifying your question or ask step by step.",
        "db_unsupported_provider": "Unsupported provider: {provider}",

        # Performance Check
        "db_performance_issue_need_confirm": "Performance issues detected, this query requires user confirmation before execution",
        "db_performance_check_passed": "Performance check passed",

        # API Server
        "api_no_api_key": "Anthropic API Key not provided",
        "api_db_connection_failed": "Database connection test failed: {error}",
        "api_session_not_found": "Session not found: {session_id}",
        "api_session_deleted": "Session deleted",
        "api_session_reset": "Session reset",

        # LLM API Error Codes
        "llm_error_400": "Bad request format, please check request parameters",
        "llm_error_401": "API Key error or authentication failed, please check your API Key",
        "llm_error_402": "Insufficient account balance, please recharge",
        "llm_error_422": "Invalid request parameters: {detail}",
        "llm_error_429": "Rate limit exceeded, please try again later",
        "llm_error_500": "Server internal error, please try again later",
        "llm_error_503": "Server is busy, please try again later",
        "llm_error_unknown": "API request failed (status code {code}): {message}",
        "llm_error_connection": "Cannot connect to API server: {error}",
        "llm_error_timeout": "API request timeout, please try again later",
    }
}


class I18n:
    """国际化类"""

    _instance = None
    _lang = "zh"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_language()
        return cls._instance

    def _init_language(self):
        """根据系统语言初始化"""
        try:
            # 获取系统语言
            if os.name == 'nt':  # Windows
                import ctypes
                windll = ctypes.windll.kernel32
                lang_id = windll.GetUserDefaultUILanguage()
                # 中文语言ID: 2052 (简体), 1028 (繁体)
                if lang_id in (2052, 1028, 0x0804, 0x0404):
                    self._lang = "zh"
                else:
                    self._lang = "en"
            else:  # Unix/Linux/Mac
                lang = locale.getdefaultlocale()[0]
                if lang and lang.startswith(('zh', 'CN')):
                    self._lang = "zh"
                else:
                    self._lang = "en"
        except Exception:
            self._lang = "zh"  # 默认中文

    @property
    def lang(self) -> str:
        return self._lang

    @lang.setter
    def lang(self, value: str):
        if value in TRANSLATIONS:
            self._lang = value

    def get(self, key: str, **kwargs) -> str:
        """获取翻译文本"""
        text = TRANSLATIONS.get(self._lang, {}).get(key, key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass
        return text

    def switch(self, lang: str = None) -> str:
        """切换语言"""
        if lang:
            self.lang = lang
        else:
            # 切换到另一种语言
            self._lang = "en" if self._lang == "zh" else "zh"
        return self._lang

    def get_available_languages(self) -> dict:
        """获取可用语言列表"""
        return {
            "zh": "中文",
            "en": "English"
        }


# 全局实例
i18n = I18n()


def t(key: str, **kwargs) -> str:
    """翻译函数快捷方式"""
    return i18n.get(key, **kwargs)
