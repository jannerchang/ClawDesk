You are Grok Build acting as a coding worker for Janner's local project ClawDesk.

Workdir: /Users/janner/Projects/ClawDesk

Task: Implement backend Phase 0 foundations under server/.

Product context:
ClawDesk is a private Apple-platform, local-first agent workspace. It uses Telegram-like lightweight chat, persistent channels/subchannels, local SQLite storage, and later Hermes/OpenClaw integration. Sensitive files must stay local; no VPS/data exfiltration.

Implement ONLY the backend skeleton and CRUD APIs. Do not implement a real Hermes call yet; create a clean adapter stub and optional endpoint/service hook but keep it disabled unless explicitly called.

Requirements:
1. Use Python FastAPI under server/.
2. Use uv-compatible pyproject.toml.
3. Use SQLite via Python stdlib sqlite3, not SQLAlchemy for now.
4. DB path default: server/.data/clawdesk-dev.db, override with CLAWDESK_DB_PATH env var.
5. Create app package:
   - app/main.py
   - app/db.py
   - app/models.py or schemas.py
   - app/api/spaces.py
   - app/api/channels.py
   - app/api/messages.py
   - app/agents/hermes_adapter.py
   - tests if straightforward.
6. Endpoints:
   - GET /health -> {"ok": true}
   - GET /spaces
   - POST /spaces {name,type?,icon?,sort_order?}
   - GET /spaces/{space_id}/channels
   - POST /channels {space_id,parent_channel_id?,name,type?,mode?,status?,description?,tags?}
   - GET /channels/{channel_id}
   - GET /channels/{channel_id}/messages
   - POST /channels/{channel_id}/messages {sender_type?,sender_name?,content,content_type?,reply_to_id?,source_message_id?}
7. Minimal schema:
   spaces(id TEXT primary key, name, type, icon, sort_order, created_at, updated_at)
   channels(id TEXT primary key, space_id, parent_channel_id, name, type, mode, status, description, tags JSON text, agent_config_id nullable, source_message_ids JSON text, created_at, updated_at)
   messages(id TEXT primary key, channel_id, sender_type, sender_name, content, content_type, reply_to_id, source_message_id, created_at, updated_at)
   agent_configs minimal placeholder table
   agent_runs minimal placeholder table
8. On app startup initialize tables and seed default spaces if none exist:
   Inbox / 随手聊, 技佐, 合议庭, 课题研究室, 个人知识库, 归档.
9. Keep code simple and testable. No auth yet. No network calls except local app serving.
10. Add README.md under server/ with setup and curl smoke test commands.

Verification you must run before finishing:
- uv run python -m compileall app
- uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 in background or use FastAPI TestClient/pytest
- Verify /health and at least create/list space, create/list channel, create/list message.

Return a concise summary with files changed and exact commands/results. Do not claim success unless you actually ran verification.
