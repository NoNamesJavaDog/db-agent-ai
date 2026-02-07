# QuickBooks Online Data Model Reference

## Overview

The QBO data model consists of ~30 tables organized into 7 groups. All tables use the `qbo_` prefix.
Every table includes: `id` (primary key), `sync_token` (for future QBO API sync), `created_at`, `updated_at`.

## Entity-Relationship Diagram (Text)

```
qbo_company (1) ─── singleton, holds company settings

qbo_account (N) ──┬── parent_id → qbo_account (self-referencing hierarchy)
                   ├── referenced by all _line tables via account_id
                   └── referenced by qbo_budget_detail

qbo_customer (N) ──── referenced by: invoice, payment, credit_memo, estimate, sales_receipt
qbo_vendor (N)   ──── referenced by: bill, bill_payment, vendor_credit, purchase_order
qbo_employee (N) ──── standalone contact

qbo_item (N) ─────┬── income_account_id → qbo_account
                   ├── expense_account_id → qbo_account
                   ├── asset_account_id → qbo_account
                   └── referenced by all _line tables via item_id

qbo_invoice ─────── qbo_invoice_line (1:N)
qbo_payment ─────── qbo_payment_line (1:N)
qbo_credit_memo ─── qbo_credit_memo_line (1:N)
qbo_estimate ────── qbo_estimate_line (1:N)
qbo_sales_receipt ── qbo_sales_receipt_line (1:N)

qbo_bill ────────── qbo_bill_line (1:N)
qbo_bill_payment ── qbo_bill_payment_line (1:N)
qbo_vendor_credit ── qbo_vendor_credit_line (1:N)
qbo_purchase_order ── qbo_purchase_order_line (1:N)

qbo_journal_entry ── qbo_journal_entry_line (1:N)
qbo_deposit ──────── qbo_deposit_line (1:N)
qbo_transfer ────── standalone (from_account → to_account)

qbo_budget ──────── qbo_budget_detail (1:N)
```

## Table Groups

---

### 1. Base Setup (6 tables)

#### qbo_company
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | INTEGER PK | Yes | Primary key |
| qbo_id | VARCHAR(50) | No | QBO company ID |
| name | VARCHAR(255) | Yes | Company display name |
| legal_name | VARCHAR(255) | No | Legal entity name |
| fiscal_year_start_month | INTEGER | No | 1-12, default 1 (January) |
| country | VARCHAR(10) | No | Country code (US, CA, etc.) |
| currency_code | VARCHAR(3) | No | Default currency (USD, etc.) |
| email | VARCHAR(255) | No | Company email |
| phone | VARCHAR(50) | No | Company phone |
| industry | VARCHAR(100) | No | Industry type |
| sync_token | INTEGER | No | Default 0, for QBO API sync |
| created_at | TIMESTAMP | Yes | Record creation time |
| updated_at | TIMESTAMP | Yes | Last update time |

#### qbo_account
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | INTEGER PK | Yes | Primary key |
| qbo_id | VARCHAR(50) | No | QBO account ID |
| acct_num | VARCHAR(20) | No | Account number |
| name | VARCHAR(255) | Yes | Account name |
| account_type | VARCHAR(50) | Yes | See AccountType enum below |
| account_sub_type | VARCHAR(50) | No | Sub-classification |
| classification | VARCHAR(20) | No | Asset/Liability/Equity/Revenue/Expense |
| current_balance | DECIMAL(15,2) | No | Default 0.00 |
| currency_code | VARCHAR(3) | No | Account currency |
| description | TEXT | No | Account description |
| active | BOOLEAN | No | Default true |
| parent_id | INTEGER FK | No | → qbo_account.id (hierarchy) |
| sync_token | INTEGER | No | Default 0 |
| created_at | TIMESTAMP | Yes | |
| updated_at | TIMESTAMP | Yes | |

**Indexes**: account_type, classification, parent_id, active

#### qbo_tax_code
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | INTEGER PK | Yes | Primary key |
| qbo_id | VARCHAR(50) | No | QBO tax code ID |
| name | VARCHAR(100) | Yes | Tax code name |
| description | VARCHAR(255) | No | Description |
| active | BOOLEAN | No | Default true |
| taxable | BOOLEAN | No | Whether this code means taxable |
| sync_token | INTEGER | No | Default 0 |
| created_at | TIMESTAMP | Yes | |
| updated_at | TIMESTAMP | Yes | |

#### qbo_tax_rate
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | INTEGER PK | Yes | Primary key |
| qbo_id | VARCHAR(50) | No | QBO tax rate ID |
| name | VARCHAR(100) | Yes | Rate name |
| rate_value | DECIMAL(8,4) | No | Rate percentage |
| agency_ref | VARCHAR(100) | No | Tax agency reference |
| description | VARCHAR(255) | No | Description |
| active | BOOLEAN | No | Default true |
| sync_token | INTEGER | No | Default 0 |
| created_at | TIMESTAMP | Yes | |
| updated_at | TIMESTAMP | Yes | |

