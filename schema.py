schema_customer = """ Customer details table
CREATE TABLE customer (
    CIF INT, customer information file, PII
    Account_no INT, Account number of customer , PII
    Account_status TEXT, Account is active or inactive, Not PII
    Customer_id TEXT, Government id of customer, PII
   
);
"""

schema_deposit = """ Customer deposits table
CREATE TABLE savings_accounts (
    Account_no INT, Account number of customer - a foreign key of Account_no of customer table, PII
    Account_scheme TEXT, deposit scheme which can be Savings or Current, Not Pii
);
"""

schema_loan = """ Customer loans table
CREATE TABLE loan (
    Account_no INT, Account number of customer - a foreign key of Account_no of customer table, PII
    Account_scheme TEXT, Loan scheme can be Personal or home,  Not Pii
);
"""