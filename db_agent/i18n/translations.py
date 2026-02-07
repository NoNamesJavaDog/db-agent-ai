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
        "cmd_file": "加载SQL文件进行分析",
        "cmd_migrate": "异构数据库迁移向导",
        "cmd_sessions": "列出所有会话",
        "cmd_session": "管理会话 (new/use/delete/rename)",
        "cmd_model": "切换AI模型",
        "cmd_language": "切换语言 (中文/English)",
        "cmd_reset": "重置对话历史",
        "cmd_history": "查看对话历史",
        "cmd_clear": "清屏",
        "cmd_exit": "退出程序",

        # 文件上传
        "file_input_path": "请输入文件路径",
        "file_not_found": "文件不存在: {path}",
        "file_type_warning": "警告: 文件类型 {ext} 可能不是SQL文件",
        "file_encoding_error": "无法读取文件，编码格式不支持",
        "file_size_warning": "文件较大 ({size}KB)，可能影响分析效果",
        "file_continue_large": "是否继续加载?",
        "file_loaded": "已加载文件: {path} ({size} 字节, 约 {sql_count} 条SQL语句)",
        "file_preview": "文件预览",
        "file_more_lines": "还有 {count} 行未显示",
        "file_usage_hint": "文件已加载，请输入您的问题（如：分析这个SQL文件、执行这些SQL、优化第3条查询）",
        "file_context_header": "以下是用户上传的SQL文件内容 ({path})",
        "file_read_error": "读取文件失败: {error}",

        # 数据库迁移
        "migrate_target_db": "目标数据库",
        "migrate_source_db": "源数据库类型",
        "migrate_select_source": "选择源数据库类型",
        "migrate_enter_number": "请输入序号 (留空取消)",
        "migrate_mode_file": "文件导入迁移",
        "migrate_mode_file_desc": "从 SQL 文件导入并转换",
        "migrate_mode_online": "在线迁移",
        "migrate_mode_online_desc": "直接从源数据库迁移到目标数据库",
        "migrate_other": "其他",
        "migrate_enter_source_name": "请输入源数据库名称",
        "migrate_source_selected": "已选择源数据库: {source}",
        "migrate_mode_select": "选择迁移模式",
        "migrate_mode_convert_only": "仅转换 - 只显示转换后的DDL，不执行",
        "migrate_mode_convert_execute": "转换并执行 - 转换DDL并在目标数据库执行",
        "migrate_enter_mode": "请输入模式序号",
        "migrate_will_execute": "将转换并执行DDL语句",
        "migrate_convert_only": "将仅显示转换后的DDL，不执行",
        "migrate_using_optimized_rules": "使用Oracle→GaussDB专用优化规则",
        "migrate_instruction_convert": "请将这个SQL文件中的 {source} DDL语句转换为 {target} 语法。分析每条语句，列出数据类型和语法的转换映射表，然后显示转换后的完整DDL。",
        "migrate_instruction_execute": "请将这个SQL文件中的 {source} DDL语句转换为 {target} 语法，并在当前数据库中执行。分析每条语句，列出数据类型和语法的转换映射表，按正确的依赖顺序（先表后索引、先主表后关联表）逐条执行转换后的DDL。",
        "migrate_instruction_oracle_to_gaussdb_convert": """请将这个SQL文件中的Oracle DDL/PL-SQL语句转换为GaussDB语法。

**重点转换规则：**
1. 高级包替换：DBMS_LOB→DBE_LOB, DBMS_OUTPUT→DBE_OUTPUT, DBMS_RANDOM→DBE_RANDOM, UTL_RAW→DBE_RAW, DBMS_SQL→DBE_SQL
2. 数据类型：NUMBER(p,-s)需手动处理；VARCHAR2(n CHAR)改为VARCHAR2(n*4)；DATE注意会变为TIMESTAMP(0)
3. SQL语法：!=不能有空格；CONNECT BY改用WITH RECURSIVE；ROWNUM用ROW_NUMBER()替代
4. 函数：DECODE可保留或改CASE WHEN；NVL可保留或改COALESCE

请逐条分析并显示：
- 原始Oracle语句
- 转换后的GaussDB语句
- 转换说明（如有改动）""",
        "migrate_instruction_oracle_to_gaussdb_execute": """请将这个SQL文件中的Oracle DDL/PL-SQL语句转换为GaussDB语法并执行。

**重点转换规则：**
1. 高级包替换：DBMS_LOB→DBE_LOB, DBMS_OUTPUT→DBE_OUTPUT, DBMS_RANDOM→DBE_RANDOM, UTL_RAW→DBE_RAW, DBMS_SQL→DBE_SQL
2. 数据类型：NUMBER(p,-s)需手动处理；VARCHAR2(n CHAR)改为VARCHAR2(n*4)；DATE注意会变为TIMESTAMP(0)
3. SQL语法：!=不能有空格；CONNECT BY改用WITH RECURSIVE；ROWNUM用ROW_NUMBER()替代
4. 函数：DECODE可保留或改CASE WHEN；NVL可保留或改COALESCE

请：
1. 先显示转换摘要（映射表）
2. 按依赖顺序执行（先序列→表→约束→索引→存储过程）
3. 每条执行前显示原始和转换后的语句""",

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
        "confirm_option_execute": "执行此操作",
        "confirm_option_skip": "跳过此操作",
        "confirm_option_execute_all": "执行全部操作",
        "confirm_option_skip_all": "跳过全部操作",
        "confirm_select_action": "请选择操作",

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
        "db_type_oracle": "Oracle",
        "db_gaussdb_centralized": "GaussDB 集中式",
        "db_gaussdb_distributed": "GaussDB 分布式",
        "db_gaussdb_mode_detected": "检测到 {mode} 模式",
        "db_gaussdb_driver_note": "请确保已安装 GaussDB 专用 psycopg2 驱动（不是标准 PostgreSQL psycopg2）",
        "oracle_no_dba_access": "无 DBA 权限，部分功能受限",
        "oracle_no_v_sql_access": "无法访问 V$SQL，显示当前活动会话",
        "oracle_11g_not_supported": "Oracle 11g 不支持此功能",
        "db_type_sqlserver": "SQL Server",
        "sqlserver_no_server_state": "无 VIEW SERVER STATE 权限，部分功能受限",
        "sqlserver_no_showplan": "无 SHOWPLAN 权限，无法获取执行计划",
        "sqlserver_azure_detected": "检测到 Azure SQL Database",
        "sqlserver_query_store_available": "Query Store 可用 (SQL Server 2016+)",
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
        "db_pending_confirmation_waiting": "有操作等待确认，请在下方选择操作。",
        "agent_thinking": "思考中... (迭代 {iteration})",
        "agent_compressing_context": "正在压缩上下文...",
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

        # Setup Wizard
        "setup_welcome": "欢迎使用 DB Agent AI!",
        "setup_first_time": "检测到您是首次使用，请完成初始配置。",
        "setup_step_db": "步骤 1/2: 配置数据库连接",
        "setup_step_llm": "步骤 2/2: 配置 AI 模型",
        "setup_db_type": "选择数据库类型",
        "setup_db_host": "数据库主机",
        "setup_db_port": "数据库端口",
        "setup_db_name": "数据库名称",
        "setup_db_user": "用户名",
        "setup_db_password": "密码",
        "setup_conn_name": "连接名称",
        "setup_testing_connection": "正在测试数据库连接...",
        "setup_connection_success": "数据库连接成功!",
        "setup_connection_failed": "数据库连接失败: {error}",
        "setup_retry_connection": "是否重新配置?",
        "setup_select_provider": "选择 AI 模型提供商",
        "setup_provider_recommended": "(推荐)",
        "setup_api_key": "API Key",
        "setup_api_key_hint": "输入您的 {provider} API Key",
        "setup_model": "模型名称",
        "setup_model_default": "默认: {model}",
        "setup_base_url": "API 地址 (可选)",
        "setup_base_url_hint": "留空使用默认地址",
        "setup_provider_name": "配置名称",
        "setup_testing_api": "正在测试 API 连接...",
        "setup_api_success": "API 连接成功!",
        "setup_api_failed": "API 连接失败: {error}",
        "setup_retry_api": "是否重新配置?",
        "setup_complete": "配置完成!",
        "setup_incomplete": "设置未完成，退出程序。",

        # Migration
        "migrate_prompt": "检测到旧版配置文件 config.ini",
        "migrate_ask": "是否将配置迁移到新存储?",
        "migrate_success": "配置迁移成功!",
        "migrate_failed": "配置迁移失败",

        # Connection Management
        "cmd_connections": "管理数据库连接",
        "cmd_providers": "管理 AI 模型",
        "connections_title": "数据库连接列表",
        "connections_empty": "暂无数据库连接",
        "connection_name": "名称",
        "connection_type": "类型",
        "connection_host": "主机",
        "connection_database": "数据库",
        "connection_status": "状态",
        "connection_active": "当前",
        "connection_add_success": "连接 [{name}] 添加成功",
        "connection_update_success": "连接 [{name}] 更新成功",
        "connection_delete_success": "连接 [{name}] 已删除",
        "connection_delete_confirm": "确定删除连接 [{name}]?",
        "connection_switch_success": "已切换到连接 [{name}]",
        "connection_not_found": "连接 [{name}] 不存在",
        "connection_test_success": "连接 [{name}] 测试成功",
        "connection_test_failed": "连接 [{name}] 测试失败: {error}",

        # Provider Management
        "providers_title": "AI 模型配置列表",
        "providers_empty": "暂无 AI 模型配置",
        "provider_name": "名称",
        "provider_type": "提供商",
        "provider_model": "模型",
        "provider_status": "状态",
        "provider_default": "默认",
        "provider_add_success": "模型配置 [{name}] 添加成功",
        "provider_update_success": "模型配置 [{name}] 更新成功",
        "provider_delete_success": "模型配置 [{name}] 已删除",
        "provider_delete_confirm": "确定删除模型配置 [{name}]?",
        "provider_switch_success": "已切换到模型配置 [{name}]",
        "provider_not_found": "模型配置 [{name}] 不存在",
        "provider_cannot_delete_default": "无法删除默认模型配置",
        "provider_cannot_delete_only": "无法删除唯一的模型配置",

        # Input prompts
        "input_enter_number": "请输入序号",
        "input_empty_cancel": "留空取消",
        "input_press_enter_default": "按回车使用默认值",

        # Session Management
        "sessions_title": "会话列表",
        "sessions_empty": "暂无会话记录",
        "session_name": "会话名称",
        "session_messages": "消息数",
        "session_created": "创建时间",
        "session_status": "状态",
        "session_current": "当前",
        "session_default_name_format": "会话 %Y-%m-%d %H:%M",
        "session_created": "会话 [{name}] 已创建",
        "session_switched": "已切换到会话 [{name}]",
        "session_restored_messages": "已恢复 {count} 条历史消息",
        "session_deleted": "会话 [{name}] 已删除",
        "session_delete_confirm": "确定删除会话 [{name}]? (包含 {count} 条消息)",
        "session_not_found": "会话 [{identifier}] 不存在",
        "session_cannot_delete_current": "无法删除当前会话",
        "session_renamed": "会话已重命名为 [{name}]",
        "session_no_current": "没有当前活动会话",
        "session_already_current": "已经在会话 [{name}] 中",
        "session_previous_found": "发现上次会话: {name} ({count} 条消息)",
        "session_continue_or_new": "请选择 (1/2)",
        "session_continue_previous": "继续上次会话",
        "session_start_new": "开始新会话",
        "session_continued": "继续会话 [{name}]",
        "session_new_created": "新会话 [{name}] 已创建",

        # ESC 中断功能
        "press_esc_to_interrupt": "按 ESC 可打断",
        "task_interrupted": "任务已打断",
        "interrupt_hint": "输入您的指示（如：继续、算了、或其他要求）",
        "interrupted_context_hint": "用户刚才打断了你正在执行的任务。请根据用户下面的输入判断意图：如果用户想继续之前的任务，请继续执行；如果用户有新的要求或修改，请按新要求处理；如果用户想放弃之前的任务，请确认并停止",

        # 在线迁移
        "cmd_migrate_online": "在线数据库对象迁移",
        "migrate_online_title": "在线数据库迁移向导",
        "migrate_no_active_connection": "请先使用 /connection use <名称> 连接到目标数据库",
        "migrate_no_source_connections": "没有可用的源数据库连接",
        "migrate_add_source_hint": "请先使用 /connection add 添加源数据库连接",
        "migrate_select_source_connection": "选择源数据库连接",
        "migrate_direction": "迁移方向",
        "migrate_confirm_direction": "确认开始迁移?",
        "migrate_source_schema": "源Schema (留空表示默认)",
        "migrate_task_created": "迁移任务已创建 (ID: {task_id})",
        "migrate_online_instruction": """请执行在线数据库迁移任务。

**任务信息：**
- 任务ID: {task_id}
- 源数据库连接名: {source_name}
- 源数据库类型: {source_type}
- 目标数据库连接名: {target_name}
- 目标数据库类型: {target_type}
- 源Schema: {source_schema}

**请按以下步骤执行：**

1. 调用 `analyze_source_database` 工具分析源数据库:
   - source_connection_name: "{source_name}"

2. 调用 `create_migration_plan` 工具创建迁移计划:
   - task_id: {task_id}
   - source_connection_name: "{source_name}"

3. 展示迁移计划给用户确认（显示对象列表、转换说明）

4. 用户确认后，调用 `execute_migration_batch` 执行迁移:
   - task_id: {task_id}

5. 完成后调用 `compare_databases` 进行对比验证:
   - task_id: {task_id}

6. 最后调用 `generate_migration_report` 生成报告:
   - task_id: {task_id}""",
        "migration_storage_required": "在线迁移功能需要启用存储",
        "migration_source_not_found": "源数据库连接不存在: {name}",
        "migration_task_not_found": "迁移任务不存在: {task_id}",
        "migration_item_not_found": "迁移项不存在: {item_id}",
        "migration_analyzing": "正在分析源数据库...",
        "migration_planning": "正在制定迁移计划...",
        "migration_executing": "正在执行迁移...",
        "migration_comparing": "正在比对数据库...",
        "migration_completed": "迁移完成",
        "migration_failed": "迁移失败",
        "migration_progress": "进度: {completed}/{total} ({percent}%)",
        "migration_object_types": "对象类型",
        "migration_tables": "表",
        "migration_indexes": "索引",
        "migration_views": "视图",
        "migration_sequences": "序列",
        "migration_procedures": "存储过程",
        "migration_functions": "函数",
        "migration_triggers": "触发器",
        "migration_constraints": "约束",

        # 迁移确认模式
        "migrate_confirm_mode": "请选择SQL执行确认模式",
        "migrate_confirm_mode_auto": "自动执行全部SQL（无需逐条确认）",
        "migrate_confirm_mode_manual": "逐条确认每个SQL语句",

        # Connection menu
        "conn_select_action": "请选择操作",
        "conn_action_use": "切换连接",
        "conn_action_add": "添加连接",
        "conn_action_edit": "编辑连接",
        "conn_action_delete": "删除连接",
        "conn_action_test": "测试连接",
        "conn_select_target": "请选择连接",

        # MCP (Model Context Protocol)
        "cmd_mcp": "管理 MCP 外部工具服务",
        "mcp_servers_title": "MCP Server 列表",
        "mcp_servers_empty": "暂无 MCP Server 配置",
        "mcp_server_name": "服务器名称",
        "mcp_server_command": "启动命令",
        "mcp_server_status": "状态",
        "mcp_enabled": "已启用",
        "mcp_disabled": "已禁用",
        "mcp_add_server": "添加 MCP Server",
        "mcp_command_hint": "输入启动 MCP Server 的命令 (如: npx, python, node)",
        "mcp_command": "命令",
        "mcp_args_hint": "输入命令参数，空格分隔 (如: -y @modelcontextprotocol/server-filesystem /tmp)",
        "mcp_args": "参数",
        "mcp_env_hint": "输入环境变量，格式: KEY=VALUE，空格分隔 (可选)",
        "mcp_env": "环境变量",
        "mcp_env_parse_error": "环境变量格式解析失败，已忽略",
        "mcp_server_added": "MCP Server [{name}] 添加成功",
        "mcp_server_exists": "MCP Server [{name}] 已存在",
        "mcp_server_not_found": "MCP Server [{name}] 不存在",
        "mcp_server_deleted": "MCP Server [{name}] 已删除",
        "mcp_server_delete_confirm": "确定删除 MCP Server [{name}]?",
        "mcp_server_enabled": "MCP Server [{name}] 已启用",
        "mcp_server_disabled": "MCP Server [{name}] 已禁用",
        "mcp_connect_now": "是否立即连接?",
        "mcp_connecting": "正在连接 MCP Server [{name}]...",
        "mcp_connected": "已连接 MCP Server [{name}] ({tools} 个工具)",
        "mcp_connect_failed": "连接 MCP Server [{name}] 失败",
        "mcp_no_connected_servers": "暂无已连接的 MCP Server",
        "mcp_tools_title": "MCP 工具列表",
        "mcp_tool_name": "工具名称",
        "mcp_tool_description": "描述",
        "mcp_no_tools": "MCP Server [{server}] 暂无可用工具",
        "mcp_no_tools_available": "暂无可用的 MCP 工具",

        # Skills
        "cmd_skills": "管理外部 Skills",
        "skills_title": "Skills 列表",
        "skills_empty": "暂无可用 Skills",
        "skills_loaded": "已加载 {count} 个 Skills",
        "skills_reloaded": "Skills 已重新加载",
        "skill_name": "名称",
        "skill_description": "描述",
        "skill_source": "来源",
        "skill_source_personal": "个人",
        "skill_source_project": "项目",
        "skill_user_invocable": "用户可调用",
        "skill_model_invocable": "AI可调用",
        "skill_not_found": "Skill [{name}] 不存在",
        "skill_executed": "已执行 Skill [{name}]",
        "skill_execute_failed": "执行 Skill [{name}] 失败: {error}",
        "skill_list_hint": "使用 /<skill-name> 调用技能，或使用 /skills reload 重新加载",

        # Tool descriptions (for tool_registry)
        "tool_desc_identify_slow_queries": "识别数据库中的慢查询。PostgreSQL使用pg_stat_statements，MySQL使用performance_schema。如不可用则显示当前活动查询。",
        "tool_desc_get_running_queries": "获取当前正在运行的查询。显示查询的PID、用户、数据库、状态、运行时间等信息。",
        "tool_desc_run_explain": "运行EXPLAIN分析SQL查询的执行计划。可以看到是否使用索引、是否全表扫描、JOIN策略等。analyze=true会实际执行查询获取真实时间。",
        "tool_desc_check_index_usage": "检查表的索引使用情况。可以发现未使用的索引、索引扫描次数、索引大小等。用于索引优化。",
        "tool_desc_get_table_stats": "获取表的统计信息。包括表大小、死元组比例、最后VACUUM/ANALYZE时间、顺序扫描次数等。用于诊断表的健康状况。",
        "tool_desc_create_index": "创建索引。需要用户确认后才能执行。默认使用在线DDL避免锁表(PostgreSQL使用CONCURRENTLY，MySQL 5.6+使用ALGORITHM=INPLACE)。",
        "tool_desc_analyze_table": "更新表的统计信息(ANALYZE)。统计信息过期会导致查询优化器选择错误的执行计划。这个操作很安全,不会锁表。",
        "tool_desc_execute_safe_query": "执行安全的SELECT查询。只允许SELECT,不允许修改数据。用于获取额外的数据库信息。",
        "tool_desc_execute_sql": "执行任意SQL语句，包括INSERT、UPDATE、DELETE、CREATE TABLE、ALTER TABLE、DROP TABLE等。用于直接操作数据库。返回影响的行数或查询结果。",
        "tool_desc_list_tables": "列出数据库中的所有表，包括表名和大小信息。用于了解数据库结构。",
        "tool_desc_describe_table": "获取表的详细结构信息，包括列名、数据类型、是否可空、默认值、主键和外键信息。",
        "tool_desc_get_sample_data": "获取表的示例数据，用于了解表中的数据内容和格式。",
        "tool_desc_analyze_source_database": "分析源数据库，获取所有对象（表、索引、视图、序列、存储过程等）及其依赖关系，用于迁移计划制定。",
        "tool_desc_create_migration_plan": "根据对象依赖关系创建迁移计划，确定执行顺序，生成转换后的DDL。",
        "tool_desc_get_migration_plan": "获取迁移计划详情，包括所有迁移项及其状态。",
        "tool_desc_get_migration_status": "获取迁移任务状态和进度摘要。",
        "tool_desc_execute_migration_item": "执行单个迁移项（在目标数据库中创建对象）。",
        "tool_desc_execute_migration_batch": "批量执行待处理的迁移项。",
        "tool_desc_compare_databases": "比对源库和目标库对象，验证迁移结果。",
        "tool_desc_generate_migration_report": "生成详细的迁移报告，包括统计信息和错误详情。",
        "tool_desc_skip_migration_item": "跳过某个迁移项（标记为已跳过）。",
        "tool_desc_retry_failed_items": "重试所有失败的迁移项。",
        "tool_desc_request_migration_setup": "当用户想要将数据库对象从一个数据库迁移到另一个数据库时，调用此工具请求迁移配置。系统将向用户展示迁移配置界面，让用户选择源库和目标库。",
        "tool_desc_request_user_input": "在聊天中显示内联表单卡片，用于收集用户的结构化输入。当你需要用户提供多个字段的信息时使用（如报销申请、数据录入、配置表单等）。支持的字段类型：text、number、select、textarea、date。",

        # Tool parameter descriptions
        "tool_param_identify_slow_queries_min_duration_ms": "最小平均执行时间(毫秒),默认1000ms",
        "tool_param_identify_slow_queries_limit": "返回结果数量,默认20",
        "tool_param_run_explain_sql": "要分析的SQL语句",
        "tool_param_run_explain_analyze": "是否实际执行查询(EXPLAIN ANALYZE),默认false。true会获取真实执行时间,但会实际执行查询。",
        "tool_param_check_index_usage_table_name": "表名",
        "tool_param_check_index_usage_schema": "模式名,默认public",
        "tool_param_get_table_stats_table_name": "表名",
        "tool_param_get_table_stats_schema": "模式名,默认public",
        "tool_param_create_index_index_sql": "CREATE INDEX语句",
        "tool_param_create_index_concurrent": "是否使用在线DDL(不锁表/少锁表),默认true",
        "tool_param_analyze_table_table_name": "表名",
        "tool_param_analyze_table_schema": "模式名,默认public",
        "tool_param_execute_safe_query_sql": "SELECT查询语句",
        "tool_param_execute_sql_sql": "要执行的SQL语句",
        "tool_param_list_tables_schema": "模式名,默认public",
        "tool_param_describe_table_table_name": "表名",
        "tool_param_describe_table_schema": "模式名,默认public",
        "tool_param_get_sample_data_table_name": "表名",
        "tool_param_get_sample_data_schema": "模式名,默认public",
        "tool_param_get_sample_data_limit": "返回的行数,默认10",
        "tool_param_analyze_source_database_source_connection_name": "源数据库连接名称",
        "tool_param_analyze_source_database_schema": "要分析的schema（可选）",
        "tool_param_analyze_source_database_object_types": "要包含的对象类型：table、view、index、sequence、procedure、function、trigger、constraint",
        "tool_param_create_migration_plan_task_id": "迁移任务ID",
        "tool_param_create_migration_plan_source_connection_name": "源数据库连接名称",
        "tool_param_create_migration_plan_target_schema": "目标schema名称（可选）",
        "tool_param_get_migration_plan_task_id": "迁移任务ID",
        "tool_param_get_migration_status_task_id": "迁移任务ID",
        "tool_param_execute_migration_item_item_id": "迁移项ID",
        "tool_param_execute_migration_batch_task_id": "迁移任务ID",
        "tool_param_execute_migration_batch_batch_size": "每批执行数量，默认10",
        "tool_param_compare_databases_task_id": "迁移任务ID",
        "tool_param_generate_migration_report_task_id": "迁移任务ID",
        "tool_param_skip_migration_item_item_id": "迁移项ID",
        "tool_param_skip_migration_item_reason": "跳过原因",
        "tool_param_retry_failed_items_task_id": "迁移任务ID",
        "tool_param_request_migration_setup_reason": "请求迁移配置的原因说明",
        "tool_param_request_migration_setup_suggested_source_db_type": "建议的源数据库类型（如oracle、mysql、postgresql等）",
        "tool_param_request_migration_setup_suggested_target_db_type": "建议的目标数据库类型（如postgresql、gaussdb、mysql等）",

        # list_databases tool
        "tool_desc_list_databases": "列出当前服务器实例上的所有数据库。用于发现同一实例的可用数据库，支持快速切换。",
        "tool_param_list_databases_schema": "模式名（可选）",

        # switch_database tool
        "tool_desc_switch_database": "切换到同实例的另一个数据库。自动查找或创建连接记录，无需用户手动配置。当用户要求查看或操作其他数据库时使用此工具。",
        "tool_param_switch_database_database": "目标数据库名称",

        # Connection use-db
        "connection_use_db": "切换数据库",
        "connection_use_db_prompt": "选择要切换的数据库",
        "connection_use_db_success": "已切换到数据库 [{database}]（连接: [{name}]）",
        "connection_use_db_created": "已为数据库 [{database}] 自动创建连接 [{name}]",
        "connection_list_databases": "当前实例上的数据库",
        "connection_current_database": "当前数据库",
        "connection_no_active": "没有活跃的数据库连接，请先使用 /connection use <name> 连接数据库",
        "connection_use_db_help": "切换同实例的其他数据库",
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
        "cmd_file": "Load SQL file for analysis",
        "cmd_migrate": "Database migration wizard",
        "cmd_sessions": "List all sessions",
        "cmd_session": "Manage sessions (new/use/delete/rename)",
        "cmd_model": "Switch AI model",
        "cmd_language": "Switch language (中文/English)",
        "cmd_reset": "Reset conversation",
        "cmd_history": "View history",
        "cmd_clear": "Clear screen",
        "cmd_exit": "Exit",

        # File upload
        "file_input_path": "Enter file path",
        "file_not_found": "File not found: {path}",
        "file_type_warning": "Warning: File type {ext} may not be a SQL file",
        "file_encoding_error": "Cannot read file, unsupported encoding",
        "file_size_warning": "File is large ({size}KB), may affect analysis",
        "file_continue_large": "Continue loading?",
        "file_loaded": "File loaded: {path} ({size} bytes, ~{sql_count} SQL statements)",
        "file_preview": "File Preview",
        "file_more_lines": "{count} more lines not shown",
        "file_usage_hint": "File loaded. Enter your question (e.g., analyze this SQL file, execute these SQLs, optimize the 3rd query)",
        "file_context_header": "Below is the SQL file content uploaded by user ({path})",
        "file_read_error": "Failed to read file: {error}",

        # Database Migration
        "migrate_target_db": "Target database",
        "migrate_source_db": "Source database type",
        "migrate_select_source": "Select source database type",
        "migrate_enter_number": "Enter number (empty to cancel)",
        "migrate_mode_file": "File import migration",
        "migrate_mode_file_desc": "Import from SQL file and convert",
        "migrate_mode_online": "Online migration",
        "migrate_mode_online_desc": "Migrate directly from source to target database",
        "migrate_other": "Other",
        "migrate_enter_source_name": "Enter source database name",
        "migrate_source_selected": "Source database selected: {source}",
        "migrate_mode_select": "Select migration mode",
        "migrate_mode_convert_only": "Convert only - Show converted DDL without execution",
        "migrate_mode_convert_execute": "Convert and execute - Convert DDL and execute on target database",
        "migrate_enter_mode": "Enter mode number",
        "migrate_will_execute": "Will convert and execute DDL statements",
        "migrate_convert_only": "Will show converted DDL only, without execution",
        "migrate_using_optimized_rules": "Using optimized Oracle→GaussDB migration rules",
        "migrate_instruction_convert": "Please convert the {source} DDL statements in this SQL file to {target} syntax. Analyze each statement, show a mapping table of data type and syntax conversions, then display the complete converted DDL.",
        "migrate_instruction_execute": "Please convert the {source} DDL statements in this SQL file to {target} syntax and execute them on the current database. Analyze each statement, show a mapping table of data type and syntax conversions, then execute the converted DDL in correct dependency order (tables before indexes, parent tables before child tables).",
        "migrate_instruction_oracle_to_gaussdb_convert": """Please convert the Oracle DDL/PL-SQL statements in this SQL file to GaussDB syntax.

**Key Conversion Rules:**
1. Package replacements: DBMS_LOB→DBE_LOB, DBMS_OUTPUT→DBE_OUTPUT, DBMS_RANDOM→DBE_RANDOM, UTL_RAW→DBE_RAW, DBMS_SQL→DBE_SQL
2. Data types: NUMBER(p,-s) needs manual handling; VARCHAR2(n CHAR)→VARCHAR2(n*4); DATE becomes TIMESTAMP(0)
3. SQL syntax: != must not have space; CONNECT BY→WITH RECURSIVE; ROWNUM→ROW_NUMBER()
4. Functions: DECODE can stay or use CASE WHEN; NVL can stay or use COALESCE

Please analyze each statement and show:
- Original Oracle statement
- Converted GaussDB statement
- Conversion notes (if changed)""",
        "migrate_instruction_oracle_to_gaussdb_execute": """Please convert the Oracle DDL/PL-SQL statements in this SQL file to GaussDB syntax and execute them.

**Key Conversion Rules:**
1. Package replacements: DBMS_LOB→DBE_LOB, DBMS_OUTPUT→DBE_OUTPUT, DBMS_RANDOM→DBE_RANDOM, UTL_RAW→DBE_RAW, DBMS_SQL→DBE_SQL
2. Data types: NUMBER(p,-s) needs manual handling; VARCHAR2(n CHAR)→VARCHAR2(n*4); DATE becomes TIMESTAMP(0)
3. SQL syntax: != must not have space; CONNECT BY→WITH RECURSIVE; ROWNUM→ROW_NUMBER()
4. Functions: DECODE can stay or use CASE WHEN; NVL can stay or use COALESCE

Please:
1. Show conversion summary (mapping table) first
2. Execute in dependency order (sequences→tables→constraints→indexes→procedures)
3. Show original and converted statement before each execution""",

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
        "confirm_option_execute": "Execute this operation",
        "confirm_option_skip": "Skip this operation",
        "confirm_option_execute_all": "Execute all operations",
        "confirm_option_skip_all": "Skip all operations",
        "confirm_select_action": "Select action",

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
        "db_type_oracle": "Oracle",
        "db_gaussdb_centralized": "GaussDB Centralized",
        "db_gaussdb_distributed": "GaussDB Distributed",
        "db_gaussdb_mode_detected": "Detected {mode} mode",
        "db_gaussdb_driver_note": "Please ensure GaussDB-specific psycopg2 driver is installed (NOT standard PostgreSQL psycopg2)",
        "oracle_no_dba_access": "No DBA privileges, some features are limited",
        "oracle_no_v_sql_access": "Cannot access V$SQL, showing current active sessions",
        "oracle_11g_not_supported": "Oracle 11g does not support this feature",
        "db_type_sqlserver": "SQL Server",
        "sqlserver_no_server_state": "No VIEW SERVER STATE permission, some features are limited",
        "sqlserver_no_showplan": "No SHOWPLAN permission, cannot get execution plan",
        "sqlserver_azure_detected": "Azure SQL Database detected",
        "sqlserver_query_store_available": "Query Store available (SQL Server 2016+)",
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
        "db_pending_confirmation_waiting": "Operation pending confirmation. Please select an action below.",
        "agent_thinking": "Thinking... (iteration {iteration})",
        "agent_compressing_context": "Compressing context...",
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

        # Setup Wizard
        "setup_welcome": "Welcome to DB Agent AI!",
        "setup_first_time": "First time setup detected. Please complete the initial configuration.",
        "setup_step_db": "Step 1/2: Configure Database Connection",
        "setup_step_llm": "Step 2/2: Configure AI Model",
        "setup_db_type": "Select database type",
        "setup_db_host": "Database host",
        "setup_db_port": "Database port",
        "setup_db_name": "Database name",
        "setup_db_user": "Username",
        "setup_db_password": "Password",
        "setup_conn_name": "Connection name",
        "setup_testing_connection": "Testing database connection...",
        "setup_connection_success": "Database connection successful!",
        "setup_connection_failed": "Database connection failed: {error}",
        "setup_retry_connection": "Retry configuration?",
        "setup_select_provider": "Select AI model provider",
        "setup_provider_recommended": "(Recommended)",
        "setup_api_key": "API Key",
        "setup_api_key_hint": "Enter your {provider} API Key",
        "setup_model": "Model name",
        "setup_model_default": "Default: {model}",
        "setup_base_url": "API URL (optional)",
        "setup_base_url_hint": "Leave empty for default",
        "setup_provider_name": "Configuration name",
        "setup_testing_api": "Testing API connection...",
        "setup_api_success": "API connection successful!",
        "setup_api_failed": "API connection failed: {error}",
        "setup_retry_api": "Retry configuration?",
        "setup_complete": "Configuration complete!",
        "setup_incomplete": "Setup incomplete, exiting.",

        # Migration
        "migrate_prompt": "Legacy config.ini file detected",
        "migrate_ask": "Migrate configuration to new storage?",
        "migrate_success": "Configuration migrated successfully!",
        "migrate_failed": "Configuration migration failed",

        # Connection Management
        "cmd_connections": "Manage database connections",
        "cmd_providers": "Manage AI models",
        "connections_title": "Database Connections",
        "connections_empty": "No database connections",
        "connection_name": "Name",
        "connection_type": "Type",
        "connection_host": "Host",
        "connection_database": "Database",
        "connection_status": "Status",
        "connection_active": "Active",
        "connection_add_success": "Connection [{name}] added successfully",
        "connection_update_success": "Connection [{name}] updated successfully",
        "connection_delete_success": "Connection [{name}] deleted",
        "connection_delete_confirm": "Delete connection [{name}]?",
        "connection_switch_success": "Switched to connection [{name}]",
        "connection_not_found": "Connection [{name}] not found",
        "connection_test_success": "Connection [{name}] test successful",
        "connection_test_failed": "Connection [{name}] test failed: {error}",

        # Provider Management
        "providers_title": "AI Model Configurations",
        "providers_empty": "No AI model configurations",
        "provider_name": "Name",
        "provider_type": "Provider",
        "provider_model": "Model",
        "provider_status": "Status",
        "provider_default": "Default",
        "provider_add_success": "Model configuration [{name}] added successfully",
        "provider_update_success": "Model configuration [{name}] updated successfully",
        "provider_delete_success": "Model configuration [{name}] deleted",
        "provider_delete_confirm": "Delete model configuration [{name}]?",
        "provider_switch_success": "Switched to model configuration [{name}]",
        "provider_not_found": "Model configuration [{name}] not found",
        "provider_cannot_delete_default": "Cannot delete default model configuration",
        "provider_cannot_delete_only": "Cannot delete the only model configuration",

        # Input prompts
        "input_enter_number": "Enter number",
        "input_empty_cancel": "empty to cancel",
        "input_press_enter_default": "Press Enter for default",

        # Session Management
        "sessions_title": "Sessions",
        "sessions_empty": "No sessions found",
        "session_name": "Session Name",
        "session_messages": "Messages",
        "session_created": "Created",
        "session_status": "Status",
        "session_current": "Current",
        "session_default_name_format": "Session %Y-%m-%d %H:%M",
        "session_created": "Session [{name}] created",
        "session_switched": "Switched to session [{name}]",
        "session_restored_messages": "Restored {count} messages from history",
        "session_deleted": "Session [{name}] deleted",
        "session_delete_confirm": "Delete session [{name}]? ({count} messages)",
        "session_not_found": "Session [{identifier}] not found",
        "session_cannot_delete_current": "Cannot delete current session",
        "session_renamed": "Session renamed to [{name}]",
        "session_no_current": "No current active session",
        "session_already_current": "Already in session [{name}]",
        "session_previous_found": "Previous session found: {name} ({count} messages)",
        "session_continue_or_new": "Please select (1/2)",
        "session_continue_previous": "Continue previous session",
        "session_start_new": "Start new session",
        "session_continued": "Continuing session [{name}]",
        "session_new_created": "New session [{name}] created",

        # ESC Interrupt Feature
        "press_esc_to_interrupt": "Press ESC to interrupt",
        "task_interrupted": "Task interrupted",
        "interrupt_hint": "Enter your instruction (e.g., continue, cancel, or other requests)",
        "interrupted_context_hint": "The user just interrupted the task you were executing. Based on the user's input below, determine their intent: if they want to continue the previous task, please resume; if they have new requirements or modifications, handle them accordingly; if they want to abort the previous task, confirm and stop",

        # Online Migration
        "cmd_migrate_online": "Online database object migration",
        "migrate_online_title": "Online Database Migration Wizard",
        "migrate_no_active_connection": "Please connect to target database first using /connection use <name>",
        "migrate_no_source_connections": "No source database connections available",
        "migrate_add_source_hint": "Please add source database connection first using /connection add",
        "migrate_select_source_connection": "Select source database connection",
        "migrate_direction": "Migration direction",
        "migrate_confirm_direction": "Confirm to start migration?",
        "migrate_source_schema": "Source schema (leave empty for default)",
        "migrate_task_created": "Migration task created (ID: {task_id})",
        "migrate_online_instruction": """Please execute online database migration task.

**Task Information:**
- Task ID: {task_id}
- Source connection name: {source_name}
- Source database type: {source_type}
- Target connection name: {target_name}
- Target database type: {target_type}
- Source schema: {source_schema}

**Please follow these steps:**

1. Call `analyze_source_database` to analyze source database:
   - source_connection_name: "{source_name}"

2. Call `create_migration_plan` to create migration plan:
   - task_id: {task_id}
   - source_connection_name: "{source_name}"

3. Show migration plan for user confirmation (display object list, conversion notes)

4. After user confirmation, call `execute_migration_batch` to execute migration:
   - task_id: {task_id}

5. After completion, call `compare_databases` to verify:
   - task_id: {task_id}

6. Finally call `generate_migration_report` to generate report:
   - task_id: {task_id}""",
        "migration_storage_required": "Online migration requires storage to be enabled",
        "migration_source_not_found": "Source database connection not found: {name}",
        "migration_task_not_found": "Migration task not found: {task_id}",
        "migration_item_not_found": "Migration item not found: {item_id}",
        "migration_analyzing": "Analyzing source database...",
        "migration_planning": "Creating migration plan...",
        "migration_executing": "Executing migration...",
        "migration_comparing": "Comparing databases...",
        "migration_completed": "Migration completed",
        "migration_failed": "Migration failed",
        "migration_progress": "Progress: {completed}/{total} ({percent}%)",
        "migration_object_types": "Object types",
        "migration_tables": "Tables",
        "migration_indexes": "Indexes",
        "migration_views": "Views",
        "migration_sequences": "Sequences",
        "migration_procedures": "Stored procedures",
        "migration_functions": "Functions",
        "migration_triggers": "Triggers",
        "migration_constraints": "Constraints",

        # Migration Confirmation Mode
        "migrate_confirm_mode": "Please select SQL execution confirmation mode",
        "migrate_confirm_mode_auto": "Auto-execute all SQL (no per-statement confirmation)",
        "migrate_confirm_mode_manual": "Confirm each SQL statement individually",

        # Connection menu
        "conn_select_action": "Select action",
        "conn_action_use": "Switch connection",
        "conn_action_add": "Add connection",
        "conn_action_edit": "Edit connection",
        "conn_action_delete": "Delete connection",
        "conn_action_test": "Test connection",
        "conn_select_target": "Select connection",

        # MCP (Model Context Protocol)
        "cmd_mcp": "Manage MCP external tool services",
        "mcp_servers_title": "MCP Servers",
        "mcp_servers_empty": "No MCP servers configured",
        "mcp_server_name": "Server Name",
        "mcp_server_command": "Command",
        "mcp_server_status": "Status",
        "mcp_enabled": "Enabled",
        "mcp_disabled": "Disabled",
        "mcp_add_server": "Add MCP Server",
        "mcp_command_hint": "Enter command to start MCP Server (e.g., npx, python, node)",
        "mcp_command": "Command",
        "mcp_args_hint": "Enter command arguments, space-separated (e.g., -y @modelcontextprotocol/server-filesystem /tmp)",
        "mcp_args": "Arguments",
        "mcp_env_hint": "Enter environment variables, format: KEY=VALUE, space-separated (optional)",
        "mcp_env": "Environment Variables",
        "mcp_env_parse_error": "Failed to parse environment variables, ignored",
        "mcp_server_added": "MCP Server [{name}] added successfully",
        "mcp_server_exists": "MCP Server [{name}] already exists",
        "mcp_server_not_found": "MCP Server [{name}] not found",
        "mcp_server_deleted": "MCP Server [{name}] deleted",
        "mcp_server_delete_confirm": "Delete MCP Server [{name}]?",
        "mcp_server_enabled": "MCP Server [{name}] enabled",
        "mcp_server_disabled": "MCP Server [{name}] disabled",
        "mcp_connect_now": "Connect now?",
        "mcp_connecting": "Connecting to MCP Server [{name}]...",
        "mcp_connected": "Connected to MCP Server [{name}] ({tools} tools)",
        "mcp_connect_failed": "Failed to connect to MCP Server [{name}]",
        "mcp_no_connected_servers": "No connected MCP servers",
        "mcp_tools_title": "MCP Tools",
        "mcp_tool_name": "Tool Name",
        "mcp_tool_description": "Description",
        "mcp_no_tools": "No tools available from MCP Server [{server}]",
        "mcp_no_tools_available": "No MCP tools available",

        # Skills
        "cmd_skills": "Manage external Skills",
        "skills_title": "Skills",
        "skills_empty": "No skills available",
        "skills_loaded": "Loaded {count} skills",
        "skills_reloaded": "Skills reloaded",
        "skill_name": "Name",
        "skill_description": "Description",
        "skill_source": "Source",
        "skill_source_personal": "Personal",
        "skill_source_project": "Project",
        "skill_user_invocable": "User invocable",
        "skill_model_invocable": "AI invocable",
        "skill_not_found": "Skill [{name}] not found",
        "skill_executed": "Executed skill [{name}]",
        "skill_execute_failed": "Failed to execute skill [{name}]: {error}",
        "skill_list_hint": "Use /<skill-name> to invoke a skill, or /skills reload to reload",

        # Tool descriptions (for tool_registry)
        "tool_desc_identify_slow_queries": "Identify slow queries in the database. For PostgreSQL uses pg_stat_statements, for MySQL uses performance_schema. Falls back to active queries if statistics are not available.",
        "tool_desc_get_running_queries": "Get currently running queries. Shows PID, user, database, state, duration, etc.",
        "tool_desc_run_explain": "Run EXPLAIN to analyze SQL query execution plan. Shows index usage, full table scans, JOIN strategies, etc. analyze=true executes the query to get actual timing.",
        "tool_desc_check_index_usage": "Check index usage for a table. Find unused indexes, scan counts, index sizes. For index optimization.",
        "tool_desc_get_table_stats": "Get table statistics. Includes size, dead tuple ratio, last VACUUM/ANALYZE time, sequential scan count. For diagnosing table health.",
        "tool_desc_create_index": "Create an index. Requires user confirmation. Uses online DDL when possible to minimize table locks (CONCURRENTLY for PostgreSQL, ALGORITHM=INPLACE for MySQL 5.6+).",
        "tool_desc_analyze_table": "Update table statistics (ANALYZE). Outdated statistics cause query optimizer to choose wrong execution plans. Safe operation, no table lock.",
        "tool_desc_execute_safe_query": "Execute safe SELECT query. Only allows SELECT, no data modification. For getting additional database information.",
        "tool_desc_execute_sql": "Execute any SQL statement including INSERT, UPDATE, DELETE, CREATE TABLE, ALTER TABLE, DROP TABLE, etc. For direct database operations. Returns affected rows or query results.",
        "tool_desc_list_tables": "List all tables in the database with name and size information. For understanding database structure.",
        "tool_desc_describe_table": "Get detailed table structure including column names, data types, nullability, defaults, primary keys and foreign keys.",
        "tool_desc_get_sample_data": "Get sample data from a table to understand the data content and format.",
        "tool_desc_analyze_source_database": "Analyze source database to get all objects (tables, indexes, views, sequences, procedures, etc.) and their dependencies for migration planning.",
        "tool_desc_create_migration_plan": "Create a migration plan with execution order based on object dependencies. Generates converted DDL for target database.",
        "tool_desc_get_migration_plan": "Get migration plan details including all items and their status.",
        "tool_desc_get_migration_status": "Get migration task status and progress summary.",
        "tool_desc_execute_migration_item": "Execute a single migration item (create object in target database).",
        "tool_desc_execute_migration_batch": "Execute multiple pending migration items in batch.",
        "tool_desc_compare_databases": "Compare source and target databases to verify migration results.",
        "tool_desc_generate_migration_report": "Generate detailed migration report with statistics and any errors.",
        "tool_desc_skip_migration_item": "Skip a migration item (mark as skipped).",
        "tool_desc_retry_failed_items": "Retry all failed migration items.",
        "tool_desc_request_migration_setup": "Call this tool when the user wants to migrate database objects from one database to another. The system will present a migration configuration UI for the user to select source and target databases.",
        "tool_desc_request_user_input": "Display an inline form card to collect structured input from the user. Use this when you need the user to provide multiple fields of information (e.g. expense report, data entry, configuration). Fields support types: text, number, select, textarea, date.",

        # Tool parameter descriptions
        "tool_param_identify_slow_queries_min_duration_ms": "Minimum average execution time in milliseconds, default 1000ms",
        "tool_param_identify_slow_queries_limit": "Number of results to return, default 20",
        "tool_param_run_explain_sql": "SQL statement to analyze",
        "tool_param_run_explain_analyze": "Whether to actually execute (EXPLAIN ANALYZE), default false. True gets real execution time but runs the query.",
        "tool_param_check_index_usage_table_name": "Table name",
        "tool_param_check_index_usage_schema": "Schema name, default public",
        "tool_param_get_table_stats_table_name": "Table name",
        "tool_param_get_table_stats_schema": "Schema name, default public",
        "tool_param_create_index_index_sql": "CREATE INDEX statement",
        "tool_param_create_index_concurrent": "Use online DDL (no/minimal table lock), default true",
        "tool_param_analyze_table_table_name": "Table name",
        "tool_param_analyze_table_schema": "Schema name, default public",
        "tool_param_execute_safe_query_sql": "SELECT query statement",
        "tool_param_execute_sql_sql": "SQL statement to execute",
        "tool_param_list_tables_schema": "Schema name, default public",
        "tool_param_describe_table_table_name": "Table name",
        "tool_param_describe_table_schema": "Schema name, default public",
        "tool_param_get_sample_data_table_name": "Table name",
        "tool_param_get_sample_data_schema": "Schema name, default public",
        "tool_param_get_sample_data_limit": "Number of rows to return, default 10",
        "tool_param_analyze_source_database_source_connection_name": "Source database connection name",
        "tool_param_analyze_source_database_schema": "Schema to analyze (optional)",
        "tool_param_analyze_source_database_object_types": "Object types to include: table, view, index, sequence, procedure, function, trigger, constraint",
        "tool_param_create_migration_plan_task_id": "Migration task ID",
        "tool_param_create_migration_plan_source_connection_name": "Source database connection name",
        "tool_param_create_migration_plan_target_schema": "Target schema name (optional)",
        "tool_param_get_migration_plan_task_id": "Migration task ID",
        "tool_param_get_migration_status_task_id": "Migration task ID",
        "tool_param_execute_migration_item_item_id": "Migration item ID",
        "tool_param_execute_migration_batch_task_id": "Migration task ID",
        "tool_param_execute_migration_batch_batch_size": "Number of items to execute, default 10",
        "tool_param_compare_databases_task_id": "Migration task ID",
        "tool_param_generate_migration_report_task_id": "Migration task ID",
        "tool_param_skip_migration_item_item_id": "Migration item ID",
        "tool_param_skip_migration_item_reason": "Reason for skipping",
        "tool_param_retry_failed_items_task_id": "Migration task ID",
        "tool_param_request_migration_setup_reason": "Reason for requesting migration setup",
        "tool_param_request_migration_setup_suggested_source_db_type": "Suggested source database type (e.g. oracle, mysql, postgresql)",
        "tool_param_request_migration_setup_suggested_target_db_type": "Suggested target database type (e.g. postgresql, gaussdb, mysql)",

        # list_databases tool
        "tool_desc_list_databases": "List all databases on the current server instance. For discovering available databases on the same instance and quick switching.",
        "tool_param_list_databases_schema": "Schema name (optional)",

        # switch_database tool
        "tool_desc_switch_database": "Switch to another database on the same server instance. Automatically finds or creates connection records. Use when the user asks to view or operate on a different database.",
        "tool_param_switch_database_database": "Target database name",

        # Connection use-db
        "connection_use_db": "Switch database",
        "connection_use_db_prompt": "Select database to switch to",
        "connection_use_db_success": "Switched to database [{database}] (connection: [{name}])",
        "connection_use_db_created": "Auto-created connection [{name}] for database [{database}]",
        "connection_list_databases": "Databases on current instance",
        "connection_current_database": "Current database",
        "connection_no_active": "No active database connection. Use /connection use <name> to connect first",
        "connection_use_db_help": "Switch to another database on the same instance",
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
