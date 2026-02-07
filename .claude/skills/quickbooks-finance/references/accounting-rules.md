# QuickBooks Online Accounting Rules & Business Logic

## 1. Double-Entry Bookkeeping

Every financial transaction records equal debits and credits:

```
Total Debits = Total Credits (for every journal entry)
```

Verification query: For each `qbo_journal_entry`, sum of lines where `posting_type = 'Debit'` MUST equal sum where `posting_type = 'Credit'`.

### Normal Balances by Account Type

| Account Type | Normal Balance | Increases With | Decreases With |
|-------------|---------------|----------------|----------------|
| Asset (Bank, AR, FixedAsset, etc.) | Debit | Debit | Credit |
| Expense, CostOfGoodsSold | Debit | Debit | Credit |
| Liability (AP, CreditCard, etc.) | Credit | Credit | Debit |
| Equity | Credit | Credit | Debit |
| Income, OtherIncome | Credit | Credit | Debit |

### The Accounting Equation

```
Assets = Liabilities + Equity
```

At any point in time, the sum of all Asset account balances must equal the sum of Liability + Equity account balances. Income and Expense accounts are temporary — they flow into Retained Earnings at period close.

---

## 2. AR Business Flow

```
Estimate → Invoice → Payment → Deposit
```

1. **Estimate** (`qbo_estimate`): Non-posting quote to customer. Status: Pending → Accepted/Rejected/Closed.
2. **Invoice** (`qbo_invoice`): Posts AR. Creates receivable from customer.
   - Debit: Accounts Receivable
   - Credit: Income / Sales account (per line item)
3. **Payment** (`qbo_payment`): Reduces AR. Links to one or more invoices via `qbo_payment_line`.
   - Debit: Undeposited Funds (or bank account)
   - Credit: Accounts Receivable
4. **Deposit** (`qbo_deposit`): Moves funds from Undeposited Funds to bank.
   - Debit: Bank account
   - Credit: Undeposited Funds
5. **Credit Memo** (`qbo_credit_memo`): Reduces AR. Can apply to outstanding invoices.
   - Debit: Income account (reversal)
   - Credit: Accounts Receivable
6. **Sales Receipt** (`qbo_sales_receipt`): Combined invoice + payment (immediate sale).
   - Debit: Undeposited Funds / Bank
   - Credit: Income account

---

## 3. AP Business Flow

```
Purchase Order → Bill → Bill Payment
```

1. **Purchase Order** (`qbo_purchase_order`): Non-posting order to vendor. Status: Open/Closed.
2. **Bill** (`qbo_bill`): Posts AP. Creates payable to vendor.
   - Debit: Expense / Inventory Asset / other account (per line)
   - Credit: Accounts Payable
3. **Bill Payment** (`qbo_bill_payment`): Reduces AP. Links to bills via `qbo_bill_payment_line`.
   - Debit: Accounts Payable
   - Credit: Bank account (Check) or Credit Card account
4. **Vendor Credit** (`qbo_vendor_credit`): Reduces AP. Credit from vendor.
   - Debit: Accounts Payable
   - Credit: Expense account (reversal)

---

## 4. Inventory & COGS Flow

```
Purchase (acquire) → Stock (hold) → Sale (release)
```

- **Purchase** (via Bill or Check):
  - Debit: Inventory Asset (qbo_account where account_type = 'OtherCurrentAsset', sub_type = InventoryAsset)
  - Credit: Accounts Payable / Bank
- **Sale** (via Invoice or Sales Receipt):
  - Debit: Cost of Goods Sold
  - Credit: Inventory Asset
  - (Simultaneously) Debit: AR / Bank, Credit: Income
- **Valuation**: `qbo_item.qty_on_hand × qbo_item.purchase_cost`

---

## 5. Period-End Close

At period end (monthly, quarterly, annually):
1. All Income and Expense accounts are netted → **Net Income**
2. Net Income is transferred to **Retained Earnings** (Equity account)
3. Income and Expense accounts reset to zero for the new period

This is a logical close — QBO does it automatically. For reporting, filter by date range.

---

## 6. KPI Formulas

### Liquidity Ratios

