# Project Context

This file provides a living context for the AI API Gateway project. It is intended to be updated whenever significant changes are made, so that future developers or AI-powered tools can understand the project's history, decisions, and requirements. This will help guide modifications, extensions, or migrations to other LLMs or AI tools.

## Project Overview
- **Project Name:** AI API Gateway
- **Purpose:** FastAPI service to manage API keys, provide an admin dashboard with public internet access via CloudFlare Tunnel, and forward authenticated requests to an Ollama model. Supports endpoints for generation, summarization, and ticket resolution workflows with automatic email notifications.
- **Main Components:**
  - `api/`: FastAPI app (`main.py`), Dockerfile, templates, requirements.
  - `data/`: SQLite database (`keys.db`) for API key metadata.
  - `scripts/`: Migration, context update, and tunnel notification scripts.
  - `docker-compose.yml`: Orchestrates API, CloudFlare Tunnel, and tunnel notifier.
  - `SETUP_GUIDE.md`: Complete deployment and configuration guide.

## Key Steps & Decisions
- **Project Structure:**
  - Modular: API logic, data, scripts, and templates are separated for clarity and maintainability.
  - Admin dashboard uses Jinja2 templates.
- **Tech Stack:**
  - Python 3, FastAPI, Uvicorn, Pydantic, Requests, Jinja2.
  - SQLite for persistent storage of API keys.
- **Endpoints:**
  - `/` (dashboard, Basic Auth), `/create`, `/delete/{key}` (admin), `/generate`, `/summarize`, `/ticket/resolve` (API key auth), `/health`.
- **Security:**
  - API keys are HMAC-SHA256 hashed with a secret key, stored only as hashes.
  - Admin dashboard protected by HTTP Basic Auth (credentials via env vars).
  - Endpoints require `x-api-key` header; expired/revoked keys are rejected.
  - Rate limiting via `slowapi` (recommended for public exposure).
  - CloudFlare Tunnel provides automatic HTTPS and DDoS protection.
- **Database:**
  - SQLite (`data/keys.db`). Schema managed by `scripts/migrate_schema.py`.
- **Deployment:**
  - Local: venv + Uvicorn. 
  - Public: Docker Compose with CloudFlare Tunnel for secure HTTPS.
  - Environment variables control secrets, DB path, admin credentials, email, and Ollama endpoint.
  - Automatic tunnel URL discovery and email notification to admin.
- **Testing:**
  - Pytest-based tests in `api/tests/`.
- **Email Integration:**
  - Gmail SMTP for sending tunnel URL to admin email (`prjctxno@gmail.com`).
  - Requires Gmail App Password (16-char).
  - Email sent automatically when tunnel is established.
- **MCP Servers:**
  - [Update here if/when MCP servers are integrated.]

## Mindset & Philosophy
- **Clarity & Maintainability:**
  - Code and configs are clear, well-documented, and easy to modify.
  - Use comments, docstrings, and this context file for transparency.
- **Extensibility:**
  - APIs and modules are designed for easy extension (new endpoints, models, workflows).
- **Security:**
  - Prioritize secure key handling, admin auth, and rate limiting.
- **AI/LLM Compatibility:**
  - Project is structured and documented for easy understanding and modification by AI-powered tools or LLMs.


## Change Log
- **[2026-01-31]**: Created `context.md` to track project context, decisions, and philosophy.
- **[2026-02-01]**: 
  - Added CloudFlare Tunnel integration for public HTTPS access
  - Implemented email notifications (Gmail SMTP) to send tunnel URL
  - Enhanced frontend dashboard with modern UI and real-time tunnel URL display
  - Added Docker support with `docker-compose.yml` and `Dockerfile`
  - Created comprehensive `SETUP_GUIDE.md` for deployment
  - Added environment variable configuration (`.env.example`)
  - Integrated `slowapi` for rate limiting
  - Added `/admin/set-tunnel-url` endpoint for tunnel URL registration
  - Added `/api/tunnel-url` endpoint for frontend to fetch tunnel URL

---
## Automated Context Updates

To automate context updates, use the script at `scripts/update_context.py`:

```bash
python scripts/update_context.py
# (or import and call update_context() in your deployment or CI scripts)
```

Call `update_context(summary, file, description)` after significant changes to append a new entry to this file.

---

## Important: AI/LLM Compatibility Notes

This project is specifically designed for easy modification by AI tools and LLMs:

### Structure for AI Understanding
- **Flat hierarchy**: Most code is in `api/main.py` (easy to understand in one file)
- **Clear naming**: Function and variable names are descriptive
- **Detailed comments**: Key sections are well-documented
- **Type hints**: Pydantic models for type safety

### Documentation for AI Modification
- **context.md** (this file): Design decisions and current state
- **README.md**: API endpoints and configuration
- **SETUP_GUIDE.md**: Step-by-step deployment
- **QUICK_START.md**: Quick onboarding
- **STATUS.md**: Feature list and roadmap
- **IMPLEMENTATION_SUMMARY.md**: What was built and how it works

### Tips for AI Tools Modifying This Project
1. Start by reading **context.md** (you are here)
2. Check **README.md** for API structure
3. Review **STATUS.md** for current features
4. Edit **api/main.py** for backend changes
5. Edit **api/templates/index.html** for frontend changes
6. Update `.env.example` if adding new environment variables
7. Update **context.md** (this file) after making changes
8. Test with: `docker-compose up --build`

### Self-Documenting Updates
After any significant change, call:
```python
from scripts.update_context import update_context

update_context(
    summary="Added new endpoint for user management",
    file="api/main.py",
    description="Created POST /users endpoint with role-based access control. Requires new USER_ROLE env var."
)
```

This keeps context.md automatically updated for future AI tools.

---

---

> **Update this file whenever you make a significant change, add a new feature, or make a key decision.**
