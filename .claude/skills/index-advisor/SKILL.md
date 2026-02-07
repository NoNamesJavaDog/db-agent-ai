---
name: index-advisor
description: Analyze table and recommend optimal indexes based on query patterns
user-invocable: true
disable-model-invocation: false
---

# Index Advisor

Analyze indexing strategy for table: **$ARGUMENTS**

If no table specified, use: $1

## Analysis Steps

### Step 1: Current Structure Analysis

Use `describe_table` to understand:
- Primary key and unique constraints
- Column data types and cardinality hints
- Existing constraints that may benefit from indexes

### Step 2: Current Index Inventory

Use `check_index_usage` to analyze existing indexes:
- List all current indexes
- Check usage statistics (scans, tuples read)
- Identify index size vs table size ratio
- Find unused indexes (0 scans)

### Step 3: Query Pattern Analysis

Use `identify_slow_queries` to find queries involving this table:
- Extract WHERE clause patterns
- Identify JOIN conditions
- Find ORDER BY columns
- Detect GROUP BY patterns

### Step 4: Missing Index Detection

Analyze for:
- Columns in WHERE clauses without indexes
- Foreign key columns without indexes
- Columns used in ORDER BY on large result sets
- Composite index opportunities

## Recommendations

### Indexes to Add

For each recommended index:
```sql
-- Reason: [why this index helps]
-- Estimated impact: [query improvement expectation]
CREATE INDEX idx_tablename_columns ON tablename (column1, column2);
```

Consider:
- Covering indexes for frequent queries
- Partial indexes for filtered data
- Expression indexes for computed values

### Indexes to Remove

For unused indexes:
```sql
-- Unused since: [date/stats]
-- Size saved: [estimated]
DROP INDEX idx_name;
```

### Indexes to Modify

For suboptimal indexes:
- Column order optimization
- Include columns for covering index
- Partial index conditions

## Cost-Benefit Analysis

| Index | Size | Maintenance Cost | Query Benefit |
|-------|------|------------------|---------------|

Consider:
- Write overhead for heavily updated tables
- Storage cost vs query improvement
- Maintenance window for index creation

## Implementation Plan

Provide safe execution order:
1. Create new indexes (CONCURRENTLY if supported)
2. Validate query improvements
3. Remove unused indexes

Include rollback commands for each change.
