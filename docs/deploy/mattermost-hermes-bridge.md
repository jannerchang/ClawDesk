# Mattermost Hermes bridge

`scripts/mattermost_hermes_bridge.py` is the home-side bridge from a Mattermost `Agents/hermes` channel to the ClawDesk Hermes endpoint.

It is the companion to `mattermost_local_agent_bridge.py`:

```text
@Hermes      → home Hermes/OpenClaw hub
@LocalAgent  → current-machine local runner
```

## Flow

```text
Mattermost Agents/hermes message
        ↓
scripts/mattermost_hermes_bridge.py
        ↓
POST /channels/{hermes_channel_id}/messages
POST /channels/{hermes_channel_id}/agent/hermes
        ↓
Hermes / OpenClaw via ClawDesk backend
        ↓
Mattermost thread reply with status + output
```

## Environment

Required:

```bash
export MATTERMOST_URL=http://<home-mattermost-tailnet-host>:8065
export MATTERMOST_TOKEN=<mattermost-bot-token>
export MATTERMOST_HERMES_CHANNEL_ID=<mattermost-channel-id>
```

Usually useful:

```bash
export CLAWDESK_URL=http://127.0.0.1:8000
export HERMES_BRIDGE_MAX_CONTEXT_MESSAGES=20
export HERMES_BRIDGE_POLL_SECONDS=3
```

Optional:

```bash
# If unset, the bridge discovers the ClawDesk "Hermes / OpenClaw" channel.
export CLAWDESK_HERMES_CHANNEL_ID=<clawdesk-channel-id>

# In Agents/hermes, messages are processed without requiring a mention by default.
# Set this to 1 if you want explicit @Hermes mentions only.
export HERMES_BRIDGE_REQUIRE_MENTION=1
export HERMES_BOT_MENTIONS=@Hermes,@hermes
```

The ClawDesk backend controls whether Hermes is real CLI mode or stub mode:

```bash
export CLAWDESK_HERMES_MODE=stub
export CLAWDESK_HERMES_MODE=cli
export CLAWDESK_HERMES_TIMEOUT_SECONDS=120
```

## Run

Start the ClawDesk backend first on the Home machine:

```bash
cd server
CLAWDESK_HERMES_MODE=cli \
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Run the bridge from the repo root:

```bash
python3 scripts/mattermost_hermes_bridge.py
```

One-shot mode for testing:

```bash
python3 scripts/mattermost_hermes_bridge.py --once
```

By default, the bridge marks posts visible at startup as already seen. To process recent posts present at startup:

```bash
python3 scripts/mattermost_hermes_bridge.py --process-existing --once
```

## Message syntax

In the Hermes channel:

```text
summarize this thread
/hermes summarize this thread
/ask what should we do next?
/home check the home service status
```

If `HERMES_BRIDGE_REQUIRE_MENTION=1`:

```text
@Hermes /ask summarize this thread
@Hermes check the home service status
```

## Safety notes

- The bridge does not execute Hermes directly; it calls ClawDesk `/agent/hermes`.
- Real Hermes execution still requires `CLAWDESK_HERMES_MODE=cli` on the backend.
- Run this only inside trusted LAN/Tailscale networks.
- Keep `MATTERMOST_TOKEN` out of git.
