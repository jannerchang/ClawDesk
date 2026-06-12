# ClawDesk

ClawDesk 是一个 Apple 原生、Telegram-like 的私人 Agent 通道客户端，用于让 Janner 通过自有界面与 Hermes / OpenClaw 等本地或远程 agent 系统交互。项目第一阶段聚焦基础通信：空间/频道、用户与 bot 成员、消息、Markdown、附件、后端连接设置与健康检查；后续逐步接入语音、图片、文件、本地 agent 控制和主题沉淀能力。核心定位不是自研 agent harness，而是作为 Discord / Telegram 之外更可控、更贴合个人工作流的私有通道。

## Repository layout

```text
server/       FastAPI + SQLite backend prototype
apple/        SwiftUI client package skeleton
planning/     FFCS planning artifacts
scripts/      Smoke-test helpers
```

## Backend quick start

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

## SwiftUI client build/run

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

Phase 0/1 prototype:

- default Spaces and starter Channels;
- Janner human user and Hermes bot member model;
- Space / Channel / Message / Attachment APIs;
- create subchannel from selected messages;
- SwiftUI Space → Channel → Chat usable client shell with backend status, channel creation, member bar, message sending, Hermes bot replies, and attachment cards;
- SwiftUI selected-message flow wired to the backend subchannel API;
- Markdown rendering in message bubbles;
- backend URL setting and health check in the SwiftUI client;
- file attachment upload entry in the SwiftUI client;
- Hermes adapter endpoint, with auto/cli/stub modes and real Hermes smoke coverage.
