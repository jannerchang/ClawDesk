# Open-source reuse map

_Last updated: 2026-06-13_

This note records the first-pass reuse scan for ClawDesk's open-source/self-hosted agent workbench direction. The research copies live outside this repository under:

```text
/Users/janner/Projects/ClawDesk-research/
  wesight/
  local-agent-gateway/
  pan-ui/
```

## Executive decision

Prefer **reuse and adaptation** over rebuilding a complete chat/workbench stack from scratch.

Recommended priority:

1. **WeSight** as the primary desktop/local-agent workspace reference.
2. **Local Agent Gateway** as the provider/session/channel-gateway reference.
3. **Pan UI** as the Hermes-specific gateway/runtime/profile management reference.

ClawDesk should keep its differentiating layer narrow:

```text
local-first agent communication node
  = trusted-device sync + channel/message/context model + per-node local agent adapters
```

Do not spend early engineering time reimplementing generic Electron workspace UI, Codex app-server plumbing, Hermes gateway lifecycle management, or chat-platform bridge mechanics when MIT projects already demonstrate them.

## Repositories scanned

| Project | Local path | Upstream | Snapshot | License | Role |
|---|---|---|---|---|---|
| WeSight | `../ClawDesk-research/wesight` | `https://github.com/freestylefly/wesight.git` | `e0ad048` | MIT | Primary desktop/local-agent workspace reference |
| Local Agent Gateway | `../ClawDesk-research/local-agent-gateway` | `https://github.com/yanfulei/local-agent-gateway.git` | `62cf4c3` | MIT | Local provider/session gateway reference |
| Pan UI | `../ClawDesk-research/pan-ui` | `https://github.com/Euraika-Labs/pan-ui.git` | `0cf6916` | MIT | Hermes runtime/web dashboard reference |

## 1. WeSight

### What it is

WeSight describes itself as an open-source desktop control console for local AI agents. It supports or references Claude Code, Codex, OpenClaw, Hermes Agent, OpenCode, Grok Build, Qwen Code, DeepSeek-TUI, provider routing, IM channels, skills, scheduled tasks, runtime metrics, and desktop packaging.

Relevant evidence from the scan:

- `package.json` scripts include Electron/Vite development, packaging, OpenClaw runtime bundling, Python runtime setup, and platform builds.
- `src/shared/cowork/constants.ts` defines engines including:
  - `openclaw`
  - `hermes`
  - `claude_code`
  - `codex`
  - `codex_app`
  - `opencode`
  - `grok_build`
  - `qwen_code`
  - `deepseek_tui`
- `src/main/libs/agentEngine/coworkEngineRouter.ts` normalizes all engines behind one `CoworkRuntime` interface.
- `src/main/libs/agentEngine/types.ts` defines the runtime surface: `startSession`, `continueSession`, `stopSession`, permission responses, active-session checks, streaming events, and runtime metrics.
- `src/main/libs/agentEngine/externalCliRuntimeAdapter.ts` is a large reusable reference for wrapping CLI agents with local history trimming, output truncation, permissions, environment setup, and streaming normalization.
- `src/main/libs/agentEngine/codexAppRuntimeAdapter.ts` implements Codex app-server JSON-RPC session/turn handling and approval mapping.
- `src/main/libs/agentEngine/hermesRuntimeAdapter.ts` streams Hermes through managed gateway connection info into the same cowork event model.
- `src/main/im/imGatewayManager.ts` centralizes IM platform integration and can route Feishu through OpenClaw/Hermes/ClaudeCode/Codex depending on engine configuration.

### What ClawDesk should reuse or copy conceptually

High-value patterns:

1. **Engine router abstraction**
   - A common runtime interface for all local agents.
   - Session-to-engine mapping so an active turn keeps using the selected engine.
   - Uniform streaming events: message, message update, permission request, metrics, complete, error.

2. **CLI runtime normalization**
   - Resolve CLI command path and environment before execution.
   - Maintain bounded local history instead of pushing unlimited messages.
   - Truncate stdout/stderr and visible output to avoid memory pressure.
   - Detect startup/no-content timeouts separately from normal failures.
   - Preserve tool output/diffs/permission requests as structured events when possible.

3. **Codex app-server integration**
   - Use JSON-RPC app-server mode when available instead of only shelling out one-shot commands.
   - Map thread/turn lifecycle, token usage, command/file-change approvals, and deltas into ClawDesk's event stream.

4. **Runtime telemetry**
   - Track engine, status, token usage, TTFT/TPS, steps, duration, and tool latency at the turn level.
   - This fits ClawDesk's planned module/status post sync.

