-- ============================================================
-- QuickBooks Online - Standard Chart of Accounts Seed Data
-- Compatible with both PostgreSQL and MySQL
-- Run AFTER setup_postgresql.sql or setup_mysql.sql
-- ============================================================

-- ============================================================
-- Asset Accounts
-- ============================================================

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('1000', 'Checking', 'Bank', 'Checking', 'Asset', 'Primary checking account', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('1010', 'Savings', 'Bank', 'Savings', 'Asset', 'Savings account', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('1100', 'Accounts Receivable', 'AccountsReceivable', 'AccountsReceivable', 'Asset', 'Trade accounts receivable', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('1200', 'Inventory Asset', 'OtherCurrentAsset', 'Inventory', 'Asset', 'Inventory of goods for sale', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('1250', 'Undeposited Funds', 'OtherCurrentAsset', 'UndepositedFunds', 'Asset', 'Funds received but not yet deposited', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('1300', 'Prepaid Expenses', 'OtherCurrentAsset', 'PrepaidExpenses', 'Asset', 'Expenses paid in advance', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('1500', 'Furniture & Equipment', 'FixedAsset', 'FurnitureAndFixtures', 'Asset', 'Office furniture and equipment', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('1510', 'Accumulated Depreciation', 'FixedAsset', 'AccumulatedDepreciation', 'Asset', 'Accumulated depreciation on fixed assets', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('1600', 'Other Assets', 'OtherAsset', 'OtherLongTermAssets', 'Asset', 'Other long-term assets', 1);

-- ============================================================
-- Liability Accounts
-- ============================================================

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('2000', 'Accounts Payable', 'AccountsPayable', 'AccountsPayable', 'Liability', 'Trade accounts payable', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('2100', 'Credit Card', 'CreditCard', 'CreditCard', 'Liability', 'Company credit card', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('2200', 'Payroll Liabilities', 'OtherCurrentLiability', 'PayrollTaxPayable', 'Liability', 'Accrued payroll taxes and withholdings', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('2300', 'Sales Tax Payable', 'OtherCurrentLiability', 'SalesTaxPayable', 'Liability', 'Sales tax collected but not yet remitted', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('2400', 'Accrued Liabilities', 'OtherCurrentLiability', 'OtherCurrentLiabilities', 'Liability', 'Other accrued expenses', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('2500', 'Loan Payable', 'LongTermLiability', 'NotesPayable', 'Liability', 'Long-term loan obligations', 1);

-- ============================================================
-- Equity Accounts
-- ============================================================

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('3000', 'Opening Balance Equity', 'Equity', 'OpeningBalanceEquity', 'Equity', 'Opening balance equity for new company setup', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('3100', 'Owner''s Equity', 'Equity', 'OwnersEquity', 'Equity', 'Owner investment and draws', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('3200', 'Retained Earnings', 'Equity', 'RetainedEarnings', 'Equity', 'Accumulated net income from prior periods', 1);

-- ============================================================
-- Income Accounts
-- ============================================================

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('4000', 'Sales of Product Income', 'Income', 'SalesOfProductIncome', 'Revenue', 'Revenue from product sales', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('4100', 'Service Income', 'Income', 'ServiceFeeIncome', 'Revenue', 'Revenue from services rendered', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('4200', 'Discounts Given', 'Income', 'DiscountsRefundsGiven', 'Revenue', 'Sales discounts and refunds (contra revenue)', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('4500', 'Other Income', 'OtherIncome', 'OtherMiscellaneousIncome', 'Revenue', 'Interest, dividends, and other non-operating income', 1);

-- ============================================================
-- Cost of Goods Sold Accounts
-- ============================================================

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('5000', 'Cost of Goods Sold', 'CostOfGoodsSold', 'SuppliesMaterialsCogs', 'Expense', 'Direct cost of products sold', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('5100', 'Supplies & Materials - COGS', 'CostOfGoodsSold', 'SuppliesMaterialsCogs', 'Expense', 'Supplies and materials used in production', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('5200', 'Shipping & Delivery - COGS', 'CostOfGoodsSold', 'ShippingFreightDeliveryCos', 'Expense', 'Freight and delivery costs for goods sold', 1);

-- ============================================================
-- Expense Accounts
-- ============================================================

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('6000', 'Advertising & Marketing', 'Expense', 'AdvertisingPromotional', 'Expense', 'Marketing and advertising costs', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('6100', 'Bank Charges & Fees', 'Expense', 'BankCharges', 'Expense', 'Bank service fees and charges', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('6200', 'Depreciation', 'Expense', 'Depreciation', 'Expense', 'Depreciation of fixed assets', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('6300', 'Insurance', 'Expense', 'Insurance', 'Expense', 'Business insurance premiums', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('6400', 'Interest Expense', 'Expense', 'InterestPaid', 'Expense', 'Interest paid on loans and credit', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('6500', 'Legal & Professional Fees', 'Expense', 'LegalProfessionalFees', 'Expense', 'Legal, accounting, and consulting fees', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('6600', 'Office Supplies', 'Expense', 'OfficeGeneralAdministrativeExpenses', 'Expense', 'General office supplies and expenses', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('6700', 'Payroll Expenses', 'Expense', 'PayrollExpenses', 'Expense', 'Salaries, wages, and payroll taxes', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('6800', 'Rent or Lease', 'Expense', 'RentOrLeaseOfBuildings', 'Expense', 'Office and facility rent', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('6900', 'Repairs & Maintenance', 'Expense', 'RepairMaintenance', 'Expense', 'Equipment and facility maintenance', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('7000', 'Telephone & Internet', 'Expense', 'CommunicationsTelephone', 'Expense', 'Phone and internet services', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('7100', 'Travel & Entertainment', 'Expense', 'Travel', 'Expense', 'Business travel and entertainment', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('7200', 'Utilities', 'Expense', 'Utilities', 'Expense', 'Electric, gas, water, and other utilities', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('7300', 'Meals', 'Expense', 'EntertainmentMeals', 'Expense', 'Business meals and related expenses', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('7900', 'Miscellaneous Expense', 'Expense', 'OtherMiscellaneousServiceCost', 'Expense', 'Other miscellaneous expenses', 1);

INSERT INTO qbo_account (acct_num, name, account_type, account_sub_type, classification, description, active)
VALUES ('8000', 'Other Expense', 'OtherExpense', 'OtherMiscellaneousExpense', 'Expense', 'Non-operating expenses', 1);

-- ============================================================
-- Standard Payment Terms
-- ============================================================

INSERT INTO qbo_term (name, due_days, discount_percent, discount_days, active) VALUES ('Due on Receipt', 0, NULL, NULL, 1);
INSERT INTO qbo_term (name, due_days, discount_percent, discount_days, active) VALUES ('Net 15', 15, NULL, NULL, 1);
INSERT INTO qbo_term (name, due_days, discount_percent, discount_days, active) VALUES ('Net 30', 30, NULL, NULL, 1);
INSERT INTO qbo_term (name, due_days, discount_percent, discount_days, active) VALUES ('Net 60', 60, NULL, NULL, 1);
INSERT INTO qbo_term (name, due_days, discount_percent, discount_days, active) VALUES ('2/10 Net 30', 30, 2.00, 10, 1);

-- ============================================================
-- Standard Payment Methods
-- ============================================================

INSERT INTO qbo_payment_method (name, type, active) VALUES ('Cash', 'Cash', 1);
INSERT INTO qbo_payment_method (name, type, active) VALUES ('Check', 'Check', 1);
INSERT INTO qbo_payment_method (name, type, active) VALUES ('Credit Card', 'CreditCard', 1);
INSERT INTO qbo_payment_method (name, type, active) VALUES ('Bank Transfer', 'BankTransfer', 1);

-- ============================================================
-- Standard Tax Codes
-- ============================================================

INSERT INTO qbo_tax_code (name, description, active, taxable) VALUES ('TAX', 'Taxable', 1, 1);
INSERT INTO qbo_tax_code (name, description, active, taxable) VALUES ('NON', 'Non-Taxable', 1, 0);