#### qbo_payment_method
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | INTEGER PK | Yes | Primary key |
| qbo_id | VARCHAR(50) | No | QBO payment method ID |
| name | VARCHAR(100) | Yes | Method name |
| type | VARCHAR(20) | No | Cash/Check/CreditCard/BankTransfer/Other |
| active | BOOLEAN | No | Default true |
| sync_token | INTEGER | No | Default 0 |
| created_at | TIMESTAMP | Yes | |
| updated_at | TIMESTAMP | Yes | |

#### qbo_term
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | INTEGER PK | Yes | Primary key |
| qbo_id | VARCHAR(50) | No | QBO term ID |
| name | VARCHAR(100) | Yes | Term name (e.g., Net 30) |
| due_days | INTEGER | No | Days until due |
| discount_percent | DECIMAL(5,2) | No | Early payment discount % |
| discount_days | INTEGER | No | Days for discount eligibility |
| active | BOOLEAN | No | Default true |
| sync_token | INTEGER | No | Default 0 |
| created_at | TIMESTAMP | Yes | |
| updated_at | TIMESTAMP | Yes | |

---

### 2. Contacts (3 tables)

#### qbo_customer
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | INTEGER PK | Yes | Primary key |
| qbo_id | VARCHAR(50) | No | QBO customer ID |
| display_name | VARCHAR(255) | Yes | Display name |
| company_name | VARCHAR(255) | No | Company name |
| given_name | VARCHAR(100) | No | First name |
| family_name | VARCHAR(100) | No | Last name |
| email | VARCHAR(255) | No | Primary email |
| phone | VARCHAR(50) | No | Primary phone |
| billing_address | TEXT | No | Billing address (JSON or text) |
| shipping_address | TEXT | No | Shipping address |
| balance | DECIMAL(15,2) | No | Default 0.00, outstanding balance |
| currency_code | VARCHAR(3) | No | Customer currency |
| taxable | BOOLEAN | No | Default true |
| tax_code_id | INTEGER FK | No | → qbo_tax_code.id |
| term_id | INTEGER FK | No | → qbo_term.id |
| parent_id | INTEGER FK | No | → qbo_customer.id (sub-customer) |
| active | BOOLEAN | No | Default true |
| sync_token | INTEGER | No | Default 0 |
| created_at | TIMESTAMP | Yes | |
| updated_at | TIMESTAMP | Yes | |

**Indexes**: display_name, email, active, balance

#### qbo_vendor
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | INTEGER PK | Yes | Primary key |
| qbo_id | VARCHAR(50) | No | QBO vendor ID |
| display_name | VARCHAR(255) | Yes | Display name |
| company_name | VARCHAR(255) | No | Company name |
| given_name | VARCHAR(100) | No | First name |
| family_name | VARCHAR(100) | No | Last name |
| email | VARCHAR(255) | No | Primary email |
| phone | VARCHAR(50) | No | Primary phone |
| billing_address | TEXT | No | Billing address |
| balance | DECIMAL(15,2) | No | Default 0.00, outstanding balance |
| acct_num | VARCHAR(50) | No | Vendor account number |
| is_1099 | BOOLEAN | No | Default false, 1099 contractor |
| term_id | INTEGER FK | No | → qbo_term.id |
| currency_code | VARCHAR(3) | No | Vendor currency |
| active | BOOLEAN | No | Default true |
| sync_token | INTEGER | No | Default 0 |
| created_at | TIMESTAMP | Yes | |
| updated_at | TIMESTAMP | Yes | |

**Indexes**: display_name, email, active, balance

#### qbo_employee
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | INTEGER PK | Yes | Primary key |
| qbo_id | VARCHAR(50) | No | QBO employee ID |
| display_name | VARCHAR(255) | Yes | Display name |
| given_name | VARCHAR(100) | No | First name |
| family_name | VARCHAR(100) | No | Last name |
| email | VARCHAR(255) | No | Email |
| phone | VARCHAR(50) | No | Phone |
| hired_date | DATE | No | Hire date |
| released_date | DATE | No | Termination date |
| active | BOOLEAN | No | Default true |
| sync_token | INTEGER | No | Default 0 |
| created_at | TIMESTAMP | Yes | |
| updated_at | TIMESTAMP | Yes | |

---

### 3. Products (1 table)

