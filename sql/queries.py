"""
Raw SQL query strings.
NO business logic, NO metadata, NO dependencies.
"""

# Independent queries
QUERY_CUSTOMER_TRANSACTIONS = """
    CREATE OR REPLACE TEMP VIEW customer_transactions AS
    SELECT ...
"""

# Dependent queries (joins existing views)
QUERY_CUSTOMER_SEGMENTS = """
    CREATE OR REPLACE TEMP VIEW customer_segments AS
    SELECT
        ct.account_id,
        ...
    FROM customer_transactions ct
    LEFT JOIN write_off_summary wo ON ct.account_id = ow.account_id
    LEFT JOIN churn_risk cr ON ct.account_id = cr.account_id
"""