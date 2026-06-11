You are Codex working in /Users/janner/Projects/ClawDesk.

Implement Phase 1.2 from planning/phase-1.2-swiftui-hermes-invoke.md.

Hard constraints:
- Preserve local-first design.
- Do not touch files outside this repo.
- Do not commit.
- Keep stub mode as default.
- Do not enable automatic Hermes replies on every user message yet.
- Keep existing tests, smoke script, and SwiftUI build passing.

Implement:
1. Swift Codable models for AgentRun, HermesInvokeResponse, HermesInvokeRequest.
2. APIClient.invokeHermes(channelId:prompt:maxContextMessages:).
3. ChatView explicit Ask Hermes action that calls backend without a direct prompt, appends/refreshes the returned Hermes message, handles loading/error state.
4. scripts/smoke.py should verify the default stub Hermes endpoint.
5. README should document Hermes endpoint and env vars accurately.

Verification commands to run and report:
- cd server && uv run pytest -q
- cd apple/ClawDesk && swift build
- ./scripts/smoke.py from repo root

Return final summary with files changed and exact verification output. If blocked, explain precisely.