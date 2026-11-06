import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "personal_expense_planner"),
        autocommit=False
    )

def init_database():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                category_id INT AUTO_INCREMENT PRIMARY KEY,
                category_name VARCHAR(60) NOT NULL UNIQUE
            )
        """)
        for name in ["Food","Rent","Health","Shopping","Groceries","Transport","Others"]:
            cur.execute("INSERT IGNORE INTO categories(category_name) VALUES (%s)", (name,))
        conn.commit()
    finally:
        conn.close()
