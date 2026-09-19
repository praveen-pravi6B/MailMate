import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "email_assistant.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Emails table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email_id TEXT UNIQUE NOT NULL,
        thread_id TEXT,
        sender TEXT,
        subject TEXT,
        received_at TEXT,
        processed_at TEXT,
        summary TEXT,
        importance TEXT,
        action_required INTEGER
    )
    ''')
    
    # Runs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        started_at TEXT,
        completed_at TEXT,
        status TEXT,
        emails_processed INTEGER,
        error TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

def is_email_processed(email_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM emails WHERE email_id = ?", (email_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def mark_email_processed(email_id: str, sender: str, subject: str, summary: str, importance: str, action_required: bool):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO emails (email_id, sender, subject, processed_at, summary, importance, action_required)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (email_id, sender, subject, datetime.utcnow().isoformat(), summary, importance, int(action_required)))
    conn.commit()
    conn.close()
