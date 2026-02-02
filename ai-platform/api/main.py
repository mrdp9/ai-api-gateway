import os
from fastapi import FastAPI, Header, HTTPException, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Boolean, text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timedelta
import requests
import secrets
import hmac
import hashlib
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional

# Security config
SECRET_KEY = os.environ.get("SECRET_KEY", "PLEASE_SET_SECRET_KEY")
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "adminpass")
security = HTTPBasic()

# Configurable endpoints via environment
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434/api/generate")
DATA_DIR = os.environ.get("DATA_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data")))
# Ensure data dir exists so SQLite can create/open the DB file
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "keys.db")
DB_URL = os.environ.get("DB_URL", f"sqlite:///{DB_PATH}")

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
Base = declarative_base()

class APIKey(Base):
    __tablename__ = "keys"
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String, nullable=True)
    key_hash = Column(String, index=True, unique=True, nullable=True)
    name = Column(String)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked = Column(Boolean, default=False)

Base.metadata.create_all(engine)

class GenerateRequest(BaseModel):
    prompt: str

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware

# Rate limiter: prefer per-API-key (falls back to IP)
limiter = Limiter(key_func=lambda request: request.headers.get("x-api-key") or get_remote_address(request))

app = FastAPI()
# attach limiter to app
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

def _require_admin(credentials: HTTPBasicCredentials = Depends(security)):
    if not (secrets.compare_digest(credentials.username, ADMIN_USER) and secrets.compare_digest(credentials.password, ADMIN_PASS)):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return credentials


@app.get("/", response_class=HTMLResponse)
def home(request: Request, credentials: HTTPBasicCredentials = Depends(_require_admin)):
    db = Session()
    try:
        keys = db.query(APIKey).all()
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "keys": keys, "now": datetime.utcnow()}
        )
    finally:
        db.close()

def _hash_key(token: str) -> str:
    return hmac.new(SECRET_KEY.encode(), token.encode(), hashlib.sha256).hexdigest()


def _verify_key(token: str) -> Optional[APIKey]:
    if not token:
        return None
    h = _hash_key(token)
    db = Session()
    try:
        return db.query(APIKey).filter(APIKey.key_hash == h, APIKey.revoked == "false").first()
    finally:
        db.close()


@app.post("/create")
def create(name: str = Form(...), days: int = Form(...), credentials: HTTPBasicCredentials = Depends(security)):
    # Basic auth for creation
    if not (secrets.compare_digest(credentials.username, ADMIN_USER) and secrets.compare_digest(credentials.password, ADMIN_PASS)):
        raise HTTPException(status_code=401, detail="Unauthorized")

    db = Session()
    token = secrets.token_hex(32)
    token_hash = _hash_key(token)
    expiry = datetime.utcnow() + timedelta(days=int(days))
    try:
        db.add(APIKey(key=None, key_hash=token_hash, name=name, expires_at=expiry))
        db.commit()
    finally:
        db.close()

    # Show the token one-time in a minimal page
    return HTMLResponse(f"<html><body><h2>API Key Created</h2><p>Save this token now — it will not be shown again:</p><pre>{token}</pre><p><a href=\"/\">Back</a></p></body></html>")

@app.post("/delete/{key}")
def delete(key: str, credentials: HTTPBasicCredentials = Depends(_require_admin)):
    db = Session()
    try:
        # Prefer deleting by key_hash; if key provided try hash
        key_hash = key
        if len(key) == 64 or len(key) == 64:  # naive check for hash
            db.query(APIKey).filter(APIKey.key_hash == key_hash).delete()
        else:
            # Try to hash provided token
            db.query(APIKey).filter(APIKey.key == key).delete()
        db.commit()
    finally:
        db.close()
    return RedirectResponse("/", status_code=302)

@app.post("/generate")
@limiter.limit("30/minute")
def generate(request: Request, req: GenerateRequest = None, prompt: Optional[str] = Form(None), x_api_key: Optional[str] = Header(None)):
    # Verify key via hash
    rec = _verify_key(x_api_key)

    if not rec:
        raise HTTPException(status_code=401, detail="Invalid API key")
    if rec.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="API key expired")

    prompt_text = None
    if req is not None and getattr(req, "prompt", None):
        prompt_text = req.prompt
    elif prompt:
        prompt_text = prompt

    if not prompt_text:
        raise HTTPException(status_code=400, detail="Missing 'prompt'")

    try:
        r = requests.post(OLLAMA_URL, json={
            "model": "llama3",
            "prompt": prompt_text,
            "stream": False
        }, timeout=10)
        r.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Upstream error: {exc}")

    try:
        return r.json()
    except ValueError:
        raise HTTPException(status_code=502, detail="Upstream returned invalid JSON")


