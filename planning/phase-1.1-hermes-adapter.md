# Phase 1.1: Hermes Adapter Invocation Switch

## Goal

Add a minimal, safe backend endpoint that lets a channel invoke Hermes and persist the result as both an `agent_runs` record and a Hermes message.

## Scope

- Default behavior remains stubbed and offline.
- Real Hermes CLI invocation is opt-in via env var.
- Existing CRUD, subchannel, smoke, and SwiftUI build must not regress.
- No secrets, VPS, or external persistence.

## Required behavior

### Environment

- `CLAWDESK_HERMES_MODE=stub` default.
- `CLAWDESK_HERMES_MODE=cli` enables real CLI invocation.
- `CLAWDESK_HERMES_TIMEOUT_SECONDS` optional timeout, default conservative.

### Endpoint

Add:

```text
POST /channels/{channel_id}/agent/hermes
```

Payload:

```json
{
  "prompt": "optional direct prompt",
  "max_context_messages": 20
}
```

If `prompt` is omitted, use recent channel messages as context.

### Persistence

For every invocation:

- insert `agent_runs` with status running/succeeded/failed;
- on success, insert a `messages` row in the channel with `sender_type=hermes`, `sender_name=Hermes`, `content=<output>`;
- on failure, record error in `agent_runs` and return a useful HTTP error.

### Stub mode

Stub mode should be deterministic enough for tests and smoke:

```text
[Hermes stub] ...
```

### CLI mode

CLI mode should call Hermes safely, preferably:

```bash
hermes chat -q <prompt> --profile default
```

Use subprocess with timeout. Avoid shell=True.

## Tests

Add pytest coverage for stub endpoint:

- create channel;
- create user message;
- call `/agent/hermes`;
- verify response;
- verify Hermes message inserted;
- verify agent_run inserted or exposed through test DB query.

## Verification

Required commands:

```bash
cd server
uv run pytest -q
cd ../apple/ClawDesk
swift build
cd ../..
./scripts/smoke.py
```
