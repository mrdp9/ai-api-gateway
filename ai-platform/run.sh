#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
API_DIR="$ROOT/api"
TOP_DIR="$(cd "$ROOT/.." && pwd)"
ENV_FILE="$API_DIR/.env"
LOG_DIR="$API_DIR/logs"
PID_DIR="$API_DIR/.run"
VENV_DIR="$API_DIR/.venv"

MODE="${1:-dev}"

# Ensure directories
mkdir -p "$LOG_DIR" "$PID_DIR" "$API_DIR/../data"

_create_env_if_missing() {
  if [ ! -f "$ENV_FILE" ]; then
    echo "Creating $ENV_FILE with generated SECRET_KEY and example values (change before production)"
    SECRET_KEY=$(python3 - <<'PY'
import secrets
print(secrets.token_hex(32))
PY
)
    cat > "$ENV_FILE" <<EOF
SECRET_KEY=$SECRET_KEY
ADMIN_USER=admin
ADMIN_PASS=change-me
OLLAMA_URL=http://host.docker.internal:11434/api/generate
EOF
  fi
}

ensure_venv_and_deps() {
  cd "$API_DIR"
  if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtualenv at $VENV_DIR"
    python3 -m venv "$VENV_DIR"
  fi
  # shellcheck disable=SC1091
  . "$VENV_DIR/bin/activate"
  pip install --upgrade pip >/dev/null
  pip install -r requirements.txt
}

start_dev() {
  echo "Starting in dev mode (uvicorn)..."
  _create_env_if_missing
  ensure_venv_and_deps

  # Run migrations from repo top
  if [ -f "$TOP_DIR/scripts/migrate_schema.py" ]; then
    echo "Running DB migrations"
    python3 "$TOP_DIR/scripts/migrate_schema.py"
    python3 "$TOP_DIR/scripts/migrate_keys.py" || true
  fi

  # Start uvicorn in background and record PID
  if [ -f "$PID_DIR/uvicorn.pid" ]; then
    if kill -0 "$(cat "$PID_DIR/uvicorn.pid")" 2>/dev/null; then
      echo "uvicorn appears to be running already (pid: $(cat "$PID_DIR/uvicorn.pid"))"
      return
    else
      rm -f "$PID_DIR/uvicorn.pid"
    fi
  fi

  # Export .env so the server process inherits ADMIN_USER, ADMIN_PASS, OLLAMA_URL, etc.
  if [ -f "$ENV_FILE" ]; then
    set -a
    # shellcheck disable=SC1090
    . "$ENV_FILE"
    set +a
  fi

  cd "$API_DIR"
  nohup "$VENV_DIR/bin/uvicorn" main:app --host 0.0.0.0 --port 3001 > "$LOG_DIR/uvicorn.log" 2>&1 &
  echo $! > "$PID_DIR/uvicorn.pid"
  echo "uvicorn started (pid: $(cat "$PID_DIR/uvicorn.pid")); logs: $LOG_DIR/uvicorn.log"
}

stop_dev() {
  if [ -f "$PID_DIR/uvicorn.pid" ]; then
    PID=$(cat "$PID_DIR/uvicorn.pid")
    echo "Stopping uvicorn (pid: $PID)"
    kill "$PID" || true
    rm -f "$PID_DIR/uvicorn.pid"
    echo "Stopped"
  else
    echo "No uvicorn PID file found; nothing to stop"
  fi
}

start_docker() {
  _create_env_if_missing
  echo "Starting via Docker Compose (compose file: $ROOT/docker-compose.yml)"
  if ! command -v docker >/dev/null; then
    echo "docker not found. Install Docker and retry." >&2
    exit 1
  fi
  if command -v docker-compose >/dev/null; then
    docker-compose -f "$ROOT/docker-compose.yml" up -d --build
  else
    docker compose -f "$ROOT/docker-compose.yml" up -d --build
  fi
  echo "Docker started. Use 'docker compose logs -f api' or 'docker-compose logs -f api' to view logs"
}

stop_docker() {
  echo "Stopping docker compose stack (if running)"
  if command -v docker-compose >/dev/null; then
    docker-compose -f "$ROOT/docker-compose.yml" down
  else
    docker compose -f "$ROOT/docker-compose.yml" down
  fi
}

case "$MODE" in
  dev)
    start_dev
    ;;
  stop)
    stop_dev
    stop_docker || true
    ;;
  docker)
    start_docker
    ;;
  down)
    stop_docker
    ;;
  *)
    echo "Usage: $0 [dev|docker|stop|down]"
    echo "  dev    - start in dev mode (venv + uvicorn, port 3001)"
    echo "  docker - build & start via Docker Compose"
    echo "  stop   - stop dev uvicorn and docker stack"
    echo "  down   - stop docker compose stack only"
    exit 2
    ;;
esac

exit 0
