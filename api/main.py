from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import sqlite3
import hashlib
import hmac
import os
from datetime import datetime, timedelta
from typing import Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = FastAPI()

# Config
DB_PATH = os.getenv("DB_URL", "../data/keys.db")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "adminpass")
TUNNEL_URL = os.getenv("TUNNEL_URL", "")  # Set by startup script
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "prjctxno@gmail.com")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")  # Your Gmail address
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")  # Your Gmail app password

# Auto-detect Ollama models
def get_available_models():
    """Fetch available Ollama models from running Ollama instance."""
    try:
        import requests
        r = requests.get("http://127.0.0.1:11434/v1/models", timeout=3)
        if r.status_code == 200:
            data = r.json()
            models = [m.get('id') for m in data.get('data', [])]
            return models if models else ["llama3.2:3b"]
    except Exception as e:
        print(f"[WARNING] Could not auto-detect Ollama models: {e}")
    return ["llama3.2:3b"]

AVAILABLE_MODELS = get_available_models()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", AVAILABLE_MODELS[0] if AVAILABLE_MODELS else "llama3.2:3b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/v1/responses")
print(f"[INFO] Using Ollama model: {OLLAMA_MODEL}")
print(f"[INFO] Available models: {AVAILABLE_MODELS}")

security = HTTPBasic()
templates = Jinja2Templates(directory="templates")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Ensure data dir exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs("static", exist_ok=True)

# --- Email helper ---
def send_email(subject: str, body: str, to_email: str = ADMIN_EMAIL):
    """Send email via SMTP (Gmail)."""
    try:
        if not SMTP_USER or not SMTP_PASSWORD:
            print(f"[WARNING] Email not configured. Would send to {to_email}: {subject}")
            return True
        
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"[INFO] Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False

# --- DB helpers ---
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_schema():
    conn = get_db()
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

create_schema()

# --- Auth helpers ---
def hash_key(key: str) -> str:
    return hmac.new(SECRET_KEY.encode(), key.encode(), hashlib.sha256).hexdigest()

def verify_key(key: str) -> bool:
    conn = get_db()
    c = conn.cursor()
    h = hash_key(key)
    c.execute("SELECT * FROM api_keys WHERE key_hash=? AND revoked=0", (h,))
    row = c.fetchone()
    conn.close()
    if not row:
        return False
    if row["expires_at"] and datetime.utcnow() > datetime.fromisoformat(row["expires_at"]):
        return False
    return True

def require_api_key(request: Request):
    key = request.headers.get("x-api-key")
    if not key or not verify_key(key):
        raise HTTPException(status_code=401, detail="Invalid or expired API key.")

# --- Admin Auth ---
def require_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_user = hmac.compare_digest(credentials.username, ADMIN_USER)
    correct_pass = hmac.compare_digest(credentials.password, ADMIN_PASS)
    if not (correct_user and correct_pass):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials.", headers={"WWW-Authenticate": "Basic"})
    return credentials.username

# --- Models ---
class KeyCreateRequest(BaseModel):
    expires_at: Optional[str] = None  # ISO date format

class PromptRequest(BaseModel):
    prompt: str

class TunnelURLRequest(BaseModel):
    tunnel_url: str

# --- Startup endpoint to receive tunnel URL from cloudflared ---
@app.post("/admin/set-tunnel-url")
def set_tunnel_url(req: TunnelURLRequest):
    """Set tunnel URL (called by cloudflared or startup script)."""
    global TUNNEL_URL
    TUNNEL_URL = req.tunnel_url
    
    # Send email with tunnel URL
    email_body = f"""
    <h2>AI API Gateway is now accessible online!</h2>
    <p>Your CloudFlare Tunnel URL:</p>
    <h3><a href="{TUNNEL_URL}">{TUNNEL_URL}</a></h3>
    <p>Access your API Key Dashboard at: <a href="{TUNNEL_URL}/">{TUNNEL_URL}/</a></p>
    <p>Login with your admin credentials.</p>
    <p>This link is valid as long as the tunnel is running.</p>
    """
    send_email("🔗 Your AI API Gateway Tunnel URL", email_body, ADMIN_EMAIL)
    
    return {"status": "Tunnel URL set", "tunnel_url": TUNNEL_URL}

# --- Endpoints ---
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, user: str = Depends(require_admin)):
    conn = get_db()
    keys = conn.execute("SELECT * FROM api_keys").fetchall()
    conn.close()
    return templates.TemplateResponse("index.html", {"request": request, "keys": keys})

@app.post("/api/create")
def create_key(req: KeyCreateRequest, user: str = Depends(require_admin)):
    import secrets
    key = secrets.token_urlsafe(32)
    key_hash = hash_key(key)
    now = datetime.utcnow()
    
    # Parse expires_at date (expected in ISO format: YYYY-MM-DD)
    if req.expires_at:
        try:
            expires = datetime.fromisoformat(req.expires_at).replace(hour=23, minute=59, second=59)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid expires_at format. Use YYYY-MM-DD")
    else:
        expires = now + timedelta(days=30)
    
    conn = get_db()
    conn.execute("INSERT INTO api_keys (key_hash, created_at, expires_at) VALUES (?, ?, ?)", 
                 (key_hash, now.isoformat(), expires.isoformat()))
    conn.commit()
    conn.close()
    return {"api_key": key, "expires_at": expires.isoformat()}

@app.delete("/api/delete/{key_id}")
def delete_key(key_id: int, user: str = Depends(require_admin)):
    conn = get_db()
    conn.execute("UPDATE api_keys SET revoked=1 WHERE id=?", (key_id,))
    conn.commit()
    conn.close()
    return {"revoked": True}

@app.post("/generate")
def generate(req: PromptRequest, _=Depends(require_api_key)):
    import requests
    # Support both older `prompt`-style endpoints and Ollama's /v1/responses
    if "/v1/responses" in OLLAMA_URL:
        payload = {"model": OLLAMA_MODEL, "input": req.prompt}
    else:
        payload = {"prompt": req.prompt}
    r = requests.post(OLLAMA_URL, json=payload)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail="Ollama error")
    return r.json()

@app.get("/health")
def health():
    # Check DB
    try:
        conn = get_db()
        conn.execute("SELECT 1")
        conn.close()
    except Exception:
        return JSONResponse({"db": False, "ollama": False}, status_code=500)
    # Check Ollama
    import requests
    try:
        if "/v1/responses" in OLLAMA_URL:
            r = requests.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "input": "ping"}, timeout=3)
        else:
            r = requests.post(OLLAMA_URL, json={"prompt": "ping"}, timeout=3)
        ok = r.status_code == 200
        return {"db": True, "ollama": ok, "ollama_status": r.status_code, "ollama_text": r.text[:500]}
    except Exception as e:
        return {"db": True, "ollama": False, "error": str(e)}

@app.get("/api/tunnel-url")
def get_tunnel_url():
    """Get the current tunnel URL (for frontend display)."""
    return {"tunnel_url": TUNNEL_URL}
