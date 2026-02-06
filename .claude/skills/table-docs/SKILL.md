---
name: table-docs
description: Generate documentation for table structure in Markdown format
user-invocable: true
disable-model-invocation: false
---

# Table Documentation Generator

Generate comprehensive documentation for table: **$ARGUMENTS**

If no table specified, use: $1

## Documentation Sections

### 1. Table Overview
- Use `describe_table` to get complete table structure
- Extract table comment/description if available
- Identify the table's purpose from naming and structure

### 2. Column Definitions

Create a table with:
| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|

Include:
- Data types with precision
- Constraints (NOT NULL, UNIQUE, CHECK)
- Default values
- Column comments

### 3. Primary Key & Constraints
- Primary key columns and type
- Unique constraints
- Check constraints
- Foreign key constraints with referenced tables

### 4. Indexes

Use `check_index_usage` to document:
| Index Name | Columns | Type | Unique | Usage |
|------------|---------|------|--------|-------|

Include:
- Index type (B-tree, Hash, GIN, etc.)
- Partial index conditions
- Usage statistics

### 5. Foreign Key Relationships

Document:
- Outgoing FKs (this table references)
- Incoming FKs (other tables reference this)
- Create a simple relationship diagram if multiple FKs exist

### 6. Sample Data

Use `get_sample_data` to show first 5 rows:
- Format as a readable table
- Mask sensitive columns (password, token, etc.)

### 7. Statistics

Use `get_table_stats` to include:
- Row count (approximate)
- Table size
- Index size
- Last analyzed/vacuumed

## Output Format

Generate clean Markdown that can be:
- Copied to a wiki/documentation system
- Saved as a .md file
- Included in project documentation
