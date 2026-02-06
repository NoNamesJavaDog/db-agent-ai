---
name: query-report
description: Generate detailed query performance analysis report
user-invocable: true
disable-model-invocation: false
---

# Query Performance Report

Analyze the following SQL query:

```sql
$ARGUMENTS
```

## Analysis Process

### 1. Execution Plan Analysis

Use `run_explain` with `analyze=true` to get actual execution metrics:
- Total execution time
- Planning time
- Rows estimated vs actual
- Buffers (shared hit/read/written)

### 2. Plan Breakdown

For each node in the plan:

| Node | Type | Cost | Rows | Time | Notes |
|------|------|------|------|------|-------|

Identify:
- **Seq Scans**: On tables > 10K rows (index opportunity)
- **Nested Loops**: On large datasets (consider hash/merge join)
- **Sort operations**: Without index support
- **Materialize nodes**: Potential memory issues
- **Hash operations**: Work_mem adequacy

### 3. Index Usage Assessment

For each table in the query:
- Use `check_index_usage` to see available indexes
- Verify expected indexes are being used
- Identify missing index opportunities

### 4. Cost Analysis

Break down query cost:
- Startup cost vs total cost
- I/O cost (sequential vs random reads)
- CPU cost (filtering, sorting, hashing)
- Network cost (if applicable)

### 5. Statistics Check

Use `get_table_stats` for involved tables:
- Row count accuracy
- Last analyze time
- Dead tuple percentage

## Optimization Recommendations

### Quick Wins
- Index additions
- Statistics updates
- Simple rewrites

### Query Rewrites

If applicable, provide:
```sql
-- Original issue: [description]
-- Improved query:
SELECT ...
```

### Configuration Suggestions
- work_mem adjustments
- effective_cache_size hints
- random_page_cost tuning

## Before/After Comparison

If optimizations are applied:

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Execution Time | | | |
| Rows Scanned | | | |
| Buffers Read | | | |
| Cost | | | |

## Summary

Provide:
1. **Performance Grade**: A-F rating
2. **Top 3 Issues**: Most impactful problems
3. **Recommended Actions**: Prioritized list
4. **Expected Improvement**: Estimated performance gain
