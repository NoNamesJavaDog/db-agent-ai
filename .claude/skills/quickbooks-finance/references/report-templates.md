# QuickBooks Online Report SQL Templates

These are generic SQL patterns. Adapt syntax to the actual database dialect (PostgreSQL or MySQL).
Replace `{start_date}` and `{end_date}` with actual date parameters.

---

## 1. Profit & Loss (Income Statement)

```sql
SELECT
    a.account_type,
    a.name AS account_name,
    SUM(CASE WHEN jl.posting_type = 'Credit' THEN jl.amount ELSE 0 END)
    - SUM(CASE WHEN jl.posting_type = 'Debit' THEN jl.amount ELSE 0 END) AS net_amount
FROM qbo_journal_entry_line jl
JOIN qbo_journal_entry je ON jl.journal_entry_id = je.id
JOIN qbo_account a ON jl.account_id = a.id
WHERE je.txn_date BETWEEN {start_date} AND {end_date}
  AND a.account_type IN ('Income', 'OtherIncome', 'CostOfGoodsSold', 'Expense', 'OtherExpense')
GROUP BY a.account_type, a.name
ORDER BY
    CASE a.account_type
        WHEN 'Income' THEN 1
        WHEN 'OtherIncome' THEN 2
        WHEN 'CostOfGoodsSold' THEN 3
        WHEN 'Expense' THEN 4
        WHEN 'OtherExpense' THEN 5
    END, a.name;
```

**Simplified alternative** using account balances directly:
```sql
-- If GL entries are not fully populated, use sub-ledger totals:
-- Revenue from invoices/sales receipts, COGS from items, Expenses from bills
SELECT 'Revenue' AS category, SUM(total_amt) AS amount
FROM qbo_invoice WHERE txn_date BETWEEN {start_date} AND {end_date}
UNION ALL
SELECT 'Revenue (Cash Sales)', SUM(total_amt)
FROM qbo_sales_receipt WHERE txn_date BETWEEN {start_date} AND {end_date}
UNION ALL
SELECT 'COGS', SUM(bl.amount)
FROM qbo_bill_line bl
JOIN qbo_bill b ON bl.bill_id = b.id
JOIN qbo_account a ON bl.account_id = a.id
WHERE b.txn_date BETWEEN {start_date} AND {end_date}
  AND a.account_type = 'CostOfGoodsSold';
```

**Display format**: Group by category with subtotals for Income, COGS, Gross Profit, Expenses, Net Income.

---

## 2. Balance Sheet

```sql
SELECT
    a.classification,
    a.account_type,
    a.name AS account_name,
    a.current_balance
FROM qbo_account a
WHERE a.active = true
ORDER BY
    CASE a.classification
        WHEN 'Asset' THEN 1
        WHEN 'Liability' THEN 2
        WHEN 'Equity' THEN 3
    END,
    a.account_type, a.name;
```

**Validation**: After generating the report, verify:
```sql
SELECT
    SUM(CASE WHEN classification = 'Asset' THEN current_balance ELSE 0 END) AS total_assets,
    SUM(CASE WHEN classification IN ('Liability', 'Equity') THEN current_balance ELSE 0 END) AS total_liab_equity
FROM qbo_account WHERE active = true;
-- total_assets SHOULD EQUAL total_liab_equity
```

---

## 3. Cash Flow Statement

Derived from GL account changes over a period:

```sql
-- Operating Activities
SELECT 'Operating' AS section, a.name, SUM(jl.amount) AS amount
FROM qbo_journal_entry_line jl
JOIN qbo_journal_entry je ON jl.journal_entry_id = je.id
JOIN qbo_account a ON jl.account_id = a.id
WHERE je.txn_date BETWEEN {start_date} AND {end_date}
  AND a.account_type IN ('AccountsReceivable', 'AccountsPayable', 'OtherCurrentAsset', 'OtherCurrentLiability')
GROUP BY a.name

UNION ALL

-- Investing Activities
SELECT 'Investing', a.name, SUM(jl.amount)
FROM qbo_journal_entry_line jl
JOIN qbo_journal_entry je ON jl.journal_entry_id = je.id
JOIN qbo_account a ON jl.account_id = a.id
WHERE je.txn_date BETWEEN {start_date} AND {end_date}
  AND a.account_type IN ('FixedAsset', 'OtherAsset')
GROUP BY a.name

UNION ALL

-- Financing Activities
SELECT 'Financing', a.name, SUM(jl.amount)
FROM qbo_journal_entry_line jl
JOIN qbo_journal_entry je ON jl.journal_entry_id = je.id
JOIN qbo_account a ON jl.account_id = a.id
WHERE je.txn_date BETWEEN {start_date} AND {end_date}
  AND a.account_type IN ('LongTermLiability', 'Equity')
GROUP BY a.name;
```

