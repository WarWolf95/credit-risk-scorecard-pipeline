import sqlite3
import pandas as pd

def init_database():
    # Setup in-memory database
    conn = sqlite3.connect("learning_lab.db")
    cursor = conn.cursor()
    
    # Create sample transaction table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id INTEGER PRIMARY KEY,
        user_id INTEGER,
        amount REAL,
        transaction_date TEXT
    )""")
    
    # Insert mock data
    mock_data = [
        (1, 101, 150.00, '2026-01-01'),
        (2, 101, 200.00, '2026-01-02'),
        (3, 101, 50.00,  '2026-01-03'),
        (4, 102, 300.00, '2026-01-01'),
        (5, 102, 100.00, '2026-01-04'),
        (6, 103, 500.00, '2026-01-02'),
        (7, 103, 250.00, '2026-01-03')
    ]
    cursor.executemany("INSERT OR REPLACE INTO transactions VALUES (?, ?, ?, ?)", mock_data)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_database()
    print("Database initialised: learning_lab.db")
