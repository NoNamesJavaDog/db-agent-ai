"""
SQL Tuning AI Agent - Core Engine
"""
import json
import time
from typing import Dict, List, Any, TYPE_CHECKING
import logging
from db_agent.llm import BaseLLMClient
from db_agent.i18n import i18n, t
from .database import DatabaseToolsFactory
from .migration_rules import get_migration_rules, format_rules_for_prompt, ORACLE_TO_GAUSSDB_RULES
from .token_counter import TokenCounter
from .tool_registry import build_tools
from .context_compression import ContextCompressor
from .migration_handler import MigrationHandler, SkillExecutorHelper
from db_agent.storage.models import MigrationTask, MigrationItem

if TYPE_CHECKING:
    from db_agent.storage import SQLiteStorage, AuditService
    from db_agent.mcp import MCPManager
    from db_agent.skills import SkillRegistry

logger = logging.getLogger(__name__)


class SQLTuningAgent:
    """SQL调优AI Agent - 智能体核心"""

    def __init__(
        self,
        llm_client: BaseLLMClient,
        db_config: Dict[str, Any],
        language: str = "zh",
        storage: "SQLiteStorage" = None,
        session_id: int = None,
        mcp_manager: "MCPManager" = None
    ):
        """
        初始化AI Agent

        Args:
            llm_client: LLM客户端
            db_config: 数据库配置 (包含 type 字段指定数据库类型: postgresql 或 mysql)
            language: 界面语言 (zh/en)
            storage: SQLite storage instance for session persistence
            session_id: Session ID to associate with this agent
            mcp_manager: MCP manager for external tool integration
        """
        self.llm_client = llm_client
        self.storage = storage
        self.session_id = session_id
        self.mcp_manager = mcp_manager

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

        # Skills 注册中心 (will be set by CLI)
        self.skill_registry: "SkillRegistry" = None

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

        # 迁移处理器
        self._migration_handler = MigrationHandler(self.storage, self.db_tools, self.db_type)

        # 迁移自动执行模式
        self.migration_auto_execute = False

        # 中断控制
        self._interrupt_requested = False
        self._interrupted_state = None  # 保存被打断时的状态

        # 审计日志服务
        self.audit_service: "AuditService" = None
        if self.storage:
            from db_agent.storage import AuditService
            self.audit_service = AuditService(self.storage)

        # 当前连接ID（用于审计日志）
        self._connection_id: int = None

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

        # 同步迁移处理器
        self._migration_handler.db_tools = self.db_tools
        self._migration_handler.db_type = self.db_type

        # 重新初始化系统提示
        self._init_system_prompt()

        logger.info(f"数据库工具已重新初始化: {db_type}")

    def get_current_model_info(self) -> Dict[str, str]:
        """获取当前模型信息"""
        return {
            "provider": self.llm_client.get_provider_name(),
            "model": self.llm_client.get_model_name()
        }

    def set_connection_id(self, connection_id: int):
        """设置当前数据库连接ID（用于审计日志）"""
        self._connection_id = connection_id

    def get_connection_id(self) -> int:
        """获取当前数据库连接ID"""
        return self._connection_id

    def set_language(self, language: str):
        """设置语言并更新系统提示和工具定义"""
        self.language = language
        i18n.lang = language  # 同步更新全局i18n语言
        self._init_system_prompt()

    def refresh_system_prompt(self):
        """
        Refresh system prompt (call when skills/MCP configuration changes).

        This method re-initializes the system prompt to include updated
        skill and MCP tool descriptions.
        """
        self._init_system_prompt()
        logger.info("System prompt refreshed with updated skills/MCP tools")

    def _init_system_prompt(self):
        """初始化系统提示(内部方法)"""
        from .prompt_builder import build_system_prompt
        self.system_prompt = build_system_prompt(
            self.db_info, self.db_type, self.language,
            self.skill_registry, self.mcp_manager
        )
        self._init_tools()

    def _init_tools(self):
        """初始化工具定义(根据语言，使用tool_registry)"""
        self.tools = build_tools(self.language)

    def get_all_tools(self) -> List[Dict]:
        """
        获取所有可用工具，包括内置工具、MCP工具和Skill工具。

        Returns:
            工具定义列表（OpenAI function格式）
        """
        all_tools = self.tools.copy()

        # 添加MCP工具
        if self.mcp_manager:
            mcp_tools = self.mcp_manager.get_all_tools()
            all_tools.extend(mcp_tools)

        # 添加Skill工具
        if self.skill_registry:
            skill_tools = self.skill_registry.get_skill_tools()
            all_tools.extend(skill_tools)

        return all_tools

    def set_mcp_manager(self, mcp_manager: "MCPManager"):
        """
        设置MCP管理器。

        Args:
            mcp_manager: MCP管理器实例
        """
        self.mcp_manager = mcp_manager

    def set_skill_registry(self, skill_registry: "SkillRegistry"):
        """
        设置Skill注册中心。

        Args:
            skill_registry: SkillRegistry实例
        """
        self.skill_registry = skill_registry

    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any],
                      on_thinking: callable = None) -> Dict[str, Any]:
        """执行工具调用"""
        logger.info(f"执行工具: {tool_name}")
        logger.debug(f"输入参数: {tool_input}")

        start_time = time.time()
        result = None

        try:
            # 检查是否为MCP工具
            if self.mcp_manager and self.mcp_manager.is_mcp_tool(tool_name):
                result = self.mcp_manager.call_tool_sync(tool_name, tool_input)
                # 将MCP结果转换为标准格式
                if result.get("status") == "success":
                    result = {
                        "status": "success",
                        "content": result.get("content"),
                        "source": "mcp"
                    }
                else:
                    result = {
                        "status": "error",
                        "error": result.get("error", "Unknown MCP error"),
                        "source": "mcp"
                    }
                self._log_tool_call(tool_name, tool_input, result, start_time)
                return result

            # 检查是否为Skill工具
            if tool_name.startswith("skill_") and self.skill_registry:
                skill_name = tool_name[6:]  # Remove 'skill_' prefix
                arguments = tool_input.get("arguments", "")
                skill_helper = SkillExecutorHelper(self.skill_registry, self.session_id)
                result = skill_helper.execute_skill(skill_name, arguments)
                self._log_tool_call(tool_name, tool_input, result, start_time)
                return result

            if tool_name == "identify_slow_queries":
                result = self.db_tools.identify_slow_queries(**tool_input)
            elif tool_name == "run_explain":
                result = self.db_tools.run_explain(**tool_input)
                # Log as SQL execution for run_explain
                self._log_sql_execution(
                    tool_input.get("sql", ""),
                    "run_explain",
                    result,
                    start_time
                )
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
                    # Log as SQL execution
                    self._log_sql_execution(sql, "execute_safe_query", result, start_time)
            elif tool_name == "execute_sql":
                # 迁移自动执行模式：自动注入confirmed=True
                if self.migration_auto_execute and not tool_input.get("confirmed"):
                    tool_input["confirmed"] = True
                result = self.db_tools.execute_sql(**tool_input)
                # 如果需要确认，加入待确认队列
                if result.get("status") == "pending_confirmation":
                    self.pending_operations.append({"type": "execute_sql", "input": tool_input})
                else:
                    # Log as SQL execution (only if actually executed)
                    self._log_sql_execution(
                        tool_input.get("sql", ""),
                        "execute_sql",
                        result,
                        start_time,
                        user_confirmed=tool_input.get("confirmed", False)
                    )
            elif tool_name == "list_tables":
                result = self.db_tools.list_tables(**tool_input)
            elif tool_name == "describe_table":
                result = self.db_tools.describe_table(**tool_input)
            elif tool_name == "get_sample_data":
                result = self.db_tools.get_sample_data(**tool_input)
            elif tool_name == "list_databases":
                result = self.db_tools.list_databases()
            elif tool_name == "switch_database":
                result = self._switch_database(tool_input.get("database", ""))
            elif tool_name == "get_running_queries":
                result = self.db_tools.get_running_queries()
            # Migration tools (delegated to MigrationHandler)
            elif tool_name == "analyze_source_database":
                result = self._migration_handler.analyze_source_database(**tool_input)
            elif tool_name == "create_migration_plan":
                result = self._migration_handler.create_migration_plan(**tool_input)
            elif tool_name == "get_migration_plan":
                result = self._migration_handler.get_migration_plan(**tool_input)
            elif tool_name == "get_migration_status":
                result = self._migration_handler.get_migration_status(**tool_input)
            elif tool_name == "execute_migration_item":
                result = self._migration_handler.execute_migration_item(**tool_input)
                self._notify_migration_progress(result, on_thinking)
            elif tool_name == "execute_migration_batch":
                result = self._migration_handler.execute_migration_batch(**tool_input)
                self._notify_migration_progress(result, on_thinking)
            elif tool_name == "compare_databases":
                result = self._migration_handler.compare_databases(**tool_input)
            elif tool_name == "generate_migration_report":
                result = self._migration_handler.generate_migration_report(**tool_input)
                self.migration_auto_execute = False  # Reset after migration report
            elif tool_name == "skip_migration_item":
                result = self._migration_handler.skip_migration_item(**tool_input)
            elif tool_name == "retry_failed_items":
                result = self._migration_handler.retry_failed_items(**tool_input)
            elif tool_name == "request_migration_setup":
                result = {
                    "status": "migration_setup_requested",
                    "reason": tool_input.get("reason", ""),
                    "suggested_source_db_type": tool_input.get("suggested_source_db_type"),
                    "suggested_target_db_type": tool_input.get("suggested_target_db_type"),
                }
            elif tool_name == "request_user_input":
                result = {
                    "status": "form_input_requested",
                    "title": tool_input.get("title", ""),
                    "description": tool_input.get("description", ""),
                    "fields": tool_input.get("fields", []),
                }
            else:
                result = {"status": "error", "error": t("db_unknown_tool", tool=tool_name)}

            # Log tool call for non-SQL tools
            if tool_name not in ("execute_sql", "execute_safe_query", "run_explain"):
                self._log_tool_call(tool_name, tool_input, result, start_time)

            logger.info(f"工具执行完成: status={result.get('status')}")
            return result

        except Exception as e:
            logger.error(f"工具执行异常: {e}")
            error_result = {"status": "error", "error": str(e)}
            # Log the error
            self._log_tool_call(tool_name, tool_input, error_result, start_time)
            return error_result

    def _notify_migration_progress(self, result: Dict[str, Any], on_thinking: callable = None):
        """Send migration progress notification after a migration tool execution."""
        if not on_thinking or not self.storage:
            return
        try:
            # Determine task_id from result
            task_id = result.get("task_id")
            if not task_id:
                item_id = result.get("item_id")
                if item_id:
                    item = self.storage.get_migration_item(item_id)
                    if item:
                        task_id = item.task_id
            if not task_id:
                return

            task = self.storage.get_migration_task(task_id)
            if not task:
                return

            on_thinking("migration_progress", {
                "task_id": task_id,
                "total": task.total_items,
                "completed": task.completed_items,
                "failed": task.failed_items,
                "skipped": task.skipped_items,
            })
        except Exception as e:
            logger.warning(f"Failed to send migration progress: {e}")

    def _log_tool_call(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        result: Dict[str, Any],
        start_time: float
    ):
        """Log a tool call to the audit service."""
        if not self.audit_service:
            return

        try:
            execution_time_ms = int((time.time() - start_time) * 1000)
            result_status = result.get("status", "unknown")
            result_summary = None

            if result_status == "error":
                result_summary = result.get("error", "")[:500]  # Truncate long errors
            elif "rows" in result:
                result_summary = f"Returned {len(result.get('rows', []))} rows"
            elif "tables" in result:
                result_summary = f"Found {len(result.get('tables', []))} tables"

            self.audit_service.log_tool_call(
                session_id=self.session_id,
                connection_id=self._connection_id,
                tool_name=tool_name,
                parameters=parameters,
                result_status=result_status,
                result_summary=result_summary,
                execution_time_ms=execution_time_ms
            )
        except Exception as e:
            logger.warning(f"Failed to log tool call: {e}")

    def _log_sql_execution(
        self,
        sql: str,
        action: str,
        result: Dict[str, Any],
        start_time: float,
        user_confirmed: bool = False
    ):
        """Log a SQL execution to the audit service."""
        if not self.audit_service:
            return

        try:
            execution_time_ms = int((time.time() - start_time) * 1000)
            result_status = result.get("status", "unknown")
            affected_rows = result.get("affected_rows")
            error_message = result.get("error") if result_status == "error" else None

            self.audit_service.log_sql_execution(
                session_id=self.session_id,
                connection_id=self._connection_id,
                sql=sql,
                action=action,
                result_status=result_status,
                affected_rows=affected_rows,
                error_message=error_message,
                execution_time_ms=execution_time_ms,
                user_confirmed=user_confirmed
            )
        except Exception as e:
            logger.warning(f"Failed to log SQL execution: {e}")

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

        pending = self.pending_operations.pop(index)

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

    def _switch_database(self, target_database: str) -> Dict[str, Any]:
        """
        切换到同实例的另一个数据库。

        Args:
            target_database: 目标数据库名称

        Returns:
            操作结果字典
        """
        if not target_database:
            return {"status": "error", "error": t("tool_param_switch_database_database")}

        if not self.storage:
            return {"status": "error", "error": t("connection_no_active")}

        active_conn = self.storage.get_active_connection()
        if not active_conn:
            return {"status": "error", "error": t("connection_no_active")}

        # Already on the target database
        if active_conn.database == target_database:
            return {
                "status": "success",
                "message": f"Already connected to database [{target_database}]",
                "database": target_database,
                "connection_name": active_conn.name
            }

        # Try to find existing connection for this instance + database
        found = self.storage.find_connection_for_instance_db(
            active_conn.db_type, active_conn.host, active_conn.port,
            active_conn.username, target_database
        )

        if found:
            self.storage.set_active_connection(found.name)
            conn_name = found.name
            conn_id = found.id
        else:
            # Auto-create a new connection record
            from datetime import datetime
            from db_agent.storage.models import DatabaseConnection
            new_name = f"{active_conn.name}__{target_database}"
            now = datetime.now()
            new_conn = DatabaseConnection(
                id=None,
                name=new_name,
                db_type=active_conn.db_type,
                host=active_conn.host,
                port=active_conn.port,
                database=target_database,
                username=active_conn.username,
                password_encrypted=active_conn.password_encrypted,
                is_active=False,
                created_at=now,
                updated_at=now
            )
            try:
                conn_id = self.storage.add_connection(new_conn)
                self.storage.set_active_connection(new_name)
                conn_name = new_name
            except Exception as e:
                return {"status": "error", "error": str(e)}

        # Reinitialize database tools with the new connection
        try:
            from db_agent.storage.encryption import decrypt
            password = decrypt(active_conn.password_encrypted)
            db_config = {
                'type': active_conn.db_type,
                'host': active_conn.host,
                'port': active_conn.port,
                'database': target_database,
                'user': active_conn.username,
                'password': password
            }
            self.reinitialize_db_tools(db_config)
            self._connection_id = conn_id
            return {
                "status": "success",
                "message": t("connection_use_db_success", database=target_database, name=conn_name),
                "database": target_database,
                "connection_name": conn_name
            }
        except Exception as e:
            return {"status": "error", "error": f"Failed to connect to database [{target_database}]: {e}"}

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

        while self.migration_auto_execute or iteration < max_iterations:
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

            # 获取所有工具（包括MCP工具）
            all_tools = self.get_all_tools()

            # 调用LLM API (统一接口)
            response = self.llm_client.chat(messages=messages, tools=all_tools)

            finish_reason = response["finish_reason"]
            content = response["content"]
            tool_calls = response["tool_calls"]

            # 检查是否需要调用工具
            if finish_reason == "tool_calls" and tool_calls:
                # 添加assistant消息(包含tool_calls)
                tool_calls_formatted = []
                for tc in tool_calls:
                    tc_fmt = {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["arguments"], ensure_ascii=False)
                        }
                    }
                    # Pass through thought_signature (Gemini requires it
                    # for multi-turn function calling conversations).
                    if tc.get("thought_signature"):
                        tc_fmt["thought_signature"] = tc["thought_signature"]
                    tool_calls_formatted.append(tc_fmt)
                self.conversation_history.append({
                    "role": "assistant",
                    "content": content,
                    "tool_calls": tool_calls_formatted
                })
                # Save assistant message with tool calls to database
                self._save_message("assistant", content=content, tool_calls=tool_calls_formatted)

                # Notify intermediate text content (LLM may output text alongside tool calls)
                if content:
                    notify("text", {"content": content})

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
                    result = self._execute_tool(tool_name, tool_input, on_thinking)

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

                    # 检查是否有待确认操作或表单输入请求，如果有则立即返回，等待用户操作
                    if result.get("status") in ("pending_confirmation", "pending_performance_confirmation", "form_input_requested"):
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

