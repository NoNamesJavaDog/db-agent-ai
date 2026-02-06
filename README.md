**English** | [中文](README_ZH.md)

# DB Agent - AI Database Assistant

> **The AI-Powered Database Expert** — Manage your database with natural language. SQL optimization, performance diagnostics, and data management made simple.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-336791.svg)](https://postgresql.org)
[![MySQL](https://img.shields.io/badge/MySQL-5.7%20%7C%208.0-4479A1.svg)](https://mysql.com)
[![Oracle](https://img.shields.io/badge/Oracle-12c+-F80000.svg)](https://www.oracle.com/database/)
[![SQL Server](https://img.shields.io/badge/SQL%20Server-2014+-CC2927.svg)](https://www.microsoft.com/sql-server)
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
- [MCP Integration](#-mcp-integration)
- [Skills System](#-skills-system)
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
| Manual DDL conversion for migration | AI converts DDL across heterogeneous databases |
| 24/7 on-call required | AI never gets tired, always responsive |

### Core Advantages

- **Intelligent Understanding** - Powered by LLMs that truly understand your intent
- **Safe & Controlled** - Dangerous operations require confirmation, preventing accidents
- **Error Recovery** - Automatically analyzes failures and retries with improved strategies
- **Multi-Model Support** - Works with DeepSeek, OpenAI, Claude, Gemini, Qwen, Ollama
- **Bilingual** - Full support for English and Chinese interactions
- **Version Aware** - Auto-detects database version, generates compatible SQL
- **Real-time Feedback** - Transparent tool execution with instant results
- **Session Management** - Persistent conversation history with SQLite storage
- **Multi-Connection** - Manage multiple database connections, switch on the fly
- **MCP Integration** - Extend capabilities with Model Context Protocol servers
- **Skills System** - Claude Code compatible skills for extensible workflows

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

### 6. Online Database Migration
```
User: /migrate
[Select: 2. Online migration]
[Select source database: mysql-test]

Agent: Analyzing source database mysql-test...
       Found 7 tables, 3 views, 3 procedures, 3 functions, 3 triggers

       Migration Plan:
       | # | Type | Object | Status |
       |---|------|--------|--------|
       | 1 | table | users | pending |
       | 2 | table | departments | pending |
       | ... | ... | ... | ... |

       Confirm to execute migration? [Yes/No]

User: Yes

Agent: Executing migration...
       ✓ Created table users
       ✓ Created table departments
       ✓ Created table employees
       ...
       Migration completed: 19/19 objects migrated successfully
```

---

## Architecture

```
+-----------------------------------------------------------------------+
|                            DB Agent                                    |
+-----------------------------------------------------------------------+
|  +-----------+  +-----------+  +-----------+                          |
|  |    CLI    |  |    API    |  |    Web    |                          |
|  +-----+-----+  +-----+-----+  +-----+-----+                          |
|        |              |              |                                 |
|        +-------+------+------+-------+                                 |
|                |                                                       |
|  +-----------------------------------------------------------+        |
|  |                    SQLTuningAgent                          |        |
|  |  +-----------+  +----------+  +------------+  +--------+  |        |
|  |  | Dialogue  |  |   Tool   |  |  Security  |  | Skills |  |        |
|  |  | Manager   |  | Executor |  | Confirmer  |  | Engine |  |        |
|  |  +-----------+  +----------+  +------------+  +--------+  |        |
|  +-----------------------------------------------------------+        |
|                |                                                       |
|    +-----------+-----------+-----------+-----------+-----------+      |
|    v           v           v           v           v           v      |
|  +-------+ +--------+ +---------+ +-------+ +----------+ +--------+   |
|  |  LLM  | |Database| |   MCP   | | i18n  | | Storage  | | Skills |   |
|  |Clients| | Tools  | | Manager | +-------+ |----------| |Registry|   |
|  |-------| |--------| |---------|           | SQLite   | |--------|   |
|  |DeepSk | | Query  | |Servers: |           |- Sessions| |Personal|   |
|  |OpenAI | | Schema | |- fs     |           |- Messages| |Project |   |
|  |Claude | | Index  | |- fetch  |           |- Configs | |        |   |
|  |Gemini | |Migrate | |- custom |           |- Tasks   | |        |   |
|  |Qwen   | +--------+ +---------+           +----------+ +--------+   |
|  |Ollama |      |                                                     |
|  +-------+      v                                                     |
|           +-------------+                                             |
|           | PostgreSQL  |                                             |
|           |    MySQL    |                                             |
|           |   Oracle    |                                             |
|           | SQL Server  |                                             |
|           |   GaussDB   |                                             |
|           +-------------+                                             |
+-----------------------------------------------------------------------+
```

### Project Structure

```
ai_agent/
├── db_agent/                      # Main package
│   ├── __init__.py                # Package exports
│   ├── core/                      # Core components
│   │   ├── agent.py               # SQLTuningAgent
│   │   ├── migration_rules.py     # DDL conversion rules
│   │   └── database/              # Database abstraction layer
│   │       ├── base.py            # Base class (interface)
│   │       ├── postgresql.py      # PostgreSQL implementation
│   │       ├── mysql.py           # MySQL implementation
│   │       ├── oracle.py          # Oracle implementation (12c+)
│   │       ├── sqlserver.py       # SQL Server implementation (2014+)
│   │       ├── gaussdb.py         # GaussDB implementation (Centralized/Distributed)
│   │       └── factory.py         # Database tools factory
│   ├── llm/                       # LLM clients
│   │   ├── base.py                # Base class
│   │   ├── openai_compatible.py   # OpenAI/DeepSeek/Qwen/Ollama
│   │   ├── claude.py              # Anthropic Claude
│   │   ├── gemini.py              # Google Gemini
│   │   └── factory.py             # Client factory
│   ├── mcp/                       # MCP (Model Context Protocol)
│   │   ├── __init__.py            # Package exports
│   │   └── manager.py             # MCP server management
│   ├── skills/                    # Skills system (Claude Code compatible)
│   │   ├── __init__.py            # Package exports
│   │   ├── models.py              # Skill data models
│   │   ├── parser.py              # SKILL.md parser
│   │   ├── loader.py              # Skills loader
│   │   ├── registry.py            # Skills registry
│   │   └── executor.py            # Skills executor
│   ├── storage/                   # Data persistence (SQLite)
│   │   ├── __init__.py            # Package exports
│   │   ├── models.py              # Data models (Session, Message, Connection, etc.)
│   │   ├── sqlite_storage.py      # SQLite storage implementation
│   │   └── encryption.py          # Password encryption utilities
│   ├── api/                       # API service
│   │   └── server.py              # FastAPI application
│   ├── cli/                       # Command line interface
│   │   ├── app.py                 # CLI application
│   │   └── config.py              # Configuration manager
│   └── i18n/                      # Internationalization
│       └── translations.py        # Translation files
├── .claude/                       # Project-level skills
│   └── skills/                    # Skills directory
│       └── <skill-name>/          # Each skill in its own folder
│           └── SKILL.md           # Skill definition file
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
- PostgreSQL 12+, MySQL 5.7/8.0, Oracle 12c+, SQL Server 2014+, or GaussDB (Centralized/Distributed)
- At least one LLM API Key (DeepSeek / OpenAI / Claude / etc.)

> **Note for GaussDB users:** GaussDB uses pg8000 driver which supports sha256 authentication. On Linux (EulerOS), you can also use the dedicated driver from Huawei. See [GaussDB Configuration](#gaussdb-huawei) for details.

> **Note for Oracle users:** Uses `oracledb` Thin mode (Oracle's official Python driver) - no Oracle Client installation required. Supports Oracle 12c and above (12.1, 12.2, 18c, 19c, 21c, 23c). Oracle 11g is not supported.

> **Note for SQL Server users:** Uses `pytds` (python-tds) - a pure Python driver requiring no ODBC installation. Supports SQL Server 2014 through 2022 and Azure SQL Database. Query Store features require SQL Server 2016+.

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
├── pg8000           # PostgreSQL/GaussDB driver (sha256 auth support)
├── pymysql          # MySQL driver
├── oracledb         # Oracle driver (Thin mode, no client required)
├── python-tds       # SQL Server driver (pure Python, no ODBC required)
├── pydantic         # Data validation (>=2.10.0 for Python 3.13 support)
├── openai           # OpenAI/DeepSeek API
├── anthropic        # Claude API
├── google-generativeai  # Gemini API
├── rich             # Terminal formatting
├── prompt-toolkit   # CLI enhancements
├── fastapi          # API service
└── uvicorn          # ASGI server
```

### Option 3: Offline Deployment (Intranet)

For environments without internet access.

#### Method A: Standalone Executable (Recommended)

No Python installation required on target machine.

**Build on a machine with internet:**
```bash
# 1. Install PyInstaller
pip install pyinstaller

# 2. Run build script
scripts\build_package.bat      # Windows
# or
./scripts/build_package.sh     # Linux/macOS
```

**Output:**
```
dist/db-agent/
├── db-agent.exe          # Main program (Windows) or db-agent (Linux)
├── config/
│   └── config.ini.example
└── ... (runtime dependencies)
```

**Deploy to target machine:**
1. Copy the entire `dist/db-agent/` folder to target machine
2. Edit `config/config.ini` with database and API settings
3. Run `db-agent.exe`

#### Method B: Offline pip Install

Target machine needs Python but no internet.

**Download dependencies on a machine with internet:**
```bash
scripts\download_deps.bat      # Windows
```

**Package contents:**
```
project_folder/
├── vendor/               # All dependency wheel packages
├── requirements.txt
├── install_offline.bat   # Offline install script
└── ... (source code)
```

**Deploy to target machine:**
1. Copy entire project folder to target machine
2. Ensure Python 3.8+ is installed
3. Run `install_offline.bat`
4. Edit `config/config.ini`
5. Run `python main.py`

---

## Quick Start

### 1. Configuration File

Edit `config/config.ini`:

```ini
[database]
type = postgresql    # postgresql, mysql, oracle, sqlserver, or gaussdb
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
| `/file [path]` | Load SQL file for analysis |
| `/migrate` | Database migration wizard (file import or online migration) |
| `/mcp` | Manage MCP external tool servers |
| `/mcp add` | Add a new MCP server |
| `/mcp list` | List all MCP servers |
| `/mcp tools` | Show available MCP tools |
| `/skills` | List all available skills |
| `/skills reload` | Reload skills from filesystem |
| `/<skill-name>` | Invoke a skill (e.g., `/db-agent`) |
| `/sessions` | List all sessions |
| `/session new` | Create a new session |
| `/session use <id/name>` | Switch to a session |
| `/session delete <id/name>` | Delete a session |
| `/session rename <name>` | Rename current session |
| `/connections` | List all database connections |
| `/connection add` | Add a new database connection |
| `/connection use <name>` | Switch to a database connection |
| `/providers` | List all AI model configurations |
| `/provider add` | Add a new AI model configuration |
| `/provider use <name>` | Switch to an AI model |
| `/model` | Quick switch AI model |
| `/language` | Switch language (EN/ZH) |
| `/reset` | Reset conversation history |
| `/history` | View conversation history |
| `/clear` | Clear screen |
| `/exit` | Exit program |

### 5. SQL File Analysis

You can load SQL files and let AI analyze or execute them:

```
De> /file C:\queries\slow_queries.sql

File loaded: slow_queries.sql (2048 bytes, ~5 SQL statements)

+------------------------------------------+
| File Preview - slow_queries.sql          |
|------------------------------------------|
| 1  SELECT * FROM users                   |
| 2  WHERE created_at > '2024-01-01'       |
| 3  ORDER BY id;                          |
| ...                                      |
+------------------------------------------+

File loaded. Enter your question...

De> Analyze the performance of these queries

Agent: I'll analyze each query in the file...
       [Shows analysis results]

De> Execute the 2nd query

Agent: [Shows SQL, awaits confirmation]
```

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

### Case 7: Online Database Migration

**Scenario: Migrate MySQL database objects to PostgreSQL**

Use the `/migrate` command to perform online migration between databases. DB Agent will analyze the source database, create a migration plan, and execute the migration with real-time progress tracking.

```
# First, add both database connections
De> /connection add
[Configure MySQL source database]

De> /connection add
[Configure PostgreSQL target database]

# Switch to target database
De> /connection use postgres-target
✓ Switched to connection [postgres-target]

# Start migration wizard
De> /migrate
1. File import migration - Import from SQL file and convert
2. Online migration - Migrate directly from source to target database

Select: 2

# Select source database
Available source connections:
| # | Name | Type | Host | Database |
|---|------|------|------|----------|
| 1 | mysql-prod | MySQL | 192.168.1.100 | myapp |

Select source connection: 1

Migration direction:
  mysql-prod (MySQL) → postgres-target (PostgreSQL)

Confirm to start migration? [y/n]: y

Agent: Analyzing source database mysql-prod...

       **Source Database Analysis:**
       | Object Type | Count |
       |-------------|-------|
       | Tables | 7 |
       | Views | 3 |
       | Procedures | 3 |
       | Functions | 3 |
       | Triggers | 3 |
       | Indexes | 12 |

       **Migration Plan:**
       Objects will be created in dependency order:
       1. Tables (with foreign key ordering)
       2. Indexes
       3. Views
       4. Functions
       5. Procedures
       6. Triggers

       **DDL Conversion Preview:**
       | MySQL | PostgreSQL |
       |-------|------------|
       | INT AUTO_INCREMENT | SERIAL |
       | VARCHAR(100) | VARCHAR(100) |
       | DATETIME | TIMESTAMP |
       | TINYINT(1) | BOOLEAN |
       | ENUM(...) | VARCHAR + CHECK |

       Ready to execute 31 migration items. Confirm? [Yes/No]

User: Yes

Agent: Executing migration...
       ✓ [1/31] Created table users
       ✓ [2/31] Created table departments
       ✓ [3/31] Created table employees
       ...
       ✓ [31/31] Created trigger tr_audit

       **Migration Complete!**
       - Total: 31 items
       - Successful: 31
       - Failed: 0
       - Skipped: 0

       **Verification:**
       Comparing source and target databases...
       All objects migrated successfully!
```

**Supported Online Migration Paths:**
- MySQL → PostgreSQL / GaussDB / Oracle / SQL Server
- PostgreSQL → MySQL / GaussDB / Oracle / SQL Server
- Oracle → PostgreSQL / MySQL / GaussDB / SQL Server
- SQL Server → PostgreSQL / MySQL / GaussDB / Oracle
- GaussDB → PostgreSQL / MySQL / Oracle / SQL Server

### Case 8: File-Based Database Migration

**Scenario: Migrate Oracle objects to GaussDB using DDL files**

Use the `/file` command to load Oracle DDL scripts and let AI convert them to the target database syntax.

```
# Connect to GaussDB
[database]
type = gaussdb
...

# In CLI, load Oracle DDL file
De> /file C:\migration\oracle_schema.sql

File loaded: oracle_schema.sql (15360 bytes, ~23 SQL statements)

+--------------------------------------------------+
| File Preview - oracle_schema.sql                  |
|--------------------------------------------------|
| 1  -- Oracle DDL Script                          |
| 2  CREATE TABLE employees (                       |
| 3      emp_id NUMBER(10) PRIMARY KEY,            |
| 4      emp_name VARCHAR2(100) NOT NULL,          |
| 5      hire_date DATE DEFAULT SYSDATE,           |
| 6      salary NUMBER(12,2),                      |
| 7      dept_id NUMBER(10) REFERENCES departments |
| 8  );                                            |
| 9                                                |
| 10 CREATE SEQUENCE emp_seq START WITH 1;         |
| ...                                              |
+--------------------------------------------------+

De> Convert these Oracle DDL statements to GaussDB syntax and execute them

Agent: I'll analyze the Oracle DDL and convert to GaussDB-compatible syntax:

    **Conversion Summary:**

    | Oracle Syntax | GaussDB Equivalent |
    |---------------|-------------------|
    | NUMBER(10) | INTEGER |
    | NUMBER(12,2) | DECIMAL(12,2) |
    | VARCHAR2(100) | VARCHAR(100) |
    | SYSDATE | CURRENT_DATE |
    | CREATE SEQUENCE | CREATE SEQUENCE (compatible) |

    **Converted DDL:**

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

    Ready to execute 23 converted statements. Confirm? [Yes/No]

User: Yes

Agent: Successfully created 23 objects:
       - 15 tables
       - 5 sequences
       - 3 indexes

       Migration completed!
```

**Supported Migration Paths:**
- **Oracle → GaussDB** (Optimized support with built-in detailed conversion rules)
- Oracle → PostgreSQL / MySQL / SQL Server
- MySQL → PostgreSQL / GaussDB / Oracle / SQL Server
- PostgreSQL → MySQL / GaussDB / Oracle / SQL Server
- SQL Server → PostgreSQL / MySQL / GaussDB / Oracle

### Oracle → GaussDB Core Conversion Rules

DB Agent has built-in detailed conversion rules for Oracle to GaussDB migration:

| Category | Oracle | GaussDB | Notes |
|----------|--------|---------|-------|
| **Packages** | DBMS_LOB | DBE_LOB | CLOB2FILE not supported |
| | DBMS_OUTPUT | DBE_OUTPUT | Interface changed from procedure to function |
| | DBMS_RANDOM | DBE_RANDOM | SEED→SET_SEED, VALUE→GET_VALUE |
| | UTL_RAW | DBE_RAW | Function names more explicit |
| | DBMS_SQL | DBE_SQL | OPEN_CURSOR→REGISTER_CONTEXT |
| **Data Types** | NUMBER(p,-s) | Not supported | Use manual ROUND/TRUNC |
| | VARCHAR2(n CHAR) | VARCHAR2(n*4) | Only BYTE unit supported |
| | DATE | TIMESTAMP(0) | Watch for precision loss |
| **SQL Syntax** | ! = | != | No space allowed, otherwise ! = factorial |
| | CONNECT BY | WITH RECURSIVE | Rewrite complex hierarchies |
| | ROWNUM | ROW_NUMBER() | Avoid in JOIN ON clause |
| **Functions** | ROUND(NULL,...) | Throws error | Oracle returns NULL |
| | '.' (regex) | Matches newline | Oracle doesn't match newline by default |
| | LOWER/UPPER(date) | Format differs | Use TO_CHAR first |

```

---

## MCP Integration

DB Agent supports the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) to extend its capabilities with external tools and services.

### What is MCP?

MCP is an open protocol that enables AI assistants to connect to external data sources and tools. With MCP integration, DB Agent can:

- Access file systems
- Fetch web content
- Query external APIs
- Use custom tools

### Managing MCP Servers

```
# List all MCP servers
De> /mcp list

+--------------------------------------------------+
| MCP Servers                                       |
|--------------------------------------------------|
| # | Name        | Command             | Status   |
|---|-------------|---------------------|----------|
| 1 | filesystem  | npx @modelcontex... | Enabled  |
| 2 | fetch       | npx @modelcontex... | Disabled |
+--------------------------------------------------+

# Add a new MCP server
De> /mcp add

Server Name: filesystem
Command: npx
Arguments: -y @modelcontextprotocol/server-filesystem /tmp
Environment Variables: (optional)

✓ MCP Server [filesystem] added successfully
Connect now? [y/n]: y
Connecting to MCP Server [filesystem]...
✓ Connected to MCP Server [filesystem] (3 tools)

# View available tools
De> /mcp tools

+--------------------------------------------------+
| MCP Tools                                         |
|--------------------------------------------------|
| # | Tool Name      | Description                 |
|---|----------------|------------------------------|
| 1 | read_file      | Read a file from disk       |
| 2 | write_file     | Write content to a file     |
| 3 | list_directory | List directory contents     |
+--------------------------------------------------+

# Enable/disable servers
De> /mcp enable filesystem
De> /mcp disable fetch

# Remove a server
De> /mcp remove fetch
```

### Available MCP Servers

Here are some useful MCP servers you can add:

| Server | Command | Description |
|--------|---------|-------------|
| Filesystem | `npx -y @modelcontextprotocol/server-filesystem /path` | Read/write files |
| Fetch | `npx -y @modelcontextprotocol/server-fetch` | Fetch web content |
| GitHub | `npx -y @modelcontextprotocol/server-github` | GitHub API access |
| PostgreSQL | `npx -y @modelcontextprotocol/server-postgres` | Direct PostgreSQL access |

### Using MCP Tools

Once MCP servers are connected, the AI can automatically use these tools:

```
De> Read the file /tmp/config.json and summarize its contents

Agent: I'll use the filesystem tool to read that file...
       [Uses MCP tool: read_file]

       The config.json contains the following settings:
       - Database: PostgreSQL on localhost:5432
       - API endpoints: 3 configured
       - Logging level: INFO
```

---

## Skills System

DB Agent includes a Claude Code compatible Skills system that allows you to extend its capabilities with custom workflows.

### What are Skills?

Skills are reusable instruction sets that can be:
- **User-invoked** via `/skill-name` commands
- **AI-invoked** automatically when relevant
- **Loaded from files** in standardized locations

### Skill Locations

Skills are loaded from two locations (in priority order):

| Location | Priority | Description |
|----------|----------|-------------|
| `~/.claude/skills/<name>/SKILL.md` | High | Personal skills (user-specific) |
| `.claude/skills/<name>/SKILL.md` | Low | Project skills (repo-specific) |

Personal skills override project skills with the same name.

### Creating a Skill

Create a `SKILL.md` file with YAML frontmatter:

```markdown
---
name: my-skill
description: A helpful skill for doing X
user-invocable: true
disable-model-invocation: false
allowed-tools: Bash, Read
---

# My Skill Instructions

This skill helps with X. Here's what to do:

1. First, check the current state
2. Then, perform the operation
3. Finally, verify the result

Arguments provided: $ARGUMENTS
First argument: $1
Second argument: $2
```

### Skill Configuration Options

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | folder name | Skill identifier |
| `description` | string | "" | Description for AI tool listing |
| `user-invocable` | boolean | true | Can be called via `/skill-name` |
| `disable-model-invocation` | boolean | false | Prevent AI auto-invocation |
| `allowed-tools` | string/list | [] | Tools the skill can use |
| `context` | string | "main" | Execution context |

### Variable Substitution

Skills support these variables:

| Variable | Description |
|----------|-------------|
| `$ARGUMENTS` | All arguments as a string |
| `$ARGUMENTS[N]` | Nth argument (0-indexed) |
| `$N` | Nth argument (1-indexed) |
| `${VAR_NAME}` | Environment variable |
| `${CLAUDE_SESSION_ID}` | Current session ID |
| `!`command`` | Execute command and insert output |

### Managing Skills

```
# List all available skills
De> /skills

+--------------------------------------------------+
| Skills                                            |
|--------------------------------------------------|
| # | Name      | Description              | Source  |
|---|-----------|--------------------------|---------|
| 1 | /db-agent | Database AI agent for... | Personal|
| 2 | /analyze  | Analyze SQL performance  | Project |
+--------------------------------------------------+

Use /<skill-name> to invoke a skill, or /skills reload to reload

# Reload skills after adding/editing
De> /skills reload
✓ Skills reloaded (Loaded 2 skills)

# Invoke a skill
De> /db-agent analyze slow queries

Executed skill [db-agent]
Thinking...
```

### Example: Database Analysis Skill

Create `~/.claude/skills/analyze-db/SKILL.md`:

```markdown
---
name: analyze-db
description: Comprehensive database health analysis
user-invocable: true
---

# Database Health Analysis

Perform a comprehensive analysis of the current database:

1. List all tables and their sizes
2. Check for unused indexes
3. Identify tables needing VACUUM
4. Find slow queries
5. Generate optimization recommendations

Focus area: $ARGUMENTS
```

Then use it:

```
De> /analyze-db index optimization

Agent: I'll perform a comprehensive database analysis focusing on index optimization...
       [Executes analysis steps]
```

### db-agent as a Claude Code Skill

DB Agent can be used as a skill from Claude Code. A default skill is created at `~/.claude/skills/db-agent/SKILL.md`:

```markdown
---
name: db-agent
description: Database AI agent for SQL tuning, migrations, and operations
user-invocable: true
allowed-tools: Bash
---

# DB-Agent Database Assistant

Execute database operations using db-agent CLI.

## Quick Start
\`\`\`bash
db-agent
\`\`\`

## Capabilities
- SQL query execution and optimization
- Query execution plan analysis
- Slow query identification
- Index recommendations
- Cross-database migrations

Arguments: $ARGUMENTS
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

**Oracle:**
```ini
[database]
type = oracle        # Database type
host = localhost     # Database host
port = 1521          # Oracle default port
database = ORCL      # Service Name or SID
user = system        # Username
password = oracle    # Password
```

> **Oracle Driver Notes**
>
> Uses `oracledb` Thin mode (Oracle's official Python driver):
> ```bash
> pip install oracledb
> ```
>
> **Features:**
> - Pure Python implementation - no Oracle Client installation required
> - Supports Oracle 12c and above (12.1, 12.2, 18c, 19c, 21c, 23c)
> - Oracle 11g is NOT supported (requires Oracle Client)
>
> **Supported Features:**
> - Full table listing and schema exploration
> - Slow query analysis via V$SQL
> - Execution plan analysis via DBMS_XPLAN
> - Index usage analysis
> - Online index creation (ONLINE keyword)
> - Statistics gathering via DBMS_STATS
>
> **Permission Notes:**
> - For full functionality, DBA privileges are recommended
> - Without DBA privileges, the tool falls back to ALL_* views instead of DBA_* views

**SQL Server:**
```ini
[database]
type = sqlserver     # Database type
host = localhost     # Database host
port = 1433          # SQL Server default port
database = mydb      # Database name
user = sa            # Username
password = secret    # Password
```

> **SQL Server Driver Notes**
>
> Uses `pytds` (python-tds) - a pure Python TDS protocol implementation:
> ```bash
> pip install python-tds
> ```
>
> **Features:**
> - Pure Python implementation - no ODBC driver installation required
> - Supports SQL Server 2014, 2016, 2017, 2019, 2022 and Azure SQL Database
> - Supports MARS (Multiple Active Result Sets) and modern date types
>
> **Version-specific Features:**
> - SQL Server 2014 (12.x): Basic support
> - SQL Server 2016 (13.x)+: Query Store for historical query analysis
> - SQL Server 2022 (16.x): New permission model (VIEW SERVER PERFORMANCE STATE)
> - Azure SQL Database: Full support with VIEW DATABASE STATE
>
> **Supported Features:**
> - Full table listing and schema exploration
> - Slow query analysis via sys.dm_exec_query_stats or Query Store
> - Execution plan analysis via SHOWPLAN_XML
> - Index usage analysis via sys.dm_db_index_usage_stats
> - Online index creation (WITH ONLINE = ON, Enterprise edition only)
> - Statistics update via UPDATE STATISTICS
>
> **Permission Notes:**
> - VIEW SERVER STATE (2019 and earlier) or VIEW SERVER PERFORMANCE STATE (2022+) for DMV access
> - SHOWPLAN permission for execution plan analysis

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

> **GaussDB Driver Installation**
>
> **Default (All platforms):** Uses pg8000 driver which supports sha256 authentication (already included in requirements.txt):
> ```bash
> pip install pg8000
> ```
>
> **Linux (EulerOS) Alternative:** You can also use the dedicated driver from Huawei:
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
**A:** Currently supports PostgreSQL 12+, MySQL 5.7/8.0, Oracle 12c+, SQL Server 2014+ (including Azure SQL), and GaussDB (both Centralized and Distributed modes).

### Q: Will it accidentally delete data?
**A:** No. All INSERT/UPDATE/DELETE/DROP operations require confirmation. You can preview the SQL before deciding to execute.

### Q: Is my API Key secure?
**A:** API Keys are stored in local config files only, never uploaded anywhere. Recommend setting appropriate file permissions.

### Q: Can I connect to remote databases?
**A:** Yes. Enter remote database credentials in the config file. Ensure network connectivity and firewall rules allow the connection.

### Q: Does it support multiple database switching?
**A:** Yes! You can manage multiple database connections and switch between them without restarting:
```
/connection add           # Add a new connection
/connections              # List all connections
/connection use <name>    # Switch to a different database
```

### Q: Are conversation histories saved?
**A:** Yes, all conversations are automatically saved to a local SQLite database. You can:
- Continue previous sessions with `/session use <name>`
- View all sessions with `/sessions`
- Create new sessions with `/session new`
- Conversation history is preserved even after restarting the program

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

### Query & Manipulation Tools

| Tool | Description | Use Case |
|------|-------------|----------|
| `list_tables` | List all tables | Explore database structure |
| `describe_table` | View table schema | Understand column info |
| `get_sample_data` | Get sample data | Understand data format |
| `execute_sql` | Execute any SQL | CRUD operations |
| `execute_safe_query` | Execute read-only query | Safe data queries |

### Performance Tools

| Tool | Description | Use Case |
|------|-------------|----------|
| `run_explain` | Analyze execution plan | Performance diagnostics |
| `check_index_usage` | Check index usage | Index optimization |
| `get_table_stats` | Get table statistics | Health checks |
| `create_index` | Create index | Performance optimization |
| `analyze_table` | Update statistics | Maintenance |
| `identify_slow_queries` | Identify slow queries | Performance diagnostics |
| `get_running_queries` | View running queries | Real-time monitoring |

### Migration Tools

| Tool | Description | Use Case |
|------|-------------|----------|
| `analyze_source_database` | Analyze source database objects | Migration planning |
| `create_migration_plan` | Create migration plan with DDL conversion | Migration preparation |
| `execute_migration_batch` | Execute migration items in batch | Migration execution |
| `compare_databases` | Compare source and target databases | Migration verification |
| `generate_migration_report` | Generate migration report | Migration documentation |
| `get_migration_status` | Get migration progress | Progress tracking |

### MCP Tools

When MCP servers are connected, additional tools become available:

| Tool | Server | Description |
|------|--------|-------------|
| `read_file` | filesystem | Read a file from disk |
| `write_file` | filesystem | Write content to a file |
| `list_directory` | filesystem | List directory contents |
| `fetch` | fetch | Fetch content from URLs |
| *(varies)* | *(custom)* | Custom MCP server tools |

### Skill Tools

Skills that allow model invocation appear as tools:

| Tool | Description |
|------|-------------|
| `skill_<name>` | Execute the named skill with arguments |

Example: `skill_db-agent` - Invoke the db-agent skill

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
