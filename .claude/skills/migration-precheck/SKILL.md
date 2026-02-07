---
name: migration-precheck
description: Pre-migration compatibility check between source and target databases
user-invocable: true
disable-model-invocation: false
---

# Migration Pre-Check

Perform compatibility analysis for database migration.

**Source Database Type**: $1 (e.g., oracle, mysql, sqlserver)
**Target**: Currently connected database

If source not specified, analyze: $ARGUMENTS

## Compatibility Checklist

### 1. Data Type Compatibility

Check for incompatible data types:

| Source Type | Target Type | Compatible | Notes |
|-------------|-------------|------------|-------|

Common issues:
- **Oracle**: NUMBER, VARCHAR2, CLOB, BLOB, DATE
- **MySQL**: TINYINT, ENUM, SET, TEXT types
- **SQL Server**: NVARCHAR, DATETIME2, MONEY, BIT
- **GaussDB**: Array types, custom types

### 2. Function/Procedure Compatibility

Analyze:
- Built-in function differences (NVL vs COALESCE, etc.)
- String function variations
- Date/time function mappings
- Aggregate function support

Provide mapping table:
| Source Function | Target Equivalent | Notes |
|----------------|-------------------|-------|

### 3. SQL Syntax Differences

Check for:
- **Pagination**: ROWNUM vs LIMIT/OFFSET
- **String concatenation**: || vs CONCAT
- **NULL handling**: NVL vs COALESCE
- **Date literals**: TO_DATE formats
- **Hierarchical queries**: CONNECT BY vs WITH RECURSIVE
- **Sequences**: CURRVAL/NEXTVAL syntax
- **Auto-increment**: IDENTITY vs SERIAL

### 4. Constraint Support

Verify support for:
- Primary keys
- Foreign keys (CASCADE rules)
- Check constraints
- Unique constraints
- Default values
- NOT NULL constraints

### 5. Index Type Support

Compare index capabilities:
| Index Type | Source Support | Target Support |
|------------|---------------|----------------|
| B-tree | | |
| Hash | | |
| Bitmap | | |
| Full-text | | |
| Spatial | | |
| Partial | | |

### 6. Character Set Compatibility

Check:
- Source character set
- Target character set
- Collation differences
- Unicode support (UTF-8, UTF-16)

### 7. Advanced Features

Evaluate compatibility for:
- Stored procedures
- Triggers
- Views (complex views with specific syntax)
- Materialized views
- Partitioning
- Sequences
- User-defined types

## Migration Risk Assessment

### High Risk Items
- Features with no direct equivalent
- Data types requiring transformation
- Business logic in incompatible syntax

### Medium Risk Items
- Features requiring syntax changes
- Performance-related differences
- Configuration differences

### Low Risk Items
- Standard SQL features
- Compatible data types
- Common functions

## Remediation Suggestions

For each incompatibility:
1. **Issue**: Description
2. **Impact**: What will fail/break
3. **Solution**: How to resolve
4. **Example**: Before and after code

## Pre-Migration Checklist

- [ ] All data types mapped
- [ ] Functions converted
- [ ] Syntax differences resolved
- [ ] Constraints verified
- [ ] Indexes planned
- [ ] Character set configured
- [ ] Test data migrated
- [ ] Performance baseline established

## Estimated Effort

| Category | Complexity | Items | Estimated Work |
|----------|------------|-------|----------------|
| Data Types | | | |
| Functions | | | |
| Procedures | | | |
| Syntax | | | |
| **Total** | | | |
