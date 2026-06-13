# Bot session bindings

ClawDesk treats “dragging a bot into a channel” as creating a **channel bot binding**: a bot identity is bound to one channel with one session key and one listening mode.

This gives each channel a stable agent session boundary without requiring every message everywhere to reach every bot.

## Concept

```text
Channel
  ├── members
  │   ├── user
  │   ├── Hermes
  │   └── LocalAgent
  └── bot bindings
      ├── Hermes      → session_key=hermes:<channel_id>
      └── LocalAgent  → session_key=local-agent:<channel_id>
```

A bot binding answers four questions:

| Field | Meaning |
|---|---|
| `channel_id` | Which channel the bot is present in |
| `user_id` | Which bot user, e.g. Hermes or LocalAgent |
| `bot_kind` | Runtime target: `hermes` or `local-agent` |
| `session_key` | Stable session/context key for this channel-bot pair |
| `listen_mode` | `mention`, `channel`, or `manual` |
| `enabled` | Whether the binding is active |
| `config` | Small JSON config such as profile/model/workspace defaults |

## Listening modes

```text
mention  → bot responds only when mentioned or explicitly selected
channel  → bot treats the whole channel as its inbox
manual   → bot is present but only runs from direct UI/API invocation
```

Default seed behavior:

- `Hermes / OpenClaw` channel: Hermes binding defaults to `channel`.
- `Local Work` channel: LocalAgent binding defaults to `channel`.
- Other channels: both bots default to `mention`.

## API

List bindings:

```http
GET /channels/{channel_id}/bot-bindings
```

Create/bind a bot:

```http
POST /channels/{channel_id}/bot-bindings
```

```json
{
  "user_id": "bot_hermes",
  "bot_kind": "hermes",
  "listen_mode": "mention",
  "session_key": "hermes:custom-session",
  "config": {"profile": "default"}
}
```

Update a binding/session:

```http
PATCH /channels/{channel_id}/bot-bindings/{binding_id}
```

```json
{
  "listen_mode": "channel",
  "session_key": "hermes:project-alpha",
  "enabled": true,
  "config": {"profile": "default", "max_context_messages": 40}
}
```

Delete/unbind:

```http
DELETE /channels/{channel_id}/bot-bindings/{binding_id}
```

## Product behavior

The intended UI behavior is:

1. Drag or add a bot to a channel.
2. ClawDesk creates a channel member and a bot binding.
3. The user chooses whether the bot listens by mention, whole-channel, or manual invocation.
4. The binding session key becomes the stable identity for that bot’s channel context.

Mattermost bridge scripts can later read these bindings to decide whether a Mattermost post should be routed to Hermes or LocalAgent.
