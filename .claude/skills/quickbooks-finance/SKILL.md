---
name: quickbooks-finance
description: QuickBooks Online financial management - AR/AP, general ledger, reporting, inventory, and financial health analysis
user-invocable: true
disable-model-invocation: false
---

# QuickBooks Online Financial Assistant

$ARGUMENTS

## Quick Start

### Initialize Database
When the user asks to setup or create the financial database:
1. Detect the connected database type (PostgreSQL or MySQL)
2. Read and execute the appropriate DDL from `scripts/setup_postgresql.sql` or `scripts/setup_mysql.sql`
3. Read and execute `scripts/seed_chart_of_accounts.sql` to populate the standard chart of accounts
4. Confirm all `qbo_*` tables are created and seeded successfully

### Data Model
See `references/data-model.md` for complete table definitions, field types, and relationships.
All tables use the `qbo_` prefix. Core entities: Account, Customer, Vendor, Item, Invoice, Bill, Payment, JournalEntry.

## Capabilities

### 1. Schema Setup
- Initialize QBO database schema using `scripts/setup_*.sql`
- Seed standard chart of accounts from `scripts/seed_chart_of_accounts.sql`
- Verify schema integrity after setup

### 2. Accounts Receivable (AR)
- Aging analysis with standard buckets: Current / 1-30 / 31-60 / 61-90 / 90+ days
- DSO (Days Sales Outstanding) calculation and payment velocity tracking
- Credit memo and refund analysis
- Estimate-to-Invoice conversion pipeline tracking
- Customer balance detail reports

### 3. Accounts Payable (AP)
- AP aging analysis with standard buckets
- DPO (Days Payable Outstanding) calculation
- Vendor spend analysis and top vendor ranking
- Purchase Order fulfillment tracking
- Cash outflow optimization recommendations

### 4. General Ledger (GL)
- Chart of accounts management and hierarchy analysis
- Journal entry audit — verify debit/credit balance on every entry
- Trial balance generation (all account balances at a point in time)
- Sub-ledger to GL reconciliation (AR/AP control accounts)
- Transfer and deposit tracking

### 5. Customer & Vendor Management
- Top customers by revenue and outstanding balance
- Top vendors by spend and outstanding balance
- Contact data quality analysis (missing emails, phones, etc.)
- Customer churn risk and vendor dependency risk detection

### 6. Products & Inventory
- Product catalog analysis by type (Inventory/Service/NonInventory)
- Inventory valuation: QtyOnHand × PurchaseCost
- Low stock alerts based on configurable thresholds
- Sales performance by product (revenue, quantity, margin)
- Gross margin and COGS analysis

### 7. Financial Reports
Supported report types (pass as `$1` argument):
- `pnl` — Profit & Loss statement (Income - Expense - COGS)
- `balance-sheet` — Balance Sheet (Assets = Liabilities + Equity)
- `cash-flow` — Cash Flow Statement (Operating / Investing / Financing)
- `ar-aging` — Accounts Receivable Aging Report
- `ap-aging` — Accounts Payable Aging Report
- `trial-balance` — Trial Balance (all account balances)
- `general-ledger` — Transaction detail by account
- `customer-balance` — Outstanding balance by customer
- `vendor-balance` — Outstanding balance by vendor

See `references/report-templates.md` for SQL patterns for each report type.

### 8. Financial Health Audit
- **KPI Dashboard**: Current Ratio, Quick Ratio, DSO, DPO, Gross Margin %, Net Margin %
- **Anomaly Detection**: Unusual amounts, duplicate transactions, weekend/holiday transactions
- **Tax Compliance**: Tax code coverage, missing tax references
- **Data Integrity**: Orphaned line items, unbalanced journal entries, negative balances

## Best Practices

1. **Schema Discovery First**: Always run `list_tables` to find `qbo_*` tables and `describe_table` to verify columns before querying
2. **Read-Only Analysis**: Use `execute_safe_query` (read-only) for all analysis queries; only use `execute_sql` for schema setup
3. **Accounting Rules**: See `references/accounting-rules.md` for double-entry rules and financial calculation formulas
4. **Report Templates**: See `references/report-templates.md` for standard report SQL patterns
5. **Structured Output**: Generate results as structured Markdown tables with totals and subtotals
6. **Health Indicators**: Use traffic-light indicators for health audit results:
   - 🟢 Healthy / Within normal range
   - 🟡 Warning / Needs attention
   - 🔴 Critical / Immediate action required
7. **Date Handling**: Support flexible period arguments — YYYY, YYYY-QN, YYYY-MM, or explicit date ranges
8. **Currency**: All monetary values use DECIMAL(15,2); display with 2 decimal places and currency symbol
9. **Pagination**: For large result sets, limit to top N and provide summary totals

## Error Handling

- If `qbo_*` tables are not found, guide the user through schema setup first
- If required columns are missing, check schema version and suggest re-running DDL
- If data appears inconsistent (e.g., unbalanced entries), flag the issue and continue with available data

## Output Format

For financial reports, use this structure:
```
### [Report Name]
**Period**: [date range]
**Generated**: [timestamp]

| Column1 | Column2 | Amount |
|---------|---------|-------:|
| data    | data    | 0.00   |

**Total**: $X,XXX.XX

---
Notes: [any caveats or data quality issues]
```
