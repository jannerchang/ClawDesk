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

Hermes stays local-first and stubbed by default:

```bash
export CLAWDESK_HERMES_MODE=stub
```

Real Hermes CLI invocation is opt-in:

```bash
export CLAWDESK_HERMES_MODE=cli
export CLAWDESK_HERMES_TIMEOUT_SECONDS=60
```

CLI mode runs `hermes chat -q <prompt> --profile <profile>` on the local machine. Default tests and smoke checks use stub mode.

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

The script starts the backend on `127.0.0.1:8000`, uses an isolated smoke DB, verifies default spaces/channels, creates a channel, posts a message, creates a subchannel, checks channel members, invokes Hermes, uploads an attachment, and verifies the response.

Expected output starts with:

```text
SMOKE_OK
```

## Current phase

Phase 0/1 prototype:

- default Spaces and starter Channels;
- Janner human user and Hermes bot member model;
- Space / Channel / Message / Attachment APIs;
- create subchannel from selected messages;
- SwiftUI Space → Channel → Chat skeleton;
- SwiftUI selected-message flow wired to the backend subchannel API;
- explicit SwiftUI “Ask Hermes” action wired to `POST /channels/{channel_id}/agent/hermes`;
- Markdown rendering in message bubbles;
- backend URL setting and health check in the SwiftUI client;
- file attachment upload entry in the SwiftUI client;
- Hermes adapter endpoint, with stub mode by default and CLI mode available.
