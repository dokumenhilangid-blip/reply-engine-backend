import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "/data/engine.db")


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():

    conn = get_conn()
    cursor = conn.cursor()

    # chat history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            message TEXT
        )
    """)

    # raw data table (NEW)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
