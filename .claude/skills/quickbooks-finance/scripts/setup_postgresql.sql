-- ============================================================
-- QuickBooks Online Financial Database Schema - PostgreSQL
-- Generated for db-agent-ai quickbooks-finance skill
-- ============================================================

-- ============================================================
-- 1. Base Setup Tables
-- ============================================================

CREATE TABLE IF NOT EXISTS qbo_company (
    id SERIAL PRIMARY KEY,
    qbo_id VARCHAR(50),
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    fiscal_year_start_month INTEGER DEFAULT 1,
    country VARCHAR(10),
    currency_code VARCHAR(3) DEFAULT 'USD',
    email VARCHAR(255),
    phone VARCHAR(50),
    industry VARCHAR(100),
    sync_token INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS qbo_account (
    id SERIAL PRIMARY KEY,
    qbo_id VARCHAR(50),
    acct_num VARCHAR(20),
    name VARCHAR(255) NOT NULL,
    account_type VARCHAR(50) NOT NULL CHECK (account_type IN (
        'Bank', 'AccountsReceivable', 'OtherCurrentAsset', 'FixedAsset', 'OtherAsset',
        'AccountsPayable', 'CreditCard', 'OtherCurrentLiability', 'LongTermLiability',
        'Equity', 'Income', 'CostOfGoodsSold', 'Expense', 'OtherIncome', 'OtherExpense'
    )),
    account_sub_type VARCHAR(50),
    classification VARCHAR(20) CHECK (classification IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')),
    current_balance DECIMAL(15,2) DEFAULT 0.00,
    currency_code VARCHAR(3),
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    parent_id INTEGER REFERENCES qbo_account(id),
    sync_token INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qbo_account_type ON qbo_account(account_type);
CREATE INDEX IF NOT EXISTS idx_qbo_account_classification ON qbo_account(classification);
CREATE INDEX IF NOT EXISTS idx_qbo_account_parent ON qbo_account(parent_id);
CREATE INDEX IF NOT EXISTS idx_qbo_account_active ON qbo_account(active);

CREATE TABLE IF NOT EXISTS qbo_tax_code (
    id SERIAL PRIMARY KEY,
    qbo_id VARCHAR(50),
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    active BOOLEAN DEFAULT TRUE,
    taxable BOOLEAN DEFAULT FALSE,
    sync_token INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS qbo_tax_rate (
    id SERIAL PRIMARY KEY,
    qbo_id VARCHAR(50),
    name VARCHAR(100) NOT NULL,
    rate_value DECIMAL(8,4),
    agency_ref VARCHAR(100),
    description VARCHAR(255),
    active BOOLEAN DEFAULT TRUE,
    sync_token INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS qbo_payment_method (
    id SERIAL PRIMARY KEY,
    qbo_id VARCHAR(50),
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) CHECK (type IN ('Cash', 'Check', 'CreditCard', 'BankTransfer', 'Other')),
    active BOOLEAN DEFAULT TRUE,
    sync_token INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS qbo_term (
    id SERIAL PRIMARY KEY,
    qbo_id VARCHAR(50),
    name VARCHAR(100) NOT NULL,
    due_days INTEGER,
    discount_percent DECIMAL(5,2),
    discount_days INTEGER,
    active BOOLEAN DEFAULT TRUE,
    sync_token INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 2. Contact Tables
-- ============================================================

CREATE TABLE IF NOT EXISTS qbo_customer (
    id SERIAL PRIMARY KEY,
    qbo_id VARCHAR(50),
    display_name VARCHAR(255) NOT NULL,
    company_name VARCHAR(255),
    given_name VARCHAR(100),
    family_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(50),
    billing_address TEXT,
    shipping_address TEXT,
    balance DECIMAL(15,2) DEFAULT 0.00,
    currency_code VARCHAR(3),
    taxable BOOLEAN DEFAULT TRUE,
    tax_code_id INTEGER REFERENCES qbo_tax_code(id),
    term_id INTEGER REFERENCES qbo_term(id),
    parent_id INTEGER REFERENCES qbo_customer(id),
    active BOOLEAN DEFAULT TRUE,
    sync_token INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qbo_customer_name ON qbo_customer(display_name);
CREATE INDEX IF NOT EXISTS idx_qbo_customer_email ON qbo_customer(email);
CREATE INDEX IF NOT EXISTS idx_qbo_customer_active ON qbo_customer(active);
CREATE INDEX IF NOT EXISTS idx_qbo_customer_balance ON qbo_customer(balance);

CREATE TABLE IF NOT EXISTS qbo_vendor (
    id SERIAL PRIMARY KEY,
    qbo_id VARCHAR(50),
    display_name VARCHAR(255) NOT NULL,
    company_name VARCHAR(255),
    given_name VARCHAR(100),
    family_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(50),
    billing_address TEXT,
    balance DECIMAL(15,2) DEFAULT 0.00,
    acct_num VARCHAR(50),
    is_1099 BOOLEAN DEFAULT FALSE,
    term_id INTEGER REFERENCES qbo_term(id),
    currency_code VARCHAR(3),
    active BOOLEAN DEFAULT TRUE,
    sync_token INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qbo_vendor_name ON qbo_vendor(display_name);
CREATE INDEX IF NOT EXISTS idx_qbo_vendor_email ON qbo_vendor(email);
CREATE INDEX IF NOT EXISTS idx_qbo_vendor_active ON qbo_vendor(active);
CREATE INDEX IF NOT EXISTS idx_qbo_vendor_balance ON qbo_vendor(balance);

CREATE TABLE IF NOT EXISTS qbo_employee (
    id SERIAL PRIMARY KEY,
    qbo_id VARCHAR(50),
    display_name VARCHAR(255) NOT NULL,
    given_name VARCHAR(100),
    family_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(50),
    hired_date DATE,
    released_date DATE,
    active BOOLEAN DEFAULT TRUE,
    sync_token INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 3. Product / Item Table
-- ============================================================

CREATE TABLE IF NOT EXISTS qbo_item (
    id SERIAL PRIMARY KEY,
    qbo_id VARCHAR(50),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(30) NOT NULL CHECK (type IN ('Inventory', 'NonInventory', 'Service', 'Bundle')),
    description TEXT,
    purchase_desc TEXT,
    unit_price DECIMAL(15,2),
    purchase_cost DECIMAL(15,2),
    qty_on_hand DECIMAL(15,4),
    sku VARCHAR(50),
    income_account_id INTEGER REFERENCES qbo_account(id),
    expense_account_id INTEGER REFERENCES qbo_account(id),
    asset_account_id INTEGER REFERENCES qbo_account(id),
    taxable BOOLEAN DEFAULT TRUE,
    active BOOLEAN DEFAULT TRUE,
    sync_token INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qbo_item_name ON qbo_item(name);
CREATE INDEX IF NOT EXISTS idx_qbo_item_type ON qbo_item(type);
CREATE INDEX IF NOT EXISTS idx_qbo_item_sku ON qbo_item(sku);
CREATE INDEX IF NOT EXISTS idx_qbo_item_active ON qbo_item(active);

-- ============================================================
-- 4. Accounts Receivable (AR) Tables
-- ============================================================

-- Invoice
CREATE TABLE IF NOT EXISTS qbo_invoice (
    id SERIAL PRIMARY KEY,
    qbo_id VARCHAR(50),
    customer_id INTEGER NOT NULL REFERENCES qbo_customer(id),
    doc_number VARCHAR(50),
    txn_date DATE NOT NULL,
    due_date DATE,
    total_amt DECIMAL(15,2) DEFAULT 0.00,
    balance DECIMAL(15,2) DEFAULT 0.00,
    email_status VARCHAR(20) DEFAULT 'NotSet',
    term_id INTEGER REFERENCES qbo_term(id),
    ar_account_id INTEGER REFERENCES qbo_account(id),
    memo TEXT,
    sync_token INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qbo_invoice_customer ON qbo_invoice(customer_id);
CREATE INDEX IF NOT EXISTS idx_qbo_invoice_txn_date ON qbo_invoice(txn_date);
CREATE INDEX IF NOT EXISTS idx_qbo_invoice_due_date ON qbo_invoice(due_date);
CREATE INDEX IF NOT EXISTS idx_qbo_invoice_doc_number ON qbo_invoice(doc_number);

CREATE TABLE IF NOT EXISTS qbo_invoice_line (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL REFERENCES qbo_invoice(id) ON DELETE CASCADE,
    line_num INTEGER,
    item_id INTEGER REFERENCES qbo_item(id),
    description TEXT,
    quantity DECIMAL(15,4),
    unit_price DECIMAL(15,2),
    amount DECIMAL(15,2),
    account_id INTEGER REFERENCES qbo_account(id),
    tax_code_id INTEGER REFERENCES qbo_tax_code(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qbo_invoice_line_invoice ON qbo_invoice_line(invoice_id);

-- Payment
CREATE TABLE IF NOT EXISTS qbo_payment (
    id SERIAL PRIMARY KEY,
    qbo_id VARCHAR(50),
    customer_id INTEGER NOT NULL REFERENCES qbo_customer(id),
    doc_number VARCHAR(50),
    txn_date DATE NOT NULL,
    total_amt DECIMAL(15,2) DEFAULT 0.00,
    payment_method_id INTEGER REFERENCES qbo_payment_method(id),
    deposit_to_account_id INTEGER REFERENCES qbo_account(id),
    unapplied_amt DECIMAL(15,2) DEFAULT 0.00,
    memo TEXT,
    sync_token INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qbo_payment_customer ON qbo_payment(customer_id);
CREATE INDEX IF NOT EXISTS idx_qbo_payment_txn_date ON qbo_payment(txn_date);

CREATE TABLE IF NOT EXISTS qbo_payment_line (
    id SERIAL PRIMARY KEY,
    payment_id INTEGER NOT NULL REFERENCES qbo_payment(id) ON DELETE CASCADE,
    line_num INTEGER,
    invoice_id INTEGER REFERENCES qbo_invoice(id),
    amount DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qbo_payment_line_payment ON qbo_payment_line(payment_id);
CREATE INDEX IF NOT EXISTS idx_qbo_payment_line_invoice ON qbo_payment_line(invoice_id);

-- Credit Memo
CREATE TABLE IF NOT EXISTS qbo_credit_memo (
    id SERIAL PRIMARY KEY,
    qbo_id VARCHAR(50),
    customer_id INTEGER NOT NULL REFERENCES qbo_customer(id),
    doc_number VARCHAR(50),
    txn_date DATE NOT NULL,
    total_amt DECIMAL(15,2) DEFAULT 0.00,
    remaining_credit DECIMAL(15,2) DEFAULT 0.00,
    memo TEXT,
    sync_token INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qbo_credit_memo_customer ON qbo_credit_memo(customer_id);
CREATE INDEX IF NOT EXISTS idx_qbo_credit_memo_txn_date ON qbo_credit_memo(txn_date);

CREATE TABLE IF NOT EXISTS qbo_credit_memo_line (
    id SERIAL PRIMARY KEY,
    credit_memo_id INTEGER NOT NULL REFERENCES qbo_credit_memo(id) ON DELETE CASCADE,
    line_num INTEGER,
    item_id INTEGER REFERENCES qbo_item(id),
    description TEXT,
    quantity DECIMAL(15,4),
    unit_price DECIMAL(15,2),
    amount DECIMAL(15,2),
    account_id INTEGER REFERENCES qbo_account(id),
    tax_code_id INTEGER REFERENCES qbo_tax_code(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qbo_credit_memo_line_memo ON qbo_credit_memo_line(credit_memo_id);

-- Estimate
CREATE TABLE IF NOT EXISTS qbo_estimate (
    id SERIAL PRIMARY KEY,
    qbo_id VARCHAR(50),
    customer_id INTEGER NOT NULL REFERENCES qbo_customer(id),
    doc_number VARCHAR(50),
    txn_date DATE NOT NULL,
    expiration_date DATE,
    total_amt DECIMAL(15,2) DEFAULT 0.00,
    accepted_date DATE,
    status VARCHAR(20) DEFAULT 'Pending' CHECK (status IN ('Pending', 'Accepted', 'Closed', 'Rejected')),
    memo TEXT,
    sync_token INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qbo_estimate_customer ON qbo_estimate(customer_id);
CREATE INDEX IF NOT EXISTS idx_qbo_estimate_txn_date ON qbo_estimate(txn_date);

CREATE TABLE IF NOT EXISTS qbo_estimate_line (
    id SERIAL PRIMARY KEY,
    estimate_id INTEGER NOT NULL REFERENCES qbo_estimate(id) ON DELETE CASCADE,
    line_num INTEGER,
    item_id INTEGER REFERENCES qbo_item(id),
    description TEXT,
    quantity DECIMAL(15,4),
    unit_price DECIMAL(15,2),
    amount DECIMAL(15,2),
    account_id INTEGER REFERENCES qbo_account(id),
    tax_code_id INTEGER REFERENCES qbo_tax_code(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qbo_estimate_line_estimate ON qbo_estimate_line(estimate_id);

-- Sales Receipt
CREATE TABLE IF NOT EXISTS qbo_sales_receipt (
    id SERIAL PRIMARY KEY,
    qbo_id VARCHAR(50),
    customer_id INTEGER NOT NULL REFERENCES qbo_customer(id),
    doc_number VARCHAR(50),
    txn_date DATE NOT NULL,
    total_amt DECIMAL(15,2) DEFAULT 0.00,
    payment_method_id INTEGER REFERENCES qbo_payment_method(id),
    deposit_to_account_id INTEGER REFERENCES qbo_account(id),
    memo TEXT,
    sync_token INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qbo_sales_receipt_customer ON qbo_sales_receipt(customer_id);
CREATE INDEX IF NOT EXISTS idx_qbo_sales_receipt_txn_date ON qbo_sales_receipt(txn_date);

CREATE TABLE IF NOT EXISTS qbo_sales_receipt_line (
    id SERIAL PRIMARY KEY,
    sales_receipt_id INTEGER NOT NULL REFERENCES qbo_sales_receipt(id) ON DELETE CASCADE,
    line_num INTEGER,
    item_id INTEGER REFERENCES qbo_item(id),
    description TEXT,
    quantity DECIMAL(15,4),
    unit_price DECIMAL(15,2),
    amount DECIMAL(15,2),
    account_id INTEGER REFERENCES qbo_account(id),
    tax_code_id INTEGER REFERENCES qbo_tax_code(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qbo_sales_receipt_line_receipt ON qbo_sales_receipt_line(sales_receipt_id);

-- ============================================================
-- 5. Accounts Payable (AP) Tables
-- ============================================================

-- Bill
CREATE TABLE IF NOT EXISTS qbo_bill (
    id SERIAL PRIMARY KEY,
    qbo_id VARCHAR(50),
    vendor_id INTEGER NOT NULL REFERENCES qbo_vendor(id),
    doc_number VARCHAR(50),
    txn_date DATE NOT NULL,
    due_date DATE,
    total_amt DECIMAL(15,2) DEFAULT 0.00,
    balance DECIMAL(15,2) DEFAULT 0.00,
    ap_account_id INTEGER REFERENCES qbo_account(id),
    term_id INTEGER REFERENCES qbo_term(id),
    memo TEXT,
    sync_token INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qbo_bill_vendor ON qbo_bill(vendor_id);
CREATE INDEX IF NOT EXISTS idx_qbo_bill_txn_date ON qbo_bill(txn_date);
CREATE INDEX IF NOT EXISTS idx_qbo_bill_due_date ON qbo_bill(due_date);
CREATE INDEX IF NOT EXISTS idx_qbo_bill_doc_number ON qbo_bill(doc_number);

CREATE TABLE IF NOT EXISTS qbo_bill_line (
    id SERIAL PRIMARY KEY,
    bill_id INTEGER NOT NULL REFERENCES qbo_bill(id) ON DELETE CASCADE,
    line_num INTEGER,
    item_id INTEGER REFERENCES qbo_item(id),
    description TEXT,
    quantity DECIMAL(15,4),
    unit_price DECIMAL(15,2),
    amount DECIMAL(15,2),
    account_id INTEGER REFERENCES qbo_account(id),
    tax_code_id INTEGER REFERENCES qbo_tax_code(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qbo_bill_line_bill ON qbo_bill_line(bill_id);

-- Bill Payment
CREATE TABLE IF NOT EXISTS qbo_bill_payment (
    id SERIAL PRIMARY KEY,
    qbo_id VARCHAR(50),
    vendor_id INTEGER NOT NULL REFERENCES qbo_vendor(id),
    doc_number VARCHAR(50),
    txn_date DATE NOT NULL,
    total_amt DECIMAL(15,2) DEFAULT 0.00,
    pay_type VARCHAR(20) CHECK (pay_type IN ('Check', 'CreditCard')),
    check_bank_account_id INTEGER REFERENCES qbo_account(id),
    cc_account_id INTEGER REFERENCES qbo_account(id),
    memo TEXT,
    sync_token INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qbo_bill_payment_vendor ON qbo_bill_payment(vendor_id);
CREATE INDEX IF NOT EXISTS idx_qbo_bill_payment_txn_date ON qbo_bill_payment(txn_date);

CREATE TABLE IF NOT EXISTS qbo_bill_payment_line (
    id SERIAL PRIMARY KEY,
    bill_payment_id INTEGER NOT NULL REFERENCES qbo_bill_payment(id) ON DELETE CASCADE,
    line_num INTEGER,
    bill_id INTEGER REFERENCES qbo_bill(id),
    amount DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qbo_bill_payment_line_payment ON qbo_bill_payment_line(bill_payment_id);
CREATE INDEX IF NOT EXISTS idx_qbo_bill_payment_line_bill ON qbo_bill_payment_line(bill_id);

-- Vendor Credit
CREATE TABLE IF NOT EXISTS qbo_vendor_credit (
    id SERIAL PRIMARY KEY,
    qbo_id VARCHAR(50),
    vendor_id INTEGER NOT NULL REFERENCES qbo_vendor(id),
    doc_number VARCHAR(50),
    txn_date DATE NOT NULL,
    total_amt DECIMAL(15,2) DEFAULT 0.00,
    balance DECIMAL(15,2) DEFAULT 0.00,
    memo TEXT,
    sync_token INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qbo_vendor_credit_vendor ON qbo_vendor_credit(vendor_id);
CREATE INDEX IF NOT EXISTS idx_qbo_vendor_credit_txn_date ON qbo_vendor_credit(txn_date);

CREATE TABLE IF NOT EXISTS qbo_vendor_credit_line (
    id SERIAL PRIMARY KEY,
    vendor_credit_id INTEGER NOT NULL REFERENCES qbo_vendor_credit(id) ON DELETE CASCADE,
    line_num INTEGER,
    item_id INTEGER REFERENCES qbo_item(id),
    description TEXT,
    quantity DECIMAL(15,4),
    unit_price DECIMAL(15,2),
    amount DECIMAL(15,2),
    account_id INTEGER REFERENCES qbo_account(id),
    tax_code_id INTEGER REFERENCES qbo_tax_code(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qbo_vendor_credit_line_credit ON qbo_vendor_credit_line(vendor_credit_id);

-- Purchase Order
CREATE TABLE IF NOT EXISTS qbo_purchase_order (
    id SERIAL PRIMARY KEY,
    qbo_id VARCHAR(50),
    vendor_id INTEGER NOT NULL REFERENCES qbo_vendor(id),
    doc_number VARCHAR(50),
    txn_date DATE NOT NULL,
    total_amt DECIMAL(15,2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'Open' CHECK (status IN ('Open', 'Closed')),
    email_status VARCHAR(20) DEFAULT 'NotSet',
    memo TEXT,
    sync_token INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qbo_purchase_order_vendor ON qbo_purchase_order(vendor_id);
CREATE INDEX IF NOT EXISTS idx_qbo_purchase_order_txn_date ON qbo_purchase_order(txn_date);
CREATE INDEX IF NOT EXISTS idx_qbo_purchase_order_doc_number ON qbo_purchase_order(doc_number);

CREATE TABLE IF NOT EXISTS qbo_purchase_order_line (
    id SERIAL PRIMARY KEY,
    purchase_order_id INTEGER NOT NULL REFERENCES qbo_purchase_order(id) ON DELETE CASCADE,
    line_num INTEGER,
    item_id INTEGER REFERENCES qbo_item(id),
    description TEXT,
    quantity DECIMAL(15,4),
    unit_price DECIMAL(15,2),
    amount DECIMAL(15,2),
    account_id INTEGER REFERENCES qbo_account(id),
    tax_code_id INTEGER REFERENCES qbo_tax_code(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qbo_purchase_order_line_po ON qbo_purchase_order_line(purchase_order_id);

-- ============================================================
-- 6. General Ledger (GL) Tables
-- ============================================================

-- Journal Entry
CREATE TABLE IF NOT EXISTS qbo_journal_entry (
    id SERIAL PRIMARY KEY,
    qbo_id VARCHAR(50),
    doc_number VARCHAR(50),
    txn_date DATE NOT NULL,
    total_amt DECIMAL(15,2) DEFAULT 0.00,
    adjustment BOOLEAN DEFAULT FALSE,
    memo TEXT,
    sync_token INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qbo_journal_entry_txn_date ON qbo_journal_entry(txn_date);
CREATE INDEX IF NOT EXISTS idx_qbo_journal_entry_doc_number ON qbo_journal_entry(doc_number);

CREATE TABLE IF NOT EXISTS qbo_journal_entry_line (
    id SERIAL PRIMARY KEY,
    journal_entry_id INTEGER NOT NULL REFERENCES qbo_journal_entry(id) ON DELETE CASCADE,
    line_num INTEGER,
    posting_type VARCHAR(10) NOT NULL CHECK (posting_type IN ('Debit', 'Credit')),
    amount DECIMAL(15,2) NOT NULL,
    account_id INTEGER NOT NULL REFERENCES qbo_account(id),
    description TEXT,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    sync_token INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qbo_je_line_entry ON qbo_journal_entry_line(journal_entry_id);
CREATE INDEX IF NOT EXISTS idx_qbo_je_line_account ON qbo_journal_entry_line(account_id);
CREATE INDEX IF NOT EXISTS idx_qbo_je_line_posting ON qbo_journal_entry_line(posting_type);

-- Transfer
CREATE TABLE IF NOT EXISTS qbo_transfer (
    id SERIAL PRIMARY KEY,
    qbo_id VARCHAR(50),
    txn_date DATE NOT NULL,
    from_account_id INTEGER NOT NULL REFERENCES qbo_account(id),
    to_account_id INTEGER NOT NULL REFERENCES qbo_account(id),
    amount DECIMAL(15,2) NOT NULL,
    memo TEXT,
    sync_token INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qbo_transfer_txn_date ON qbo_transfer(txn_date);
CREATE INDEX IF NOT EXISTS idx_qbo_transfer_from ON qbo_transfer(from_account_id);
CREATE INDEX IF NOT EXISTS idx_qbo_transfer_to ON qbo_transfer(to_account_id);

-- Deposit
CREATE TABLE IF NOT EXISTS qbo_deposit (
    id SERIAL PRIMARY KEY,
    qbo_id VARCHAR(50),
    txn_date DATE NOT NULL,
    deposit_to_account_id INTEGER NOT NULL REFERENCES qbo_account(id),
    total_amt DECIMAL(15,2) DEFAULT 0.00,
    memo TEXT,
    sync_token INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qbo_deposit_txn_date ON qbo_deposit(txn_date);
CREATE INDEX IF NOT EXISTS idx_qbo_deposit_account ON qbo_deposit(deposit_to_account_id);

CREATE TABLE IF NOT EXISTS qbo_deposit_line (
    id SERIAL PRIMARY KEY,
    deposit_id INTEGER NOT NULL REFERENCES qbo_deposit(id) ON DELETE CASCADE,
    line_num INTEGER,
    amount DECIMAL(15,2),
    account_id INTEGER REFERENCES qbo_account(id),
    entity_type VARCHAR(50),
    entity_id INTEGER,
    payment_id INTEGER REFERENCES qbo_payment(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qbo_deposit_line_deposit ON qbo_deposit_line(deposit_id);
CREATE INDEX IF NOT EXISTS idx_qbo_deposit_line_payment ON qbo_deposit_line(payment_id);

-- ============================================================
-- 7. Budget Tables
-- ============================================================

CREATE TABLE IF NOT EXISTS qbo_budget (
    id SERIAL PRIMARY KEY,
    qbo_id VARCHAR(50),
    name VARCHAR(255) NOT NULL,
    start_date DATE,
    end_date DATE,
    budget_type VARCHAR(30) CHECK (budget_type IN ('ProfitAndLoss', 'BalanceSheet')),
    active BOOLEAN DEFAULT TRUE,
    sync_token INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS qbo_budget_detail (
    id SERIAL PRIMARY KEY,
    budget_id INTEGER NOT NULL REFERENCES qbo_budget(id) ON DELETE CASCADE,
    account_id INTEGER NOT NULL REFERENCES qbo_account(id),
    period_start DATE NOT NULL,
    amount DECIMAL(15,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qbo_budget_detail_budget ON qbo_budget_detail(budget_id);
CREATE INDEX IF NOT EXISTS idx_qbo_budget_detail_account ON qbo_budget_detail(account_id);
CREATE INDEX IF NOT EXISTS idx_qbo_budget_detail_period ON qbo_budget_detail(period_start);
