schema_customer = """ Customer details table
CREATE TABLE customer (
    CIF INT,
    Account_no INT, Account number of customer 
    Account_status TEXT,
    Customer_id TEXT,
   
);
"""

schema_deposit = """ Customer deposits table
CREATE TABLE savings_accounts (
    Account_no INT, Account number of customer , a foreign key of Account_no of customer table
    Account_scheme TEXT, deposit scheme which can be Savings or Current
);
"""

schema_loan = """ Customer loans table
CREATE TABLE loan (
    Account_no INT, Account number of customer , a foreign key of Account_no of customer table
    Account_scheme TEXT, Loan scheme can be Personal or home
);
"""