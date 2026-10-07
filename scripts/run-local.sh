#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
[ -f "$BACKEND/.env" ] || cp "$ROOT/.env.example" "$BACKEND/.env"
python3 -m uvicorn app.main:app --reload --port 8000 &
cd "$FRONTEND"
npm run dev
