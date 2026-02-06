[English](README.md) | **中文**

# DB Agent - 数据库智能助手

> **让 DBA 失业的 AI 数据库管理专家** —— 自然语言操作数据库，SQL 优化、性能诊断、数据管理一句话搞定

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-336791.svg)](https://postgresql.org)
[![MySQL](https://img.shields.io/badge/MySQL-5.7%20%7C%208.0-4479A1.svg)](https://mysql.com)
[![Oracle](https://img.shields.io/badge/Oracle-12c+-F80000.svg)](https://www.oracle.com/database/)
[![SQL Server](https://img.shields.io/badge/SQL%20Server-2014+-CC2927.svg)](https://www.microsoft.com/sql-server)
[![GaussDB](https://img.shields.io/badge/GaussDB-集中式%20%7C%20分布式-red.svg)](https://www.huaweicloud.com/product/gaussdb.html)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📖 目录

- [产品介绍](#-产品介绍)
- [核心功能](#-核心功能)
- [系统架构](#-系统架构)
- [安装部署](#-安装部署)
- [快速开始](#-快速开始)
- [使用场景](#-使用场景)
- [MCP 集成](#-mcp-集成)
- [Skills 技能系统](#-skills-技能系统)
- [配置说明](#-配置说明)
- [API 服务](#-api-服务)
- [常见问题](#-常见问题)

---

## 🎯 产品介绍

**DB Agent** 是一款革命性的 AI 数据库管理助手，它将复杂的数据库操作转化为简单的自然语言对话。无论你是开发者、数据分析师还是产品经理，都可以通过与 AI 对话的方式完成数据库的增删改查、性能优化、结构设计等工作。

### 为什么选择 DB Agent？

| 传统 DBA 方式 | DB Agent 方式 |
|--------------|---------------|
| 需要精通 SQL 语法 | 用自然语言描述需求 |
| 手动分析执行计划 | AI 自动诊断性能问题 |
| 查阅文档编写复杂查询 | 一句话生成优化 SQL |
| 需要了解表结构才能操作 | AI 自动探索数据库结构 |
| 索引优化需要丰富经验 | 智能推荐最佳索引策略 |
| 手动转换异构数据库 DDL | AI 自动转换并执行对象迁移 |
| 7x24 小时待命 | AI 永不疲倦随时响应 |

### 核心优势

- **🧠 智能理解** - 基于大语言模型，真正理解你的意图
- **🔒 安全可控** - 危险操作需二次确认，杜绝误操作
- **🔄 错误恢复** - 自动分析执行失败原因，智能调整策略重试
- **🌍 多模型支持** - 支持 DeepSeek、OpenAI、Claude、Gemini、通义千问等主流模型
- **🇨🇳 中英双语** - 完美支持中文交互，告别语言障碍
- **📊 版本感知** - 自动识别数据库版本，生成兼容的 SQL
- **⚡ 实时反馈** - 工具调用过程透明可见，执行结果即时展示
- **💾 会话管理** - 基于 SQLite 的对话历史持久化存储
- **🔌 多连接管理** - 支持多个数据库连接，随时切换
- **🔧 MCP 集成** - 通过 Model Context Protocol 扩展外部工具能力
- **📦 Skills 系统** - 兼容 Claude Code 的技能系统，支持自定义工作流

---

## 🚀 核心功能

### 1. 数据查询与操作
```
👤 用户: 查看 users 表里上个月注册的用户有多少
🤖 Agent: 正在查询... 上个月共有 1,234 位新用户注册

👤 用户: 把状态为 inactive 且超过一年没登录的用户标记为 archived
🤖 Agent: 这个操作会影响 856 条记录，确认执行吗？[是/否]
```

### 2. 表结构管理
```
👤 用户: 帮我创建一个商品表，包含名称、价格、库存、分类
🤖 Agent: 好的，我来创建 products 表...
         [展示建表 SQL，等待确认]

👤 用户: 给 orders 表加一个 shipping_address 字段
🤖 Agent: 已添加 shipping_address 字段 (VARCHAR(500))
```

### 3. 性能诊断与优化
```
👤 用户: 这个查询很慢，帮我分析一下：SELECT * FROM orders WHERE user_id = 123
🤖 Agent: 分析结果：
         ❌ 问题：user_id 列缺少索引，导致全表扫描
         ✅ 建议：CREATE INDEX idx_orders_user_id ON orders(user_id)
         📈 预期提升：查询速度提升 50-100 倍
```

### 4. 索引管理
```
👤 用户: 检查 orders 表的索引使用情况
🤖 Agent: 发现 3 个索引：
         ✅ idx_orders_pkey - 使用频繁 (125,000 次扫描)
         ✅ idx_orders_user_id - 使用正常 (45,000 次扫描)
         ⚠️ idx_orders_old_status - 从未使用，建议删除 (节省 128MB)
```

### 5. 数据库健康检查
```
👤 用户: 检查数据库的整体健康状态
🤖 Agent: 健康报告：
         📊 表数量：23 个
         💾 总大小：4.5 GB
         ⚠️ 发现 3 个表有大量死元组，建议执行 VACUUM
         ⚠️ 有 2 个慢查询需要优化
```

### 6. 在线数据库迁移
```
👤 用户: /migrate
[选择: 2. 在线迁移]
[选择源数据库: mysql-test]

🤖 Agent: 正在分析源数据库 mysql-test...
         发现 7 个表, 3 个视图, 3 个存储过程, 3 个函数, 3 个触发器

         迁移计划：
         | # | 类型 | 对象 | 状态 |
         |---|------|------|------|
         | 1 | 表 | users | 待执行 |
         | 2 | 表 | departments | 待执行 |
         | ... | ... | ... | ... |

         确认执行迁移？[是/否]

👤 用户: 是

🤖 Agent: 正在执行迁移...
         ✓ 创建表 users
         ✓ 创建表 departments
         ✓ 创建表 employees
         ...
         迁移完成：19/19 个对象迁移成功
```

---

## 🏗 系统架构

```
┌───────────────────────────────────────────────────────────────────────┐
│                              DB Agent                                  │
├───────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                    │
│  │   CLI 界面   │  │  API 服务   │  │  Web 界面   │                    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                    │
│         │                │                │                            │
│         └────────────────┼────────────────┘                            │
│                          ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                       SQLTuningAgent                             │  │
│  │  ┌───────────┐  ┌───────────┐  ┌─────────────┐  ┌────────────┐  │  │
│  │  │ 对话管理器 │  │ 工具执行器 │  │ 安全确认机制 │  │ Skills引擎 │  │  │
│  │  └───────────┘  └───────────┘  └─────────────┘  └────────────┘  │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                          │                                             │
│  ┌───────────┬───────────┼───────────┬───────────┬───────────┬─────┐  │
│  ▼           ▼           ▼           ▼           ▼           ▼     │  │
│┌───────┐ ┌────────┐ ┌─────────┐ ┌───────┐ ┌──────────┐ ┌────────┐  │  │
││  LLM  │ │数据库  │ │   MCP   │ │ 国际化 │ │ 数据存储  │ │ Skills │  │  │
││ 客户端 │ │  工具  │ │ 管理器  │ └───────┘ │ ──────── │ │ 注册表 │  │  │
││───────│ │────────│ │─────────│           │ SQLite   │ │────────│  │  │
││DeepSk │ │• 查询  │ │服务器:  │           │ • 会话   │ │• 个人  │  │  │
││OpenAI │ │• 结构  │ │• fs     │           │ • 消息   │ │• 项目  │  │  │
││Claude │ │• 索引  │ │• fetch  │           │ • 连接   │ │        │  │  │
││Gemini │ │• 迁移  │ │• custom │           │ • 任务   │ │        │  │  │
││Qwen   │ └────────┘ └─────────┘           └──────────┘ └────────┘  │  │
││Ollama │      │                                                     │  │
│└───────┘      ▼                                                     │  │
│         ┌─────────────┐                                             │  │
│         │ PostgreSQL  │                                             │  │
│         │   MySQL     │                                             │  │
│         │   Oracle    │                                             │  │
│         │ SQL Server  │                                             │  │
│         │   GaussDB   │                                             │  │
│         └─────────────┘                                             │  │
└───────────────────────────────────────────────────────────────────────┘
```

### 项目结构

```
ai_agent/
├── db_agent/                      # 主程序包
│   ├── __init__.py                # 包导出
│   ├── core/                      # 核心组件
│   │   ├── agent.py               # SQLTuningAgent 智能体
│   │   ├── migration_rules.py     # DDL 转换规则
│   │   └── database/              # 数据库抽象层
│   │       ├── base.py            # 基类（接口定义）
│   │       ├── postgresql.py      # PostgreSQL 实现
│   │       ├── mysql.py           # MySQL 实现
│   │       ├── oracle.py          # Oracle 实现（12c+）
│   │       ├── sqlserver.py       # SQL Server 实现（2014+）
│   │       ├── gaussdb.py         # GaussDB 实现（集中式/分布式）
│   │       └── factory.py         # 数据库工具工厂
│   ├── llm/                       # LLM 客户端
│   │   ├── base.py                # 基类
│   │   ├── openai_compatible.py   # OpenAI/DeepSeek/Qwen/Ollama
│   │   ├── claude.py              # Anthropic Claude
│   │   ├── gemini.py              # Google Gemini
│   │   └── factory.py             # 客户端工厂
│   ├── mcp/                       # MCP（Model Context Protocol）
│   │   ├── __init__.py            # 包导出
│   │   └── manager.py             # MCP 服务器管理
│   ├── skills/                    # Skills 技能系统（兼容 Claude Code）
│   │   ├── __init__.py            # 包导出
│   │   ├── models.py              # 技能数据模型
│   │   ├── parser.py              # SKILL.md 解析器
│   │   ├── loader.py              # 技能加载器
│   │   ├── registry.py            # 技能注册中心
│   │   └── executor.py            # 技能执行器
│   ├── storage/                   # 数据持久化（SQLite）
│   │   ├── __init__.py            # 包导出
│   │   ├── models.py              # 数据模型（会话、消息、连接等）
│   │   ├── sqlite_storage.py      # SQLite 存储实现
│   │   └── encryption.py          # 密码加密工具
│   ├── api/                       # API 服务
│   │   └── server.py              # FastAPI 应用
│   ├── cli/                       # 命令行界面
│   │   ├── app.py                 # CLI 应用
│   │   └── config.py              # 配置管理
│   └── i18n/                      # 国际化
│       └── translations.py        # 翻译文件
├── .claude/                       # 项目级技能
│   └── skills/                    # 技能目录
│       └── <skill-name>/          # 每个技能一个文件夹
│           └── SKILL.md           # 技能定义文件
├── scripts/                       # 启动脚本
│   ├── start.sh                   # Linux/macOS
│   └── start.bat                  # Windows
├── examples/                      # 示例代码
│   └── examples.py
├── main.py                        # 程序入口
├── requirements.txt               # 依赖清单
└── README.md                      # 说明文档
```

---

## 📦 安装部署

### 环境要求

- Python 3.8+
- PostgreSQL 12+、MySQL 5.7/8.0、Oracle 12c+、SQL Server 2014+ 或 GaussDB（集中式/分布式）
- 至少一个 LLM API Key（DeepSeek / OpenAI / Claude 等）

> **GaussDB 用户注意：** GaussDB 使用 pg8000 驱动（支持 sha256 认证）。Linux（欧拉系统）也可使用华为提供的专用驱动。详见 [GaussDB 配置](#gaussdb华为) 章节。

> **Oracle 用户注意：** 使用 `oracledb` Thin 模式（Oracle 官方 Python 驱动）- 无需安装 Oracle Client。支持 Oracle 12c 及以上版本（12.1、12.2、18c、19c、21c、23c）。不支持 Oracle 11g。

> **SQL Server 用户注意：** 使用 `pytds` (python-tds) - 纯 Python 驱动，无需安装 ODBC。支持 SQL Server 2014 至 2022 及 Azure SQL Database。Query Store 功能需要 SQL Server 2016+。

### 方式一：直接安装

```bash
# 1. 克隆项目
git clone https://github.com/NoNamesJavaDog/db-agent-ai.git
cd db-agent

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置
cp config/config.ini.example config/config.ini
# 编辑 config/config.ini，填写数据库连接信息和 API Key

# 4. 启动
python main.py
```

### 方式二：使用启动脚本

**Linux / macOS:**
```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

**Windows:**
```cmd
scripts\start.bat
```

### 依赖清单

```
requirements.txt
├── pg8000           # PostgreSQL/GaussDB 驱动（支持 sha256 认证）
├── pymysql          # MySQL 驱动
├── oracledb         # Oracle 驱动（Thin 模式，无需客户端）
├── python-tds       # SQL Server 驱动（纯 Python，无需 ODBC）
├── pydantic         # 数据验证（>=2.10.0 支持 Python 3.13）
├── openai           # OpenAI/DeepSeek API
├── anthropic        # Claude API
├── google-generativeai  # Gemini API
├── rich             # 终端美化
├── prompt-toolkit   # 命令行增强
├── fastapi          # API 服务
└── uvicorn          # ASGI 服务器
```

### 方式三：内网离线部署

适用于无法访问外网的内网环境。

#### 方案 A：打包成独立可执行文件（推荐）

无需在目标机器安装 Python，直接运行 exe 文件。

**在联网机器上打包：**
```bash
# 1. 安装 PyInstaller
pip install pyinstaller

# 2. 运行打包脚本
scripts\build_package.bat      # Windows
# 或
./scripts/build_package.sh     # Linux/macOS
```

**打包输出：**
```
dist/db-agent/
├── db-agent.exe          # 主程序（Windows）或 db-agent（Linux）
├── config/
│   └── config.ini.example
└── ... (运行时依赖)
```

**部署到目标机器：**
1. 将 `dist/db-agent/` 整个文件夹复制到目标机器
2. 编辑 `config/config.ini` 配置数据库和 API Key
3. 运行 `db-agent.exe`

#### 方案 B：离线 pip 安装

目标机器需要有 Python 环境，但无需联网。

**在联网机器上下载依赖：**
```bash
scripts\download_deps.bat      # Windows
```

**打包内容：**
```
项目目录/
├── vendor/               # 所有依赖的 wheel 包
├── requirements.txt
├── install_offline.bat   # 离线安装脚本
└── ... (源代码)
```

**部署到目标机器：**
1. 将整个项目文件夹复制到目标机器
2. 确保目标机器已安装 Python 3.8+
3. 运行 `install_offline.bat`
4. 编辑 `config/config.ini`
5. 运行 `python main.py`

---

## ⚡ 快速开始

### 1. 配置文件

编辑 `config/config.ini`：

```ini
[database]
type = postgresql    # postgresql、mysql、oracle、sqlserver 或 gaussdb
host = localhost
port = 5432          # PostgreSQL/GaussDB 默认 5432，MySQL 默认 3306
database = your_database
user = postgres
password = your_password

[llm]
default_provider = deepseek

[deepseek]
api_key = sk-your-deepseek-api-key
model = deepseek-chat

[openai]
api_key = sk-your-openai-api-key
model = gpt-4o

[claude]
api_key = sk-ant-your-claude-api-key
model = claude-sonnet-4-20250514
```

### 2. 启动 CLI

```bash
python main.py
```

### 3. 开始对话

```
╭──────────────────────────────────────────╮
│  数据库智能助手 - DeepSeek / deepseek-chat │
╰──────────────────────────────────────────╯

✓ 已连接: PostgreSQL 16.4

输入 /help 查看帮助，/model 切换模型，/language 切换语言，/exit 退出

De> 列出所有表
  ● 列出表
    ✓ 返回 12 条记录

╭─────────────────────────────────────────────────────────╮
│ 当前数据库共有 12 张表：                                  │
│                                                         │
│ | 表名 | 大小 |                                          │
│ |------|------|                                          │
│ | users | 2.5 MB |                                       │
│ | orders | 15.8 MB |                                     │
│ | products | 1.2 MB |                                    │
│ | ...  | ... |                                           │
╰─────────────────────────────────────────────────────────╯
```

### 4. 常用命令

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助信息 |
| `/file [路径]` | 加载SQL文件进行分析 |
| `/migrate` | 数据库迁移向导（文件导入或在线迁移） |
| `/mcp` | 管理 MCP 外部工具服务 |
| `/mcp add` | 添加新的 MCP 服务器 |
| `/mcp list` | 列出所有 MCP 服务器 |
| `/mcp tools` | 显示可用的 MCP 工具 |
| `/skills` | 列出所有可用技能 |
| `/skills reload` | 重新加载技能 |
| `/<skill-name>` | 调用技能（如 `/db-agent`） |
| `/sessions` | 列出所有会话 |
| `/session new` | 创建新会话 |
| `/session use <id/名称>` | 切换到指定会话 |
| `/session delete <id/名称>` | 删除会话 |
| `/session rename <名称>` | 重命名当前会话 |
| `/connections` | 列出所有数据库连接 |
| `/connection add` | 添加新的数据库连接 |
| `/connection use <名称>` | 切换到指定数据库连接 |
| `/providers` | 列出所有 AI 模型配置 |
| `/provider add` | 添加新的 AI 模型配置 |
| `/provider use <名称>` | 切换 AI 模型 |
| `/model` | 快速切换 AI 模型 |
| `/language` | 切换语言（中/英） |
| `/reset` | 重置对话历史 |
| `/history` | 查看对话历史 |
| `/clear` | 清屏 |
| `/exit` | 退出程序 |

### 5. SQL 文件分析

您可以加载 SQL 文件，让 AI 分析或执行：

```
De> /file C:\queries\slow_queries.sql

已加载文件: slow_queries.sql (2048 字节, 约 5 条SQL语句)

╭──────────────────────────────────────────╮
│ 文件预览 - slow_queries.sql               │
├──────────────────────────────────────────┤
│ 1  SELECT * FROM users                   │
│ 2  WHERE created_at > '2024-01-01'       │
│ 3  ORDER BY id;                          │
│ ...                                      │
╰──────────────────────────────────────────╯

文件已加载，请输入您的问题...

De> 分析这些查询的性能

🤖: 我来分析文件中的每条查询...
    [显示分析结果]

De> 执行第2条查询

🤖: [展示SQL，等待确认]
```

---

## 💡 使用场景

### 场景一：开发者日常查询

**传统方式：** 打开数据库客户端 → 查看表结构 → 编写 SQL → 调试 → 执行

**DB Agent 方式：**
```
👤: 查看最近7天每天的订单数量和总金额

🤖: 好的，我来查询最近7天的订单统计...

    | 日期 | 订单数 | 总金额 |
    |------|--------|--------|
    | 2024-01-20 | 156 | ¥45,230.00 |
    | 2024-01-19 | 143 | ¥38,920.00 |
    | ... | ... | ... |
```

### 场景二：紧急故障排查

**凌晨3点，系统告警：数据库响应缓慢**

```
👤: 现在有哪些正在执行的慢查询？

🤖: 发现 3 个长时间运行的查询：

    1. PID: 12345 | 运行时间: 45.2秒
       SELECT * FROM logs WHERE created_at > ...
       ⚠️ 问题：全表扫描 logs 表（2000万行）

    2. PID: 12346 | 运行时间: 23.8秒
       UPDATE orders SET status = ...
       ⚠️ 问题：锁等待

    建议：
    - 考虑终止 PID 12345
    - 为 logs.created_at 添加索引

👤: 帮我创建那个索引

🤖: 将创建索引：
    CREATE INDEX CONCURRENTLY idx_logs_created_at ON logs(created_at);

    ⚠️ 这是一个在线创建索引操作，不会锁表，但可能需要几分钟。
    确认执行吗？[是/否]
```

### 场景三：数据分析师提数

**产品经理：我需要一份用户分析报告**

```
👤: 统计每个用户等级的用户数量、平均订单金额、最后活跃时间分布

🤖: 好的，我来生成这份分析报告...

    | 用户等级 | 用户数 | 平均订单金额 | 30天内活跃 | 90天内活跃 | 不活跃 |
    |---------|--------|-------------|-----------|-----------|--------|
    | VIP     | 1,234  | ¥892.50     | 78%       | 15%       | 7%     |
    | 高级    | 5,678  | ¥456.30     | 65%       | 22%       | 13%    |
    | 普通    | 23,456 | ¥123.80     | 45%       | 30%       | 25%    |

    💡 洞察：
    - VIP 用户活跃度最高，但占比仅 4%
    - 普通用户中有 25% 已不活跃，建议进行召回营销
```

### 场景四：新项目表结构设计

```
👤: 我要做一个博客系统，帮我设计数据库表结构

🤖: 好的，我为你设计以下表结构：

    1. **users** - 用户表
       - id, username, email, password_hash, avatar, created_at

    2. **posts** - 文章表
       - id, user_id, title, content, status, view_count, created_at, updated_at

    3. **categories** - 分类表
       - id, name, slug, parent_id

    4. **tags** - 标签表
       - id, name, slug

    5. **post_tags** - 文章标签关联表
       - post_id, tag_id

    6. **comments** - 评论表
       - id, post_id, user_id, content, parent_id, created_at

    需要我创建这些表吗？我可以生成完整的建表语句。

👤: 好的，创建吧

🤖: [展示完整建表 SQL]
    确认执行吗？[是/否]
```

### 场景五：定期维护优化

```
👤: 帮我做一次全面的数据库健康检查

🤖: 正在进行全面检查...

    📊 **数据库概况**
    - 版本：PostgreSQL 16.4
    - 数据库大小：12.5 GB
    - 表数量：45
    - 活跃连接：23

    ⚠️ **发现的问题**

    1. **死元组过多** (3个表)
       - orders: 15% 死元组，建议 VACUUM
       - logs: 23% 死元组，建议 VACUUM FULL
       - sessions: 45% 死元组，紧急！

    2. **未使用的索引** (5个)
       - idx_users_old_email: 从未使用，占用 56MB
       - idx_orders_legacy: 从未使用，占用 128MB
       ...

    3. **缺少索引** (2个查询)
       - orders.customer_id 经常被查询但无索引
       - products.category_id 经常被查询但无索引

    4. **大表预警**
       - logs 表已达 5GB，建议考虑分区或归档

    ✅ **优化建议**
    1. 立即执行：VACUUM ANALYZE sessions;
    2. 计划执行：删除 5 个未使用索引，释放 280MB
    3. 长期规划：logs 表按月分区

    需要我执行这些优化操作吗？
```

### 场景六：非技术人员使用

**运营同事想查数据，但不会写 SQL**

```
👤: 我想看看上周销售额最高的10个商品

🤖: 好的，我来查询上周销售额 TOP 10 商品...

    | 排名 | 商品名称 | 销量 | 销售额 |
    |------|----------|------|--------|
    | 1 | iPhone 15 Pro | 234 | ¥1,872,000 |
    | 2 | MacBook Air M3 | 156 | ¥1,248,000 |
    | 3 | AirPods Pro 2 | 445 | ¥889,110 |
    | ... | ... | ... | ... |

👤: 这些商品主要是哪些地区的用户购买的？

🤖: 我来分析这些热销商品的购买地区分布...
    [AI 记得上下文，自动分析这 10 个商品]
```

### 场景七：在线数据库迁移

**场景：将 MySQL 数据库对象在线迁移到 PostgreSQL**

使用 `/migrate` 命令进行数据库之间的在线迁移。DB Agent 会分析源数据库、创建迁移计划、并实时跟踪迁移进度。

```
# 首先，添加两个数据库连接
De> /connection add
[配置 MySQL 源数据库]

De> /connection add
[配置 PostgreSQL 目标数据库]

# 切换到目标数据库
De> /connection use postgres-target
✓ 已切换到连接 [postgres-target]

# 启动迁移向导
De> /migrate
1. 文件导入迁移 - 从 SQL 文件导入并转换
2. 在线迁移 - 直接从源数据库迁移到目标数据库

选择: 2

# 选择源数据库
可用的源数据库连接：
| # | 名称 | 类型 | 主机 | 数据库 |
|---|------|------|------|--------|
| 1 | mysql-prod | MySQL | 192.168.1.100 | myapp |

选择源数据库连接: 1

迁移方向：
  mysql-prod (MySQL) → postgres-target (PostgreSQL)

确认开始迁移？[y/n]: y

🤖 Agent: 正在分析源数据库 mysql-prod...

       **源数据库分析：**
       | 对象类型 | 数量 |
       |----------|------|
       | 表 | 7 |
       | 视图 | 3 |
       | 存储过程 | 3 |
       | 函数 | 3 |
       | 触发器 | 3 |
       | 索引 | 12 |

       **迁移计划：**
       将按依赖顺序创建对象：
       1. 表（按外键顺序）
       2. 索引
       3. 视图
       4. 函数
       5. 存储过程
       6. 触发器

       **DDL 转换预览：**
       | MySQL | PostgreSQL |
       |-------|------------|
       | INT AUTO_INCREMENT | SERIAL |
       | VARCHAR(100) | VARCHAR(100) |
       | DATETIME | TIMESTAMP |
       | TINYINT(1) | BOOLEAN |
       | ENUM(...) | VARCHAR + CHECK |

       准备执行 31 个迁移项，确认？[是/否]

👤 用户: 是

🤖 Agent: 正在执行迁移...
       ✓ [1/31] 创建表 users
       ✓ [2/31] 创建表 departments
       ✓ [3/31] 创建表 employees
       ...
       ✓ [31/31] 创建触发器 tr_audit

       **迁移完成！**
       - 总计：31 项
       - 成功：31
       - 失败：0
       - 跳过：0

       **验证：**
       正在比对源数据库和目标数据库...
       所有对象迁移成功！
```

**支持的在线迁移路径：**
- MySQL → PostgreSQL / GaussDB / Oracle / SQL Server
- PostgreSQL → MySQL / GaussDB / Oracle / SQL Server
- Oracle → PostgreSQL / MySQL / GaussDB / SQL Server
- SQL Server → PostgreSQL / MySQL / GaussDB / Oracle
- GaussDB → PostgreSQL / MySQL / Oracle / SQL Server

### 场景八：基于文件的数据库迁移

**场景：使用 DDL 文件将 Oracle 数据库对象迁移到 GaussDB**

使用 `/file` 命令加载 Oracle DDL 脚本，让 AI 自动转换为目标数据库语法并执行。

```
# 已连接 GaussDB
[database]
type = gaussdb
...

# 在 CLI 中加载 Oracle DDL 文件
De> /file C:\migration\oracle_schema.sql

✓ 已加载文件: oracle_schema.sql (15360 字节, 约 23 条SQL语句)

╭──────────────────────────────────────────────────╮
│ 文件预览 - oracle_schema.sql                      │
├──────────────────────────────────────────────────┤
│ 1  -- Oracle DDL Script                          │
│ 2  CREATE TABLE employees (                       │
│ 3      emp_id NUMBER(10) PRIMARY KEY,            │
│ 4      emp_name VARCHAR2(100) NOT NULL,          │
│ 5      hire_date DATE DEFAULT SYSDATE,           │
│ 6      salary NUMBER(12,2),                      │
│ 7      dept_id NUMBER(10) REFERENCES departments │
│ 8  );                                            │
│ 9                                                │
│ 10 CREATE SEQUENCE emp_seq START WITH 1;         │
│ ...                                              │
╰──────────────────────────────────────────────────╯

De> 把这些 Oracle DDL 语句转换成 GaussDB 语法并执行

🤖: 我来分析 Oracle DDL 并转换为 GaussDB 兼容语法：

    **转换摘要：**

    | Oracle 语法 | GaussDB 等效语法 |
    |------------|-----------------|
    | NUMBER(10) | INTEGER |
    | NUMBER(12,2) | DECIMAL(12,2) |
    | VARCHAR2(100) | VARCHAR(100) |
    | SYSDATE | CURRENT_DATE |
    | CREATE SEQUENCE | CREATE SEQUENCE (兼容) |

    **转换后的 DDL：**

    ```sql
    CREATE TABLE employees (
        emp_id INTEGER PRIMARY KEY,
        emp_name VARCHAR(100) NOT NULL,
        hire_date DATE DEFAULT CURRENT_DATE,
        salary DECIMAL(12,2),
        dept_id INTEGER REFERENCES departments
    );

    CREATE SEQUENCE emp_seq START WITH 1;
    ```

    准备执行 23 条转换后的语句，确认执行吗？[是/否]

👤: 是

🤖: 成功创建 23 个对象：
    - 15 个表
    - 5 个序列
    - 3 个索引

    迁移完成！
```

**支持的迁移路径：**
- **Oracle → GaussDB**（优化支持，内置详细转换规则）
- Oracle → PostgreSQL / MySQL / SQL Server
- MySQL → PostgreSQL / GaussDB / Oracle / SQL Server
- PostgreSQL → MySQL / GaussDB / Oracle / SQL Server
- SQL Server → PostgreSQL / MySQL / GaussDB / Oracle

### Oracle → GaussDB 核心转换规则

DB Agent 针对 Oracle 到 GaussDB 的迁移内置了详细的转换规则：

| 类别 | Oracle | GaussDB | 说明 |
|------|--------|---------|------|
| **高级包** | DBMS_LOB | DBE_LOB | 不支持 CLOB2FILE |
| | DBMS_OUTPUT | DBE_OUTPUT | 接口由存储过程变为函数 |
| | DBMS_RANDOM | DBE_RANDOM | SEED→SET_SEED, VALUE→GET_VALUE |
| | UTL_RAW | DBE_RAW | 函数名更明确 |
| | DBMS_SQL | DBE_SQL | OPEN_CURSOR→REGISTER_CONTEXT |
| **数据类型** | NUMBER(p,-s) | 不支持 | 需手动 ROUND/TRUNC |
| | VARCHAR2(n CHAR) | VARCHAR2(n*4) | 仅支持 BYTE 单位 |
| | DATE | TIMESTAMP(0) | 注意精度丢失 |
| **SQL语法** | ! = | != | 禁止空格，否则 ! 被识别为阶乘 |
| | CONNECT BY | WITH RECURSIVE | 复杂层次查询改写 |
| | ROWNUM | ROW_NUMBER() | 避免在 JOIN ON 中使用 |
| **函数** | ROUND(NULL,...) | 报错 | Oracle 返回 NULL |
| | '.' (正则) | 匹配换行 | Oracle 默认不匹配换行 |
| | LOWER/UPPER(日期) | 格式不同 | 建议先 TO_CHAR |

---

## 🔧 MCP 集成

DB Agent 支持 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 来扩展外部工具和服务能力。

### 什么是 MCP？

MCP 是一个开放协议，使 AI 助手能够连接外部数据源和工具。通过 MCP 集成，DB Agent 可以：

- 访问文件系统
- 获取网页内容
- 查询外部 API
- 使用自定义工具

### 管理 MCP 服务器

```
# 列出所有 MCP 服务器
De> /mcp list

+--------------------------------------------------+
| MCP 服务器列表                                    |
|--------------------------------------------------|
| # | 名称        | 命令                 | 状态    |
|---|-------------|---------------------|---------|
| 1 | filesystem  | npx @modelcontex... | 已启用  |
| 2 | fetch       | npx @modelcontex... | 已禁用  |
+--------------------------------------------------+

# 添加新的 MCP 服务器
De> /mcp add

服务器名称: filesystem
命令: npx
参数: -y @modelcontextprotocol/server-filesystem /tmp
环境变量: (可选)

✓ MCP Server [filesystem] 添加成功
是否立即连接? [y/n]: y
正在连接 MCP Server [filesystem]...
✓ 已连接 MCP Server [filesystem] (3 个工具)

# 查看可用工具
De> /mcp tools

+--------------------------------------------------+
| MCP 工具列表                                      |
|--------------------------------------------------|
| # | 工具名称       | 描述                        |
|---|----------------|------------------------------|
| 1 | read_file      | 从磁盘读取文件               |
| 2 | write_file     | 将内容写入文件               |
| 3 | list_directory | 列出目录内容                 |
+--------------------------------------------------+

# 启用/禁用服务器
De> /mcp enable filesystem
De> /mcp disable fetch

# 删除服务器
De> /mcp remove fetch
```

### 可用的 MCP 服务器

以下是一些常用的 MCP 服务器：

| 服务器 | 命令 | 描述 |
|--------|---------|-------------|
| Filesystem | `npx -y @modelcontextprotocol/server-filesystem /path` | 读写文件 |
| Fetch | `npx -y @modelcontextprotocol/server-fetch` | 获取网页内容 |
| GitHub | `npx -y @modelcontextprotocol/server-github` | GitHub API 访问 |
| PostgreSQL | `npx -y @modelcontextprotocol/server-postgres` | 直接访问 PostgreSQL |

### 使用 MCP 工具

一旦 MCP 服务器连接成功，AI 可以自动使用这些工具：

```
De> 读取 /tmp/config.json 文件并总结其内容

Agent: 我来使用文件系统工具读取该文件...
       [使用 MCP 工具: read_file]

       config.json 包含以下配置：
       - 数据库: PostgreSQL 在 localhost:5432
       - API 端点: 配置了 3 个
       - 日志级别: INFO
```

---

## 📦 Skills 技能系统

DB Agent 内置了兼容 Claude Code 的 Skills 系统，允许你通过自定义工作流扩展其能力。

### 什么是 Skills？

Skills 是可重用的指令集，可以：
- **用户调用** - 通过 `/skill-name` 命令调用
- **AI 自动调用** - 当相关时自动触发
- **从文件加载** - 从标准化位置加载

### Skill 存放位置

Skills 从以下两个位置加载（按优先级排序）：

| 位置 | 优先级 | 描述 |
|------|--------|------|
| `~/.claude/skills/<name>/SKILL.md` | 高 | 个人技能（用户级） |
| `.claude/skills/<name>/SKILL.md` | 低 | 项目技能（仓库级） |

同名时个人技能会覆盖项目技能。

### 创建 Skill

创建一个带有 YAML frontmatter 的 `SKILL.md` 文件：

```markdown
---
name: my-skill
description: 一个帮助完成 X 任务的技能
user-invocable: true
disable-model-invocation: false
allowed-tools: Bash, Read
---

# 我的技能说明

这个技能帮助完成 X 任务。操作步骤：

1. 首先，检查当前状态
2. 然后，执行操作
3. 最后，验证结果

传入的参数: $ARGUMENTS
第一个参数: $1
第二个参数: $2
```

### Skill 配置选项

| 字段 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `name` | string | 文件夹名 | 技能标识符 |
| `description` | string | "" | AI 工具列表中的描述 |
| `user-invocable` | boolean | true | 是否可通过 `/skill-name` 调用 |
| `disable-model-invocation` | boolean | false | 是否禁止 AI 自动调用 |
| `allowed-tools` | string/list | [] | 技能可使用的工具 |
| `context` | string | "main" | 执行上下文 |

### 变量替换

Skills 支持以下变量：

| 变量 | 描述 |
|------|------|
| `$ARGUMENTS` | 所有参数作为字符串 |
| `$ARGUMENTS[N]` | 第 N 个参数（0 索引） |
| `$N` | 第 N 个参数（1 索引） |
| `${VAR_NAME}` | 环境变量 |
| `${CLAUDE_SESSION_ID}` | 当前会话 ID |
| `!`command`` | 执行命令并插入输出 |

### 管理 Skills

```
# 列出所有可用技能
De> /skills

+--------------------------------------------------+
| 技能列表                                          |
|--------------------------------------------------|
| # | 名称      | 描述                     | 来源   |
|---|-----------|--------------------------|--------|
| 1 | /db-agent | 数据库 AI 助手...        | 个人   |
| 2 | /analyze  | 分析 SQL 性能            | 项目   |
+--------------------------------------------------+

使用 /<skill-name> 调用技能，或使用 /skills reload 重新加载

# 添加/编辑后重新加载
De> /skills reload
✓ Skills 已重新加载 (已加载 2 个技能)

# 调用技能
De> /db-agent 分析慢查询

已执行 Skill [db-agent]
思考中...
```

### 示例：数据库分析技能

创建 `~/.claude/skills/analyze-db/SKILL.md`：

```markdown
---
name: analyze-db
description: 全面的数据库健康分析
user-invocable: true
---

# 数据库健康分析

对当前数据库执行全面分析：

1. 列出所有表及其大小
2. 检查未使用的索引
3. 识别需要 VACUUM 的表
4. 找出慢查询
5. 生成优化建议

关注领域: $ARGUMENTS
```

然后使用：

```
De> /analyze-db 索引优化

Agent: 我将对数据库进行全面分析，重点关注索引优化...
       [执行分析步骤]
```

### db-agent 作为 Claude Code Skill

DB Agent 可以作为 Claude Code 的一个技能使用。默认技能创建在 `~/.claude/skills/db-agent/SKILL.md`：

```markdown
---
name: db-agent
description: 数据库 AI 助手，支持 SQL 调优、迁移和操作
user-invocable: true
allowed-tools: Bash
---

# DB-Agent 数据库助手

使用 db-agent CLI 执行数据库操作。

## 快速开始
\`\`\`bash
db-agent
\`\`\`

## 功能
- SQL 查询执行和优化
- 执行计划分析
- 慢查询识别
- 索引建议
- 跨数据库迁移

参数: $ARGUMENTS
```

---

## ⚙️ 配置说明

### 数据库配置

**PostgreSQL:**
```ini
[database]
type = postgresql     # 数据库类型
host = localhost      # 数据库主机
port = 5432          # PostgreSQL 默认端口
database = mydb      # 数据库名
user = postgres      # 用户名
password = secret    # 密码
```

**MySQL:**
```ini
[database]
type = mysql         # 数据库类型
host = localhost     # 数据库主机
port = 3306          # MySQL 默认端口
database = mydb      # 数据库名
user = root          # 用户名
password = secret    # 密码
```

**Oracle:**
```ini
[database]
type = oracle        # 数据库类型
host = localhost     # 数据库主机
port = 1521          # Oracle 默认端口
database = ORCL      # Service Name 或 SID
user = system        # 用户名
password = oracle    # 密码
```

> **Oracle 驱动说明**
>
> 使用 `oracledb` Thin 模式（Oracle 官方 Python 驱动）：
> ```bash
> pip install oracledb
> ```
>
> **特性：**
> - 纯 Python 实现 - 无需安装 Oracle Client
> - 支持 Oracle 12c 及以上版本（12.1、12.2、18c、19c、21c、23c）
> - 不支持 Oracle 11g（需要安装 Oracle Client）
>
> **支持的功能：**
> - 完整的表列表和模式探索
> - 通过 V$SQL 分析慢查询
> - 通过 DBMS_XPLAN 分析执行计划
> - 索引使用分析
> - 在线索引创建（ONLINE 关键字）
> - 通过 DBMS_STATS 收集统计信息
>
> **权限说明：**
> - 建议使用 DBA 权限以获得完整功能
> - 无 DBA 权限时，工具会自动降级使用 ALL_* 视图代替 DBA_* 视图

**SQL Server:**
```ini
[database]
type = sqlserver     # 数据库类型
host = localhost     # 数据库主机
port = 1433          # SQL Server 默认端口
database = mydb      # 数据库名
user = sa            # 用户名
password = secret    # 密码
```

> **SQL Server 驱动说明**
>
> 使用 `pytds` (python-tds) - 纯 Python TDS 协议实现：
> ```bash
> pip install python-tds
> ```
>
> **特性：**
> - 纯 Python 实现 - 无需安装 ODBC 驱动
> - 支持 SQL Server 2014、2016、2017、2019、2022 及 Azure SQL Database
> - 支持 MARS（多活动结果集）和现代日期类型
>
> **版本特定功能：**
> - SQL Server 2014 (12.x)：基础支持
> - SQL Server 2016 (13.x)+：Query Store 历史查询分析
> - SQL Server 2022 (16.x)：新权限模型 (VIEW SERVER PERFORMANCE STATE)
> - Azure SQL Database：完整支持，使用 VIEW DATABASE STATE
>
> **支持的功能：**
> - 完整的表列表和模式探索
> - 通过 sys.dm_exec_query_stats 或 Query Store 进行慢查询分析
> - 通过 SHOWPLAN_XML 进行执行计划分析
> - 通过 sys.dm_db_index_usage_stats 进行索引使用分析
> - 在线索引创建 (WITH ONLINE = ON，仅企业版)
> - 通过 UPDATE STATISTICS 更新统计信息
>
> **权限说明：**
> - VIEW SERVER STATE（2019及以前）或 VIEW SERVER PERFORMANCE STATE（2022+）用于 DMV 访问
> - SHOWPLAN 权限用于执行计划分析

**GaussDB（华为）:**
```ini
[database]
type = gaussdb       # 数据库类型
host = localhost     # 数据库主机
port = 5432          # GaussDB 默认端口（与 PostgreSQL 相同）
database = postgres  # 数据库名
user = gaussdb       # 用户名
password = secret    # 密码
```

> **GaussDB 驱动安装说明**
>
> **默认方式（所有平台）：** 使用 pg8000 驱动，支持 sha256 认证（已包含在 requirements.txt 中）：
> ```bash
> pip install pg8000
> ```
>
> **Linux（欧拉系统）备选方案：** 也可使用华为提供的专用驱动：
> ```bash
> # 1. 解压驱动包（由华为提供）
> tar -zxvf GaussDB-Kernel-V500R002C10-EULER-64bit-Python.tar.gz
>
> # 2. 复制 psycopg2 到 Python site-packages
> cp -r psycopg2 /usr/lib/python3.x/site-packages/
>
> # 3. 设置权限
> chmod 755 /usr/lib/python3.x/site-packages/psycopg2
>
> # 4. 配置环境变量
> export LD_LIBRARY_PATH=/path/to/gaussdb/lib:$LD_LIBRARY_PATH
> export PYTHONPATH=/path/to/gaussdb:$PYTHONPATH
> ```
>
> **支持的模式：**
> - **集中式模式**：单节点或高可用集群，适合 OLTP 场景。使用 `PG_STAT_ACTIVITY` 进行监控。
> - **分布式模式**：MPP 架构多节点，适合 OLAP 场景。使用 `PGXC_STAT_ACTIVITY` 进行跨节点监控。
>
> 系统会根据 `pgxc_node` 系统表自动检测运行模式。

### LLM 提供商配置

支持的提供商及配置方式：

#### DeepSeek（推荐，性价比高）
```ini
[deepseek]
api_key = sk-your-api-key
model = deepseek-chat
```

#### OpenAI / ChatGPT
```ini
[openai]
api_key = sk-your-api-key
model = gpt-4o
```

#### Anthropic Claude
```ini
[claude]
api_key = sk-ant-your-api-key
model = claude-sonnet-4-20250514
```

#### Google Gemini
```ini
[gemini]
api_key = your-api-key
model = gemini-pro
```

#### 阿里云通义千问
```ini
[qwen]
api_key = your-api-key
model = qwen-turbo
```

#### Ollama（本地部署，免费）
```ini
[ollama]
api_key = ollama
model = llama2
base_url = http://localhost:11434/v1
```

---

## 🌐 API 服务

DB Agent 提供 RESTful API，方便集成到其他系统。

### 启动 API 服务

```bash
python -m db_agent.api.server
# 或指定端口
PORT=8080 python -m db_agent.api.server
```

### API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/sessions` | 创建会话 |
| POST | `/api/v1/chat` | 发送消息 |
| GET | `/api/v1/sessions` | 列出会话 |
| GET | `/api/v1/sessions/{id}/history` | 获取历史 |
| DELETE | `/api/v1/sessions/{id}` | 删除会话 |
| POST | `/api/v1/sessions/{id}/reset` | 重置会话 |
| GET | `/api/v1/health` | 健康检查 |

### 使用示例

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. 创建会话
resp = requests.post(f"{BASE_URL}/api/v1/sessions", json={
    "config": {
        "db_type": "postgresql",  # 或 "mysql" 或 "gaussdb"
        "db_host": "localhost",
        "db_port": 5432,          # PostgreSQL/GaussDB 5432，MySQL 3306
        "db_name": "mydb",
        "db_user": "postgres",
        "db_password": "secret"
    }
})
session_id = resp.json()["session_id"]
print(f"会话ID: {session_id}")

# 2. 发送消息
resp = requests.post(f"{BASE_URL}/api/v1/chat", json={
    "session_id": session_id,
    "message": "列出所有表"
})
print(resp.json()["response"])

# 3. 继续对话（AI 会记住上下文）
resp = requests.post(f"{BASE_URL}/api/v1/chat", json={
    "session_id": session_id,
    "message": "第一个表有多少条数据？"
})
print(resp.json()["response"])

# 4. 删除会话
requests.delete(f"{BASE_URL}/api/v1/sessions/{session_id}")
```

### API 文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🔒 安全机制

### 1. 操作确认机制

所有危险操作（INSERT / UPDATE / DELETE / DROP / CREATE 等）都需要用户二次确认：

```
🤖: 即将执行以下 SQL：

    DELETE FROM users WHERE status = 'inactive';

    ⚠️ 此操作将影响 1,234 行数据
    确认执行吗？[是/否]
```

### 2. 只读查询保护

`execute_safe_query` 工具允许只读语句无需确认直接执行：

```python
# 只读语句直接执行
result = db_tools.execute_safe_query("SELECT * FROM users")      # ✅
result = db_tools.execute_safe_query("SHOW TABLES")              # ✅ (MySQL)
result = db_tools.execute_safe_query("DESCRIBE users")           # ✅ (MySQL)
result = db_tools.execute_safe_query("EXPLAIN SELECT * FROM t")  # ✅
result = db_tools.execute_safe_query("DELETE FROM users")        # ❌ 被拒绝
```

**支持的只读语句：**
- `SELECT` - 数据查询
- `SHOW` - 查看数据库对象 (MySQL)
- `DESCRIBE` / `DESC` - 查看表结构 (MySQL)
- `EXPLAIN` - 查看执行计划

### 3. 索引创建保护

默认使用在线 DDL 创建索引，最小化锁表：

**PostgreSQL:**
```sql
-- Agent 自动转换为：
CREATE INDEX CONCURRENTLY idx_name ON table(column);
```

**MySQL (5.6+):**
```sql
-- Agent 自动转换为：
ALTER TABLE table ADD INDEX idx_name (column), ALGORITHM=INPLACE, LOCK=NONE;
```

### 4. 数据库版本感知

Agent 自动检测数据库版本，生成兼容的 SQL：

```
🤖: 检测到 PostgreSQL 16.4
    将使用兼容此版本的 SQL 语法
```

### 5. 智能错误恢复

当 SQL 执行失败时，Agent 会自动分析错误原因，调整策略后重试：

```
👤: 往 users 表插入测试数据

🤖: 好的，我来插入 100 条测试记录...
    [展示 INSERT SQL，等待确认]

👤: 是

🤖: 错误：Duplicate entry 'user001' for key 'users.username'

    检测到重复键错误，我来调整策略处理已存在的记录...

    [展示修改后的 SQL（使用 INSERT IGNORE），等待确认]

👤: 是

🤖: 成功插入 95 条新记录（跳过 5 条重复数据）。
    继续执行下一步...
```

**错误恢复策略：**
- **重复键错误** - 使用 `INSERT IGNORE` 或 `ON DUPLICATE KEY UPDATE`
- **约束违反** - 分析并修正数据，使用修正后的 SQL 重试
- **语法错误** - 修正 SQL 语法后重试
- **表/列不存在** - 先确认结构，再调整查询

---

## ❓ 常见问题

### Q: 支持哪些数据库？
**A:** 目前支持 PostgreSQL 12+、MySQL 5.7/8.0、Oracle 12c+、SQL Server 2014+（包括 Azure SQL）和 GaussDB（集中式和分布式模式）。

### Q: 会不会误操作删除数据？
**A:** 不会。所有 INSERT/UPDATE/DELETE/DROP 等危险操作都需要二次确认，你可以预览将要执行的 SQL 后再决定是否执行。

### Q: API Key 安全吗？
**A:** API Key 存储在本地配置文件中，不会上传到任何服务器。建议设置适当的文件权限保护配置文件。

### Q: 可以连接远程数据库吗？
**A:** 可以。在配置文件中填写远程数据库的地址和凭据即可。请确保网络可达且防火墙允许连接。

### Q: 支持多数据库切换吗？
**A:** 支持！你可以管理多个数据库连接，并在运行时自由切换：
```
/connection add           # 添加新连接
/connections              # 列出所有连接
/connection use <名称>    # 切换到其他数据库
```

### Q: 对话历史会保存吗？
**A:** 会的，所有对话都会自动保存到本地 SQLite 数据库中。你可以：
- 使用 `/session use <名称>` 继续之前的会话
- 使用 `/sessions` 查看所有会话
- 使用 `/session new` 创建新会话
- 重启程序后对话历史仍然保留

### Q: 如何处理大结果集？
**A:** Agent 会自动限制返回的数据量。如需查看更多数据，可以明确告诉 Agent 你需要多少条记录。

### Q: pg_stat_statements 未启用怎么办？（PostgreSQL）
**A:** 不影响使用。Agent 会自动降级使用 `pg_stat_activity` 来查看当前查询。如需历史慢查询分析，请启用 pg_stat_statements：

```sql
-- postgresql.conf
shared_preload_libraries = 'pg_stat_statements'

-- 重启后执行
CREATE EXTENSION pg_stat_statements;
```

### Q: performance_schema 未启用怎么办？（MySQL）
**A:** 不影响基本使用。Agent 会自动降级使用 `information_schema.PROCESSLIST` 来查看当前查询。如需详细的慢查询分析，请在 MySQL 配置中启用 performance_schema：

```ini
# my.cnf
[mysqld]
performance_schema = ON
```

### Q: 使用哪个 LLM 模型效果最好？
**A:** 推荐：
- **性价比首选**: DeepSeek（便宜且效果好）
- **效果最佳**: Claude Sonnet 或 GPT-4o
- **免费方案**: Ollama 本地部署 Llama2

---

## 🛠 Agent 工具集

Agent 可自动调用以下数据库工具：

### 查询与操作工具

| 工具 | 说明 | 用途 |
|------|------|------|
| `list_tables` | 列出所有表 | 了解数据库结构 |
| `describe_table` | 查看表结构 | 了解字段信息 |
| `get_sample_data` | 获取示例数据 | 了解数据格式 |
| `execute_sql` | 执行任意 SQL | 增删改查操作 |
| `execute_safe_query` | 执行只读查询 | 安全查询数据 |

### 性能工具

| 工具 | 说明 | 用途 |
|------|------|------|
| `run_explain` | 分析执行计划 | 性能诊断 |
| `check_index_usage` | 检查索引使用 | 索引优化 |
| `get_table_stats` | 获取表统计 | 健康检查 |
| `create_index` | 创建索引 | 性能优化 |
| `analyze_table` | 更新统计信息 | 维护优化 |
| `identify_slow_queries` | 识别慢查询 | 性能诊断 |
| `get_running_queries` | 查看运行中查询 | 实时监控 |

### 迁移工具

| 工具 | 说明 | 用途 |
|------|------|------|
| `analyze_source_database` | 分析源数据库对象 | 迁移规划 |
| `create_migration_plan` | 创建迁移计划并转换DDL | 迁移准备 |
| `execute_migration_batch` | 批量执行迁移项 | 迁移执行 |
| `compare_databases` | 比对源库和目标库 | 迁移验证 |
| `generate_migration_report` | 生成迁移报告 | 迁移文档 |
| `get_migration_status` | 获取迁移进度 | 进度跟踪 |

### MCP 工具

当 MCP 服务器连接后，以下工具可用：

| 工具 | 服务器 | 说明 |
|------|--------|------|
| `read_file` | filesystem | 从磁盘读取文件 |
| `write_file` | filesystem | 将内容写入文件 |
| `list_directory` | filesystem | 列出目录内容 |
| `fetch` | fetch | 从 URL 获取内容 |
| *(自定义)* | *(自定义)* | 自定义 MCP 服务器工具 |

### Skill 工具

允许 AI 调用的技能会作为工具出现：

| 工具 | 说明 |
|------|------|
| `skill_<name>` | 执行指定技能并传入参数 |

示例：`skill_db-agent` - 调用 db-agent 技能

---

## 📄 开源协议

本项目采用 MIT 协议开源。

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 提交 Pull Request

---

## 📮 联系我们

- 提交 Issue: [GitHub Issues](https://github.com/NoNamesJavaDog/db-agent-ai/issues)
- 邮箱: 1057135186@qq.com

---

<p align="center">
  <b>🚀 让每个人都能轻松管理数据库，让 DBA 去做更有价值的事</b><br><br>
  <sub>Built with ❤️ by DB Agent Team</sub>
</p>
