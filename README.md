**English** | [中文](README_ZH.md)

<div align="center">

# DB Agent AI

### The Open-Source AI-Native Database Management Platform

> Talk to your database in natural language. Query, optimize, migrate, and manage — across 5 database engines and 6 LLM providers — through CLI, Web UI, REST API, or MCP.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-3178C6.svg)](https://www.typescriptlang.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Supported Databases**

[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-336791.svg)](https://postgresql.org)
[![MySQL](https://img.shields.io/badge/MySQL-5.7%20%7C%208.0-4479A1.svg)](https://mysql.com)
[![Oracle](https://img.shields.io/badge/Oracle-12c+-F80000.svg)](https://www.oracle.com/database/)
[![SQL Server](https://img.shields.io/badge/SQL%20Server-2014+-CC2927.svg)](https://www.microsoft.com/sql-server)
[![GaussDB](https://img.shields.io/badge/GaussDB-Centralized%20%7C%20Distributed-red.svg)](https://www.huaweicloud.com/product/gaussdb.html)

**Supported LLM Providers**

[![DeepSeek](https://img.shields.io/badge/DeepSeek-Chat-blue.svg)](https://deepseek.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991.svg)](https://openai.com)
[![Claude](https://img.shields.io/badge/Anthropic-Claude-orange.svg)](https://anthropic.com)
[![Gemini](https://img.shields.io/badge/Google-Gemini-4285F4.svg)](https://ai.google.dev)
[![Qwen](https://img.shields.io/badge/Alibaba-Qwen-FF6A00.svg)](https://tongyi.aliyun.com)
[![Ollama](https://img.shields.io/badge/Ollama-Local-000000.svg)](https://ollama.ai)

</div>

---

## Why DB Agent AI?

Most database tools require you to know SQL. DB Agent AI flips the script — **you describe what you want, the AI figures out the SQL, executes it safely, and explains the results**. It's not a chatbot wrapper; it's a full autonomous agent with 20+ database tools, safety guardrails, and self-healing error recovery.

| Capability | Traditional Tools | DB Agent AI |
|---|---|---|
| Query data | Write SQL manually | "Show me last month's revenue by region" |
| Performance tuning | Read EXPLAIN plans yourself | AI diagnoses + recommends + creates indexes |
| Schema design | Design ER diagrams manually | "Build me a blog system schema" |
| Database migration | Write DDL conversion scripts | One-click cross-database migration with auto-conversion |
| Error handling | Debug errors yourself | AI auto-retries with corrected SQL |
| Multi-database | Learn each dialect | Single interface for 5 databases |
| Structured data collection | Manual form coding | AI triggers inline forms dynamically |

---

## Platform Overview

```
                         ┌──────────────────────────────────────┐
                         │         DB Agent AI Platform         │
                         └──────────────┬───────────────────────┘
                                        │
              ┌─────────────┬───────────┼───────────┬─────────────┐
              ▼             ▼           ▼           ▼             ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
        │   CLI    │ │  Web UI  │ │ REST API │ │   MCP    │ │  Skills  │
        │ (Rich)   │ │ (React)  │ │(FastAPI) │ │ Server   │ │ Engine   │
        └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
             └─────────────┴────────────┴────────────┴────────────┘
                                        │
                              ┌─────────┴─────────┐
                              │  SQLTuningAgent    │
                              │  ┌───────────────┐ │
                              │  │ Tool Registry  │ │  20+ built-in tools
                              │  │ Context Mgmt   │ │  Auto-compression
                              │  │ Safety Layer   │ │  Confirm before write
                              │  │ Error Recovery │ │  Self-healing retries
                              │  │ Audit Logger   │ │  Full operation audit
                              │  └───────────────┘ │
                              └─────────┬──────────┘
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
             ┌────────────┐     ┌────────────┐     ┌────────────┐
             │ LLM Layer  │     │  DB Layer  │     │  Storage   │
             │ 6 Providers│     │ 5 Engines  │     │  SQLite    │
             └────────────┘     └────────────┘     └────────────┘
```

---

## Key Features

### 1. Multi-Database, One Interface

Connect to **PostgreSQL, MySQL, Oracle, SQL Server, or GaussDB** — and switch between them mid-conversation. DB Agent auto-detects the database version and generates compatible SQL.

- **Version-aware SQL generation** — never uses syntax your database doesn't support
- **Hot-switch connections** — manage multiple databases without restarting
- **Cross-database migration** — migrate schemas and objects between any two databases
- **Pure Python drivers** — no ODBC, no Oracle Client, no external dependencies

### 2. Autonomous AI Agent (Not Just a Chatbot)

DB Agent is a **tool-calling agent** that autonomously chains multiple operations to complete complex tasks:

```
You: "Generate 10,000 test invoices for the billing system"

Agent: 1. describe_table → understand schema
       2. execute_sql   → create generator function  [Confirm? ✓]
       3. execute_sql   → call function              [Confirm? ✓]
       4. execute_safe_query → SELECT COUNT(*) to verify

       "Created 10,000 invoices in the billing table.
        Total amount: $4,523,891.50. All records verified."
```

- **Multi-step task completion** — chains tools until the job is done
- **Self-healing error recovery** — analyzes failures and retries with improved SQL
- **Context compression** — automatically summarizes long conversations to stay within token limits
- **Interrupt & resume** — press ESC to interrupt, then continue or change direction

### 3. Safety-First Design

Every dangerous operation goes through a confirmation layer:

```
Agent: About to execute:
       DELETE FROM users WHERE last_login < '2023-01-01';
       This will affect ~2,340 rows.

       [Execute] [Skip] [Edit SQL]
```

- **Automatic confirmation** for INSERT / UPDATE / DELETE / DROP / CREATE
- **Performance pre-check** — warns about full table scans before execution
- **Read-only fast path** — SELECT queries execute without confirmation
- **Concurrent index creation** — auto-uses `CONCURRENTLY` / `ONLINE` to avoid table locks
- **Full audit trail** — every SQL execution, tool call, and config change is logged

### 4. Modern Web UI (React + TypeScript)

A full-featured web interface with real-time streaming:

- **SSE streaming chat** — see AI thinking process in real-time
- **Tool call visualization** — watch each tool execute with live status
- **Inline confirmation cards** — approve/reject SQL directly in the chat
- **Inline form cards** — AI can request structured input via dynamic forms
- **Migration wizard** — visual step-by-step database migration
- **Migration progress bar** — real-time migration tracking
- **Connection manager** — add/edit/test database connections in the UI
- **Provider manager** — configure and switch LLM providers
- **MCP server manager** — add and monitor MCP tool servers
- **Skills browser** — discover and invoke skills
- **Bilingual** — full English and Chinese support
- **8 dedicated pages**: Chat, Connections, Providers, Sessions, MCP, Skills, Migration, Settings

### 5. Cross-Database Migration Engine

Migrate database objects between any two supported databases with intelligent DDL conversion:

```
You: "Migrate my Oracle database to PostgreSQL"

Agent: [Displays Migration Card in chat]
       → Select source & target connections
       → Analyze source: 7 tables, 3 views, 3 procedures, 12 indexes
       → Auto-convert DDL syntax (NUMBER→INTEGER, SYSDATE→CURRENT_TIMESTAMP, ...)
       → Execute with real-time progress bar
       → Verify: compare source vs target
       → Generate migration report
```

**Supported object types:** Tables, Indexes, Views, Functions, Procedures, Triggers, Sequences, Constraints

**All migration paths supported:**
| From \ To | PostgreSQL | MySQL | Oracle | SQL Server | GaussDB |
|---|---|---|---|---|---|
| **PostgreSQL** | — | ✓ | ✓ | ✓ | ✓ |
| **MySQL** | ✓ | — | ✓ | ✓ | ✓ |
| **Oracle** | ✓ | ✓ | — | ✓ | ✓ (optimized) |
| **SQL Server** | ✓ | ✓ | ✓ | — | ✓ |
| **GaussDB** | ✓ | ✓ | ✓ | ✓ | — |

Oracle → GaussDB migration includes **built-in expert rules** covering package replacements (DBMS_LOB→DBE_LOB, etc.), data type edge cases, PL/SQL differences, and syntax pitfalls.

### 6. MCP Integration (Model Context Protocol)

Extend DB Agent with external tools via the open MCP standard:

**As MCP Client** — connect to external MCP servers:
```
/mcp add filesystem npx -y @modelcontextprotocol/server-filesystem /tmp
→ Now AI can read/write files, list directories
```

**As MCP Server** — expose DB Agent tools to Claude Desktop or any MCP client:
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

10 database tools exposed: `list_tables`, `describe_table`, `get_sample_data`, `execute_query`, `run_explain`, `identify_slow_queries`, `get_table_stats`, `check_index_usage`, `get_running_queries`, `get_db_info`

### 7. Skills System (Claude Code Compatible)

Extend AI capabilities with reusable instruction sets — compatible with the Claude Code skill format:

**8 built-in skills:**

| Skill | Command | Description |
|---|---|---|
| Database Health Check | `/db-health-check` | Comprehensive diagnostics: slow queries, bloat, indexes, storage |
| Index Advisor | `/index-advisor` | Analyze index usage, find missing/redundant indexes, recommend optimizations |
| SQL Code Review | `/sql-review` | Performance issues, security vulnerabilities, best practice violations |
| Query Report | `/query-report` | Deep execution plan analysis with optimization recommendations |
| Table Docs | `/table-docs` | Auto-generate Markdown documentation for table schemas |
| Migration Pre-Check | `/migration-precheck` | Compatibility assessment before cross-database migration |
| QuickBooks Finance | `/quickbooks-finance` | Full financial management: AR/AP, GL, inventory, reporting |
| DB Agent (Claude Code) | `/db-agent` | Use DB Agent as a skill from Claude Code |

**Create your own skills** — just add a `SKILL.md` file:

```markdown
---
name: my-audit
description: Run security audit on database
user-invocable: true
---
# Security Audit
1. Check for default passwords
2. Review permission grants
3. Scan for SQL injection patterns
Focus: $ARGUMENTS
```

### 8. Inline Form Cards

When the AI needs structured data from the user, it dynamically generates form cards embedded in the chat:

```
You: "I want to submit an expense report"

Agent: [Displays Form Card]
       ┌─────────────────────────────────┐
       │ Expense Report                  │
       │                                 │
       │ Date:        [2024-01-20    ]   │
       │ Amount:      [              ]   │
       │ Category:    [Transportation ▼] │
       │ Description: [              ]   │
       │                                 │
       │ [Submit]  [Cancel]              │
       └─────────────────────────────────┘

→ User fills form → Data sent to AI → AI processes structured data
```

Supports field types: text, number, select, textarea, date. The AI decides when and what form to show based on context.

### 9. Triple Interface: CLI + Web + API

**CLI** — Rich terminal UI with command history, arrow-key navigation, inline select menus:
```bash
python main.py
```

**Web UI** — Modern React SPA with real-time SSE streaming:
```bash
PORT=8000 python -m db_agent.api.server
# Open http://localhost:8000
```

**REST API** — Full v2 API for programmatic integration:
```bash
# SSE streaming chat
curl -N -X POST http://localhost:8000/api/v2/chat/1/message \
  -H "Content-Type: application/json" \
  -d '{"message": "list all tables"}'
```

### 10. Enterprise-Ready Features

- **Audit logging** — every SQL execution, tool call, and config change tracked with timestamps
- **Session persistence** — conversations survive restarts, stored in SQLite
- **Password encryption** — all database passwords and API keys encrypted at rest
- **Context compression** — automatic summarization to handle unlimited conversation length
- **Bilingual i18n** — full English and Chinese support across CLI, Web, and API
- **Offline deployment** — PyInstaller support for air-gapped environments

---

## Quick Start

### Prerequisites

- Python 3.8+
- One of: PostgreSQL 12+, MySQL 5.7+, Oracle 12c+, SQL Server 2014+, GaussDB
- At least one LLM API key (or Ollama for free local LLMs)

### Installation

```bash
# Clone
git clone https://github.com/NoNamesJavaDog/db-agent-ai.git
cd db-agent-ai

# Install dependencies
pip install -r requirements.txt

# Configure
cp config/config.ini.example config/config.ini
# Edit config/config.ini with your database and LLM credentials

# Start CLI
python main.py

# Or start Web UI + API
PORT=8000 python -m db_agent.api.server
```

### Minimal Configuration

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

## Supported LLM Providers

| Provider | Default Model | Cost | Best For |
|---|---|---|---|
| **DeepSeek** | deepseek-chat | Low | Best value, strong SQL understanding |
| **OpenAI** | gpt-4o | Medium | Broad knowledge, reliable tool calling |
| **Claude** | claude-sonnet-4-20250514 | Medium | Complex reasoning, detailed explanations |
| **Gemini** | gemini-2.0-flash | Low | Fast responses, multi-modal |
| **Qwen** | qwen-turbo | Low | Chinese language strength |
| **Ollama** | llama2 | Free | Privacy-first, on-premises deployment |

Switch providers on the fly via CLI (`/model`), Web UI, or API.

---

## Database Driver Notes

| Database | Driver | Install | Notes |
|---|---|---|---|
| PostgreSQL | pg8000 | Included | Pure Python, no external deps |
| MySQL | pymysql | Included | Pure Python |
| Oracle | oracledb | `pip install oracledb` | Thin mode, no Oracle Client needed. 12c+ only |
| SQL Server | pytds | `pip install python-tds` | Pure Python, no ODBC. 2014+ and Azure SQL |
| GaussDB | pg8000 | Included | SHA256 auth support. Auto-detects centralized/distributed |

---

## 20+ Built-in Agent Tools

### Data & Schema Tools
| Tool | Description |
|---|---|
| `list_tables` | List all tables with sizes |
| `describe_table` | Column definitions, constraints, indexes |
| `get_sample_data` | Preview table data |
| `execute_sql` | Execute any SQL (with confirmation) |
| `execute_safe_query` | Execute read-only queries (no confirmation) |
| `list_databases` | List databases on the server |
| `switch_database` | Switch to another database on the same instance |

### Performance & Optimization Tools
| Tool | Description |
|---|---|
| `run_explain` | Analyze execution plans (with ANALYZE option) |
| `identify_slow_queries` | Find slow queries by duration threshold |
| `get_running_queries` | Show currently executing queries |
| `check_index_usage` | Analyze index utilization |
| `get_table_stats` | Table statistics, bloat, dead tuples |
| `create_index` | Create indexes (concurrent mode) |
| `analyze_table` | Update table statistics |

### Migration Tools
| Tool | Description |
|---|---|
| `analyze_source_database` | Scan source schema objects |
| `create_migration_plan` | Generate DDL conversion plan |
| `execute_migration_batch` | Batch execute migration items |
| `compare_databases` | Verify source/target consistency |
| `generate_migration_report` | Create detailed report |
| `request_migration_setup` | Trigger migration configuration UI |

### Interaction Tools
| Tool | Description |
|---|---|
| `request_user_input` | Display dynamic inline forms for structured data collection |

### Extensible via MCP and Skills
Any MCP server tools and skill tools are automatically added to the agent's toolbox.

---

## CLI Commands

| Command | Description |
|---|---|
| `/help` | Show help |
| `/connections` | List database connections |
| `/connection add` | Add a new connection |
| `/connection use <name>` | Switch database |
| `/providers` | List LLM providers |
| `/provider add` | Add a new LLM provider |
| `/model` | Quick switch AI model |
| `/sessions` | List sessions |
| `/session new` | New session |
| `/session use <id>` | Switch session |
| `/migrate` | Migration wizard (file or online) |
| `/file <path>` | Load SQL file for analysis |
| `/mcp list` | List MCP servers |
| `/mcp add` | Add MCP server |
| `/mcp tools` | Show MCP tools |
| `/skills` | List available skills |
| `/<skill-name>` | Invoke a skill |
| `/language` | Switch EN/ZH |
| `/reset` | Reset conversation |
| `/exit` | Exit |

---

## API Reference

### V2 API Endpoints

| Category | Method | Path | Description |
|---|---|---|---|
| **Chat** | POST | `/api/v2/chat/{id}/message` | SSE streaming chat |
| | POST | `/api/v2/chat/{id}/confirm` | Confirm pending SQL |
| | POST | `/api/v2/chat/{id}/confirm-all` | Confirm all pending |
| | POST | `/api/v2/chat/{id}/skip-all` | Skip all pending |
| | POST | `/api/v2/chat/{id}/submit-form` | Submit inline form data |
| | POST | `/api/v2/chat/{id}/interrupt` | Interrupt AI |
| | POST | `/api/v2/chat/{id}/upload` | Upload SQL file |
| | POST | `/api/v2/chat/{id}/start-migration` | Start migration |
| **Connections** | GET/POST | `/api/v2/connections` | List/Create |
| | GET/PUT/DELETE | `/api/v2/connections/{id}` | Read/Update/Delete |
| | POST | `/api/v2/connections/{id}/test` | Test connection |
| **Providers** | GET/POST | `/api/v2/providers` | List/Create |
| | GET/PUT/DELETE | `/api/v2/providers/{id}` | Read/Update/Delete |
| **Sessions** | GET/POST | `/api/v2/sessions` | List/Create |
| | GET/DELETE | `/api/v2/sessions/{id}` | Read/Delete |
| | GET | `/api/v2/sessions/{id}/messages` | Get history |
| **MCP** | GET/POST | `/api/v2/mcp/servers` | List/Add servers |
| | DELETE | `/api/v2/mcp/servers/{name}` | Remove server |
| | GET | `/api/v2/mcp/tools` | List all tools |
| **Skills** | GET | `/api/v2/skills` | List skills |
| | GET | `/api/v2/skills/{name}` | Skill details |
| **Migration** | GET | `/api/v2/migration/tasks` | List tasks |
| | GET | `/api/v2/migration/tasks/{id}` | Task details |
| **Settings** | GET/PUT | `/api/v2/settings` | Get/Update settings |
| **Audit** | GET | `/api/v2/audit/logs` | Query audit logs |
| **Health** | GET | `/api/v2/health` | Service health check |

Full Swagger docs at `http://localhost:8000/docs` after starting the server.

---

## SSE Event Protocol

The chat endpoint streams Server-Sent Events:

| Event | Payload | Description |
|---|---|---|
| `tool_call` | `{name, input}` | Tool execution started |
| `tool_result` | `{name, status, summary}` | Tool execution completed |
| `text_delta` | `{content}` | Incremental AI text response |
| `pending` | `{index, type, sql}` | SQL awaiting user confirmation |
| `form_input` | `{title, description, fields}` | Inline form for structured input |
| `migration_setup` | `{reason, suggested_*}` | Migration configuration request |
| `migration_progress` | `{task_id, total, completed, ...}` | Migration progress update |
| `done` | `{has_pending, pending_count}` | Stream complete |
| `error` | `{message}` | Error occurred |

---

## Project Structure

```
db-agent-ai/
├── db_agent/
│   ├── core/                           # Core AI Agent Engine
│   │   ├── agent.py                    # SQLTuningAgent — the brain
│   │   ├── tool_registry.py            # 20+ tool definitions with i18n
│   │   ├── prompt_builder.py           # Dynamic system prompt construction
│   │   ├── migration_handler.py        # Cross-database migration engine
│   │   ├── migration_rules.py          # DDL conversion rules (Oracle→GaussDB, etc.)
│   │   ├── context_compression.py      # Auto-summarization for long conversations
│   │   ├── token_counter.py            # Model-aware token counting
│   │   └── database/                   # Database abstraction layer
│   │       ├── base.py                 # Abstract interface
│   │       ├── postgresql.py           # PostgreSQL implementation
│   │       ├── mysql.py                # MySQL implementation
│   │       ├── oracle.py               # Oracle implementation
│   │       ├── sqlserver.py            # SQL Server implementation
│   │       ├── gaussdb.py              # GaussDB implementation
│   │       └── factory.py              # Database factory
│   ├── llm/                            # LLM Provider Layer
│   │   ├── base.py                     # Abstract LLM client
│   │   ├── openai_compatible.py        # OpenAI / DeepSeek / Qwen / Ollama
│   │   ├── claude.py                   # Anthropic Claude
│   │   ├── gemini.py                   # Google Gemini
│   │   └── factory.py                  # LLM factory
│   ├── api/                            # REST API Layer
│   │   ├── server.py                   # FastAPI application
│   │   └── v2/                         # V2 API
│   │       ├── app.py                  # Router setup
│   │       ├── models.py               # Pydantic models
│   │       ├── deps.py                 # Dependencies
│   │       └── routes/                 # Endpoint modules
│   │           ├── chat.py             # SSE streaming chat
│   │           ├── connections.py      # Connection CRUD
│   │           ├── providers.py        # Provider CRUD
│   │           ├── sessions.py         # Session management
│   │           ├── mcp.py              # MCP management
│   │           ├── skills.py           # Skills management
│   │           ├── migration.py        # Migration management
│   │           ├── settings.py         # Settings
│   │           ├── audit.py            # Audit logs
│   │           └── health.py           # Health checks
│   ├── cli/                            # Interactive CLI
│   │   ├── app.py                      # Main CLI application
│   │   ├── ui.py                       # UI utilities
│   │   ├── config.py                   # Configuration manager
│   │   └── commands/                   # Command modules
│   │       ├── connections.py          # Connection commands
│   │       ├── providers.py            # Provider commands
│   │       ├── sessions.py             # Session commands
│   │       ├── mcp.py                  # MCP commands
│   │       ├── skills.py              # Skills commands
│   │       └── migration.py            # Migration commands
│   ├── mcp/                            # MCP Integration
│   │   ├── client.py                   # MCP client
│   │   ├── manager.py                  # Multi-server management
│   │   ├── server.py                   # Expose as MCP server
│   │   └── errors.py                   # Error definitions
│   ├── skills/                         # Skills System
│   │   ├── models.py                   # Skill data models
│   │   ├── parser.py                   # SKILL.md parser
│   │   ├── loader.py                   # Filesystem loader
│   │   ├── registry.py                 # Skill registry
│   │   └── executor.py                 # Skill executor
│   ├── storage/                        # Data Persistence
│   │   ├── sqlite_storage.py           # SQLite storage engine
│   │   ├── models.py                   # Data models
│   │   ├── audit.py                    # Audit service
│   │   └── encryption.py              # Password encryption
│   └── i18n/                           # Internationalization
│       └── translations.py             # EN/ZH translations
├── web/                                # React Web UI
│   └── src/
│       ├── pages/                      # 8 page components
│       ├── components/chat/            # Chat UI components
│       ├── stores/                     # Zustand state management
│       ├── hooks/                      # Custom hooks (SSE, etc.)
│       ├── api/                        # API client layer
│       ├── i18n/                       # Frontend translations
│       └── types/                      # TypeScript type definitions
├── .claude/skills/                     # 8 built-in skills
├── scripts/                            # Build & deploy scripts
├── main.py                             # CLI entry point
└── requirements.txt                    # Python dependencies
```

---

## Deployment Options

### Development
```bash
python main.py                              # CLI mode
PORT=8000 python -m db_agent.api.server     # Web + API mode
```

### Production (Standalone Executable)
```bash
pip install pyinstaller
scripts/build_package.sh    # or .bat on Windows
# Output: dist/db-agent/ — copy to target machine, no Python needed
```

### Offline (Air-Gapped)
```bash
scripts/download_deps.bat   # Download all wheels
# Copy to target → install_offline.bat → run
```

### As MCP Server (Claude Desktop)
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

## Security

- **Write confirmation** — all non-SELECT operations require explicit user approval
- **Performance pre-check** — detects and warns about potentially expensive queries
- **Encrypted credentials** — database passwords and API keys encrypted in SQLite
- **Read-only fast path** — SELECT / SHOW / DESCRIBE / EXPLAIN execute without confirmation
- **Concurrent DDL** — index creation uses online mode to avoid table locks
- **Full audit trail** — every operation logged with session, timestamp, and result
- **No data exfiltration** — API keys stored locally, never sent to third parties

---

## FAQ

**Q: Will it accidentally delete my data?**
A: No. All INSERT/UPDATE/DELETE/DROP operations require confirmation. You see the exact SQL before it runs.

**Q: Can I use it without internet?**
A: Yes — use Ollama with a local model for LLM, and deploy via the standalone executable.

**Q: Does it support multiple databases at once?**
A: Yes. Add multiple connections via CLI or Web UI. Switch between them mid-conversation with `/connection use <name>` or the `switch_database` tool.

**Q: How does it handle long conversations?**
A: Automatic context compression. When the conversation approaches the model's token limit, older messages are summarized to free up space while preserving important context.

**Q: Which LLM works best?**
A: DeepSeek offers the best value. Claude and GPT-4o provide the highest quality. Ollama is free for local deployment.

**Q: Can I extend it with custom tools?**
A: Yes — via MCP servers (any MCP-compatible tool server) or Skills (SKILL.md files with custom instructions).

---

## Contributing

Issues and Pull Requests are welcome!

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes
4. Push and open a Pull Request

---

## License

MIT License — see [LICENSE](LICENSE)

---

## Contact

- Issues: [GitHub Issues](https://github.com/NoNamesJavaDog/db-agent-ai/issues)
- Email: 1057135186@qq.com

---

<div align="center">
  <b>Stop writing SQL. Start talking to your database.</b>
  <br><br>
  <sub>Built with care by the DB Agent Team</sub>
</div>
