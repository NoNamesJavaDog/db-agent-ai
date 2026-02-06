# DB-Agent-AI 技术架构文档

## 概述

DB-Agent-AI 是一个基于大语言模型的数据库智能助手，采用**自研 Agent 框架**，无需依赖 LangChain、LlamaIndex 等第三方框架。本文档详细介绍框架的技术架构和运作原理。

---

## 目录

1. [整体架构](#整体架构)
2. [核心组件](#核心组件)
3. [运作流程](#运作流程)
4. [工具系统](#工具系统)
5. [安全机制](#安全机制)
6. [扩展机制](#扩展机制)
7. [与 LangChain 对比](#与-langchain-对比)

---

## 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                           用户输入                                   │
│                      "列出所有表并分析慢查询"                          │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         CLI 层 (app.py)                              │
│  • 接收输入 • 显示进度 • 处理确认 • 渲染输出                           │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Agent 核心 (agent.py)                            │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    chat() 主循环                             │    │
│  │  ┌─────────────────────────────────────────────────────┐    │    │
│  │  │ 1. 构建消息: system_prompt + conversation_history   │    │    │
│  │  │ 2. 检查上下文是否需要压缩                            │    │    │
│  │  │ 3. 调用 LLM API                                     │    │    │
│  │  │ 4. 解析响应 (tool_calls / stop / error)             │    │    │
│  │  │ 5. 如果有 tool_calls → 执行工具 → 继续循环           │    │    │
│  │  │ 6. 如果 stop → 返回最终响应                         │    │    │
│  │  └─────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
          │                           │                      │
          ▼                           ▼                      ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   LLM 客户端      │    │   数据库工具      │    │   审计日志        │
│ (OpenAI/Claude)  │    │ (PostgreSQL等)   │    │  (AuditService)  │
└──────────────────┘    └──────────────────┘    └──────────────────┘
```

### 目录结构

```
db_agent/
├── cli/                    # 命令行界面
│   └── app.py              # CLI 主入口
├── core/                   # 核心逻辑
│   ├── agent.py            # Agent 核心引擎
│   ├── database/           # 数据库工具
│   │   ├── base.py         # 基类
│   │   ├── postgresql.py   # PostgreSQL 实现
│   │   ├── mysql.py        # MySQL 实现
│   │   ├── gaussdb.py      # GaussDB 实现
│   │   ├── oracle.py       # Oracle 实现
│   │   └── sqlserver.py    # SQL Server 实现
│   ├── token_counter.py    # Token 计数
│   └── context_compression.py  # 上下文压缩
├── llm/                    # LLM 客户端
│   ├── base.py             # 抽象基类
│   ├── openai_compatible.py # OpenAI 兼容接口
│   ├── claude.py           # Claude 客户端
│   └── gemini.py           # Gemini 客户端
├── storage/                # 数据存储
│   ├── sqlite_storage.py   # SQLite 存储
│   ├── models.py           # 数据模型
│   └── audit.py            # 审计日志服务
├── mcp/                    # MCP 协议支持
└── skills/                 # 技能扩展
```

---

## 核心组件

### 1. SQLTuningAgent (agent.py)

Agent 核心类，负责：
- 管理对话历史
- 调用 LLM 并解析响应
- 执行工具调用
- 处理待确认操作
- 上下文压缩

```python
class SQLTuningAgent:
    def __init__(self, llm_client, db_config, storage, session_id):
        self.llm_client = llm_client          # LLM 客户端
        self.db_tools = DatabaseToolsFactory.create(db_type, db_config)  # 数据库工具
        self.conversation_history = []         # 对话历史
        self.pending_operations = []           # 待确认操作队列
        self.audit_service = AuditService(storage)  # 审计日志
        self.context_compressor = ContextCompressor(...)  # 上下文压缩
```

### 2. BaseLLMClient (llm/base.py)

LLM 客户端抽象接口，统一不同 LLM 提供商的调用方式：

```python
class BaseLLMClient(ABC):
    @abstractmethod
    def chat(self, messages: List[Dict], tools: List[Dict] = None) -> Dict:
        """
        统一返回格式:
        {
            "finish_reason": "tool_calls" | "stop" | "error",
            "content": "文本内容",
            "tool_calls": [{"id": "...", "name": "...", "arguments": {...}}]
        }
        """
        pass
```

支持的 LLM 提供商：
- OpenAI (GPT-4, GPT-3.5)
- Anthropic Claude
- Google Gemini
- DeepSeek
- Qwen (通义千问)
- Ollama (本地模型)

### 3. BaseDatabaseTools (core/database/base.py)

数据库工具抽象基类，定义统一的工具接口：

```python
class BaseDatabaseTools(ABC):
    @abstractmethod
    def list_tables(self, schema: str = None) -> Dict

    @abstractmethod
    def describe_table(self, table_name: str) -> Dict

    @abstractmethod
    def execute_sql(self, sql: str, confirmed: bool = False) -> Dict

    @abstractmethod
    def execute_safe_query(self, sql: str) -> Dict

    @abstractmethod
    def run_explain(self, sql: str, analyze: bool = False) -> Dict

    # ... 更多工具方法
```

### 4. AuditService (storage/audit.py)

审计日志服务，记录所有操作：

```python
class AuditService:
    def log_sql_execution(self, session_id, connection_id, sql, action, result_status, ...)
    def log_tool_call(self, session_id, connection_id, tool_name, parameters, result_status, ...)
    def log_config_change(self, action, target_type, target_name, ...)
    def get_logs_by_session(self, session_id, limit) -> List[AuditLog]
    def cleanup_old_logs(self, days: int = 30) -> int
```

---

## 运作流程

### 主循环流程

```python
def chat(self, user_message: str, max_iterations: int = 30):
    # 1️⃣ 添加用户消息到历史
    self.conversation_history.append({
        "role": "user",
        "content": user_message
    })

    # 2️⃣ 主循环（最多30轮工具调用）
    while iteration < max_iterations:

        # 3️⃣ 检查上下文是否过长，需要压缩
        if self.context_compressor.needs_compression(...):
            self._compress_context()

        # 4️⃣ 构建完整消息
        messages = [{"role": "system", "content": self.system_prompt}]
                   + self.conversation_history

        # 5️⃣ 调用 LLM
        response = self.llm_client.chat(messages=messages, tools=all_tools)

        # 6️⃣ 根据响应类型处理
        if finish_reason == "tool_calls":
            for tc in tool_calls:
                result = self._execute_tool(tc["name"], tc["arguments"])
                # 结果加入历史
                self.conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json.dumps(result)
                })
            # 继续循环

        elif finish_reason == "stop":
            # 返回最终响应
            return content
```

### 工具执行流程

```python
def _execute_tool(self, tool_name: str, tool_input: Dict):
    start_time = time.time()  # 计时（用于审计）

    # 路由到对应的工具实现
    if tool_name == "list_tables":
        result = self.db_tools.list_tables(**tool_input)
    elif tool_name == "execute_sql":
        result = self.db_tools.execute_sql(**tool_input)
        # 危险操作返回 pending_confirmation，等待用户确认
        if result.get("status") == "pending_confirmation":
            self.pending_operations.append(...)
    elif tool_name == "describe_table":
        result = self.db_tools.describe_table(**tool_input)
    # ... 更多工具

    # 记录审计日志
    self._log_tool_call(tool_name, tool_input, result, start_time)

    return result
```

### 完整对话示例

```
用户: "查看 users 表结构"

┌─ 第1轮 ─────────────────────────────────────────────────────────────┐
│ Messages 发送给 LLM:                                                │
│   [system]: "你是数据库专家..."                                      │
│   [user]: "查看 users 表结构"                                        │
│                                                                     │
│ LLM 响应:                                                           │
│   finish_reason: "tool_calls"                                       │
│   tool_calls: [{                                                    │
│     "name": "describe_table",                                       │
│     "arguments": {"table": "users"}                                 │
│   }]                                                                │
│                                                                     │
│ 执行工具: describe_table("users")                                   │
│ 结果: {"status": "success", "columns": [...], "indexes": [...]}     │
│                                                                     │
│ 工具结果加入历史，继续循环...                                         │
└─────────────────────────────────────────────────────────────────────┘

┌─ 第2轮 ─────────────────────────────────────────────────────────────┐
│ Messages 发送给 LLM:                                                │
│   [system]: "你是数据库专家..."                                      │
│   [user]: "查看 users 表结构"                                        │
│   [assistant]: (tool_calls)                                         │
│   [tool]: {"status": "success", "columns": [...]}                   │
│                                                                     │
│ LLM 响应:                                                           │
│   finish_reason: "stop"                                             │
│   content: "users 表包含以下字段：id (INTEGER), name (VARCHAR)..."   │
│                                                                     │
│ 返回最终响应给用户                                                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 工具系统

### 内置数据库工具

| 工具名 | 功能 | 是否需要确认 |
|--------|------|-------------|
| `list_tables` | 列出所有表 | 否 |
| `describe_table` | 查看表结构 | 否 |
| `get_sample_data` | 获取样本数据 | 否 |
| `execute_safe_query` | 执行 SELECT 查询 | 性能问题时需确认 |
| `execute_sql` | 执行任意 SQL | DDL/DML 需确认 |
| `run_explain` | 分析执行计划 | 否 |
| `check_index_usage` | 检查索引使用 | 否 |
| `get_table_stats` | 获取表统计 | 否 |
| `create_index` | 创建索引 | 是 |
| `analyze_table` | 分析表 | 否 |
| `identify_slow_queries` | 识别慢查询 | 否 |

### 工具定义格式

```python
{
    "type": "function",
    "function": {
        "name": "describe_table",
        "description": "查看表结构，包括列定义、索引、约束等",
        "parameters": {
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "表名"
                }
            },
            "required": ["table_name"]
        }
    }
}
```

### MCP 工具扩展

通过 Model Context Protocol (MCP) 支持外部工具扩展：

```python
if self.mcp_manager and self.mcp_manager.is_mcp_tool(tool_name):
    result = self.mcp_manager.call_tool_sync(tool_name, tool_input)
```

---

## 安全机制

### 1. 危险操作确认

对于 DDL/DML 操作，返回 `pending_confirmation` 状态，等待用户确认：

```python
def execute_sql(self, sql: str, confirmed: bool = False):
    if not confirmed and self._is_dangerous_sql(sql):
        return {
            "status": "pending_confirmation",
            "sql": sql,
            "message": "此操作需要确认"
        }
    # 执行 SQL...
```

### 2. 性能检查

对于可能影响性能的查询，进行预检查：

```python
def execute_safe_query(self, sql: str):
    perf_check = self.check_query_performance(sql)
    if perf_check.get("should_confirm"):
        return {
            "status": "pending_performance_confirmation",
            "issues": perf_check.get("issues")
        }
    # 执行查询...
```

### 3. 审计日志

所有操作记录到审计日志：

```python
# SQL 执行审计
self.audit_service.log_sql_execution(
    session_id=self.session_id,
    connection_id=self._connection_id,
    sql=sql,
    action="execute_sql",
    result_status="success",
    affected_rows=result.get("affected_rows"),
    execution_time_ms=execution_time,
    user_confirmed=True
)

# 工具调用审计
self.audit_service.log_tool_call(
    session_id=self.session_id,
    tool_name=tool_name,
    parameters=tool_input,
    result_status=result.get("status")
)
```

### 4. 参数脱敏

审计日志自动脱敏敏感参数：

```python
def _sanitize_parameters(self, params: Dict) -> Dict:
    sensitive_keys = {"password", "api_key", "secret", "token"}
    for key in params:
        if any(s in key.lower() for s in sensitive_keys):
            params[key] = "***"
    return params
```

---

## 扩展机制

### 1. 上下文压缩

当对话历史过长时，自动压缩：

```python
class ContextCompressor:
    def needs_compression(self, system_prompt, conversation_history) -> bool:
        total_tokens = self.token_counter.count_tokens(...)
        return total_tokens > self.max_context_tokens * 0.8

    def compress(self, conversation_history) -> str:
        # 使用 LLM 总结历史对话
        summary = self.llm_client.chat([
            {"role": "system", "content": "请总结以下对话..."},
            {"role": "user", "content": json.dumps(conversation_history)}
        ])
        return summary
```

### 2. 中断恢复

支持用户中断操作并恢复：

```python
def chat(self, user_message: str):
    while iteration < max_iterations:
        # 检查中断请求
        if self._interrupt_requested:
            self._interrupted_state = {
                "iteration": iteration,
                "original_message": original_message
            }
            return None

        # 恢复被中断的任务
        if self._interrupted_state:
            context_hint = "[之前的操作被中断]"
            full_message = f"{context_hint}\n{user_message}"
```

### 3. Skills 技能系统

支持注册自定义技能：

```python
class SkillRegistry:
    def register(self, name: str, skill: BaseSkill)
    def execute(self, name: str, arguments: str) -> Dict
```

---

## 与 LangChain 对比

| 维度 | 自研框架 | LangChain |
|------|----------|-----------|
| **架构复杂度** | 简单直接，约 2000 行核心代码 | 复杂抽象层，数万行代码 |
| **依赖数量** | 约 15 个直接依赖 | 100+ 依赖，常有冲突 |
| **学习成本** | 低，代码即文档 | 高，概念多 |
| **启动速度** | 快（< 1s） | 慢（依赖加载多） |
| **调试难度** | 易，调用栈清晰 | 难，抽象层多 |
| **定制灵活性** | 高，完全可控 | 中，受框架约束 |
| **生态丰富度** | 低，需自行实现 | 高，开箱即用 |

### 选择自研的理由

1. **专注单一领域** - 数据库操作场景明确，不需要通用抽象
2. **性能敏感** - 需要精细控制连接、Token、审计
3. **长期维护** - 避免 LangChain 频繁 breaking changes
4. **代码透明** - 出问题能快速定位和修复

---

## 附录

### 核心依赖

```
anthropic>=0.18.1      # Claude API
openai>=1.0.0          # OpenAI 兼容 API
google-generativeai    # Gemini API
pg8000                 # PostgreSQL 驱动
pymysql                # MySQL 驱动
oracledb               # Oracle 驱动
python-tds             # SQL Server 驱动
tiktoken               # Token 计数
mcp                    # Model Context Protocol
rich                   # CLI 渲染
prompt_toolkit         # CLI 输入
```

### 数据模型

```python
@dataclass
class AuditLog:
    id: Optional[int]
    session_id: Optional[int]
    connection_id: Optional[int]
    category: str           # sql_execute / tool_call / config_change
    action: str             # 具体操作
    target_type: Optional[str]
    target_name: Optional[str]
    sql_text: Optional[str]
    parameters: Optional[str]  # JSON
    result_status: str      # success / error / pending
    result_summary: Optional[str]
    affected_rows: Optional[int]
    execution_time_ms: Optional[int]
    user_confirmed: bool
    created_at: datetime
```

---

*文档版本: 1.0*
*最后更新: 2024*
