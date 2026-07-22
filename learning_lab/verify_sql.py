import sqlite3
import pandas as pd
import sys

def verify():
    # Import the query from the user's challenge file
    try:
        from sql_challenge import SQL_QUERY
    except ImportError:
        print("[ERROR] sql_challenge.py not found or contains errors.")
        sys.exit(1)
        
    if "WRITE YOUR SQL QUERY HERE" in SQL_QUERY or len(SQL_QUERY.strip()) < 50:
        print("[STATUS] Please write your solution in sql_challenge.py.")
        sys.exit(0)
        
    conn = sqlite3.connect("learning_lab.db")
    
    try:
        user_df = pd.read_sql_query(SQL_QUERY, conn)
    except Exception as e:
        print(f"[ERROR] SQL Execution Error:\n{str(e)}")
        conn.close()
        sys.exit(1)
        
    conn.close()
    
    # Expected output structure & values
    required_cols = ["user_id", "transaction_date", "amount", "row_num", "prev_amount", "cumulative_sum"]
    for col in required_cols:
        if col not in user_df.columns:
            print(f"[FAIL] Missing required column '{col}'. Got: {list(user_df.columns)}")
            sys.exit(1)
            
    # Correct calculation check
    u101 = user_df[user_df['user_id'] == 101].sort_values('transaction_date').reset_index(drop=True)
    
    if len(u101) != 3:
        print(f"[FAIL] Expected 3 transactions for user 101, got {len(u101)}.")
        sys.exit(1)
        
    try:
        # Check row numbers
        assert list(u101['row_num']) == [1, 2, 3], f"row_num is incorrect: {list(u101['row_num'])}"
        # Check prev_amount (lag)
        assert list(u101['prev_amount']) == [0.0, 150.0, 200.0], f"prev_amount (lag) is incorrect: {list(u101['prev_amount'])}"
        # Check cumulative_sum
        assert list(u101['cumulative_sum']) == [150.0, 350.0, 400.0], f"cumulative_sum is incorrect: {list(u101['cumulative_sum'])}"
    except AssertionError as ae:
        print(f"[FAIL] Calculation Failure: {str(ae)}")
        print("\nYour current output:")
        print(user_df.to_string(index=False))
        sys.exit(1)
        
    print("[OK] Success! Your SQL Window Functions query is correct.")
    print("\nResult:")
    print(user_df.to_string(index=False))

if __name__ == "__main__":
    verify()
