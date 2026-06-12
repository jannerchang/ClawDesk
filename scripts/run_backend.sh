#!/bin/bash
set -euo pipefail

HOST="${CLAWDESK_HOST:-127.0.0.1}"
PORT="${CLAWDESK_PORT:-8765}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SERVER="$ROOT/server"
DB_PATH="${CLAWDESK_DB_PATH:-$SERVER/.data/clawdesk-dev.db}"
HERMES_MODE="${CLAWDESK_HERMES_MODE:-auto}"
TIMEOUT_SECONDS="${CLAWDESK_HERMES_TIMEOUT_SECONDS:-120}"

mkdir -p "$(dirname "$DB_PATH")"

echo "ClawDesk backend"
echo "  host:        $HOST"
echo "  port:        $PORT"
echo "  db:          $DB_PATH"
echo "  hermes_mode: $HERMES_MODE"
echo
echo "Health URL: http://$HOST:$PORT/health"
echo "If HOST is 0.0.0.0, use your Tailscale IP from the remote client, e.g. http://100.x.y.z:$PORT"
echo

cd "$SERVER"
CLAWDESK_DB_PATH="$DB_PATH" \
CLAWDESK_HERMES_MODE="$HERMES_MODE" \
CLAWDESK_HERMES_TIMEOUT_SECONDS="$TIMEOUT_SECONDS" \
uv run uvicorn app.main:app --host "$HOST" --port "$PORT"
