# Two-bot Mattermost workspace: Hermes + Local Agent

ClawDesk's practical collaboration model is a self-hosted Mattermost workspace with two visible agent participants:

```text
Home-hosted Mattermost
  ├── @Hermes        remote/home agent for long-running assistant work
  └── @LocalAgent    current-machine runner for local coding tools
```

This avoids requiring Hermes on every workstation. A work machine can run ClawDesk plus local coding agents directly, while the home machine keeps the long-lived Hermes/OpenClaw hub.

## Roles

| Bot | Runs where | Main job | Typical tools |
|---|---|---|---|
| `@Hermes` | Home server / Mac mini | Long-term assistant, memory, archive, scheduled/background work, home-side services | Hermes, OpenClaw, Obsidian/local knowledge store |
| `@LocalAgent` | Current workstation | Local project execution and coding-agent orchestration | Codex CLI, Antigravity CLI, Grok Build, local shell/build/test tools |

## Suggested channels

```text
Agents
  - hermes          # direct long-running assistant work
  - local-work      # current workstation tasks handled by @LocalAgent
  - handoff         # summaries/results that need to move between local and home contexts
  - logs            # bot status and job logs
```

The important channel is `local-work`: it is where the workstation-side ClawDesk runner listens for local tasks and returns results.

## Message routing

```text
User message in Mattermost
        ↓
Mention or channel rule
        ↓
@Hermes      → Home Hermes/OpenClaw
@LocalAgent  → workstation ClawDesk runner
        ↓
Bot posts result back to the same channel/thread
```

Examples:

```text
@Hermes summarize this thread and archive the decision.
@LocalAgent run the Swift build in the current ClawDesk checkout.
@LocalAgent ask codex to review the staged diff.
@LocalAgent use antigravity to draft the SwiftUI sidebar change.
@LocalAgent ask grok to scaffold the FastAPI endpoint, then show the diff.
```

## Local Agent runner boundary

`@LocalAgent` should not be a second Hermes installation. It is a thin local runner controlled by ClawDesk:

```text
ClawDesk local runner
  ├── selects a workspace/project directory
  ├── starts codex / agy / grok as subprocesses
  ├── captures stdout/stderr and artifacts
  ├── optionally runs verification commands
  └── posts result summaries back to Mattermost
```

Local files stay on the workstation unless the user explicitly uploads, summarizes, or hands off specific material.

## First milestone

1. Create two bot accounts in Mattermost: `Hermes` and `LocalAgent`.
2. Create an `Agents/local-work` channel.
3. Let `@Hermes` be backed by the home Hermes/OpenClaw bridge.
4. Let `@LocalAgent` be backed by a lightweight ClawDesk local runner on the current workstation.
5. Support only explicit mentions at first; no automatic channel-wide ingestion until the behavior is safe.

## Safety defaults

- Run local commands from an explicit workspace directory, not arbitrary filesystem roots.
- Show the selected workspace in every local job result.
- Require confirmation before destructive commands or broad file operations.
- Prefer summaries and diffs over uploading whole local directories.
- Keep bot tokens in local environment/config files, not in the repository.
