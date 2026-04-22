import sqlite3
import time
import os
import pathlib

DB_PATH = os.environ.get("DB_PATH", "skins.db")

def get_conn():
    pathlib.Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def create_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_seen INTEGER,
        last_seen INTEGER
    )""")
    conn.commit()
    conn.close()

def save_user(user_id, username):
    conn = get_conn()
    c = conn.cursor()
    now = int(time.time())
    c.execute("""INSERT INTO users (user_id, username, first_seen, last_seen)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET last_seen=?, username=?""",
        (user_id, username, now, now, now, username))
    conn.commit()
    conn.close()

def get_stats():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE last_seen > ?", (int(time.time()) - 300,))
    online = c.fetchone()[0]
    conn.close()
    return total, online

def get_all_users():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT user_id, username, first_seen, last_seen FROM users ORDER BY last_seen DESC")
    rows = c.fetchall()
    conn.close()
    return rows
