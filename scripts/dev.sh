#!/usr/bin/env bash
# Dev stack: FastAPI :8000 + Next.js :3000. Memory-safe: scoped reload dirs,
# Turbopack with a 1GB heap cap (conventions carried from the Taabel stack).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ -f "$ROOT/.env" ]; then
  set -a; source "$ROOT/.env"; set +a
fi

cleanup() { kill 0 2>/dev/null || true; }
trap cleanup EXIT

(
  cd "$ROOT/backend"
  .venv/bin/uvicorn app:app --port 8000 \
    --reload --reload-dir . --reload-exclude '.venv/*' --reload-exclude 'output/*'
) &

(
  cd "$ROOT/frontend"
  npm run dev
) &

wait
