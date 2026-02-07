[English](README.md) | **中文**

<div align="center">

# DB Agent AI

### 开源 AI 原生数据库管理平台

> 用自然语言和数据库对话。查询、优化、迁移、管理 —— 横跨 5 大数据库引擎、6 大 LLM 厂商 —— 通过 CLI、Web UI、REST API 或 MCP 随心使用。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-3178C6.svg)](https://www.typescriptlang.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**支持的数据库**

[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-336791.svg)](https://postgresql.org)
[![MySQL](https://img.shields.io/badge/MySQL-5.7%20%7C%208.0-4479A1.svg)](https://mysql.com)
[![Oracle](https://img.shields.io/badge/Oracle-12c+-F80000.svg)](https://www.oracle.com/database/)
[![SQL Server](https://img.shields.io/badge/SQL%20Server-2014+-CC2927.svg)](https://www.microsoft.com/sql-server)
[![GaussDB](https://img.shields.io/badge/GaussDB-集中式%20%7C%20分布式-red.svg)](https://www.huaweicloud.com/product/gaussdb.html)

**支持的 LLM 厂商**

[![DeepSeek](https://img.shields.io/badge/DeepSeek-Chat-blue.svg)](https://deepseek.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991.svg)](https://openai.com)
[![Claude](https://img.shields.io/badge/Anthropic-Claude-orange.svg)](https://anthropic.com)
[![Gemini](https://img.shields.io/badge/Google-Gemini-4285F4.svg)](https://ai.google.dev)
[![Qwen](https://img.shields.io/badge/阿里云-通义千问-FF6A00.svg)](https://tongyi.aliyun.com)
[![Ollama](https://img.shields.io/badge/Ollama-本地部署-000000.svg)](https://ollama.ai)

</div>

---

## 为什么选择 DB Agent AI？

大部分数据库工具都要求你会写 SQL。DB Agent AI 彻底反转了这个模式 —— **你只需描述需求，AI 自动生成 SQL、安全执行、解释结果**。它不是简单的聊天包装器，而是一个拥有 20+ 数据库工具、安全防护、自愈式错误恢复的完整自主智能体。

| 能力维度 | 传统工具 | DB Agent AI |
|---|---|---|
| 查询数据 | 手写 SQL | "查一下上月各区域销售额" |
| 性能调优 | 自己读 EXPLAIN 计划 | AI 诊断 + 建议 + 自动建索引 |
| 表结构设计 | 手画 ER 图 | "帮我设计一个博客系统的表结构" |
| 数据库迁移 | 手写 DDL 转换脚本 | 一键跨库迁移，自动语法转换 |
| 错误处理 | 自己排查 | AI 自动分析错误并重试 |
| 多数据库 | 学各家方言 | 一个界面管 5 种数据库 |
| 结构化数据收集 | 手写表单代码 | AI 动态生成内联表单 |

---

## 平台全景

```
                         ┌──────────────────────────────────────┐
                         │       DB Agent AI 平台                │
                         └──────────────┬───────────────────────┘
                                        │
              ┌─────────────┬───────────┼───────────┬─────────────┐
              ▼             ▼           ▼           ▼             ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
        │   CLI    │ │  Web UI  │ │ REST API │ │   MCP    │ │  Skills  │
        │ (Rich)   │ │ (React)  │ │(FastAPI) │ │  服务器   │ │  引擎    │
        └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
             └─────────────┴────────────┴────────────┴────────────┘
                                        │
                              ┌─────────┴─────────┐
                              │  SQLTuningAgent    │
                              │  ┌───────────────┐ │
                              │  │ 工具注册中心    │ │  20+ 内置工具
                              │  │ 上下文管理      │ │  自动压缩
                              │  │ 安全防护层      │ │  写操作需确认
                              │  │ 错误自愈        │ │  智能重试
                              │  │ 审计日志        │ │  全链路追踪
                              │  └───────────────┘ │
                              └─────────┬──────────┘
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
             ┌────────────┐     ┌────────────┐     ┌────────────┐
             │ LLM 层     │     │ 数据库层    │     │ 存储层     │
             │ 6 大厂商    │     │ 5 大引擎    │     │ SQLite    │
             └────────────┘     └────────────┘     └────────────┘
```

---

## 十大核心能力

### 1. 多库统一，一个界面

连接 **PostgreSQL、MySQL、Oracle、SQL Server、GaussDB** —— 对话中随时切换。AI 自动检测数据库版本，生成兼容 SQL。

- **版本感知 SQL 生成** —— 绝不使用你数据库不支持的语法
- **热切换连接** —— 多数据库无需重启
- **跨库迁移** —— 任意两个数据库之间迁移对象
- **纯 Python 驱动** —— 无需 ODBC、Oracle Client 等外部依赖

### 2. 自主 AI 智能体（不只是聊天机器人）

DB Agent 是一个**工具调用智能体**，自主串联多步操作完成复杂任务：

```
你: "给账单系统生成 10000 条测试发票"

Agent: 1. describe_table → 了解表结构
       2. execute_sql   → 创建生成函数  [确认? ✓]
       3. execute_sql   → 调用函数      [确认? ✓]
       4. execute_safe_query → SELECT COUNT(*) 验证

       "已在 billing 表创建 10,000 条发票。
        总金额：¥4,523,891.50。全部验证通过。"
```

- **多步任务自动完成** —— 串联工具直到任务完成
- **错误自愈** —— 分析失败原因，自动调整 SQL 重试
- **上下文压缩** —— 长对话自动摘要，不怕超 token 限制
- **中断与恢复** —— 按 ESC 中断，随时继续或调整方向

### 3. 安全第一

每个危险操作都经过确认层：

```
Agent: 即将执行:
       DELETE FROM users WHERE last_login < '2023-01-01';
       将影响约 2,340 行。

       [执行] [跳过] [修改SQL]
```

- **写操作自动确认** —— INSERT / UPDATE / DELETE / DROP / CREATE 全需确认
- **性能预检** —— 执行前检测全表扫描等性能问题
- **只读快速通道** —— SELECT 查询无需确认直接执行
- **在线索引创建** —— 自动使用 `CONCURRENTLY` / `ONLINE` 避免锁表
- **全链路审计** —— 每条 SQL、每次工具调用、每次配置变更全部记录

### 4. 现代 Web UI（React + TypeScript）

全功能 Web 界面，实时流式交互：

- **SSE 流式对话** —— 实时看到 AI 思考过程
- **工具调用可视化** —— 每个工具执行状态实时展示
- **内联确认卡片** —— 在聊天中直接审批/拒绝 SQL
- **内联表单卡片** —— AI 可动态生成表单收集结构化数据
- **迁移向导** —— 可视化分步数据库迁移
- **迁移进度条** —— 实时迁移进度追踪
- **连接管理器** —— UI 中添加/编辑/测试数据库连接
- **模型管理器** —— 配置和切换 LLM 模型
- **MCP 服务管理** —— 添加和监控 MCP 工具服务
- **技能浏览器** —— 发现和调用 Skills
- **中英双语** —— 完整的中英文支持
- **8 个独立页面**：对话、连接、模型、会话、MCP、技能、迁移、设置

### 5. 跨库迁移引擎

在任意两个数据库之间迁移对象，智能 DDL 转换：

```
你: "把我的 Oracle 数据库迁移到 PostgreSQL"

Agent: [在聊天中展示迁移卡片]
       → 选择源库和目标库连接
       → 分析源库：7 个表、3 个视图、3 个存储过程、12 个索引
       → 自动转换 DDL 语法（NUMBER→INTEGER、SYSDATE→CURRENT_TIMESTAMP...）
       → 实时进度条执行迁移
       → 验证：比对源库和目标库
       → 生成迁移报告
```

**支持的对象类型：** 表、索引、视图、函数、存储过程、触发器、序列、约束

**全路径支持：**
| 从 \ 到 | PostgreSQL | MySQL | Oracle | SQL Server | GaussDB |
|---|---|---|---|---|---|
| **PostgreSQL** | — | ✓ | ✓ | ✓ | ✓ |
| **MySQL** | ✓ | — | ✓ | ✓ | ✓ |
| **Oracle** | ✓ | ✓ | — | ✓ | ✓ (专项优化) |
| **SQL Server** | ✓ | ✓ | ✓ | — | ✓ |
| **GaussDB** | ✓ | ✓ | ✓ | ✓ | — |

Oracle → GaussDB 迁移内置**专家级转换规则**，覆盖高级包替换（DBMS_LOB→DBE_LOB 等）、数据类型边界情况、PL/SQL 差异和语法陷阱。

### 6. MCP 集成（Model Context Protocol）

通过开放的 MCP 标准扩展 DB Agent 外部工具能力：

**作为 MCP 客户端** —— 连接外部 MCP 服务器：
```
/mcp add filesystem npx -y @modelcontextprotocol/server-filesystem /tmp
→ AI 现在可以读写文件、列出目录
```

**作为 MCP 服务器** —— 将 DB Agent 工具暴露给 Claude Desktop 或任何 MCP 客户端：
```json
{
  "mcpServers": {
    "db-agent": {
      "command": "python",
      "args": ["-m", "db_agent.mcp.server", "--db-type", "postgresql", "--host", "localhost", "--database", "mydb"]
    }
  }
}
```

暴露 10 个数据库工具：`list_tables`、`describe_table`、`get_sample_data`、`execute_query`、`run_explain`、`identify_slow_queries`、`get_table_stats`、`check_index_usage`、`get_running_queries`、`get_db_info`

### 7. Skills 技能系统（兼容 Claude Code）

通过可复用的指令集扩展 AI 能力 —— 兼容 Claude Code 技能格式：

**8 个内置技能：**

| 技能 | 命令 | 说明 |
|---|---|---|
| 数据库健康检查 | `/db-health-check` | 全面诊断：慢查询、膨胀、索引、存储 |
| 索引顾问 | `/index-advisor` | 分析索引使用、发现缺失/冗余索引、推荐优化 |
| SQL 代码审查 | `/sql-review` | 性能问题、安全漏洞、最佳实践违规 |
| 查询分析报告 | `/query-report` | 深度执行计划分析与优化建议 |
| 表文档生成 | `/table-docs` | 自动生成 Markdown 格式的表结构文档 |
| 迁移预检 | `/migration-precheck` | 跨库迁移前的兼容性评估 |
| QuickBooks 财务 | `/quickbooks-finance` | 全套财务管理：应收/应付、总账、库存、报表 |
| DB Agent (Claude Code) | `/db-agent` | 在 Claude Code 中使用 DB Agent |

**创建自定义技能** —— 只需添加一个 `SKILL.md` 文件：

```markdown
---
name: my-audit
description: 对数据库执行安全审计
user-invocable: true
---
# 安全审计
1. 检查默认密码
2. 审查权限授予
3. 扫描 SQL 注入风险
关注领域: $ARGUMENTS
```

### 8. 内联表单卡片

当 AI 需要用户提供结构化数据时，动态生成嵌入聊天的表单卡片：

```
你: "我要报销"

Agent: [展示表单卡片]
       ┌─────────────────────────────────┐
       │ 报销申请                         │
       │                                 │
       │ 日期:        [2024-01-20    ]   │
       │ 金额:        [              ]   │
       │ 类别:        [交通费        ▼] │
       │ 说明:        [              ]   │
       │                                 │
       │ [提交]  [取消]                   │
       └─────────────────────────────────┘

→ 用户填写表单 → 数据发送给 AI → AI 处理结构化数据
```

支持字段类型：text、number、select、textarea、date。AI 根据上下文自行判断何时显示什么表单。

### 9. 三端合一：CLI + Web + API

**CLI** —— 富文本终端 UI，支持命令历史、方向键导航、内联选择菜单：
```bash
python main.py
```

**Web UI** —— 现代 React SPA，实时 SSE 流式交互：
```bash
PORT=8000 python -m db_agent.api.server
# 打开 http://localhost:8000
```

**REST API** —— 完整 v2 API，支持编程集成：
```bash
# SSE 流式对话
curl -N -X POST http://localhost:8000/api/v2/chat/1/message \
  -H "Content-Type: application/json" \
  -d '{"message": "列出所有表"}'
```

### 10. 企业级能力

- **审计日志** —— 每条 SQL 执行、工具调用、配置变更全部带时间戳记录
- **会话持久化** —— 对话跨重启保留，SQLite 存储
- **密码加密** —— 所有数据库密码和 API Key 加密存储
- **上下文压缩** —— 自动摘要，支持无限长度对话
- **中英双语 i18n** —— CLI、Web、API 全链路双语支持
- **离线部署** —— 支持 PyInstaller 打包，适用于内网环境

---

## 快速开始

### 环境要求

- Python 3.8+
- 以下数据库之一：PostgreSQL 12+、MySQL 5.7+、Oracle 12c+、SQL Server 2014+、GaussDB
- 至少一个 LLM API Key（或使用 Ollama 免费本地部署）

### 安装

```bash
# 克隆
git clone https://github.com/NoNamesJavaDog/db-agent-ai.git
cd db-agent-ai

# 安装依赖
pip install -r requirements.txt

# 配置
cp config/config.ini.example config/config.ini
# 编辑 config/config.ini 填写数据库和 LLM 凭据

# 启动 CLI
python main.py

# 或启动 Web UI + API
PORT=8000 python -m db_agent.api.server
```

### 最简配置

```ini
[database]
type = postgresql
host = localhost
port = 5432
database = mydb
user = postgres
password = secret

[llm]
default_provider = deepseek

[deepseek]
api_key = sk-your-key
model = deepseek-chat
```

---

## LLM 模型支持

| 厂商 | 默认模型 | 成本 | 适用场景 |
|---|---|---|---|
| **DeepSeek** | deepseek-chat | 低 | 性价比之王，SQL 理解力强 |
| **OpenAI** | gpt-4o | 中 | 知识面广，工具调用稳定 |
| **Claude** | claude-sonnet-4-20250514 | 中 | 复杂推理，详细解释 |
| **Gemini** | gemini-2.0-flash | 低 | 响应快速，多模态 |
| **通义千问** | qwen-turbo | 低 | 中文理解力强 |
| **Ollama** | llama2 | 免费 | 隐私优先，离线部署 |

通过 CLI (`/model`)、Web UI 或 API 随时切换模型。

---

## 数据库驱动说明

| 数据库 | 驱动 | 安装 | 说明 |
|---|---|---|---|
| PostgreSQL | pg8000 | 已包含 | 纯 Python，无外部依赖 |
| MySQL | pymysql | 已包含 | 纯 Python |
| Oracle | oracledb | `pip install oracledb` | Thin 模式，无需 Oracle Client。仅支持 12c+ |
| SQL Server | pytds | `pip install python-tds` | 纯 Python，无需 ODBC。支持 2014+ 和 Azure SQL |
| GaussDB | pg8000 | 已包含 | 支持 SHA256 认证。自动检测集中式/分布式模式 |

---

## 20+ 内置工具

### 数据与结构工具
| 工具 | 说明 |
|---|---|
| `list_tables` | 列出所有表及大小 |
| `describe_table` | 列定义、约束、索引 |
| `get_sample_data` | 预览表数据 |
| `execute_sql` | 执行任意 SQL（需确认） |
| `execute_safe_query` | 执行只读查询（无需确认） |
| `list_databases` | 列出服务器上所有数据库 |
| `switch_database` | 切换到同实例的另一个数据库 |

### 性能与优化工具
| 工具 | 说明 |
|---|---|
| `run_explain` | 分析执行计划（支持 ANALYZE） |
| `identify_slow_queries` | 按耗时阈值查找慢查询 |
| `get_running_queries` | 显示当前正在执行的查询 |
| `check_index_usage` | 分析索引利用率 |
| `get_table_stats` | 表统计信息、膨胀、死元组 |
| `create_index` | 创建索引（支持在线模式） |
| `analyze_table` | 更新表统计信息 |

### 迁移工具
| 工具 | 说明 |
|---|---|
| `analyze_source_database` | 扫描源库对象 |
| `create_migration_plan` | 生成 DDL 转换计划 |
| `execute_migration_batch` | 批量执行迁移项 |
| `compare_databases` | 验证源库/目标库一致性 |
| `generate_migration_report` | 生成详细迁移报告 |
| `request_migration_setup` | 触发迁移配置 UI |

### 交互工具
| 工具 | 说明 |
|---|---|
| `request_user_input` | 显示动态内联表单收集结构化数据 |

### 通过 MCP 和 Skills 扩展
MCP 服务器工具和技能工具自动加入智能体工具箱。

---

## CLI 命令

| 命令 | 说明 |
|---|---|
| `/help` | 显示帮助 |
| `/connections` | 列出数据库连接 |
| `/connection add` | 添加新连接 |
| `/connection use <名称>` | 切换数据库 |
| `/providers` | 列出 LLM 模型 |
| `/provider add` | 添加新模型 |
| `/model` | 快速切换模型 |
| `/sessions` | 列出会话 |
| `/session new` | 新建会话 |
| `/session use <id>` | 切换会话 |
| `/migrate` | 迁移向导（文件或在线） |
| `/file <路径>` | 加载 SQL 文件 |
| `/mcp list` | 列出 MCP 服务器 |
| `/mcp add` | 添加 MCP 服务器 |
| `/mcp tools` | 显示 MCP 工具 |
| `/skills` | 列出可用技能 |
| `/<技能名>` | 调用技能 |
| `/language` | 切换中/英文 |
| `/reset` | 重置对话 |
| `/exit` | 退出 |

---

## API 参考

### V2 API 端点

| 分类 | 方法 | 路径 | 说明 |
|---|---|---|---|
| **对话** | POST | `/api/v2/chat/{id}/message` | SSE 流式对话 |
| | POST | `/api/v2/chat/{id}/confirm` | 确认待执行 SQL |
| | POST | `/api/v2/chat/{id}/confirm-all` | 确认全部 |
| | POST | `/api/v2/chat/{id}/skip-all` | 跳过全部 |
| | POST | `/api/v2/chat/{id}/submit-form` | 提交内联表单数据 |
| | POST | `/api/v2/chat/{id}/interrupt` | 中断 AI |
| | POST | `/api/v2/chat/{id}/upload` | 上传 SQL 文件 |
| | POST | `/api/v2/chat/{id}/start-migration` | 启动迁移 |
| **连接** | GET/POST | `/api/v2/connections` | 列出/创建 |
| | GET/PUT/DELETE | `/api/v2/connections/{id}` | 查看/更新/删除 |
| | POST | `/api/v2/connections/{id}/test` | 测试连接 |
| **模型** | GET/POST | `/api/v2/providers` | 列出/创建 |
| | GET/PUT/DELETE | `/api/v2/providers/{id}` | 查看/更新/删除 |
| **会话** | GET/POST | `/api/v2/sessions` | 列出/创建 |
| | GET/DELETE | `/api/v2/sessions/{id}` | 查看/删除 |
| | GET | `/api/v2/sessions/{id}/messages` | 获取历史 |
| **MCP** | GET/POST | `/api/v2/mcp/servers` | 列出/添加服务器 |
| | DELETE | `/api/v2/mcp/servers/{name}` | 移除服务器 |
| | GET | `/api/v2/mcp/tools` | 列出所有工具 |
| **技能** | GET | `/api/v2/skills` | 列出技能 |
| | GET | `/api/v2/skills/{name}` | 技能详情 |
| **迁移** | GET | `/api/v2/migration/tasks` | 列出任务 |
| | GET | `/api/v2/migration/tasks/{id}` | 任务详情 |
| **设置** | GET/PUT | `/api/v2/settings` | 获取/更新设置 |
| **审计** | GET | `/api/v2/audit/logs` | 查询审计日志 |
| **健康** | GET | `/api/v2/health` | 服务健康检查 |

启动服务后访问 `http://localhost:8000/docs` 查看完整 Swagger 文档。

---

## SSE 事件协议

对话端点通过 Server-Sent Events 流式返回：

| 事件 | 数据 | 说明 |
|---|---|---|
| `tool_call` | `{name, input}` | 工具开始执行 |
| `tool_result` | `{name, status, summary}` | 工具执行完成 |
| `text_delta` | `{content}` | AI 文本增量 |
| `pending` | `{index, type, sql}` | SQL 等待用户确认 |
| `form_input` | `{title, description, fields}` | 内联表单请求 |
| `migration_setup` | `{reason, suggested_*}` | 迁移配置请求 |
| `migration_progress` | `{task_id, total, completed, ...}` | 迁移进度更新 |
| `done` | `{has_pending, pending_count}` | 流结束 |
| `error` | `{message}` | 错误发生 |

---

## 项目结构

```
db-agent-ai/
├── db_agent/
│   ├── core/                           # 核心 AI 引擎
│   │   ├── agent.py                    # SQLTuningAgent — 大脑
│   │   ├── tool_registry.py            # 20+ 工具定义（含 i18n）
│   │   ├── prompt_builder.py           # 动态系统提示词构建
│   │   ├── migration_handler.py        # 跨库迁移引擎
│   │   ├── migration_rules.py          # DDL 转换规则（Oracle→GaussDB 等）
│   │   ├── context_compression.py      # 长对话自动摘要
│   │   ├── token_counter.py            # 模型感知 Token 计算
│   │   └── database/                   # 数据库抽象层
│   │       ├── base.py                 # 抽象接口
│   │       ├── postgresql.py           # PostgreSQL 实现
│   │       ├── mysql.py                # MySQL 实现
│   │       ├── oracle.py               # Oracle 实现
│   │       ├── sqlserver.py            # SQL Server 实现
│   │       ├── gaussdb.py              # GaussDB 实现
│   │       └── factory.py              # 数据库工厂
│   ├── llm/                            # LLM 层
│   │   ├── base.py                     # 抽象 LLM 客户端
│   │   ├── openai_compatible.py        # OpenAI / DeepSeek / 千问 / Ollama
│   │   ├── claude.py                   # Anthropic Claude
│   │   ├── gemini.py                   # Google Gemini
│   │   └── factory.py                  # LLM 工厂
│   ├── api/                            # REST API 层
│   │   ├── server.py                   # FastAPI 应用
│   │   └── v2/                         # V2 API
│   │       ├── app.py                  # 路由配置
│   │       ├── models.py               # Pydantic 模型
│   │       ├── deps.py                 # 依赖注入
│   │       └── routes/                 # 端点模块
│   │           ├── chat.py             # SSE 流式对话
│   │           ├── connections.py      # 连接 CRUD
│   │           ├── providers.py        # 模型 CRUD
│   │           ├── sessions.py         # 会话管理
│   │           ├── mcp.py              # MCP 管理
│   │           ├── skills.py           # 技能管理
│   │           ├── migration.py        # 迁移管理
│   │           ├── settings.py         # 设置
│   │           ├── audit.py            # 审计日志
│   │           └── health.py           # 健康检查
│   ├── cli/                            # 交互式 CLI
│   │   ├── app.py                      # CLI 主程序
│   │   ├── ui.py                       # UI 工具
│   │   ├── config.py                   # 配置管理
│   │   └── commands/                   # 命令模块
│   │       ├── connections.py          # 连接命令
│   │       ├── providers.py            # 模型命令
│   │       ├── sessions.py             # 会话命令
│   │       ├── mcp.py                  # MCP 命令
│   │       ├── skills.py              # 技能命令
│   │       └── migration.py            # 迁移命令
│   ├── mcp/                            # MCP 集成
│   │   ├── client.py                   # MCP 客户端
│   │   ├── manager.py                  # 多服务器管理
│   │   ├── server.py                   # 作为 MCP 服务器暴露
│   │   └── errors.py                   # 错误定义
│   ├── skills/                         # Skills 技能系统
│   │   ├── models.py                   # 技能数据模型
│   │   ├── parser.py                   # SKILL.md 解析器
│   │   ├── loader.py                   # 文件系统加载
│   │   ├── registry.py                 # 技能注册中心
│   │   └── executor.py                 # 技能执行器
│   ├── storage/                        # 数据持久化
│   │   ├── sqlite_storage.py           # SQLite 存储引擎
│   │   ├── models.py                   # 数据模型
│   │   ├── audit.py                    # 审计服务
│   │   └── encryption.py              # 密码加密
│   └── i18n/                           # 国际化
│       └── translations.py             # 中英文翻译
├── web/                                # React Web UI
│   └── src/
│       ├── pages/                      # 8 个页面组件
│       ├── components/chat/            # 聊天 UI 组件
│       ├── stores/                     # Zustand 状态管理
│       ├── hooks/                      # 自定义 Hooks（SSE 等）
│       ├── api/                        # API 客户端层
│       ├── i18n/                       # 前端翻译
│       └── types/                      # TypeScript 类型定义
├── .claude/skills/                     # 8 个内置技能
├── scripts/                            # 构建和部署脚本
├── main.py                             # CLI 入口
└── requirements.txt                    # Python 依赖
```

---

## 部署方式

### 开发环境
```bash
python main.py                              # CLI 模式
PORT=8000 python -m db_agent.api.server     # Web + API 模式
```

### 生产环境（独立可执行文件）
```bash
pip install pyinstaller
scripts/build_package.sh    # 或 Windows 用 .bat
# 输出：dist/db-agent/ — 复制到目标机器，无需 Python
```

### 离线部署（内网）
```bash
scripts/download_deps.bat   # 下载所有 wheel 包
# 复制到目标机器 → install_offline.bat → 运行
```

### 作为 MCP 服务器（Claude Desktop）
```json
{
  "mcpServers": {
    "db-agent": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "db_agent.mcp.server", "--use-active"],
      "env": { "DB_PASSWORD": "secret" }
    }
  }
}
```

---

## 安全机制

- **写操作确认** —— 所有非 SELECT 操作需用户明确同意
- **性能预检** —— 检测并预警潜在高耗查询
- **凭据加密** —— 数据库密码和 API Key 在 SQLite 中加密存储
- **只读快速通道** —— SELECT / SHOW / DESCRIBE / EXPLAIN 无需确认
- **在线 DDL** —— 索引创建使用 online 模式避免锁表
- **全链路审计** —— 每个操作记录会话、时间戳和结果
- **数据不外泄** —— API Key 仅存本地，绝不发送给第三方

---

## 常见问题

**Q: 会不会误删数据？**
A: 不会。所有 INSERT/UPDATE/DELETE/DROP 操作都需确认，你能看到完整 SQL 再决定执行。

**Q: 能不能离线使用？**
A: 可以 —— LLM 用 Ollama 本地模型，部署用独立可执行文件。

**Q: 支持同时管理多个数据库吗？**
A: 支持。通过 CLI 或 Web UI 添加多个连接，对话中随时切换 `/connection use <名称>` 或用 `switch_database` 工具。

**Q: 长对话怎么处理？**
A: 自动上下文压缩。当对话接近模型 token 限制时，自动摘要旧消息释放空间，同时保留重要上下文。

**Q: 用哪个 LLM 效果最好？**
A: DeepSeek 性价比最高。Claude 和 GPT-4o 质量最好。Ollama 免费离线部署。

**Q: 能自定义扩展吗？**
A: 能 —— 通过 MCP 服务器（任何 MCP 兼容工具服务）或 Skills（SKILL.md 自定义指令文件）。

---

## 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改
4. Push 并发起 Pull Request

---

## 开源协议

MIT License — 详见 [LICENSE](LICENSE)

---

## 联系

- Issue: [GitHub Issues](https://github.com/NoNamesJavaDog/db-agent-ai/issues)
- 邮箱: 1057135186@qq.com

---

<div align="center">
  <b>别写 SQL 了，直接跟数据库说话。</b>
  <br><br>
  <sub>Built with care by the DB Agent Team</sub>
</div>