#### qbo_item
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | INTEGER PK | Yes | Primary key |
| qbo_id | VARCHAR(50) | No | QBO item ID |
| name | VARCHAR(255) | Yes | Item name |
| type | VARCHAR(30) | Yes | Inventory/NonInventory/Service/Bundle |
| description | TEXT | No | Sales description |
| purchase_desc | TEXT | No | Purchase description |
| unit_price | DECIMAL(15,2) | No | Sales price |
| purchase_cost | DECIMAL(15,2) | No | Purchase cost |
| qty_on_hand | DECIMAL(15,4) | No | Current quantity in stock |
| sku | VARCHAR(50) | No | SKU code |
| income_account_id | INTEGER FK | No | → qbo_account.id (sales) |
| expense_account_id | INTEGER FK | No | → qbo_account.id (COGS/expense) |
| asset_account_id | INTEGER FK | No | → qbo_account.id (inventory asset) |
| taxable | BOOLEAN | No | Default true |
| active | BOOLEAN | No | Default true |
| sync_token | INTEGER | No | Default 0 |
| created_at | TIMESTAMP | Yes | |
| updated_at | TIMESTAMP | Yes | |

**Indexes**: name, type, sku, active

---

### 4. Accounts Receivable — AR (10 tables: 5 header + 5 line)

#### Header Tables

| Table | Key Fields |
|-------|-----------|
| qbo_invoice | customer_id, doc_number, txn_date, due_date, total_amt, balance, email_status, term_id |
| qbo_payment | customer_id, txn_date, total_amt, payment_method_id, deposit_to_account_id, unapplied_amt |
| qbo_credit_memo | customer_id, txn_date, total_amt, remaining_credit |
| qbo_estimate | customer_id, txn_date, expiration_date, total_amt, accepted_date, status |
| qbo_sales_receipt | customer_id, txn_date, total_amt, payment_method_id, deposit_to_account_id |

All AR header tables include: customer_id FK → qbo_customer.id, doc_number, txn_date, total_amt, memo, sync_token, created_at, updated_at.

**Indexes on all header tables**: customer_id, txn_date, doc_number

#### qbo_invoice (additional fields)
- due_date DATE
- balance DECIMAL(15,2) — remaining unpaid amount
- email_status VARCHAR(20) — NotSet/NeedToSend/EmailSent
- term_id FK → qbo_term.id
- ar_account_id FK → qbo_account.id

#### qbo_payment (additional fields)
- payment_method_id FK → qbo_payment_method.id
- deposit_to_account_id FK → qbo_account.id
- unapplied_amt DECIMAL(15,2) — unapplied payment amount

#### qbo_estimate (additional fields)
- expiration_date DATE
- accepted_date DATE
- status VARCHAR(20) — Pending/Accepted/Closed/Rejected

---

### 5. Accounts Payable — AP (8 tables: 4 header + 4 line)

| Table | Key Fields |
|-------|-----------|
| qbo_bill | vendor_id, doc_number, txn_date, due_date, total_amt, balance, ap_account_id, term_id |
| qbo_bill_payment | vendor_id, txn_date, total_amt, pay_type, check_bank_account_id, cc_account_id |
| qbo_vendor_credit | vendor_id, txn_date, total_amt, balance |
| qbo_purchase_order | vendor_id, doc_number, txn_date, total_amt, status, email_status |

All AP header tables include: vendor_id FK → qbo_vendor.id, doc_number, txn_date, total_amt, memo, sync_token, created_at, updated_at.

**Indexes on all header tables**: vendor_id, txn_date, doc_number

#### qbo_bill_payment (additional fields)
- pay_type VARCHAR(20) — Check/CreditCard
- check_bank_account_id FK → qbo_account.id
- cc_account_id FK → qbo_account.id

#### qbo_purchase_order (additional fields)
- status VARCHAR(20) — Open/Closed
- email_status VARCHAR(20) — NotSet/NeedToSend/EmailSent

---

### 6. General Ledger — GL (5 tables)

#### qbo_journal_entry
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | INTEGER PK | Yes | Primary key |
| qbo_id | VARCHAR(50) | No | QBO ID |
| doc_number | VARCHAR(50) | No | Document number |
| txn_date | DATE | Yes | Transaction date |
| total_amt | DECIMAL(15,2) | No | Total amount |
| adjustment | BOOLEAN | No | Default false, is adjustment entry |
| memo | TEXT | No | Memo / description |
| sync_token | INTEGER | No | Default 0 |
| created_at | TIMESTAMP | Yes | |
| updated_at | TIMESTAMP | Yes | |

#### qbo_journal_entry_line
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | INTEGER PK | Yes | Primary key |
| journal_entry_id | INTEGER FK | Yes | → qbo_journal_entry.id |
| line_num | INTEGER | No | Line sequence |
| posting_type | VARCHAR(10) | Yes | Debit or Credit |
| amount | DECIMAL(15,2) | Yes | Line amount |
| account_id | INTEGER FK | Yes | → qbo_account.id |
| description | TEXT | No | Line description |
| entity_type | VARCHAR(50) | No | Customer/Vendor/Employee |
| entity_id | INTEGER | No | Reference to entity |
| sync_token | INTEGER | No | Default 0 |
| created_at | TIMESTAMP | Yes | |
| updated_at | TIMESTAMP | Yes | |

