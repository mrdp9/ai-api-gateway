#!/usr/bin/env python3
"""Ensure the `keys` table has the new schema (id PK, key_hash, created_at, revoked boolean).
If necessary, perform a safe migration by creating a new table, copying data, and renaming it."""
import os
import sqlite3

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
# Match the DATA_DIR used in main.py (ai-platform/ai-platform/data)
DEFAULT_DATA_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'ai-platform', 'data'))
os.makedirs(DEFAULT_DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DEFAULT_DATA_DIR, 'keys.db')

print('Using DB at', DB_PATH)
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Check if table exists
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='keys'")
if not cur.fetchone():
    print('No keys table found; creating new one with desired schema')
    cur.execute('''
        CREATE TABLE keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT,
            key_hash TEXT UNIQUE,
            name TEXT,
            expires_at DATETIME,
            created_at DATETIME,
            revoked BOOLEAN DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()
    print('Created new keys table')
    exit(0)

# Inspect existing columns
cur.execute("PRAGMA table_info(keys)")
cols = [r[1] for r in cur.fetchall()]
print('Existing columns:', cols)
needed = ['id', 'key_hash', 'created_at', 'revoked']
if all(c in cols for c in needed):
    print('Schema already up to date')
    conn.close()
    exit(0)

print('Performing table migration')
# Create new table
cur.execute('''
    CREATE TABLE keys_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT,
        key_hash TEXT UNIQUE,
        name TEXT,
        expires_at DATETIME,
        created_at DATETIME,
        revoked BOOLEAN DEFAULT 0
    )
''')

# Copy existing data into new table, mapping known columns
existing_cols = cols
common_cols = [c for c in ['key','key_hash','name','expires_at'] if c in existing_cols]
col_list = ','.join(common_cols)
cur.execute(f"INSERT INTO keys_new ({col_list}) SELECT {col_list} FROM keys")
conn.commit()
# Drop old table and rename
cur.execute('DROP TABLE keys')
cur.execute('ALTER TABLE keys_new RENAME TO keys')
conn.commit()
conn.close()
print('Migration complete')