5. **Desktop packaging and local runtime bundling**
   - WeSight already has Electron packaging, macOS builds, OpenClaw runtime bundling, and release scripts.
   - If ClawDesk moves away from native SwiftUI for a faster MVP, WeSight is the best candidate to fork or mine.

### What not to copy blindly

- Full product surface: WeSight is already a broad desktop agent console, while ClawDesk's differentiator is trusted-device communication/sync.
- Any auth/cloud/portal assumptions not needed for a single-user LAN/Tailscale node.
- Full IM matrix unless ClawDesk decides to support the same platforms.

### Reuse recommendation

**Primary reference, possible fork candidate.**

Do not fork immediately. First isolate the reusable pieces:

```text
engine registry / runtime interface
external CLI adapter patterns
Codex app-server adapter
Hermes adapter
runtime telemetry schema
IM gateway manager patterns
```

If ClawDesk's SwiftUI client becomes slower than adapting WeSight's Electron app, then consider a fork decision separately.

## 2. Local Agent Gateway

### What it is

Local Agent Gateway is a smaller MIT project focused on exposing desktop coding-agent sessions to chat platforms. The current MVP supports macOS, Codex CLI app-server/remote-control, a local Web UI, provider management, and Feishu/Lark long-connection bots.

Relevant evidence from the scan:

- `package.json` stack: Fastify + Vite + React + TypeScript.
- `src/shared/types.ts` defines:
  - `ProviderType = "codex" | "claude-code" | "openclaw" | "hermes"`
  - `ProviderConfig`
  - `EnvironmentConfig`
  - `ChannelBotConfig`
  - `AgentSessionSummary`
  - `AgentSessionMessage`
  - `GatewayTask`
  - approval/task status types.
- `src/server/providers/types.ts` defines an `AgentProvider` interface with session list/create/history, task execution, cancel, approval, and attachment content methods.
- `src/server/providers/providerRegistry.ts` resolves provider/environment/session relationships and deduplicates sessions.
- `src/server/codex/appServerClient.ts` starts `codex app-server --listen stdio://`, initializes JSON-RPC, sends requests/notifications, handles stdout lines and pending request timeouts.
- `src/server/codex/codexProvider.ts` uses the app-server client and a session scanner, manages session overlays, creates provider threads, reads historical messages, and maps approvals.
- `src/server/feishu/feishuBotManager.ts` handles Feishu bot lifecycle, task cards, card patching, callbacks, processing reactions, retries, and channel restrictions.
- `src/server/feishu/larkChannelAdapter.ts` abstracts the Feishu manager behind a `ChannelAdapter`.
- `src/server/api.ts` exposes state/config/provider/environment/bot/session/task APIs.

### What ClawDesk should reuse or copy conceptually

High-value patterns:

1. **Provider registry**
   - This maps almost directly to ClawDesk's planned `AgentAdapter registry`.
   - Keep provider, environment, session key, native session id, and provider type separate.

2. **Environment model**
   - An environment is a named local workspace/root bound to a provider.
   - This is better than passing arbitrary workspace paths per message.
   - It supports Janner's safety boundary: each node can expose only configured roots.

3. **Session overlays**
   - The gateway can create/rename/bind sessions even when the underlying provider has its own native thread/session id.
   - This is useful for mapping ClawDesk channels to local agent sessions without losing provider-native history.

4. **GatewayTask lifecycle**
   - `queued/running/waiting_approval/completed/failed/cancelled` is a good minimal run state model.
   - Approval requests should be first-class records, not hidden in log text.

5. **Channel adapter boundary**
   - A chat platform bridge should update task messages/cards through a channel adapter, not through provider logic.
   - ClawDesk can apply the same boundary to Mattermost, Discord, Matrix, or native ClawDesk channels.

### What not to copy blindly

- It is Feishu-first at the channel layer. For ClawDesk's current self-hosted direction, Mattermost/Matrix/native channel adapters matter more.
- It is smaller and less feature-complete than WeSight for desktop UI and multi-engine handling.

### Reuse recommendation

**Use as the clearest backend/gateway pattern.**

It is probably easier to adapt its `ProviderRegistry`, `AgentProvider`, `EnvironmentConfig`, `GatewayTask`, and Codex app-server client patterns into ClawDesk than to lift WeSight's larger implementation wholesale.

## 3. Pan UI

### What it is

Pan UI is a self-hosted WebUI for Hermes Agent. It runs as a Next.js server and bridges the browser to Hermes through the Hermes gateway and direct filesystem reads under `~/.hermes`.

Relevant evidence from the scan:

- README says Pan chat streams through Hermes's OpenAI-compatible SSE endpoint and auto-launches Hermes gateway if it is not already running.
- `docs/architecture.md` describes two channels:
  - Hermes Gateway at `:8642` for chat streaming/runtime operations.
  - Hermes filesystem for skills, memory, profiles, sessions.
