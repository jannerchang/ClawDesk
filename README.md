# ClawDesk

ClawDesk 正在转向一个更务实的目标：**本地自托管、可经 Tailscale 访问的局域网版 Discord / Telegram + Hermes/OpenClaw Agent 工作台**。

它不是为了把所有聊天、同步、文件系统从零重写一遍；相反，ClawDesk 会优先复用成熟开源通信底座，把个人协作、资料管理和 Agent 对话的数据主权留在本地。核心边界是：消息、文件、附件、索引和 Agent 上下文默认保存在用户自己的 Mac mini / Home server / 局域网存储上；远程访问走 Tailscale，不依赖第三方聊天平台存储敏感材料。

## Direction

Current preferred deployment path:

```text
iPhone / iPad / Mac / Web client
        ↓ LAN or Tailscale
Self-hosted Mattermost on Home server / Mac mini
        ↓
Local PostgreSQL + local file storage
        ↓
Two visible bots:
  - @Hermes for the home Hermes/OpenClaw hub
  - @LocalAgent for workstation-local Codex / Antigravity / Grok Build
```

Mattermost is the first practical self-hosted communication base because it already provides Discord/Slack-like channels, direct messages, mobile clients, file uploads, bot/webhook APIs, and local storage. ClawDesk then adds the agent-workbench layer: `@Hermes` handles long-running/home-side assistant work, while `@LocalAgent` runs current-machine coding agents directly. Matrix / Element, Zulip, Nextcloud Talk, AppFlowy, AFFiNE, and Obsidian integrations remain candidates for later borrowing or integration.

## Goals

- Keep private messages and files off third-party chat storage.
- Run the communication server locally or on a trusted home machine.
- Access it over LAN or Tailscale instead of exposing it publicly.
- Reuse open-source infrastructure where it is already good enough.
- Add two visible bot participants: `@Hermes` for the home assistant hub and `@LocalAgent` for local workstation tools.
- Later provide a polished Apple/iOS experience for personal and small-team use.

## Repository layout

```text
server/                FastAPI + SQLite prototype from the earlier native ClawDesk path
apple/                 SwiftUI client package skeleton from the earlier native ClawDesk path
deploy/mattermost/     Local Mattermost deployment starter for LAN/Tailscale use
docs/deploy/           Deployment notes, including Mattermost + Tailscale
docs/architecture/     Architecture notes, including the two-bot local workspace model
planning/              FFCS planning artifacts
scripts/               Smoke-test helpers
```

## Mattermost local deployment starter

The first self-hosted path lives under:

```text
deploy/mattermost/
```

Create a local `.env` from the example:

```bash
cd deploy/mattermost
cp .env.example .env
```

Edit `.env` before first start, especially the PostgreSQL password and site URL. For local-only testing:

```bash
MM_HOST=127.0.0.1
MM_SITEURL=http://127.0.0.1:8065
```

For LAN/Tailscale access from other devices, bind on all interfaces and set a LAN or Tailscale URL:

```bash
MM_HOST=0.0.0.0
MM_SITEURL=http://<home-machine-tailscale-ip-or-dns>:8065
```

Start:

```bash
docker compose up -d
```

Open:

```text
http://127.0.0.1:8065
```

or the configured LAN/Tailscale URL. Mattermost data, uploaded files, config, logs, and PostgreSQL data stay under `deploy/mattermost/mattermost/`, which is intentionally ignored by git.

Full notes: [`docs/deploy/mattermost-local-tailscale.md`](docs/deploy/mattermost-local-tailscale.md).

LocalAgent bridge notes: [`docs/deploy/mattermost-local-agent-bridge.md`](docs/deploy/mattermost-local-agent-bridge.md).

## Two-bot workspace model

The preferred agent model uses two Mattermost bot identities:

- `@Hermes`: backed by the home Hermes/OpenClaw hub for long-running assistant work, memory, archive, scheduled/background jobs, and home-side services.
- `@LocalAgent`: backed by a lightweight ClawDesk runner on the current workstation for local Codex, Antigravity, Grok Build, shell/build/test tasks, and current-project operations.

This keeps workstation work direct: the office/current machine does not need a full Hermes install just to run local coding agents. Details: [`docs/architecture/two-bot-local-workspace.md`](docs/architecture/two-bot-local-workspace.md).

## Earlier native prototype

The existing FastAPI + SwiftUI prototype is kept as a native-client exploration path. It remains useful for Hermes-specific UX and Apple-native experiments, but it is no longer the only or default path.

### Backend quick start

```bash
cd server
uv sync
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Use real Hermes CLI mode:

```bash
CLAWDESK_HERMES_MODE=cli uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Default mode is `auto`: the backend tries local Hermes CLI first and falls back to stub output if Hermes is unavailable. Use `cli` with `CLAWDESK_HERMES_FALLBACK_TO_STUB=0` when you want failures to be explicit.

