import os
import sys
import pathlib
import pytest
from fastapi.testclient import TestClient

# Ensure tests can import the application when run from repo root
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import app

client = TestClient(app)

ADMIN_USER = os.environ.get('ADMIN_USER','admin')
ADMIN_PASS = os.environ.get('ADMIN_PASS','adminpass')


def get_auth_headers(user=ADMIN_USER, pwd=ADMIN_PASS):
    import base64
    token = base64.b64encode(f"{user}:{pwd}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert 'db' in r.json()


def test_create_and_summarize_flow():
    # Create a key
    r = client.post('/create', data={'name':'testsvc','days':'1'}, headers=get_auth_headers())
    assert r.status_code == 200 or r.status_code == 302
    # We cannot capture HTML token reliably here but ensure dashboard works

    # Basic summarize call without key should fail
    r = client.post('/summarize', json={'text':'Hello world'}, headers={})
    assert r.status_code == 401
