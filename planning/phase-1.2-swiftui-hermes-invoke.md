# Phase 1.2: SwiftUI Hermes Invoke Flow

## Goal

Wire the existing backend Hermes invocation endpoint into the SwiftUI client so Janner can send a user message and explicitly ask Hermes to reply inside the same channel.

## Scope

- Keep backend stub mode as default.
- Do not enable automatic Hermes invocation on every send yet.
- Add SwiftUI/API models for `POST /channels/{channel_id}/agent/hermes`.
- Add a visible “Ask Hermes” action in `ChatView`.
- Refresh/append the returned Hermes message.
- Update smoke test and README so Phase 1.1/1.2 behavior is documented.

## Required behavior

### Apple client

1. Add Codable models for:
   - `AgentRun`
   - `HermesInvokeResponse`
   - `HermesInvokeRequest`
2. Add `APIClient.invokeHermes(channelId:prompt:maxContextMessages:)`.
3. Add a toolbar or composer-row button in `ChatView`:
   - label can be `Ask Hermes` or icon + text;
   - disabled while sending/invoking;
   - when tapped, calls backend with no direct prompt so backend uses recent channel messages;
   - appends the returned Hermes message or reloads messages.
4. Surface errors in the existing error message area.

### Backend/smoke/docs

1. Update `scripts/smoke.py` to call `/channels/{id}/agent/hermes` in default stub mode and verify:
   - returned message sender_type is `hermes`;
   - returned content starts with `[Hermes stub]`.
2. Update README:
   - Hermes endpoint exists;
   - stub default;
   - CLI mode env vars: `CLAWDESK_HERMES_MODE=cli`, `CLAWDESK_HERMES_TIMEOUT_SECONDS`;
   - current phase no longer says “Hermes adapter stub only, real Hermes calls not yet enabled” without nuance.

## Verification

Run from repo root:

```bash
cd server && uv run pytest -q
cd ../apple/ClawDesk && swift build
cd ../.. && ./scripts/smoke.py
```

## Non-goals

- No background WebSocket streaming.
- No automatic reply per message.
- No OpenClaw adapter.
- No real Hermes CLI smoke in default tests.
