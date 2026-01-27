[English](README.md) | **中文**

# DB Agent - 数据库智能助手

> **让 DBA 失业的 AI 数据库管理专家** —— 自然语言操作数据库，SQL 优化、性能诊断、数据管理一句话搞定

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-336791.svg)](https://postgresql.org)
[![MySQL](https://img.shields.io/badge/MySQL-5.7%20%7C%208.0-4479A1.svg)](https://mysql.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📖 目录

- [产品介绍](#-产品介绍)
- [核心功能](#-核心功能)
- [系统架构](#-系统架构)
- [安装部署](#-安装部署)
- [快速开始](#-快速开始)
- [使用场景](#-使用场景)
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
| 7x24 小时待命 | AI 永不疲倦随时响应 |

### 核心优势

- **🧠 智能理解** - 基于大语言模型，真正理解你的意图
- **🔒 安全可控** - 危险操作需二次确认，杜绝误操作
- **🔄 错误恢复** - 自动分析执行失败原因，智能调整策略重试
- **🌍 多模型支持** - 支持 DeepSeek、OpenAI、Claude、Gemini、通义千问等主流模型
- **🇨🇳 中英双语** - 完美支持中文交互，告别语言障碍
- **📊 版本感知** - 自动识别数据库版本，生成兼容的 SQL
- **⚡ 实时反馈** - 工具调用过程透明可见，执行结果即时展示

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

---

## 🏗 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        DB Agent                              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   CLI 界面   │  │  API 服务   │  │  Web 界面   │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          ▼                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │                   SQLTuningAgent                       │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌───────────────┐  │ │
│  │  │ 对话管理器   │  │  工具执行器  │  │ 安全确认机制  │  │ │
│  │  └─────────────┘  └─────────────┘  └───────────────┘  │ │
│  └───────────────────────────────────────────────────────┘ │
│                          │                                  │
│         ┌────────────────┼────────────────┐                │
│         ▼                ▼                ▼                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ LLM 客户端   │  │ 数据库工具   │  │   国际化     │        │
│  │ ─────────── │  │ ─────────── │  │ ─────────── │        │
│  │ • DeepSeek  │  │ • 查询执行   │  │ • 中文      │        │
│  │ • OpenAI    │  │ • 表结构管理 │  │ • English   │        │
│  │ • Claude    │  │ • 索引分析   │  └─────────────┘        │
│  │ • Gemini    │  │ • 性能诊断   │                         │
│  │ • Qwen      │  │ • EXPLAIN   │                         │
│  │ • Ollama    │  └─────────────┘                         │
│  └─────────────┘         │                                 │
│                          ▼                                  │
│                   ┌─────────────┐                          │
│                   │ PostgreSQL  │                          │
│                   │   MySQL     │                          │
│                   └─────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

### 项目结构

```
ai_agent/
├── db_agent/                      # 主程序包
│   ├── __init__.py                # 包导出
│   ├── core/                      # 核心组件
│   │   ├── agent.py               # SQLTuningAgent 智能体
│   │   └── database/              # 数据库抽象层
│   │       ├── base.py            # 基类（接口定义）
│   │       ├── postgresql.py      # PostgreSQL 实现
│   │       ├── mysql.py           # MySQL 实现
│   │       └── factory.py         # 数据库工具工厂
│   ├── llm/                       # LLM 客户端
│   │   ├── base.py                # 基类
│   │   ├── openai_compatible.py   # OpenAI/DeepSeek/Qwen/Ollama
│   │   ├── claude.py              # Anthropic Claude
│   │   ├── gemini.py              # Google Gemini
│   │   └── factory.py             # 客户端工厂
│   ├── api/                       # API 服务
│   │   └── server.py              # FastAPI 应用
│   ├── cli/                       # 命令行界面
│   │   ├── app.py                 # CLI 应用
│   │   └── config.py              # 配置管理
│   └── i18n/                      # 国际化
│       └── translations.py        # 翻译文件
├── config/                        # 配置文件
│   └── config.ini                 # 主配置文件
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
- PostgreSQL 12+ 或 MySQL 5.7/8.0
- 至少一个 LLM API Key（DeepSeek / OpenAI / Claude 等）

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
├── psycopg2-binary  # PostgreSQL 驱动
├── pymysql          # MySQL 驱动
├── openai           # OpenAI/DeepSeek API
├── anthropic        # Claude API
├── google-generativeai  # Gemini API
├── rich             # 终端美化
├── prompt-toolkit   # 命令行增强
├── fastapi          # API 服务
└── uvicorn          # ASGI 服务器
```

---

## ⚡ 快速开始

### 1. 配置文件

编辑 `config/config.ini`：

```ini
[database]
type = postgresql    # postgresql 或 mysql
host = localhost
port = 5432          # PostgreSQL 默认 5432，MySQL 默认 3306
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
| `/model` | 切换 AI 模型 |
| `/language` | 切换语言（中/英） |
| `/reset` | 重置对话历史 |
| `/history` | 查看对话历史 |
| `/clear` | 清屏 |
| `/exit` | 退出程序 |

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
        "db_type": "postgresql",  # 或 "mysql"
        "db_host": "localhost",
        "db_port": 5432,          # PostgreSQL 5432，MySQL 3306
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
**A:** 目前支持 PostgreSQL 12+ 和 MySQL 5.7/8.0。SQL Server 等支持正在开发中。

### Q: 会不会误操作删除数据？
**A:** 不会。所有 INSERT/UPDATE/DELETE/DROP 等危险操作都需要二次确认，你可以预览将要执行的 SQL 后再决定是否执行。

### Q: API Key 安全吗？
**A:** API Key 存储在本地配置文件中，不会上传到任何服务器。建议设置适当的文件权限保护配置文件。

### Q: 可以连接远程数据库吗？
**A:** 可以。在配置文件中填写远程数据库的地址和凭据即可。请确保网络可达且防火墙允许连接。

### Q: 支持多数据库切换吗？
**A:** 目前一个会话连接一个数据库。如需切换数据库，请重启程序并修改配置。

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

| 工具 | 说明 | 用途 |
|------|------|------|
| `list_tables` | 列出所有表 | 了解数据库结构 |
| `describe_table` | 查看表结构 | 了解字段信息 |
| `get_sample_data` | 获取示例数据 | 了解数据格式 |
| `execute_sql` | 执行任意 SQL | 增删改查操作 |
| `execute_safe_query` | 执行只读查询 | 安全查询数据 |
| `run_explain` | 分析执行计划 | 性能诊断 |
| `check_index_usage` | 检查索引使用 | 索引优化 |
| `get_table_stats` | 获取表统计 | 健康检查 |
| `create_index` | 创建索引 | 性能优化 |
| `analyze_table` | 更新统计信息 | 维护优化 |
| `identify_slow_queries` | 识别慢查询 | 性能诊断 |
| `get_running_queries` | 查看运行中查询 | 实时监控 |

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