# Summarize endpoint
class SummarizeRequest(BaseModel):
    text: Optional[str] = None
    url: Optional[str] = None
    length: Optional[str] = "short"  # short|long


@app.post("/summarize")
@limiter.limit("10/minute")
def summarize(request: Request, req: SummarizeRequest, x_api_key: Optional[str] = Header(None)):
    rec = _verify_key(x_api_key)
    if not rec:
        raise HTTPException(status_code=401, detail="Invalid API key")
    if rec.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="API key expired")

    text = None
    if req.text:
        text = req.text
    elif req.url:
        try:
            r = requests.get(req.url, timeout=5)
            r.raise_for_status()
            text = r.text
        except requests.RequestException as exc:
            raise HTTPException(status_code=400, detail=f"Could not fetch URL: {exc}")
    else:
        raise HTTPException(status_code=400, detail="Either 'text' or 'url' must be provided")

    # Build a prompt for Ollama to summarize
    prompt = f"Summarize the following text in a {req.length} summary:\n\n{text}"

    try:
        r = requests.post(OLLAMA_URL, json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }, timeout=15)
        r.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Upstream error: {exc}")

    try:
        return r.json()
    except ValueError:
        raise HTTPException(status_code=502, detail="Upstream returned invalid JSON")


# Ticket resolve endpoint
GOOGLE_APPSCRIPT_URL = os.environ.get("GOOGLE_APPSCRIPT_URL")

@app.post("/ticket/resolve")
@limiter.limit("5/minute")
def ticket_resolve(request: Request, ticket_id: str = Form(...), x_api_key: Optional[str] = Header(None)):
    """Fetch a ticket via configured Google AppScript URL and ask Ollama to draft a resolution/summarize."""
    rec = _verify_key(x_api_key)
    if not rec:
        raise HTTPException(status_code=401, detail="Invalid API key")
    if rec.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="API key expired")

    if not GOOGLE_APPSCRIPT_URL:
        raise HTTPException(status_code=500, detail="GOOGLE_APPSCRIPT_URL not configured")

    try:
        r = requests.get(GOOGLE_APPSCRIPT_URL, params={"ticket_id": ticket_id}, timeout=10)
        r.raise_for_status()
        ticket = r.json()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Error fetching ticket: {exc}")
    except ValueError:
        raise HTTPException(status_code=502, detail="Ticket endpoint returned non-JSON")

    # Expect ticket to contain at least 'subject' and 'description'
    subject = ticket.get("subject") or ticket.get("title") or f"Ticket {ticket_id}"
    description = ticket.get("description") or ticket.get("body") or ""

    prompt = (
        f"You are an assistant that helps support engineers.\nSummarize the ticket and propose a short resolution message to send to the reporter.\n\n"
        f"Subject: {subject}\n\nDescription:\n{description}\n\nProvide: 1) Short summary 2) Proposed response 3) Steps to reproduce or fix (if any)."
    )

    try:
        r = requests.post(OLLAMA_URL, json={"model": "llama3", "prompt": prompt, "stream": False}, timeout=20)
        r.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Upstream error: {exc}")

    try:
        return {"ticket": ticket, "ai_response": r.json()}
    except ValueError:
        raise HTTPException(status_code=502, detail="Upstream returned invalid JSON")


@app.get("/health")
def health():
    """Health endpoint to check DB accessibility and OLLAMA reachability."""
    # Check DB
    try:
        db = Session()
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        return {"ok": False, "db": False, "error": str(e)}
    finally:
        try:
            db.close()
        except Exception:
            pass

    # Check OLLAMA (optional) using a GET with short timeout
    try:
        r = requests.get(OLLAMA_URL, timeout=2)
        return {"ok": r.ok and db_ok, "db": True, "ollama_status": r.status_code}
    except Exception as e:
        return {"ok": False, "db": True, "ollama_error": str(e)}