---

## 4. AR Aging Report

```sql
SELECT
    c.display_name AS customer,
    i.doc_number,
    i.txn_date,
    i.due_date,
    i.total_amt,
    i.balance,
    CASE
        WHEN i.due_date >= CURRENT_DATE THEN 'Current'
        WHEN CURRENT_DATE - i.due_date BETWEEN 1 AND 30 THEN '1-30'
        WHEN CURRENT_DATE - i.due_date BETWEEN 31 AND 60 THEN '31-60'
        WHEN CURRENT_DATE - i.due_date BETWEEN 61 AND 90 THEN '61-90'
        ELSE '90+'
    END AS aging_bucket
FROM qbo_invoice i
JOIN qbo_customer c ON i.customer_id = c.id
WHERE i.balance > 0
ORDER BY c.display_name, i.due_date;
```

**Summary view** (grouped by customer):
```sql
SELECT
    c.display_name AS customer,
    SUM(CASE WHEN i.due_date >= CURRENT_DATE THEN i.balance ELSE 0 END) AS current_amt,
    SUM(CASE WHEN CURRENT_DATE - i.due_date BETWEEN 1 AND 30 THEN i.balance ELSE 0 END) AS days_1_30,
    SUM(CASE WHEN CURRENT_DATE - i.due_date BETWEEN 31 AND 60 THEN i.balance ELSE 0 END) AS days_31_60,
    SUM(CASE WHEN CURRENT_DATE - i.due_date BETWEEN 61 AND 90 THEN i.balance ELSE 0 END) AS days_61_90,
    SUM(CASE WHEN CURRENT_DATE - i.due_date > 90 THEN i.balance ELSE 0 END) AS days_90_plus,
    SUM(i.balance) AS total
FROM qbo_invoice i
JOIN qbo_customer c ON i.customer_id = c.id
WHERE i.balance > 0
GROUP BY c.display_name
ORDER BY total DESC;
```

**MySQL note**: Replace `CURRENT_DATE - i.due_date` with `DATEDIFF(CURRENT_DATE, i.due_date)`.

---

## 5. AP Aging Report

```sql
SELECT
    v.display_name AS vendor,
    b.doc_number,
    b.txn_date,
    b.due_date,
    b.total_amt,
    b.balance,
    CASE
        WHEN b.due_date >= CURRENT_DATE THEN 'Current'
        WHEN CURRENT_DATE - b.due_date BETWEEN 1 AND 30 THEN '1-30'
        WHEN CURRENT_DATE - b.due_date BETWEEN 31 AND 60 THEN '31-60'
        WHEN CURRENT_DATE - b.due_date BETWEEN 61 AND 90 THEN '61-90'
        ELSE '90+'
    END AS aging_bucket
FROM qbo_bill b
JOIN qbo_vendor v ON b.vendor_id = v.id
WHERE b.balance > 0
ORDER BY v.display_name, b.due_date;
```

**Summary**: Same pattern as AR aging, replace invoice→bill, customer→vendor.

**MySQL note**: Replace `CURRENT_DATE - b.due_date` with `DATEDIFF(CURRENT_DATE, b.due_date)`.

---

## 6. Trial Balance

```sql
SELECT
    a.acct_num,
    a.name AS account_name,
    a.account_type,
    CASE
        WHEN a.classification IN ('Asset') OR a.account_type IN ('Expense', 'CostOfGoodsSold', 'OtherExpense')
        THEN a.current_balance ELSE 0
    END AS debit_balance,
    CASE
        WHEN a.classification IN ('Liability', 'Equity') OR a.account_type IN ('Income', 'OtherIncome')
        THEN a.current_balance ELSE 0
    END AS credit_balance
FROM qbo_account a
WHERE a.active = true AND a.current_balance != 0
ORDER BY a.acct_num, a.account_type;
```

**Validation**: `SUM(debit_balance) = SUM(credit_balance)`.

---

## 7. General Ledger Detail

For a specific account, show all transactions with running balance:

```sql
SELECT
    je.txn_date,
    je.doc_number,
    jl.description,
    jl.posting_type,
    jl.amount,
    SUM(CASE
        WHEN jl.posting_type = 'Debit' THEN jl.amount
        ELSE -jl.amount
    END) OVER (ORDER BY je.txn_date, je.id) AS running_balance
FROM qbo_journal_entry_line jl
JOIN qbo_journal_entry je ON jl.journal_entry_id = je.id
WHERE jl.account_id = {account_id}
  AND je.txn_date BETWEEN {start_date} AND {end_date}
ORDER BY je.txn_date, je.id, jl.line_num;
```

**Note**: For credit-normal accounts (Income, Liability, Equity), reverse the running balance sign.

---

## 8. Customer Balance Summary

