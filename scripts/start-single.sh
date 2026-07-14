#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/server-core"

echo "Starting LocalMeetingAI backend on http://127.0.0.1:8000"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python main.py