Default dev database:

```text
server/.data/clawdesk-dev.db
```

Override:

```bash
export CLAWDESK_DB_PATH=/path/to/clawdesk.db
```

### Hermes agent endpoint

The backend exposes an explicit Hermes invocation endpoint:

```text
POST /channels/{channel_id}/agent/hermes
```

When `prompt` is omitted or blank, the backend builds the prompt from recent channel messages. Each invocation writes an `agent_runs` record and inserts a Hermes message into the channel.

Hermes is local-first. The backend defaults to `auto` mode:

```bash
export CLAWDESK_HERMES_MODE=auto
```

`auto` tries the local Hermes CLI first, then falls back to deterministic stub output if Hermes is unavailable. For offline/dev tests, force stub mode:

```bash
export CLAWDESK_HERMES_MODE=stub
```

For strict real Hermes CLI invocation:

```bash
export CLAWDESK_HERMES_MODE=cli
export CLAWDESK_HERMES_TIMEOUT_SECONDS=120
export CLAWDESK_HERMES_FALLBACK_TO_STUB=0
```

CLI mode runs `hermes chat -q <prompt> --profile <profile> --quiet` on the local machine. Default tests and `scripts/smoke.py` use stub mode; `scripts/smoke_real_hermes.py` verifies the real CLI path.

### Attachment endpoint

The backend has a minimal local attachment endpoint:

```text
POST /messages/{message_id}/attachments
GET /messages/{message_id}/attachments
```

Uploads use `multipart/form-data` field `file`. Files are stored under the local backend data directory and metadata is recorded in SQLite. This is the Phase 0.5 foundation for images, photos, files, and voice; Hermes does not interpret attachments yet.

### SwiftUI client build/run

```bash
swift build --package-path apple/ClawDesk
swift run --package-path apple/ClawDesk ClawDeskApp
```

The client defaults to:

```text
http://127.0.0.1:8000
```

Override with environment variable:

```bash
CLAWDESK_BASE_URL=http://127.0.0.1:8000 swift run --package-path apple/ClawDesk ClawDeskApp
```

You can also configure the backend URL in the client settings panel.

## API notes

- `GET /health` checks backend connectivity.
- Space / Channel / Message APIs provide the base communication model.
- `GET /channels/{channel_id}/members` returns human/bot participants.
- `POST /channels/{channel_id}/agent/hermes` asks Hermes to respond in a channel.
- `POST /channels/{channel_id}/agent/local` asks the current-machine LocalAgent runner to respond in a channel.
- `POST /messages/{message_id}/attachments` uploads a file attachment.
- `GET /messages/{message_id}/attachments` lists attachments for a message.

## End-to-end smoke test

From the repo root:

```bash
./scripts/smoke.py
```

The script starts the backend on `127.0.0.1:8000`, uses an isolated smoke DB, verifies default spaces/channels, creates a channel, posts a message, creates a subchannel, checks channel members, invokes Hermes in stub mode, uploads an attachment, and verifies the response.

To verify real Hermes CLI communication as well:

```bash
./scripts/smoke_real_hermes.py
```

That script starts the backend on `127.0.0.1:8001` with `CLAWDESK_HERMES_MODE=cli` and expects Hermes to reply through the local CLI path.

Expected output starts with:

```text
SMOKE_OK
```

## macOS package build

```bash
./scripts/package_macos.py
```

Outputs:

```text
dist/ClawDesk.app
dist/ClawDesk-0.1.0-macOS.zip
```

The package is a local macOS app bundle with the SwiftUI release executable and bundled FastAPI backend. It is ad-hoc signed, not notarized. See `docs/deploy/macos-packaging.md`.

For the Office-client/Home-backend model, build the client-only package instead:

```bash
./scripts/package_macos_client.py
```

Outputs:

```text
dist/ClawDesk-Client.app
dist/ClawDesk-0.1.0-macOS-client.zip
```

Run the backend on the Hermes machine with:

```bash
CLAWDESK_HOST=0.0.0.0 CLAWDESK_PORT=8765 ./scripts/run_backend.sh
```

Then set the Office client Backend URL to the Hermes machine's Tailscale URL, for example `http://100.95.79.69:8765`. See `docs/deploy/remote-client-tailscale.md`.

## Current phase

Current phase:

- primary direction: self-hosted Mattermost over LAN/Tailscale for local message and file ownership;
- next integration: two Mattermost bots, `@Hermes` and `@LocalAgent`, plus an `Agents/local-work` channel;
- retained native prototype: FastAPI + SQLite + SwiftUI client, useful for Apple-native UX experiments and custom Hermes workflows.