```sql
SELECT
    c.display_name,
    c.email,
    c.balance AS current_balance,
    COUNT(DISTINCT i.id) AS open_invoices,
    SUM(i.balance) AS total_outstanding,
    MIN(i.due_date) AS oldest_due_date
FROM qbo_customer c
LEFT JOIN qbo_invoice i ON c.id = i.customer_id AND i.balance > 0
WHERE c.active = true
GROUP BY c.id, c.display_name, c.email, c.balance
HAVING c.balance != 0 OR SUM(i.balance) > 0
ORDER BY total_outstanding DESC;
```

---

## 9. Vendor Balance Summary

```sql
SELECT
    v.display_name,
    v.email,
    v.balance AS current_balance,
    COUNT(DISTINCT b.id) AS open_bills,
    SUM(b.balance) AS total_outstanding,
    MIN(b.due_date) AS oldest_due_date
FROM qbo_vendor v
LEFT JOIN qbo_bill b ON v.id = b.vendor_id AND b.balance > 0
WHERE v.active = true
GROUP BY v.id, v.display_name, v.email, v.balance
HAVING v.balance != 0 OR SUM(b.balance) > 0
ORDER BY total_outstanding DESC;
```

---

## 10. Period Comparison (Year-over-Year / Month-over-Month)

```sql
-- P&L comparison: current period vs prior period
SELECT
    a.account_type,
    a.name,
    SUM(CASE
        WHEN je.txn_date BETWEEN {current_start} AND {current_end}
        THEN CASE WHEN jl.posting_type = 'Credit' THEN jl.amount ELSE -jl.amount END
        ELSE 0
    END) AS current_period,
    SUM(CASE
        WHEN je.txn_date BETWEEN {prior_start} AND {prior_end}
        THEN CASE WHEN jl.posting_type = 'Credit' THEN jl.amount ELSE -jl.amount END
        ELSE 0
    END) AS prior_period,
    SUM(CASE
        WHEN je.txn_date BETWEEN {current_start} AND {current_end}
        THEN CASE WHEN jl.posting_type = 'Credit' THEN jl.amount ELSE -jl.amount END
        ELSE 0
    END)
    - SUM(CASE
        WHEN je.txn_date BETWEEN {prior_start} AND {prior_end}
        THEN CASE WHEN jl.posting_type = 'Credit' THEN jl.amount ELSE -jl.amount END
        ELSE 0
    END) AS change_amount
FROM qbo_journal_entry_line jl
JOIN qbo_journal_entry je ON jl.journal_entry_id = je.id
JOIN qbo_account a ON jl.account_id = a.id
WHERE a.account_type IN ('Income', 'OtherIncome', 'CostOfGoodsSold', 'Expense', 'OtherExpense')
  AND (je.txn_date BETWEEN {prior_start} AND {current_end})
GROUP BY a.account_type, a.name
ORDER BY a.account_type, a.name;
```

Add a computed `change_pct` column: `(current_period - prior_period) / NULLIF(prior_period, 0) * 100`.

---

## 11. Budget vs Actual

```sql
SELECT
    a.name AS account_name,
    bd.period_start,
    bd.amount AS budget_amount,
    COALESCE(SUM(
        CASE WHEN jl.posting_type = 'Debit' THEN jl.amount ELSE -jl.amount END
    ), 0) AS actual_amount,
    bd.amount - COALESCE(SUM(
        CASE WHEN jl.posting_type = 'Debit' THEN jl.amount ELSE -jl.amount END
    ), 0) AS variance
FROM qbo_budget_detail bd
JOIN qbo_budget bu ON bd.budget_id = bu.id
JOIN qbo_account a ON bd.account_id = a.id
LEFT JOIN qbo_journal_entry_line jl ON jl.account_id = a.id
LEFT JOIN qbo_journal_entry je ON jl.journal_entry_id = je.id
    AND je.txn_date >= bd.period_start
    AND je.txn_date < bd.period_start + INTERVAL '1 month'
WHERE bu.name = {budget_name}
GROUP BY a.name, bd.period_start, bd.amount
ORDER BY bd.period_start, a.name;
```

**MySQL note**: Replace `bd.period_start + INTERVAL '1 month'` with `DATE_ADD(bd.period_start, INTERVAL 1 MONTH)`.

---

## Dialect Notes

| Feature | PostgreSQL | MySQL |
|---------|-----------|-------|
| Date arithmetic | `date1 - date2` (returns integer) | `DATEDIFF(date1, date2)` |
| Interval | `+ INTERVAL '1 month'` | `DATE_ADD(col, INTERVAL 1 MONTH)` |
| Boolean | `true` / `false` | `1` / `0` |
| Window functions | Full support | MySQL 8.0+ |
| String concat | `\|\|` | `CONCAT()` |
| NULLIF | Supported | Supported |
| COALESCE | Supported | Supported |
