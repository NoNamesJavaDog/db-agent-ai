---
name: db-health-check
description: Comprehensive database health check including performance, storage, and configuration
user-invocable: true
disable-model-invocation: false
---

# Database Health Check

Perform a comprehensive health check on the connected database.

## 1. Performance Analysis

### Slow Query Detection
- Use `identify_slow_queries` to find problematic queries
- Analyze query patterns and frequency
- Identify queries with high total execution time

### Current Load
- Use `get_running_queries` to check active queries
- Identify long-running transactions
- Check for blocking queries or deadlocks

## 2. Table Health

### Table Statistics
- Use `list_tables` to get all tables
- For each significant table, use `get_table_stats` to check:
  - **Dead tuple ratio**: Flag if > 10% (needs VACUUM)
  - **Last analyze time**: Flag if > 7 days ago
  - **Sequential scan ratio**: Flag if high on large tables
  - **Table bloat percentage**

### Storage Analysis
- Check table sizes and growth trends
- Identify tables with excessive bloat
- Review tablespace utilization

## 3. Index Health

### Index Usage
- Use `check_index_usage` to identify:
  - Unused indexes (candidates for removal)
  - Duplicate/redundant indexes
  - Missing indexes on frequently scanned columns

### Index Efficiency
- Check index bloat
- Review partial indexes effectiveness
- Analyze covering index opportunities

## 4. Connection Analysis
- Current connection count vs max_connections
- Connection pool efficiency
- Idle connection detection

## 5. Configuration Review
- Memory settings (shared_buffers, work_mem)
- Checkpoint configuration
- Logging settings

## Output Format

Generate a summary report with:
1. **Critical Issues**: Immediate action required
2. **Warnings**: Should be addressed soon
3. **Recommendations**: Best practice improvements
4. **Metrics Summary**: Key performance indicators

Include specific remediation commands for each issue found.
