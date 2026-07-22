# ==============================================================================
# CHALLENGE: SQL Window Functions
# ==============================================================================
# INSTRUCTIONS:
# Write a SQL query in the string variable below that computes the:
# 1. Row number for each user ordered by transaction_date ascending.
# 2. Lagged amount (amount of the PREVIOUS transaction for that user).
#    If there is no previous transaction, default to 0.0.
# 3. Cumulative sum of transaction amounts for each user ordered by date.
#
# Return columns: user_id, transaction_date, amount, row_num, prev_amount, cumulative_sum
# ==============================================================================

SQL_QUERY = """
-- WRITE YOUR SQL QUERY HERE
SELECT 
    user_id,
    transaction_date,
    amount
    -- Add your window functions here
FROM transactions
"""
