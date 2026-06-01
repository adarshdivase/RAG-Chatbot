#!/usr/bin/env bash
# One-command demo: starts API + UI (macOS / Linux)
set -euo pipefail

RAG_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECTS_ROOT="$(dirname "$RAG_ROOT")"
BACKEND="$RAG_ROOT/backend"
FRONTEND="$PROJECTS_ROOT/RAG-Chatbot-Frontend/frontend"
VENV_PY="$BACKEND/venv/bin/python"

echo "Aura Enterprise Demo Launcher"
echo "  Backend:  $BACKEND"
echo "  Frontend: $FRONTEND"

[[ -f "$BACKEND/.env" ]] || cp "$BACKEND/.env.example" "$BACKEND/.env"

if [[ ! -x "$VENV_PY" ]]; then
  python3 -m venv "$BACKEND/venv"
  "$BACKEND/venv/bin/pip" install -r "$BACKEND/requirements.txt"
fi

[[ -d "$FRONTEND" ]] || { echo "Frontend not found: $FRONTEND"; exit 1; }

cleanup() {
  kill "$API_PID" "$UI_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

(cd "$BACKEND" && "$VENV_PY" -m uvicorn main:app --host 127.0.0.1 --port 8000) &
API_PID=$!

(cd "$FRONTEND" && python3 -m http.server 5500 --bind 127.0.0.1) &
UI_PID=$!

sleep 3
URL="http://127.0.0.1:5500/?api=http://127.0.0.1:8000"
echo ""
echo "  API:  http://127.0.0.1:8000/docs"
echo "  UI:   $URL"
echo ""

if command -v xdg-open >/dev/null; then xdg-open "$URL"
elif command -v open >/dev/null; then open "$URL"
fi

echo "Press Ctrl+C to stop both servers."
wait
