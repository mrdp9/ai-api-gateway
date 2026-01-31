import sqlite3
import os

DB_PATH = os.getenv("DB_URL", "../data/keys.db")

def migrate():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY,
        key_hash TEXT NOT NULL,
        created_at TEXT NOT NULL,
        expires_at TEXT,
        revoked INTEGER DEFAULT 0
    )''')
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
