**English** | [中文](README_ZH.md)

# DB Agent - AI Database Assistant

> **The AI-Powered Database Expert** — Manage your database with natural language. SQL optimization, performance diagnostics, and data management made simple.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-336791.svg)](https://postgresql.org)
[![MySQL](https://img.shields.io/badge/MySQL-5.7%20%7C%208.0-4479A1.svg)](https://mysql.com)
[![GaussDB](https://img.shields.io/badge/GaussDB-Centralized%20%7C%20Distributed-red.svg)](https://www.huaweicloud.com/product/gaussdb.html)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Table of Contents

- [Introduction](#-introduction)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Use Cases](#-use-cases)
- [Configuration](#-configuration)
- [API Service](#-api-service)
- [FAQ](#-faq)

---

## Introduction

**DB Agent** is a revolutionary AI database management assistant that transforms complex database operations into simple natural language conversations. Whether you're a developer, data analyst, or product manager, you can perform CRUD operations, performance optimization, and schema design through conversation with AI.

### Why DB Agent?

| Traditional DBA Approach | DB Agent Approach |
|--------------------------|-------------------|
| Must master SQL syntax | Describe requirements in plain English |
| Manually analyze execution plans | AI automatically diagnoses performance issues |
| Consult docs for complex queries | Generate optimized SQL with one sentence |
| Need to know table structures | AI explores database schema automatically |
| Index optimization requires experience | Smart recommendations for best index strategies |
| 24/7 on-call required | AI never gets tired, always responsive |

### Core Advantages

- **Intelligent Understanding** - Powered by LLMs that truly understand your intent
- **Safe & Controlled** - Dangerous operations require confirmation, preventing accidents
- **Error Recovery** - Automatically analyzes failures and retries with improved strategies
- **Multi-Model Support** - Works with DeepSeek, OpenAI, Claude, Gemini, Qwen, Ollama
- **Bilingual** - Full support for English and Chinese interactions
- **Version Aware** - Auto-detects database version, generates compatible SQL
- **Real-time Feedback** - Transparent tool execution with instant results

---

## Key Features

### 1. Data Query & Manipulation
```
User: How many users registered last month in the users table?
Agent: Querying... There were 1,234 new user registrations last month.

User: Mark users with 'inactive' status who haven't logged in for over a year as 'archived'
Agent: This operation will affect 856 records. Confirm execution? [Yes/No]
```

### 2. Schema Management
```
User: Create a products table with name, price, inventory, and category
Agent: I'll create the products table...
       [Shows CREATE TABLE SQL, awaits confirmation]

User: Add a shipping_address field to the orders table
Agent: Added shipping_address field (VARCHAR(500))
```

### 3. Performance Diagnostics & Optimization
```
User: This query is slow, help me analyze it: SELECT * FROM orders WHERE user_id = 123
Agent: Analysis results:
       Problem: user_id column lacks an index, causing full table scan
       Suggestion: CREATE INDEX idx_orders_user_id ON orders(user_id)
       Expected improvement: 50-100x faster query performance
```

### 4. Index Management
```
User: Check index usage on the orders table
Agent: Found 3 indexes:
       idx_orders_pkey - Frequently used (125,000 scans)
       idx_orders_user_id - Normal usage (45,000 scans)
       idx_orders_old_status - Never used, recommend deletion (saves 128MB)
```

### 5. Database Health Check
```
User: Check the overall health status of the database
Agent: Health Report:
       Tables: 23
       Total Size: 4.5 GB
       Found 3 tables with excessive dead tuples, recommend VACUUM
       Found 2 slow queries needing optimization
```

---

## Architecture

```
+-------------------------------------------------------------+
|                        DB Agent                              |
+-------------------------------------------------------------+
|  +-----------+  +-----------+  +-----------+                |
|  |    CLI    |  |    API    |  |    Web    |                |
|  +-----+-----+  +-----+-----+  +-----+-----+                |
|        |              |              |                       |
|        +-------+------+------+-------+                       |
|                |                                             |
|  +-----------------------------------------------+          |
|  |              SQLTuningAgent                    |          |
|  |  +-----------+  +----------+  +------------+  |          |
|  |  | Dialogue  |  |   Tool   |  |  Security  |  |          |
|  |  | Manager   |  | Executor |  | Confirmer  |  |          |
|  |  +-----------+  +----------+  +------------+  |          |
|  +-----------------------------------------------+          |
|                |                                             |
|        +-------+-------+-------+                             |
|        v               v       v                             |
|  +-----------+  +-----------+  +-----------+                |
|  |    LLM    |  | Database  |  |   i18n    |                |
|  |  Clients  |  |   Tools   |  |           |                |
|  | --------- |  | --------- |  | --------- |                |
|  | DeepSeek  |  | Query     |  | English   |                |
|  | OpenAI    |  | Schema    |  | Chinese   |                |
|  | Claude    |  | Index     |  +-----------+                |
|  | Gemini    |  | EXPLAIN   |                               |
|  | Qwen      |  +-----------+                               |
|  | Ollama    |        |                                     |
|  +-----------+        v                                     |
|                +-------------+                              |
|                | PostgreSQL  |                              |
|                |    MySQL    |                              |
|                |   GaussDB   |                              |
|                +-------------+                              |
+-------------------------------------------------------------+
```

### Project Structure

```
ai_agent/
├── db_agent/                      # Main package
│   ├── __init__.py                # Package exports
│   ├── core/                      # Core components
│   │   ├── agent.py               # SQLTuningAgent
│   │   └── database/              # Database abstraction layer
│   │       ├── base.py            # Base class (interface)
│   │       ├── postgresql.py      # PostgreSQL implementation
│   │       ├── mysql.py           # MySQL implementation
│   │       ├── gaussdb.py         # GaussDB implementation (Centralized/Distributed)
│   │       └── factory.py         # Database tools factory
│   ├── llm/                       # LLM clients
│   │   ├── base.py                # Base class
│   │   ├── openai_compatible.py   # OpenAI/DeepSeek/Qwen/Ollama
│   │   ├── claude.py              # Anthropic Claude
│   │   ├── gemini.py              # Google Gemini
│   │   └── factory.py             # Client factory
│   ├── api/                       # API service
│   │   └── server.py              # FastAPI application
│   ├── cli/                       # Command line interface
│   │   ├── app.py                 # CLI application
│   │   └── config.py              # Configuration manager
│   └── i18n/                      # Internationalization
│       └── translations.py        # Translation files
├── config/                        # Configuration files
│   └── config.ini                 # Main configuration
├── scripts/                       # Startup scripts
│   ├── start.sh                   # Linux/macOS
│   └── start.bat                  # Windows
├── examples/                      # Example code
│   └── examples.py
├── main.py                        # Entry point
├── requirements.txt               # Dependencies
└── README.md                      # Documentation
```

---

## Installation

### Requirements

- Python 3.8+
- PostgreSQL 12+, MySQL 5.7/8.0, or GaussDB (Centralized/Distributed)
- At least one LLM API Key (DeepSeek / OpenAI / Claude / etc.)

> **Note for GaussDB users:** GaussDB requires a dedicated psycopg2 driver (NOT the standard PostgreSQL psycopg2). See [GaussDB Configuration](#gaussdb-huawei) for installation details.

### Option 1: Direct Installation

```bash
# 1. Clone the repository
git clone https://github.com/NoNamesJavaDog/db-agent-ai.git
cd db-agent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure
# Edit config/config.ini with your database credentials and API keys

# 4. Start
python main.py
```

### Option 2: Using Startup Scripts

**Linux / macOS:**
```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

**Windows:**
```cmd
scripts\start.bat
```

### Dependencies

```
requirements.txt
├── psycopg2-binary  # PostgreSQL driver
├── pymysql          # MySQL driver
├── openai           # OpenAI/DeepSeek API
├── anthropic        # Claude API
├── google-generativeai  # Gemini API
├── rich             # Terminal formatting
├── prompt-toolkit   # CLI enhancements
├── fastapi          # API service
└── uvicorn          # ASGI server
```

---

## Quick Start

### 1. Configuration File

Edit `config/config.ini`:

```ini
[database]
type = postgresql    # postgresql, mysql, or gaussdb
host = localhost
port = 5432          # 5432 for PostgreSQL/GaussDB, 3306 for MySQL
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

### 2. Start CLI

```bash
python main.py
```

### 3. Start Chatting

```
+----------------------------------------------+
|  Database Assistant - DeepSeek / deepseek-chat |
+----------------------------------------------+

Connected: PostgreSQL 16.4

Type /help for help, /model to switch models, /language to switch language, /exit to quit

De> list all tables
  * Listing tables
    Returned 12 records

+-----------------------------------------------------+
| The database contains 12 tables:                     |
|                                                     |
| | Table | Size |                                    |
| |-------|------|                                    |
| | users | 2.5 MB |                                  |
| | orders | 15.8 MB |                                |
| | products | 1.2 MB |                               |
| | ...  | ... |                                      |
+-----------------------------------------------------+
```

### 4. Common Commands

| Command | Description |
|---------|-------------|
| `/help` | Show help information |
| `/model` | Switch AI model |
| `/language` | Switch language (EN/ZH) |
| `/reset` | Reset conversation history |
| `/history` | View conversation history |
| `/clear` | Clear screen |
| `/exit` | Exit program |

---

## Use Cases

### Case 1: Developer Daily Queries

**Traditional approach:** Open database client -> Check schema -> Write SQL -> Debug -> Execute

**DB Agent approach:**
```
User: Show me the order count and total amount for each of the last 7 days

Agent: I'll query the order statistics for the last 7 days...

    | Date | Orders | Total Amount |
    |------|--------|--------------|
    | 2024-01-20 | 156 | $45,230.00 |
    | 2024-01-19 | 143 | $38,920.00 |
    | ... | ... | ... |
```

### Case 2: Emergency Troubleshooting

**3 AM, system alert: Database responding slowly**

```
User: What slow queries are currently running?

Agent: Found 3 long-running queries:

    1. PID: 12345 | Runtime: 45.2s
       SELECT * FROM logs WHERE created_at > ...
       Problem: Full table scan on logs table (20 million rows)

    2. PID: 12346 | Runtime: 23.8s
       UPDATE orders SET status = ...
       Problem: Lock wait

    Recommendations:
    - Consider terminating PID 12345
    - Add index on logs.created_at

User: Create that index for me

Agent: Will create index:
    CREATE INDEX CONCURRENTLY idx_logs_created_at ON logs(created_at);

    This is an online index creation, won't lock the table, but may take a few minutes.
    Confirm execution? [Yes/No]
```

### Case 3: Data Analyst Reporting

**Product Manager: I need a user analysis report**

```
User: Show user counts, average order amounts, and activity distribution by user tier

Agent: Generating the analysis report...

    | Tier | Users | Avg Order | Active 30d | Active 90d | Inactive |
    |------|-------|-----------|------------|------------|----------|
    | VIP  | 1,234 | $892.50   | 78%        | 15%        | 7%       |
    | Gold | 5,678 | $456.30   | 65%        | 22%        | 13%      |
    | Basic| 23,456| $123.80   | 45%        | 30%        | 25%      |

    Insights:
    - VIP users have highest engagement but only 4% of total
    - 25% of basic users are inactive, consider re-engagement campaigns
```

### Case 4: New Project Schema Design

```
User: I'm building a blog system, design the database schema for me

Agent: Here's the proposed schema:

    1. **users** - User table
       - id, username, email, password_hash, avatar, created_at

    2. **posts** - Article table
       - id, user_id, title, content, status, view_count, created_at, updated_at

    3. **categories** - Category table
       - id, name, slug, parent_id

    4. **tags** - Tag table
       - id, name, slug

    5. **post_tags** - Post-tag association
       - post_id, tag_id

    6. **comments** - Comment table
       - id, post_id, user_id, content, parent_id, created_at

    Want me to create these tables? I can generate the complete DDL statements.

User: Yes, create them

Agent: [Shows complete CREATE TABLE SQL]
    Confirm execution? [Yes/No]
```

### Case 5: Routine Maintenance

```
User: Run a comprehensive database health check

Agent: Running full diagnostics...

    **Database Overview**
    - Version: PostgreSQL 16.4
    - Size: 12.5 GB
    - Tables: 45
    - Active Connections: 23

    **Issues Found**

    1. **Excessive Dead Tuples** (3 tables)
       - orders: 15% dead tuples, recommend VACUUM
       - logs: 23% dead tuples, recommend VACUUM FULL
       - sessions: 45% dead tuples, urgent!

    2. **Unused Indexes** (5 indexes)
       - idx_users_old_email: Never used, 56MB
       - idx_orders_legacy: Never used, 128MB
       ...

    3. **Missing Indexes** (2 queries)
       - orders.customer_id frequently queried but no index
       - products.category_id frequently queried but no index

    4. **Large Table Warning**
       - logs table at 5GB, consider partitioning or archiving

    **Recommendations**
    1. Immediate: VACUUM ANALYZE sessions;
    2. Scheduled: Drop 5 unused indexes, free 280MB
    3. Long-term: Partition logs table by month

    Want me to execute these optimizations?
```

### Case 6: Non-Technical Users

**Operations colleague wants data but doesn't know SQL**

```
User: Show me the top 10 best-selling products last week

Agent: Querying top 10 products by sales last week...

    | Rank | Product | Quantity | Revenue |
    |------|---------|----------|---------|
    | 1 | iPhone 15 Pro | 234 | $187,200 |
    | 2 | MacBook Air M3 | 156 | $124,800 |
    | 3 | AirPods Pro 2 | 445 | $88,911 |
    | ... | ... | ... | ... |

User: Which regions are these products mainly purchased from?

Agent: Analyzing purchase regions for these top products...
    [AI remembers context, automatically analyzes these 10 products]
```

---

## Configuration

### Database Configuration

**PostgreSQL:**
```ini
[database]
type = postgresql     # Database type
host = localhost      # Database host
port = 5432          # PostgreSQL default port
database = mydb      # Database name
user = postgres      # Username
password = secret    # Password
```

**MySQL:**
```ini
[database]
type = mysql         # Database type
host = localhost     # Database host
port = 3306          # MySQL default port
database = mydb      # Database name
user = root          # Username
password = secret    # Password
```

**GaussDB (Huawei):**
```ini
[database]
type = gaussdb       # Database type
host = localhost     # Database host
port = 5432          # GaussDB default port (same as PostgreSQL)
database = postgres  # Database name
user = gaussdb       # Username
password = secret    # Password
```

> **Important: GaussDB Driver Installation**
>
> GaussDB requires a **dedicated psycopg2 driver** - the standard PostgreSQL psycopg2 will NOT work.
>
> **Installation Steps:**
> ```bash
> # 1. Extract the driver package (provided by Huawei)
> tar -zxvf GaussDB-Kernel-V500R002C10-EULER-64bit-Python.tar.gz
>
> # 2. Copy psycopg2 to Python site-packages
> cp -r psycopg2 /usr/lib/python3.x/site-packages/
>
> # 3. Set permissions
> chmod 755 /usr/lib/python3.x/site-packages/psycopg2
>
> # 4. Configure environment variables
> export LD_LIBRARY_PATH=/path/to/gaussdb/lib:$LD_LIBRARY_PATH
> export PYTHONPATH=/path/to/gaussdb:$PYTHONPATH
> ```
>
> **Supported Modes:**
> - **Centralized Mode**: Single node or HA cluster, suitable for OLTP workloads. Uses `PG_STAT_ACTIVITY` for monitoring.
> - **Distributed Mode**: MPP architecture with multiple nodes, suitable for OLAP workloads. Uses `PGXC_STAT_ACTIVITY` for cross-node monitoring.
>
> The mode is automatically detected based on the `pgxc_node` system table.

### LLM Provider Configuration

Supported providers and configuration:

#### DeepSeek (Recommended - Best value)
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

#### Alibaba Qwen
```ini
[qwen]
api_key = your-api-key
model = qwen-turbo
```

#### Ollama (Local deployment, free)
```ini
[ollama]
api_key = ollama
model = llama2
base_url = http://localhost:11434/v1
```

---

## API Service

DB Agent provides a RESTful API for integration with other systems.

### Start API Service

```bash
python -m db_agent.api.server
# Or specify port
PORT=8080 python -m db_agent.api.server
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/sessions` | Create session |
| POST | `/api/v1/chat` | Send message |
| GET | `/api/v1/sessions` | List sessions |
| GET | `/api/v1/sessions/{id}/history` | Get history |
| DELETE | `/api/v1/sessions/{id}` | Delete session |
| POST | `/api/v1/sessions/{id}/reset` | Reset session |
| GET | `/api/v1/health` | Health check |

### Usage Example

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Create session
resp = requests.post(f"{BASE_URL}/api/v1/sessions", json={
    "config": {
        "db_type": "postgresql",  # or "mysql" or "gaussdb"
        "db_host": "localhost",
        "db_port": 5432,          # 5432 for PostgreSQL/GaussDB, 3306 for MySQL
        "db_name": "mydb",
        "db_user": "postgres",
        "db_password": "secret"
    }
})
session_id = resp.json()["session_id"]
print(f"Session ID: {session_id}")

# 2. Send message
resp = requests.post(f"{BASE_URL}/api/v1/chat", json={
    "session_id": session_id,
    "message": "list all tables"
})
print(resp.json()["response"])

# 3. Continue conversation (AI remembers context)
resp = requests.post(f"{BASE_URL}/api/v1/chat", json={
    "session_id": session_id,
    "message": "how many rows in the first table?"
})
print(resp.json()["response"])

# 4. Delete session
requests.delete(f"{BASE_URL}/api/v1/sessions/{session_id}")
```

### API Documentation

After starting the service, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Security

### 1. Operation Confirmation

All dangerous operations (INSERT / UPDATE / DELETE / DROP / CREATE) require user confirmation:

```
Agent: About to execute the following SQL:

    DELETE FROM users WHERE status = 'inactive';

    This operation will affect 1,234 rows
    Confirm execution? [Yes/No]
```

### 2. Read-Only Query Protection

The `execute_safe_query` tool allows read-only statements without confirmation:

```python
# Read-only statements execute directly
result = db_tools.execute_safe_query("SELECT * FROM users")      # OK
result = db_tools.execute_safe_query("SHOW TABLES")              # OK (MySQL)
result = db_tools.execute_safe_query("DESCRIBE users")           # OK (MySQL)
result = db_tools.execute_safe_query("EXPLAIN SELECT * FROM t")  # OK
result = db_tools.execute_safe_query("DELETE FROM users")        # Rejected
```

**Supported read-only statements:**
- `SELECT` - Data queries
- `SHOW` - Show database objects (MySQL)
- `DESCRIBE` / `DESC` - Show table structure (MySQL)
- `EXPLAIN` - Show execution plan

### 3. Index Creation Protection

Uses online DDL by default for index creation, minimizing table locks:

**PostgreSQL:**
```sql
-- Agent automatically converts to:
CREATE INDEX CONCURRENTLY idx_name ON table(column);
```

**MySQL (5.6+):**
```sql
-- Agent automatically converts to:
ALTER TABLE table ADD INDEX idx_name (column), ALGORITHM=INPLACE, LOCK=NONE;
```

### 4. Database Version Awareness

Agent auto-detects database version and generates compatible SQL:

```
Agent: Detected PostgreSQL 16.4
       Will use SQL syntax compatible with this version
```

### 5. Intelligent Error Recovery

When SQL execution fails, Agent automatically analyzes the error and retries with an improved approach:

```
User: Insert test data into users table

Agent: I'll insert 100 test records...
       [Shows INSERT SQL, awaits confirmation]

User: Yes

Agent: Error: Duplicate entry 'user001' for key 'users.username'

       I see there's a duplicate key error. Let me modify the approach
       to handle existing records...

       [Shows modified SQL with INSERT IGNORE, awaits confirmation]

User: Yes

Agent: Successfully inserted 95 new records (5 duplicates skipped).
       Continuing with the next step...
```

**Error recovery strategies:**
- **Duplicate key** - Uses `INSERT IGNORE` or `ON DUPLICATE KEY UPDATE`
- **Constraint violation** - Analyzes and fixes data, retries with corrected SQL
- **Syntax error** - Fixes SQL syntax and retries
- **Table/column not found** - Verifies structure first, then adjusts query

---

## FAQ

### Q: Which databases are supported?
**A:** Currently supports PostgreSQL 12+, MySQL 5.7/8.0, and GaussDB (both Centralized and Distributed modes). SQL Server support is under development.

### Q: Will it accidentally delete data?
**A:** No. All INSERT/UPDATE/DELETE/DROP operations require confirmation. You can preview the SQL before deciding to execute.

### Q: Is my API Key secure?
**A:** API Keys are stored in local config files only, never uploaded anywhere. Recommend setting appropriate file permissions.

### Q: Can I connect to remote databases?
**A:** Yes. Enter remote database credentials in the config file. Ensure network connectivity and firewall rules allow the connection.

### Q: Does it support multiple database switching?
**A:** Currently one session connects to one database. To switch databases, restart the program with updated config.

### Q: How are large result sets handled?
**A:** Agent automatically limits returned data. If you need more records, explicitly tell the Agent how many you need.

### Q: What if pg_stat_statements is not enabled? (PostgreSQL)
**A:** Won't affect usage. Agent falls back to `pg_stat_activity` for current queries. For historical slow query analysis, enable pg_stat_statements:

```sql
-- postgresql.conf
shared_preload_libraries = 'pg_stat_statements'

-- After restart, execute:
CREATE EXTENSION pg_stat_statements;
```

### Q: What if performance_schema is not enabled? (MySQL)
**A:** Won't affect basic usage. Agent falls back to `information_schema.PROCESSLIST` for current queries. For detailed slow query analysis, enable performance_schema in MySQL configuration:

```ini
# my.cnf
[mysqld]
performance_schema = ON
```

### Q: Which LLM model works best?
**A:** Recommendations:
- **Best Value**: DeepSeek (affordable and effective)
- **Best Quality**: Claude Sonnet or GPT-4o
- **Free Option**: Ollama with local Llama2

---

## Agent Tools

The Agent can automatically invoke these database tools:

| Tool | Description | Use Case |
|------|-------------|----------|
| `list_tables` | List all tables | Explore database structure |
| `describe_table` | View table schema | Understand column info |
| `get_sample_data` | Get sample data | Understand data format |
| `execute_sql` | Execute any SQL | CRUD operations |
| `execute_safe_query` | Execute read-only query | Safe data queries |
| `run_explain` | Analyze execution plan | Performance diagnostics |
| `check_index_usage` | Check index usage | Index optimization |
| `get_table_stats` | Get table statistics | Health checks |
| `create_index` | Create index | Performance optimization |
| `analyze_table` | Update statistics | Maintenance |
| `identify_slow_queries` | Identify slow queries | Performance diagnostics |
| `get_running_queries` | View running queries | Real-time monitoring |

---

## License

This project is open source under the MIT License.

---

## Contributing

Issues and Pull Requests are welcome!

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## Contact

- Submit Issues: [GitHub Issues](https://github.com/NoNamesJavaDog/db-agent-ai/issues)
- Email: 1057135186@qq.com

---

<p align="center">
  <b>Making database management accessible to everyone</b><br><br>
  <sub>Built with care by the DB Agent Team</sub>
</p>
