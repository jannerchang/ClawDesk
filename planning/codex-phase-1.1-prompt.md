You are Codex working in /Users/janner/Projects/ClawDesk.

Implement Phase 1.1 from planning/phase-1.1-hermes-adapter.md.

Hard constraints:
- Preserve local-first design. Do not add network services except local Hermes CLI subprocess support.
- Do not touch files outside this repo.
- Do not commit.
- Keep stub mode as default.
- Use subprocess without shell=True for CLI mode.
- Keep existing tests, smoke script, and SwiftUI build passing.

Implement:
1. Backend endpoint POST /channels/{channel_id}/agent/hermes.
2. Request schema with optional prompt and max_context_messages default 20.
3. Response schema that includes agent_run and message.
4. Hermes adapter modes:
   - CLAWDESK_HERMES_MODE=stub by default.
   - CLAWDESK_HERMES_MODE=cli invokes: hermes chat -q <prompt> --profile default
   - CLAWDESK_HERMES_TIMEOUT_SECONDS default 60.
5. Persist agent_runs with status succeeded/failed and relevant fields.
6. On success insert channel message sender_type=hermes sender_name=Hermes content=<output>.
7. In stub mode return deterministic output starting with [Hermes stub].
8. Add pytest coverage for stub endpoint and agent_runs persistence.
9. Update README with endpoint and env vars.

Verification commands to run and report:
- cd server && uv run pytest -q
- cd apple/ClawDesk && swift build
- ./scripts/smoke.py from repo root

Return final summary with files changed and exact verification output. If blocked, explain precisely.