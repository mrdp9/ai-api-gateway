#!/usr/bin/env python3
"""Migration to hash existing plaintext keys into key_hash and remove plaintext keys."""
import os
import hmac
import hashlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ai-platform', 'api'))
from main import APIKey, Base

# Derive DB path in same way main.py does
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
# Match the DATA_DIR used in main.py (ai-platform/ai-platform/data)
DEFAULT_DATA_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'ai-platform', 'data'))
os.makedirs(DEFAULT_DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DEFAULT_DATA_DIR, 'keys.db')
DB_URL = os.environ.get("DB_URL", f"sqlite:///{DB_PATH}")
SECRET_KEY = os.environ.get("SECRET_KEY", "PLEASE_SET_SECRET_KEY")

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)

def hash_key(token: str) -> str:
    return hmac.new(SECRET_KEY.encode(), token.encode(), hashlib.sha256).hexdigest()


def migrate():
    Base.metadata.create_all(engine)
    db = Session()
    try:
        rows = db.query(APIKey).filter(APIKey.key != None).all()
        print(f"Found {len(rows)} keys to migrate")
        for r in rows:
            if r.key:
                r.key_hash = hash_key(r.key)
                r.key = None
        db.commit()
    finally:
        db.close()


if __name__ == '__main__':
    migrate()
    print("Done")
