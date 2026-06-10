# ClawDesk

ClawDesk is Janner's private, local-first Apple-platform agent workspace.

## Project Shape

- `server/`: FastAPI and SQLite backend prototype.
- `apple/`: SwiftUI client package skeleton for Apple platforms.
- `docs/`: project notes, worker prompts, and architecture/development/deploy docs.
- `planning/`: FFCS planning artifacts.
- `scripts/`: smoke-test helpers.

## FFCS

Use `.claude/ffcs.local.md` for local FFCS settings. Runtime state belongs in `.ff-state/` and should not be committed.

After init, start with `/ffcs:need ClawDesk` unless a specific milestone already exists.
