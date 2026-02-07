-- ============================================================
-- QuickBooks Online Financial Database Schema - MySQL
-- Generated for db-agent-ai quickbooks-finance skill
-- Requires MySQL 8.0+ for full compatibility
-- ============================================================

-- ============================================================
-- 1. Base Setup Tables
-- ============================================================

CREATE TABLE IF NOT EXISTS qbo_company (
    id INT AUTO_INCREMENT PRIMARY KEY,
    qbo_id VARCHAR(50),
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    fiscal_year_start_month INT DEFAULT 1,
    country VARCHAR(10),
    currency_code VARCHAR(3) DEFAULT 'USD',
    email VARCHAR(255),
    phone VARCHAR(50),
    industry VARCHAR(100),
    sync_token INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS qbo_account (
    id INT AUTO_INCREMENT PRIMARY KEY,
    qbo_id VARCHAR(50),
    acct_num VARCHAR(20),
    name VARCHAR(255) NOT NULL,
    account_type VARCHAR(50) NOT NULL,
    account_sub_type VARCHAR(50),
    classification VARCHAR(20),
    current_balance DECIMAL(15,2) DEFAULT 0.00,
    currency_code VARCHAR(3),
    description TEXT,
    active TINYINT(1) DEFAULT 1,
    parent_id INT,
    sync_token INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_qbo_account_parent FOREIGN KEY (parent_id) REFERENCES qbo_account(id),
    INDEX idx_qbo_account_type (account_type),
    INDEX idx_qbo_account_classification (classification),
    INDEX idx_qbo_account_parent (parent_id),
    INDEX idx_qbo_account_active (active)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS qbo_tax_code (
    id INT AUTO_INCREMENT PRIMARY KEY,
    qbo_id VARCHAR(50),
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    active TINYINT(1) DEFAULT 1,
    taxable TINYINT(1) DEFAULT 0,
    sync_token INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS qbo_tax_rate (
    id INT AUTO_INCREMENT PRIMARY KEY,
    qbo_id VARCHAR(50),
    name VARCHAR(100) NOT NULL,
    rate_value DECIMAL(8,4),
    agency_ref VARCHAR(100),
    description VARCHAR(255),
    active TINYINT(1) DEFAULT 1,
    sync_token INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS qbo_payment_method (
    id INT AUTO_INCREMENT PRIMARY KEY,
    qbo_id VARCHAR(50),
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20),
    active TINYINT(1) DEFAULT 1,
    sync_token INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS qbo_term (
    id INT AUTO_INCREMENT PRIMARY KEY,
    qbo_id VARCHAR(50),
    name VARCHAR(100) NOT NULL,
    due_days INT,
    discount_percent DECIMAL(5,2),
    discount_days INT,
    active TINYINT(1) DEFAULT 1,
    sync_token INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- ============================================================
-- 2. Contact Tables
-- ============================================================

CREATE TABLE IF NOT EXISTS qbo_customer (
    id INT AUTO_INCREMENT PRIMARY KEY,
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
    taxable TINYINT(1) DEFAULT 1,
    tax_code_id INT,
    term_id INT,
    parent_id INT,
    active TINYINT(1) DEFAULT 1,
    sync_token INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_qbo_customer_tax_code FOREIGN KEY (tax_code_id) REFERENCES qbo_tax_code(id),
    CONSTRAINT fk_qbo_customer_term FOREIGN KEY (term_id) REFERENCES qbo_term(id),
    CONSTRAINT fk_qbo_customer_parent FOREIGN KEY (parent_id) REFERENCES qbo_customer(id),
    INDEX idx_qbo_customer_name (display_name),
    INDEX idx_qbo_customer_email (email),
    INDEX idx_qbo_customer_active (active),
    INDEX idx_qbo_customer_balance (balance)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS qbo_vendor (
    id INT AUTO_INCREMENT PRIMARY KEY,
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
    is_1099 TINYINT(1) DEFAULT 0,
    term_id INT,
    currency_code VARCHAR(3),
    active TINYINT(1) DEFAULT 1,
    sync_token INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_qbo_vendor_term FOREIGN KEY (term_id) REFERENCES qbo_term(id),
    INDEX idx_qbo_vendor_name (display_name),
    INDEX idx_qbo_vendor_email (email),
    INDEX idx_qbo_vendor_active (active),
    INDEX idx_qbo_vendor_balance (balance)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS qbo_employee (
    id INT AUTO_INCREMENT PRIMARY KEY,
    qbo_id VARCHAR(50),
    display_name VARCHAR(255) NOT NULL,
    given_name VARCHAR(100),
    family_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(50),
    hired_date DATE,
    released_date DATE,
    active TINYINT(1) DEFAULT 1,
    sync_token INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- ============================================================
-- 3. Product / Item Table
-- ============================================================

CREATE TABLE IF NOT EXISTS qbo_item (
    id INT AUTO_INCREMENT PRIMARY KEY,
    qbo_id VARCHAR(50),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(30) NOT NULL,
    description TEXT,
    purchase_desc TEXT,
    unit_price DECIMAL(15,2),
    purchase_cost DECIMAL(15,2),
    qty_on_hand DECIMAL(15,4),
    sku VARCHAR(50),
    income_account_id INT,
    expense_account_id INT,
    asset_account_id INT,
    taxable TINYINT(1) DEFAULT 1,
    active TINYINT(1) DEFAULT 1,
    sync_token INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_qbo_item_income_acct FOREIGN KEY (income_account_id) REFERENCES qbo_account(id),
    CONSTRAINT fk_qbo_item_expense_acct FOREIGN KEY (expense_account_id) REFERENCES qbo_account(id),
    CONSTRAINT fk_qbo_item_asset_acct FOREIGN KEY (asset_account_id) REFERENCES qbo_account(id),
    INDEX idx_qbo_item_name (name),
    INDEX idx_qbo_item_type (type),
    INDEX idx_qbo_item_sku (sku),
    INDEX idx_qbo_item_active (active)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- ============================================================
-- 4. Accounts Receivable (AR) Tables
-- ============================================================

-- Invoice
CREATE TABLE IF NOT EXISTS qbo_invoice (
    id INT AUTO_INCREMENT PRIMARY KEY,
    qbo_id VARCHAR(50),
    customer_id INT NOT NULL,
    doc_number VARCHAR(50),
    txn_date DATE NOT NULL,
    due_date DATE,
    total_amt DECIMAL(15,2) DEFAULT 0.00,
    balance DECIMAL(15,2) DEFAULT 0.00,
    email_status VARCHAR(20) DEFAULT 'NotSet',
    term_id INT,
    ar_account_id INT,
    memo TEXT,
    sync_token INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_qbo_invoice_customer FOREIGN KEY (customer_id) REFERENCES qbo_customer(id),
    CONSTRAINT fk_qbo_invoice_term FOREIGN KEY (term_id) REFERENCES qbo_term(id),
    CONSTRAINT fk_qbo_invoice_ar_acct FOREIGN KEY (ar_account_id) REFERENCES qbo_account(id),
    INDEX idx_qbo_invoice_customer (customer_id),
    INDEX idx_qbo_invoice_txn_date (txn_date),
    INDEX idx_qbo_invoice_due_date (due_date),
    INDEX idx_qbo_invoice_doc_number (doc_number)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS qbo_invoice_line (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT NOT NULL,
    line_num INT,
    item_id INT,
    description TEXT,
    quantity DECIMAL(15,4),
    unit_price DECIMAL(15,2),
    amount DECIMAL(15,2),
    account_id INT,
    tax_code_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_qbo_invoice_line_invoice FOREIGN KEY (invoice_id) REFERENCES qbo_invoice(id) ON DELETE CASCADE,
    CONSTRAINT fk_qbo_invoice_line_item FOREIGN KEY (item_id) REFERENCES qbo_item(id),
    CONSTRAINT fk_qbo_invoice_line_account FOREIGN KEY (account_id) REFERENCES qbo_account(id),
    CONSTRAINT fk_qbo_invoice_line_tax FOREIGN KEY (tax_code_id) REFERENCES qbo_tax_code(id),
    INDEX idx_qbo_invoice_line_invoice (invoice_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Payment
CREATE TABLE IF NOT EXISTS qbo_payment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    qbo_id VARCHAR(50),
    customer_id INT NOT NULL,
    doc_number VARCHAR(50),
    txn_date DATE NOT NULL,
    total_amt DECIMAL(15,2) DEFAULT 0.00,
    payment_method_id INT,
    deposit_to_account_id INT,
    unapplied_amt DECIMAL(15,2) DEFAULT 0.00,
    memo TEXT,
    sync_token INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_qbo_payment_customer FOREIGN KEY (customer_id) REFERENCES qbo_customer(id),
    CONSTRAINT fk_qbo_payment_method FOREIGN KEY (payment_method_id) REFERENCES qbo_payment_method(id),
    CONSTRAINT fk_qbo_payment_deposit_acct FOREIGN KEY (deposit_to_account_id) REFERENCES qbo_account(id),
    INDEX idx_qbo_payment_customer (customer_id),
    INDEX idx_qbo_payment_txn_date (txn_date)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS qbo_payment_line (
    id INT AUTO_INCREMENT PRIMARY KEY,
    payment_id INT NOT NULL,
    line_num INT,
    invoice_id INT,
    amount DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_qbo_payment_line_payment FOREIGN KEY (payment_id) REFERENCES qbo_payment(id) ON DELETE CASCADE,
    CONSTRAINT fk_qbo_payment_line_invoice FOREIGN KEY (invoice_id) REFERENCES qbo_invoice(id),
    INDEX idx_qbo_payment_line_payment (payment_id),
    INDEX idx_qbo_payment_line_invoice (invoice_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Credit Memo
CREATE TABLE IF NOT EXISTS qbo_credit_memo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    qbo_id VARCHAR(50),
    customer_id INT NOT NULL,
    doc_number VARCHAR(50),
    txn_date DATE NOT NULL,
    total_amt DECIMAL(15,2) DEFAULT 0.00,
    remaining_credit DECIMAL(15,2) DEFAULT 0.00,
    memo TEXT,
    sync_token INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_qbo_credit_memo_customer FOREIGN KEY (customer_id) REFERENCES qbo_customer(id),
    INDEX idx_qbo_credit_memo_customer (customer_id),
    INDEX idx_qbo_credit_memo_txn_date (txn_date)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS qbo_credit_memo_line (
    id INT AUTO_INCREMENT PRIMARY KEY,
    credit_memo_id INT NOT NULL,
    line_num INT,
    item_id INT,
    description TEXT,
    quantity DECIMAL(15,4),
    unit_price DECIMAL(15,2),
    amount DECIMAL(15,2),
    account_id INT,
    tax_code_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_qbo_credit_memo_line_memo FOREIGN KEY (credit_memo_id) REFERENCES qbo_credit_memo(id) ON DELETE CASCADE,
    CONSTRAINT fk_qbo_credit_memo_line_item FOREIGN KEY (item_id) REFERENCES qbo_item(id),
    CONSTRAINT fk_qbo_credit_memo_line_acct FOREIGN KEY (account_id) REFERENCES qbo_account(id),
    CONSTRAINT fk_qbo_credit_memo_line_tax FOREIGN KEY (tax_code_id) REFERENCES qbo_tax_code(id),
    INDEX idx_qbo_credit_memo_line_memo (credit_memo_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Estimate
CREATE TABLE IF NOT EXISTS qbo_estimate (
    id INT AUTO_INCREMENT PRIMARY KEY,
    qbo_id VARCHAR(50),
    customer_id INT NOT NULL,
    doc_number VARCHAR(50),
    txn_date DATE NOT NULL,
    expiration_date DATE,
    total_amt DECIMAL(15,2) DEFAULT 0.00,
    accepted_date DATE,
    status VARCHAR(20) DEFAULT 'Pending',
    memo TEXT,
    sync_token INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_qbo_estimate_customer FOREIGN KEY (customer_id) REFERENCES qbo_customer(id),
    INDEX idx_qbo_estimate_customer (customer_id),
    INDEX idx_qbo_estimate_txn_date (txn_date)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS qbo_estimate_line (
    id INT AUTO_INCREMENT PRIMARY KEY,
    estimate_id INT NOT NULL,
    line_num INT,
    item_id INT,
    description TEXT,
    quantity DECIMAL(15,4),
    unit_price DECIMAL(15,2),
    amount DECIMAL(15,2),
    account_id INT,
    tax_code_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_qbo_estimate_line_est FOREIGN KEY (estimate_id) REFERENCES qbo_estimate(id) ON DELETE CASCADE,
    CONSTRAINT fk_qbo_estimate_line_item FOREIGN KEY (item_id) REFERENCES qbo_item(id),
    CONSTRAINT fk_qbo_estimate_line_acct FOREIGN KEY (account_id) REFERENCES qbo_account(id),
    CONSTRAINT fk_qbo_estimate_line_tax FOREIGN KEY (tax_code_id) REFERENCES qbo_tax_code(id),
    INDEX idx_qbo_estimate_line_est (estimate_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Sales Receipt
CREATE TABLE IF NOT EXISTS qbo_sales_receipt (
    id INT AUTO_INCREMENT PRIMARY KEY,
    qbo_id VARCHAR(50),
    customer_id INT NOT NULL,
    doc_number VARCHAR(50),
    txn_date DATE NOT NULL,
    total_amt DECIMAL(15,2) DEFAULT 0.00,
    payment_method_id INT,
    deposit_to_account_id INT,
    memo TEXT,
    sync_token INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_qbo_sales_receipt_customer FOREIGN KEY (customer_id) REFERENCES qbo_customer(id),
    CONSTRAINT fk_qbo_sales_receipt_method FOREIGN KEY (payment_method_id) REFERENCES qbo_payment_method(id),
    CONSTRAINT fk_qbo_sales_receipt_acct FOREIGN KEY (deposit_to_account_id) REFERENCES qbo_account(id),
    INDEX idx_qbo_sales_receipt_customer (customer_id),
    INDEX idx_qbo_sales_receipt_txn_date (txn_date)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS qbo_sales_receipt_line (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sales_receipt_id INT NOT NULL,
    line_num INT,
    item_id INT,
    description TEXT,
    quantity DECIMAL(15,4),
    unit_price DECIMAL(15,2),
    amount DECIMAL(15,2),
    account_id INT,
    tax_code_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_qbo_sr_line_receipt FOREIGN KEY (sales_receipt_id) REFERENCES qbo_sales_receipt(id) ON DELETE CASCADE,
    CONSTRAINT fk_qbo_sr_line_item FOREIGN KEY (item_id) REFERENCES qbo_item(id),
    CONSTRAINT fk_qbo_sr_line_acct FOREIGN KEY (account_id) REFERENCES qbo_account(id),
    CONSTRAINT fk_qbo_sr_line_tax FOREIGN KEY (tax_code_id) REFERENCES qbo_tax_code(id),
    INDEX idx_qbo_sales_receipt_line_receipt (sales_receipt_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- ============================================================
-- 5. Accounts Payable (AP) Tables
-- ============================================================

-- Bill
CREATE TABLE IF NOT EXISTS qbo_bill (
    id INT AUTO_INCREMENT PRIMARY KEY,
    qbo_id VARCHAR(50),
    vendor_id INT NOT NULL,
    doc_number VARCHAR(50),
    txn_date DATE NOT NULL,
    due_date DATE,
    total_amt DECIMAL(15,2) DEFAULT 0.00,
    balance DECIMAL(15,2) DEFAULT 0.00,
    ap_account_id INT,
    term_id INT,
    memo TEXT,
    sync_token INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_qbo_bill_vendor FOREIGN KEY (vendor_id) REFERENCES qbo_vendor(id),
    CONSTRAINT fk_qbo_bill_ap_acct FOREIGN KEY (ap_account_id) REFERENCES qbo_account(id),
    CONSTRAINT fk_qbo_bill_term FOREIGN KEY (term_id) REFERENCES qbo_term(id),
    INDEX idx_qbo_bill_vendor (vendor_id),
    INDEX idx_qbo_bill_txn_date (txn_date),
    INDEX idx_qbo_bill_due_date (due_date),
    INDEX idx_qbo_bill_doc_number (doc_number)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS qbo_bill_line (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bill_id INT NOT NULL,
    line_num INT,
    item_id INT,
    description TEXT,
    quantity DECIMAL(15,4),
    unit_price DECIMAL(15,2),
    amount DECIMAL(15,2),
    account_id INT,
    tax_code_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_qbo_bill_line_bill FOREIGN KEY (bill_id) REFERENCES qbo_bill(id) ON DELETE CASCADE,
    CONSTRAINT fk_qbo_bill_line_item FOREIGN KEY (item_id) REFERENCES qbo_item(id),
    CONSTRAINT fk_qbo_bill_line_acct FOREIGN KEY (account_id) REFERENCES qbo_account(id),
    CONSTRAINT fk_qbo_bill_line_tax FOREIGN KEY (tax_code_id) REFERENCES qbo_tax_code(id),
    INDEX idx_qbo_bill_line_bill (bill_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Bill Payment
CREATE TABLE IF NOT EXISTS qbo_bill_payment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    qbo_id VARCHAR(50),
    vendor_id INT NOT NULL,
    doc_number VARCHAR(50),
    txn_date DATE NOT NULL,
    total_amt DECIMAL(15,2) DEFAULT 0.00,
    pay_type VARCHAR(20),
    check_bank_account_id INT,
    cc_account_id INT,
    memo TEXT,
    sync_token INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_qbo_bill_payment_vendor FOREIGN KEY (vendor_id) REFERENCES qbo_vendor(id),
    CONSTRAINT fk_qbo_bill_payment_bank FOREIGN KEY (check_bank_account_id) REFERENCES qbo_account(id),
    CONSTRAINT fk_qbo_bill_payment_cc FOREIGN KEY (cc_account_id) REFERENCES qbo_account(id),
    INDEX idx_qbo_bill_payment_vendor (vendor_id),
    INDEX idx_qbo_bill_payment_txn_date (txn_date)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS qbo_bill_payment_line (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bill_payment_id INT NOT NULL,
    line_num INT,
    bill_id INT,
    amount DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_qbo_bp_line_payment FOREIGN KEY (bill_payment_id) REFERENCES qbo_bill_payment(id) ON DELETE CASCADE,
    CONSTRAINT fk_qbo_bp_line_bill FOREIGN KEY (bill_id) REFERENCES qbo_bill(id),
    INDEX idx_qbo_bill_payment_line_payment (bill_payment_id),
    INDEX idx_qbo_bill_payment_line_bill (bill_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Vendor Credit
CREATE TABLE IF NOT EXISTS qbo_vendor_credit (
    id INT AUTO_INCREMENT PRIMARY KEY,
    qbo_id VARCHAR(50),
    vendor_id INT NOT NULL,
    doc_number VARCHAR(50),
    txn_date DATE NOT NULL,
    total_amt DECIMAL(15,2) DEFAULT 0.00,
    balance DECIMAL(15,2) DEFAULT 0.00,
    memo TEXT,
    sync_token INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_qbo_vendor_credit_vendor FOREIGN KEY (vendor_id) REFERENCES qbo_vendor(id),
    INDEX idx_qbo_vendor_credit_vendor (vendor_id),
    INDEX idx_qbo_vendor_credit_txn_date (txn_date)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS qbo_vendor_credit_line (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vendor_credit_id INT NOT NULL,
    line_num INT,
    item_id INT,
    description TEXT,
    quantity DECIMAL(15,4),
    unit_price DECIMAL(15,2),
    amount DECIMAL(15,2),
    account_id INT,
    tax_code_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_qbo_vc_line_credit FOREIGN KEY (vendor_credit_id) REFERENCES qbo_vendor_credit(id) ON DELETE CASCADE,
    CONSTRAINT fk_qbo_vc_line_item FOREIGN KEY (item_id) REFERENCES qbo_item(id),
    CONSTRAINT fk_qbo_vc_line_acct FOREIGN KEY (account_id) REFERENCES qbo_account(id),
    CONSTRAINT fk_qbo_vc_line_tax FOREIGN KEY (tax_code_id) REFERENCES qbo_tax_code(id),
    INDEX idx_qbo_vendor_credit_line_credit (vendor_credit_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Purchase Order
CREATE TABLE IF NOT EXISTS qbo_purchase_order (
    id INT AUTO_INCREMENT PRIMARY KEY,
    qbo_id VARCHAR(50),
    vendor_id INT NOT NULL,
    doc_number VARCHAR(50),
    txn_date DATE NOT NULL,
    total_amt DECIMAL(15,2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'Open',
    email_status VARCHAR(20) DEFAULT 'NotSet',
    memo TEXT,
    sync_token INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_qbo_po_vendor FOREIGN KEY (vendor_id) REFERENCES qbo_vendor(id),
    INDEX idx_qbo_purchase_order_vendor (vendor_id),
    INDEX idx_qbo_purchase_order_txn_date (txn_date),
    INDEX idx_qbo_purchase_order_doc_number (doc_number)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS qbo_purchase_order_line (
    id INT AUTO_INCREMENT PRIMARY KEY,
    purchase_order_id INT NOT NULL,
    line_num INT,
    item_id INT,
    description TEXT,
    quantity DECIMAL(15,4),
    unit_price DECIMAL(15,2),
    amount DECIMAL(15,2),
    account_id INT,
    tax_code_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_qbo_po_line_po FOREIGN KEY (purchase_order_id) REFERENCES qbo_purchase_order(id) ON DELETE CASCADE,
    CONSTRAINT fk_qbo_po_line_item FOREIGN KEY (item_id) REFERENCES qbo_item(id),
    CONSTRAINT fk_qbo_po_line_acct FOREIGN KEY (account_id) REFERENCES qbo_account(id),
    CONSTRAINT fk_qbo_po_line_tax FOREIGN KEY (tax_code_id) REFERENCES qbo_tax_code(id),
    INDEX idx_qbo_purchase_order_line_po (purchase_order_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- ============================================================
-- 6. General Ledger (GL) Tables
-- ============================================================

-- Journal Entry
CREATE TABLE IF NOT EXISTS qbo_journal_entry (
    id INT AUTO_INCREMENT PRIMARY KEY,
    qbo_id VARCHAR(50),
    doc_number VARCHAR(50),
    txn_date DATE NOT NULL,
    total_amt DECIMAL(15,2) DEFAULT 0.00,
    adjustment TINYINT(1) DEFAULT 0,
    memo TEXT,
    sync_token INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_qbo_journal_entry_txn_date (txn_date),
    INDEX idx_qbo_journal_entry_doc_number (doc_number)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS qbo_journal_entry_line (
    id INT AUTO_INCREMENT PRIMARY KEY,
    journal_entry_id INT NOT NULL,
    line_num INT,
    posting_type VARCHAR(10) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    account_id INT NOT NULL,
    description TEXT,
    entity_type VARCHAR(50),
    entity_id INT,
    sync_token INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_qbo_je_line_entry FOREIGN KEY (journal_entry_id) REFERENCES qbo_journal_entry(id) ON DELETE CASCADE,
    CONSTRAINT fk_qbo_je_line_account FOREIGN KEY (account_id) REFERENCES qbo_account(id),
    INDEX idx_qbo_je_line_entry (journal_entry_id),
    INDEX idx_qbo_je_line_account (account_id),
    INDEX idx_qbo_je_line_posting (posting_type)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Transfer
CREATE TABLE IF NOT EXISTS qbo_transfer (
    id INT AUTO_INCREMENT PRIMARY KEY,
    qbo_id VARCHAR(50),
    txn_date DATE NOT NULL,
    from_account_id INT NOT NULL,
    to_account_id INT NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    memo TEXT,
    sync_token INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_qbo_transfer_from FOREIGN KEY (from_account_id) REFERENCES qbo_account(id),
    CONSTRAINT fk_qbo_transfer_to FOREIGN KEY (to_account_id) REFERENCES qbo_account(id),
    INDEX idx_qbo_transfer_txn_date (txn_date),
    INDEX idx_qbo_transfer_from (from_account_id),
    INDEX idx_qbo_transfer_to (to_account_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Deposit
CREATE TABLE IF NOT EXISTS qbo_deposit (
    id INT AUTO_INCREMENT PRIMARY KEY,
    qbo_id VARCHAR(50),
    txn_date DATE NOT NULL,
    deposit_to_account_id INT NOT NULL,
    total_amt DECIMAL(15,2) DEFAULT 0.00,
    memo TEXT,
    sync_token INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_qbo_deposit_account FOREIGN KEY (deposit_to_account_id) REFERENCES qbo_account(id),
    INDEX idx_qbo_deposit_txn_date (txn_date),
    INDEX idx_qbo_deposit_account (deposit_to_account_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS qbo_deposit_line (
    id INT AUTO_INCREMENT PRIMARY KEY,
    deposit_id INT NOT NULL,
    line_num INT,
    amount DECIMAL(15,2),
    account_id INT,
    entity_type VARCHAR(50),
    entity_id INT,
    payment_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_qbo_deposit_line_deposit FOREIGN KEY (deposit_id) REFERENCES qbo_deposit(id) ON DELETE CASCADE,
    CONSTRAINT fk_qbo_deposit_line_acct FOREIGN KEY (account_id) REFERENCES qbo_account(id),
    CONSTRAINT fk_qbo_deposit_line_payment FOREIGN KEY (payment_id) REFERENCES qbo_payment(id),
    INDEX idx_qbo_deposit_line_deposit (deposit_id),
    INDEX idx_qbo_deposit_line_payment (payment_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- ============================================================
-- 7. Budget Tables
-- ============================================================

CREATE TABLE IF NOT EXISTS qbo_budget (
    id INT AUTO_INCREMENT PRIMARY KEY,
    qbo_id VARCHAR(50),
    name VARCHAR(255) NOT NULL,
    start_date DATE,
    end_date DATE,
    budget_type VARCHAR(30),
    active TINYINT(1) DEFAULT 1,
    sync_token INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS qbo_budget_detail (
    id INT AUTO_INCREMENT PRIMARY KEY,
    budget_id INT NOT NULL,
    account_id INT NOT NULL,
    period_start DATE NOT NULL,
    amount DECIMAL(15,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_qbo_budget_detail_budget FOREIGN KEY (budget_id) REFERENCES qbo_budget(id) ON DELETE CASCADE,
    CONSTRAINT fk_qbo_budget_detail_account FOREIGN KEY (account_id) REFERENCES qbo_account(id),
    INDEX idx_qbo_budget_detail_budget (budget_id),
    INDEX idx_qbo_budget_detail_account (account_id),
    INDEX idx_qbo_budget_detail_period (period_start)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
