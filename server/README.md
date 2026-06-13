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

## Hermes agent endpoint

Phase 1.1 adds a safe Hermes invocation endpoint. Stub mode is the default.

```bash
curl -s -X POST http://127.0.0.1:8000/channels/$CHANNEL_ID/agent/hermes \
  -H 'content-type: application/json' \
  -d '{"prompt":"请简短回复"}'
```

Environment:

```bash
export CLAWDESK_HERMES_MODE=stub   # default, deterministic offline response
export CLAWDESK_HERMES_MODE=cli    # opt-in real Hermes CLI call
export CLAWDESK_HERMES_TIMEOUT_SECONDS=60
```

CLI mode invokes:

```bash
hermes chat -q <prompt> --profile default
```

Every invocation writes an `agent_runs` record. Successful invocations also insert a channel message with `sender_type=hermes` and `sender_name=Hermes`.

## LocalAgent endpoint

The LocalAgent endpoint is the current-machine runner for the `@LocalAgent` bot. It is intentionally separate from Hermes: it can run local coding agents or a bounded shell command from an explicit workspace.

```bash
curl -s -X POST http://127.0.0.1:8000/channels/$CHANNEL_ID/agent/local \
  -H 'content-type: application/json' \
  -d '{"agent":"shell","workspace":"/path/to/project","prompt":"printf LOCAL_OK"}'
```

Environment:

```bash
export CLAWDESK_LOCAL_AGENT_MODE=stub   # default, deterministic offline response
export CLAWDESK_LOCAL_AGENT_MODE=exec   # opt-in local subprocess execution
export CLAWDESK_LOCAL_AGENT_WORKSPACE_ROOT=$HOME
export CLAWDESK_LOCAL_AGENT_TIMEOUT_SECONDS=120
```

Supported `agent` values:

```text
shell, codex, antigravity, agy, grok, grok-build
```

`exec` mode requires the requested workspace to be inside `CLAWDESK_LOCAL_AGENT_WORKSPACE_ROOT`. Every invocation writes an `agent_runs` record. Successful invocations also insert a channel message with `sender_type=local-agent` and `sender_name=LocalAgent`.

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
