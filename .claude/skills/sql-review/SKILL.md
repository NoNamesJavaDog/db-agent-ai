---
name: sql-review
description: Review SQL code for performance issues, security vulnerabilities, and best practices
user-invocable: true
disable-model-invocation: false
---

# SQL Code Review

Please review the following SQL code:

```sql
$ARGUMENTS
```

## Review Checklist

Analyze the SQL for:

### 1. Performance Issues
- Missing indexes on WHERE/JOIN columns
- Full table scans (SELECT *)
- Inefficient JOIN operations
- Subquery optimization opportunities
- N+1 query patterns

### 2. Security Vulnerabilities
- SQL injection risks
- Privilege escalation concerns
- Sensitive data exposure
- Missing input validation patterns

### 3. Best Practices
- Proper use of aliases
- Consistent naming conventions
- Appropriate use of transactions
- NULL handling
- Data type compatibility

### 4. Optimization Opportunities
- Query rewriting suggestions
- Index recommendations
- Partitioning considerations
- Caching strategies

## Actions

1. Use `run_explain` to analyze the execution plan if the SQL is a SELECT/UPDATE/DELETE
2. Use `describe_table` to check table structures involved
3. Use `check_index_usage` to verify index utilization
4. Provide specific, actionable recommendations with corrected SQL examples
