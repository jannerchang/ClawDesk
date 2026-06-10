# ClawDesk Server

Local FastAPI prototype for ClawDesk.

## Setup

```bash
cd /Users/janner/Projects/ClawDesk/server
uv sync
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Default database path:

```text
server/.data/clawdesk-dev.db
```

Override with:

```bash
export CLAWDESK_DB_PATH=/path/to/clawdesk.db
```

## Smoke test

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/spaces

SPACE_ID=$(curl -s http://127.0.0.1:8000/spaces | python3 -c 'import json,sys; print(json.load(sys.stdin)[0]["id"])')
CHANNEL_ID=$(curl -s -X POST http://127.0.0.1:8000/channels \
  -H 'content-type: application/json' \
  -d "{\"space_id\":\"$SPACE_ID\",\"name\":\"技术聊天\",\"type\":\"tech\",\"mode\":\"mixed\"}" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')

curl -s -X POST http://127.0.0.1:8000/channels/$CHANNEL_ID/messages \
  -H 'content-type: application/json' \
  -d '{"content":"第一条测试消息"}'

curl http://127.0.0.1:8000/channels/$CHANNEL_ID/messages
```
