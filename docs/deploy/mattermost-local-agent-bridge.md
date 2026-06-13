# Mattermost LocalAgent bridge

`scripts/mattermost_local_agent_bridge.py` is the first bridge from a Mattermost `Agents/local-work` channel to the current-machine ClawDesk LocalAgent endpoint.

It deliberately uses only Python stdlib and Mattermost REST polling, so it can run on a workstation without a heavier bot framework.

## Flow

```text
Mattermost Agents/local-work message
        ↓
scripts/mattermost_local_agent_bridge.py
        ↓
POST /channels/{local_work_channel_id}/messages
POST /channels/{local_work_channel_id}/agent/local
        ↓
LocalAgent runner: shell / codex / agy / antigravity / grok
        ↓
Mattermost thread reply with status + output
```

## Environment

Required:

```bash
export MATTERMOST_URL=http://<home-mattermost-tailnet-host>:8065
export MATTERMOST_TOKEN=<mattermost-bot-token>
export MATTERMOST_LOCAL_WORK_CHANNEL_ID=<mattermost-channel-id>
```

Usually useful:

```bash
export CLAWDESK_URL=http://127.0.0.1:8000
export CLAWDESK_LOCAL_WORKSPACE=/Users/you/Projects/ClawDesk
export LOCAL_AGENT_BRIDGE_DEFAULT_AGENT=shell
export LOCAL_AGENT_BRIDGE_POLL_SECONDS=3
```

Optional:

```bash
# If unset, the bridge discovers the ClawDesk "Local Work" channel.
export CLAWDESK_LOCAL_CHANNEL_ID=<clawdesk-channel-id>

# In Agents/local-work, messages are processed without requiring a mention by default.
# Set this to 1 if you want explicit @LocalAgent mentions only.
export LOCAL_AGENT_BRIDGE_REQUIRE_MENTION=1
export LOCAL_AGENT_BOT_MENTIONS=@LocalAgent,@localagent
```

The ClawDesk backend controls whether LocalAgent really executes subprocesses:

```bash
export CLAWDESK_LOCAL_AGENT_MODE=stub   # safe default
export CLAWDESK_LOCAL_AGENT_MODE=exec   # opt-in real local execution
export CLAWDESK_LOCAL_AGENT_WORKSPACE_ROOT=/Users/you/Projects
```

## Run

Start the ClawDesk backend first:

```bash
cd server
CLAWDESK_LOCAL_AGENT_MODE=exec \
CLAWDESK_LOCAL_AGENT_WORKSPACE_ROOT=/Users/you/Projects \
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Run the bridge from the repo root:

```bash
python3 scripts/mattermost_local_agent_bridge.py
```

One-shot mode for testing:

```bash
python3 scripts/mattermost_local_agent_bridge.py --once
```

By default, the bridge marks posts visible at startup as already seen. To process recent posts present at startup:

```bash
python3 scripts/mattermost_local_agent_bridge.py --process-existing --once
```

## Message syntax

In the local-work channel:

```text
printf hello from local shell
/codex review the staged diff
/agy draft the SwiftUI settings panel
/grok scaffold a FastAPI endpoint
/grok-build scaffold a FastAPI endpoint
```

If `LOCAL_AGENT_BRIDGE_REQUIRE_MENTION=1`:

```text
@LocalAgent /shell pwd
@LocalAgent /codex review the staged diff
```

## Safety notes

- The bridge does not execute commands directly; it calls ClawDesk `/agent/local`.
- Real execution still requires `CLAWDESK_LOCAL_AGENT_MODE=exec` on the backend.
- The backend enforces `CLAWDESK_LOCAL_AGENT_WORKSPACE_ROOT`.
- Run this only inside trusted LAN/Tailscale networks.
- Keep `MATTERMOST_TOKEN` out of git.