- `src/server/hermes/gateway-manager.ts` checks `/health`, finds `hermes`, spawns `hermes gateway run`, waits for readiness, monitors child process health, and shuts down gracefully.
- `src/server/hermes/runtime-bridge.ts` detects Hermes binary/home/profile, probes `/v1/models`, reads `state.db`, profiles, skills, memory, config, and produces a runtime status object.
- `src/server/hermes/*` includes focused bridge modules for sessions, skills, memory, profiles, plugins, MCP, stream parsing, approvals, and runtime maintenance.

### What ClawDesk should reuse or copy conceptually

High-value patterns:

1. **Hermes gateway lifecycle**
   - Check whether a gateway is already running before spawning one.
   - If ClawDesk spawns it, ClawDesk owns restart/shutdown.
   - If an external service already owns it, leave it alone.

2. **Runtime health/status view**
   - Detect binary, version, home path, active profile, config, API reachability, skills count, sessions count, recent sessions, memory files.
   - This fits ClawDesk's planned node/agent presence panel.

3. **Server-side Hermes bridge**
   - Browser/client should not directly read `~/.hermes` or call arbitrary runtime operations.
   - Keep a server-side bridge that gates auth, CORS, filesystem scope, and input validation.

4. **Profile-aware Hermes handling**
   - Avoid hardcoded Hermes profile names or home paths.
   - ClawDesk should model Hermes profile as part of adapter/session config.

### What not to copy blindly

- Pan is Hermes-specific. It should not become the whole ClawDesk architecture.
- Direct filesystem reads are useful on the Home/Hermes node, but remote devices should get filtered status/context through ClawDesk sync APIs.

### Reuse recommendation

**Use for Hermes-specific control plane and health handling.**

Pan's gateway manager and runtime status model should shape ClawDesk's `@Hermes` adapter. Its full UI can be embedded/linked later if ClawDesk wants a Hermes admin tab.

## Derived ClawDesk architecture direction

The open-source projects point to this architecture:

```text
ClawDesk Node
  ├── Channel / Message / Event / Context Snapshot store
  ├── Sync stream over LAN/Tailscale
  ├── AgentAdapter registry
  │     ├── HermesAdapter       ← Pan UI patterns
  │     ├── CodexAppAdapter     ← WeSight + Local Agent Gateway patterns
  │     ├── ExternalCliAdapter  ← WeSight patterns
  │     ├── OpenClawAdapter     ← WeSight patterns
  │     └── ShellAdapter        ← keep minimal and permission-gated
  ├── Environment / Workspace roots
  ├── Task / Approval / Telemetry records
  └── ChannelAdapters
        ├── Native ClawDesk
        ├── Mattermost
        ├── Matrix bridge / appservice later
        └── Discord/Feishu/etc. optional
```

Core data concepts to add next:

```text
nodes
agent_adapters
environments
agent_sessions
agent_tasks
approval_requests
runtime_events
sync_cursors
context_snapshots
```

Keep existing ClawDesk concepts:

```text
spaces
channels
messages
channel_bot_bindings
module_post_bindings
```

But refactor the current `LocalAgent` endpoint toward provider/session/task records rather than one-shot command execution.

## Concrete next implementation batch

Suggested next batch for ClawDesk:

1. Add an architecture doc for `Node + AgentAdapter registry + Environment + Task`.
2. Add database/API skeletons:
   - `nodes`
   - `agent_adapters`
   - `environments`
   - `agent_sessions`
   - `agent_tasks`
3. Keep current `/channels/{channel_id}/agent/local` as compatibility, but internally produce an `agent_task`.
4. Add adapter status detection:
   - command exists
   - version if available
   - mode: `unavailable | available | running | error`
   - capabilities: `session.create`, `message.send`, `approval`, `stream`, `files`, etc.
5. Add a future-facing Codex app-server spike using the Local Agent Gateway / WeSight JSON-RPC patterns.

## Fork/import policy

Because all three scanned repositories are MIT licensed, direct source reuse is legally possible if license notices are preserved. Still keep the engineering boundary clean:

- Do not vendor whole repos into ClawDesk yet.
- Do not mix copied code without attribution headers or a `NOTICE` entry.
- Prefer reimplementing narrow interfaces first, then copy small proven modules only when needed.
- If directly copying files, record upstream repo, commit, source path, and local modifications.

## Current verdict

- **WeSight:** strongest candidate for desktop workspace/fork reference.
- **Local Agent Gateway:** strongest candidate for backend gateway/provider/session model.
- **Pan UI:** strongest candidate for Hermes gateway/runtime/profile management.

ClawDesk's unique work should be the **local-first node sync and channel/context layer**, not another full coding-agent UI or another Hermes dashboard.
