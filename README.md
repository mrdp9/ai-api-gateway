# AI Platform (local) 🔧

**What this project is**

- A local **FastAPI** service that: manages API keys, provides a small web dashboard (admin), and forwards authenticated requests to an Ollama model running on your laptop (GPU-enabled). It includes endpoints for general generation, summarization, and a ticket-resolve workflow that can call a Google AppsScript to fetch ticket data.

---

## Architecture & components 🏗️

- `api/main.py` — the FastAPI app (dashboard, auth, endpoints).
- `api/templates/index.html` — admin dashboard to create/revoke keys.
- `ai-platform/data/keys.db` — SQLite database storing key metadata (hashed keys, expiry, revoked flag).
- `docker-compose.yml` (top-level and nested) — services: `api` (FastAPI) and `tunnel` (optional `cloudflared` tunnel).
- `scripts/migrate_schema.py` & `scripts/migrate_keys.py` — DB migration & key migration helpers.
- `tests/` — lightweight tests using `pytest`.

---

## Key security model 🔐

- API keys are generated and shown **once** at creation. The server stores only an **HMAC-SHA256** hash of the key (using `SECRET_KEY`).
- Admin dashboard is protected with **HTTP Basic Auth**. Default (development) credentials: `admin` / `adminpass` (change via env vars!).
- Endpoints that accept client requests use `x-api-key: <token>` header for authentication.
- Expired or revoked keys are rejected.

> Important: set a strong `SECRET_KEY` in production. Keys are validated by HMAC comparison — if you lose a key, revoke it and create a new one.

---

## Available endpoints 🚦

- `GET /` — **Admin dashboard** (Basic Auth protected).
- `POST /create` — Create a new API key (Basic Auth). Returns plaintext token **one-time**.
- `POST /delete/{key}` — Revoke/delete a key (Basic Auth).
- `POST /generate` — Forward prompt to Ollama. Auth: `x-api-key` header.
- `POST /summarize` — Summarize text or URL. Auth: `x-api-key` header. Rate-limited.
- `POST /ticket/resolve` — Fetch a ticket via `GOOGLE_APPSCRIPT_URL` and ask Ollama to draft a resolution. Auth: `x-api-key` header. Rate-limited.
- `GET /health` — Health check (DB + Ollama connectivity).

---

## Environment variables (important) ⚙️

- `SECRET_KEY` (required) — secret used to HMAC API keys.
- `ADMIN_USER`, `ADMIN_PASS` — admin Basic Auth credentials. Recommended to set to secure values.
- `OLLAMA_URL` — default: `http://host.docker.internal:11434/api/generate` (point to your Ollama instance).
- `DB_URL` or `DATA_DIR` — override SQLite path (defaults to `ai-platform/data/keys.db`).
- `GOOGLE_APPSCRIPT_URL` — optional ticket-fetch endpoint for `/ticket/resolve`.

Example `.env` in `api/`:

```env
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
ADMIN_USER=admin
ADMIN_PASS=change-me
OLLAMA_URL=http://host.docker.internal:11434/api/generate
```

---

## Run locally (dev) 🧑‍💻

1. Create and activate venv:

```bash
cd ai-platform/ai-platform/api
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

2. Run DB migrations (idempotent):

```bash
cd $(git rev-parse --show-toplevel)
python3 scripts/migrate_schema.py
python3 scripts/migrate_keys.py
```

3. Start FastAPI (dev):

```bash
cd ai-platform/ai-platform/api
uvicorn main:app --host 0.0.0.0 --port 3001
# open http://localhost:3001/ and authenticate with ADMIN_USER/ADMIN_PASS
```

> Note: on this machine `port 3000` was already used by another Docker process; the project uses **3001** by default. If you need `3000`, stop the process that binds it (e.g. `sudo lsof -i :3000`).

---

## Run with Docker Compose (expose public HTTPS)

- Two compose files exist (nested + top-level). The top-level `docker-compose.yml` is intended for running from the repo root.
- By default the `api` service runs `uvicorn` inside the container on port **8000**; the compose file maps it to host port **3001**.
- `cloudflared` service is included for creating a secure HTTPS tunnel (Cloudflare Tunnel). Configure Cloudflare credentials and follow Cloudflare docs to expose the container without opening inbound ports.

Start:

```bash
docker-compose up --build
# then visit http://localhost:3001/ or the Cloudflare tunnel URL when configured
```

---

## Rate limiting & abuse protection ⚖️

- Per-key (fallback to IP) rate limiting with `slowapi` applied to sensitive endpoints (`/generate`, `/summarize`, `/ticket/resolve`).
- Recommended: add IP-level firewall rules and monitoring if you expose the service publicly.

---

## Testing 🧪

- Tests are in `api/tests/` and run with `pytest`.

```bash
cd ai-platform/ai-platform/api
. .venv/bin/activate
pytest -q
```

Note: tests import the `main` module; if pytest fails to import `main` run tests from the `api` directory or set `PYTHONPATH` accordingly.

---

## Troubleshooting ⚠️

- SQLite errors ("unable to open database file"): ensure `ai-platform/ai-platform/data/` exists and is writable.
- Missing packages: run `pip install -r requirements.txt` inside the virtualenv.
- Port in use: check `ss -ltnp | grep :3000` and stop conflicting container.
- If Ollama is not reachable, ensure it is running locally and `OLLAMA_URL` is set correctly.

---

## Next steps / enhancements ✨

- Harden admin auth (hash password or use token-based admin auth).
- Add Prometheus metrics and better logging/alerts.
- Add CI to run tests and linting, and a small e2e test that spins up a local Ollama mock.

---

If you want, I can now: 1) consolidate nested compose files, 2) enable Cloudflare Tunnel configuration, or 3) replace Basic Auth with a stronger admin auth flow. Which should I do next? ✅# ai-api-gateway