**Indexes**: journal_entry_id, account_id, posting_type

#### qbo_transfer
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | INTEGER PK | Yes | Primary key |
| qbo_id | VARCHAR(50) | No | QBO ID |
| txn_date | DATE | Yes | Transfer date |
| from_account_id | INTEGER FK | Yes | → qbo_account.id |
| to_account_id | INTEGER FK | Yes | → qbo_account.id |
| amount | DECIMAL(15,2) | Yes | Transfer amount |
| memo | TEXT | No | |
| sync_token | INTEGER | No | Default 0 |
| created_at | TIMESTAMP | Yes | |
| updated_at | TIMESTAMP | Yes | |

#### qbo_deposit / qbo_deposit_line
- qbo_deposit: txn_date, deposit_to_account_id FK, total_amt, memo
- qbo_deposit_line: deposit_id FK, line_num, amount, account_id FK, entity_type, entity_id, payment_id FK → qbo_payment.id

---

### 7. Budget (2 tables)

#### qbo_budget
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | INTEGER PK | Yes | Primary key |
| qbo_id | VARCHAR(50) | No | QBO ID |
| name | VARCHAR(255) | Yes | Budget name |
| start_date | DATE | No | Budget start |
| end_date | DATE | No | Budget end |
| budget_type | VARCHAR(30) | No | ProfitAndLoss / BalanceSheet |
| active | BOOLEAN | No | Default true |
| sync_token | INTEGER | No | Default 0 |
| created_at | TIMESTAMP | Yes | |
| updated_at | TIMESTAMP | Yes | |

#### qbo_budget_detail
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | INTEGER PK | Yes | Primary key |
| budget_id | INTEGER FK | Yes | → qbo_budget.id |
| account_id | INTEGER FK | Yes | → qbo_account.id |
| period_start | DATE | Yes | Period start date |
| amount | DECIMAL(15,2) | No | Budgeted amount |
| created_at | TIMESTAMP | Yes | |
| updated_at | TIMESTAMP | Yes | |

**Indexes**: budget_id, account_id, period_start

---

## Line Item Table — Unified Schema

All `_line` tables share this common structure:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | INTEGER PK | Yes | Primary key |
| {header}_id | INTEGER FK | Yes | → parent header table |
| line_num | INTEGER | No | Line sequence number |
| item_id | INTEGER FK | No | → qbo_item.id |
| description | TEXT | No | Line description |
| quantity | DECIMAL(15,4) | No | Quantity |
| unit_price | DECIMAL(15,2) | No | Unit price |
| amount | DECIMAL(15,2) | No | Line total (qty × price or override) |
| account_id | INTEGER FK | No | → qbo_account.id |
| tax_code_id | INTEGER FK | No | → qbo_tax_code.id |
| created_at | TIMESTAMP | Yes | |
| updated_at | TIMESTAMP | Yes | |

**Exceptions**:
- `qbo_journal_entry_line` adds: posting_type, entity_type, entity_id (see GL section)
- `qbo_deposit_line` adds: entity_type, entity_id, payment_id
- `qbo_payment_line` adds: invoice_id FK → qbo_invoice.id (links payment to invoice)
- `qbo_bill_payment_line` adds: bill_id FK → qbo_bill.id (links payment to bill)

---

## AccountType Enum Values

| AccountType | Classification | Normal Balance | Financial Statement |
|-------------|---------------|----------------|-------------------|
| Bank | Asset | Debit | Balance Sheet |
| AccountsReceivable | Asset | Debit | Balance Sheet |
| OtherCurrentAsset | Asset | Debit | Balance Sheet |
| FixedAsset | Asset | Debit | Balance Sheet |
| OtherAsset | Asset | Debit | Balance Sheet |
| AccountsPayable | Liability | Credit | Balance Sheet |
| CreditCard | Liability | Credit | Balance Sheet |
| OtherCurrentLiability | Liability | Credit | Balance Sheet |
| LongTermLiability | Liability | Credit | Balance Sheet |
| Equity | Equity | Credit | Balance Sheet |
| Income | Revenue | Credit | Profit & Loss |
| CostOfGoodsSold | Expense | Debit | Profit & Loss |
| Expense | Expense | Debit | Profit & Loss |
| OtherIncome | Revenue | Credit | Profit & Loss |
| OtherExpense | Expense | Debit | Profit & Loss |

---

## sync_token Field

Every table includes `sync_token INTEGER DEFAULT 0`. This field is reserved for future QuickBooks Online API integration:
- QBO uses sync_token for optimistic concurrency control
- On each update via API, sync_token must match the current value
- After successful update, QBO increments the token
- Currently unused for local-only operations; always defaults to 0