```
Current Ratio = Current Assets / Current Liabilities
```
- Current Assets = SUM(balance) WHERE account_type IN ('Bank', 'AccountsReceivable', 'OtherCurrentAsset')
- Current Liabilities = SUM(balance) WHERE account_type IN ('AccountsPayable', 'CreditCard', 'OtherCurrentLiability')
- 🟢 > 2.0 | 🟡 1.0–2.0 | 🔴 < 1.0

```
Quick Ratio = (Current Assets - Inventory) / Current Liabilities
```
- Exclude Inventory Asset from current assets
- 🟢 > 1.5 | 🟡 1.0–1.5 | 🔴 < 1.0

### Efficiency Ratios

```
DSO (Days Sales Outstanding) = (Accounts Receivable / Total Credit Sales) × Days in Period
```
- AR = SUM(balance) from qbo_invoice WHERE balance > 0
- Credit Sales = SUM(total_amt) from qbo_invoice for the period
- 🟢 < 30 days | 🟡 30–60 days | 🔴 > 60 days

```
DPO (Days Payable Outstanding) = (Accounts Payable / COGS) × Days in Period
```
- AP = SUM(balance) from qbo_bill WHERE balance > 0
- COGS = SUM(balance) from qbo_account WHERE account_type = 'CostOfGoodsSold' for the period
- 🟢 30–60 days | 🟡 > 60 or < 20 days | 🔴 > 90 days

### Profitability Ratios

```
Gross Margin % = (Revenue - COGS) / Revenue × 100
```
- Revenue = SUM from accounts WHERE account_type IN ('Income')
- COGS = SUM from accounts WHERE account_type IN ('CostOfGoodsSold')
- 🟢 > 40% | 🟡 20–40% | 🔴 < 20%

```
Net Margin % = Net Income / Revenue × 100
```
- Net Income = Revenue - COGS - Expenses
- 🟢 > 15% | 🟡 5–15% | 🔴 < 5%

---

## 7. Aging Bucket Rules

Based on the difference between the document's `due_date` and the current date:

```
Days Overdue = CURRENT_DATE - due_date
```

| Bucket | Condition |
|--------|-----------|
| Current | due_date >= CURRENT_DATE (not yet due) |
| 1-30 | 1 <= Days Overdue <= 30 |
| 31-60 | 31 <= Days Overdue <= 60 |
| 61-90 | 61 <= Days Overdue <= 90 |
| 90+ | Days Overdue > 90 |

For AR aging: Use `qbo_invoice.due_date` WHERE `balance > 0`.
For AP aging: Use `qbo_bill.due_date` WHERE `balance > 0`.

---

## 8. Reconciliation Rules

### AR Sub-ledger to GL
```
SUM(qbo_invoice.balance) - SUM(qbo_credit_memo.remaining_credit)
  = qbo_account.current_balance WHERE account_type = 'AccountsReceivable'
```

### AP Sub-ledger to GL
```
SUM(qbo_bill.balance) - SUM(qbo_vendor_credit.balance)
  = qbo_account.current_balance WHERE account_type = 'AccountsPayable'
```

### Bank Reconciliation
```
GL Bank Balance = Opening Balance + SUM(Deposits) - SUM(Withdrawals)
```

### Trial Balance
```
SUM(all Debit balances) = SUM(all Credit balances)
```
If imbalanced, investigate recent journal entries and sub-ledger postings.

---

## 9. Date Period Handling

When the user specifies a period, interpret as follows:

| Input | Interpretation |
|-------|---------------|
| `2024` | Full year: 2024-01-01 to 2024-12-31 |
| `2024-Q1` | Quarter: 2024-01-01 to 2024-03-31 |
| `2024-Q2` | Quarter: 2024-04-01 to 2024-06-30 |
| `2024-Q3` | Quarter: 2024-07-01 to 2024-09-30 |
| `2024-Q4` | Quarter: 2024-10-01 to 2024-12-31 |
| `2024-03` | Month: 2024-03-01 to 2024-03-31 |
| `2024-01-01 to 2024-06-30` | Explicit range |
| (none specified) | Current fiscal year to date |

Use the company's `fiscal_year_start_month` from `qbo_company` when calculating YTD or fiscal periods.
