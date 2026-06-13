# Mattermost local deployment over LAN/Tailscale

This is ClawDesk's first practical self-hosted communication base: a local Mattermost Team Edition server with PostgreSQL and local file storage.

## Purpose

Use Mattermost as a LAN/Tailscale version of Discord or Telegram:

- messages stay in a self-hosted database;
- uploaded files stay on the local server filesystem;
- iOS, macOS, desktop, and web clients can connect;
- Hermes/OpenClaw can later join as bot participants through webhooks, bot tokens, or plugins;
- private files and discussions do not need to live on third-party chat platforms.

## Directory layout

Runtime data is stored under `deploy/mattermost/mattermost/`:

```text
deploy/mattermost/
  docker-compose.yml
  .env.example
  mattermost/          # generated runtime data, ignored by git
    postgres/          # PostgreSQL data
    data/              # uploaded files
    config/            # Mattermost config
    logs/              # logs
    plugins/           # server plugins
    client/plugins/    # webapp plugin assets
```

Do not commit `mattermost/` runtime data.

## Prerequisites

Install and start Docker Desktop, Colima, or another Docker Engine that supports Docker Compose v2.

Check:

```bash
docker --version
docker compose version
```

## First start

```bash
cd deploy/mattermost
cp .env.example .env
```

Edit `.env`:

```bash
MM_POSTGRES_PASSWORD=<replace-with-a-real-local-password>
```

For local-only testing, keep:

```bash
MM_HOST=127.0.0.1
MM_SITEURL=http://127.0.0.1:8065
```

Start:

```bash
docker compose up -d
```

Follow logs:

```bash
docker compose logs -f mattermost
```

Open:

```text
http://127.0.0.1:8065
```

Create the first admin account in the web setup flow.

## LAN/Tailscale access

After local verification, expose only to trusted networks by changing `.env`:

```bash
MM_HOST=0.0.0.0
MM_SITEURL=http://<home-machine-tailscale-ip-or-magicdns-name>:8065
```

Then restart:

```bash
docker compose up -d
```

Recommended access boundary:

- prefer Tailscale and LAN;
- do not expose Mattermost directly to the public Internet unless you have a real reverse proxy, TLS, update, backup, and hardening plan;
- for trusted users, invite accounts after confirming Tailscale or LAN reachability.

## Suggested initial channels

```text
Work
  - daily
  - discussion
  - documents
  - archive-candidates

Research
  - literature
  - notes
  - data

Personal
  - home
  - files
  - photos
  - todos

Agents
  - hermes
  - openclaw
  - logs
```

## Two-bot agent workspace plan

Mattermost should own communication primitives:

- users;
- channels;
- messages;
- file uploads;
- mobile/desktop clients.

Hermes/OpenClaw and the workstation-local runner should join as separate bot participants:

```text
Mattermost channel message
        ↓ outgoing webhook / bot websocket / plugin
Mention/channel routing
        ├── @Hermes      → home Hermes/OpenClaw bridge
        └── @LocalAgent  → current-machine ClawDesk local runner
        ↓
Bot reply back into the same Mattermost channel/thread
```

Minimum next bridge:

1. create two Mattermost bot accounts: `Hermes` and `LocalAgent`;
2. create an `Agents/local-work` channel for workstation-local jobs;
3. let `@Hermes` listen for mentions or a dedicated `Agents/hermes` channel;
4. let `@LocalAgent` listen only for explicit mentions or messages in `Agents/local-work`;
5. route `@Hermes` to the home Hermes/OpenClaw bridge;
6. route `@LocalAgent` to local Codex / Antigravity / Grok Build subprocesses;
7. post results back as the corresponding bot.

Architecture note: [`../architecture/two-bot-local-workspace.md`](../architecture/two-bot-local-workspace.md).

## Backup notes

Back up at least:

```text
deploy/mattermost/mattermost/postgres/
deploy/mattermost/mattermost/data/
deploy/mattermost/mattermost/config/
```

For consistent backups, stop the stack or use PostgreSQL dumps:

```bash
docker compose exec postgres pg_dump -U "$MM_POSTGRES_USER" "$MM_POSTGRES_DB" > mattermost-backup.sql
```

Also back up uploaded files under `mattermost/data/`.

## Stop / update

Stop:

```bash
docker compose down
```

Update images:

```bash
docker compose pull
docker compose up -d
```

Read logs after update:

```bash
docker compose logs --tail=200 mattermost
```
