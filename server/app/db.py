from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.utils import new_id, now_iso

DEFAULT_SPACES = [
    ("Inbox / 随手聊", "inbox", "tray", 10),
    ("技佐", "tech", "wrench", 20),
    ("合议庭", "case", "scale", 30),
    ("课题研究室", "research", "books", 40),
    ("个人知识库", "knowledge", "archivebox", 50),
    ("归档", "archive", "archive", 60),
]


def db_path() -> Path:
    raw = os.getenv("CLAWDESK_DB_PATH")
    if raw:
        return Path(raw).expanduser()
    return Path(__file__).resolve().parents[1] / ".data" / "clawdesk-dev.db"


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS spaces (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'normal',
                icon TEXT,
                sort_order INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS channels (
                id TEXT PRIMARY KEY,
                space_id TEXT NOT NULL REFERENCES spaces(id) ON DELETE CASCADE,
                parent_channel_id TEXT REFERENCES channels(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'normal',
                mode TEXT NOT NULL DEFAULT 'mixed',
                status TEXT NOT NULL DEFAULT 'active',
                description TEXT,
                tags TEXT NOT NULL DEFAULT '[]',
                agent_config_id TEXT,
                source_message_ids TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                channel_id TEXT NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
                sender_type TEXT NOT NULL DEFAULT 'user',
                sender_name TEXT NOT NULL DEFAULT 'Janner',
                content TEXT NOT NULL,
                content_type TEXT NOT NULL DEFAULT 'text',
                reply_to_id TEXT REFERENCES messages(id) ON DELETE SET NULL,
                source_message_id TEXT REFERENCES messages(id) ON DELETE SET NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS agent_configs (
                id TEXT PRIMARY KEY,
                scope_type TEXT NOT NULL,
                scope_id TEXT,
                agent TEXT NOT NULL DEFAULT 'hermes',
                profile TEXT NOT NULL DEFAULT 'default',
                provider TEXT,
                model TEXT,
                reasoning TEXT,
                toolsets TEXT NOT NULL DEFAULT '[]',
                max_context_messages INTEGER NOT NULL DEFAULT 40,
                attachment_policy TEXT NOT NULL DEFAULT 'ask',
                sensitive_mode INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS agent_runs (
                id TEXT PRIMARY KEY,
                channel_id TEXT REFERENCES channels(id) ON DELETE SET NULL,
                agent_config_id TEXT REFERENCES agent_configs(id) ON DELETE SET NULL,
                agent TEXT NOT NULL DEFAULT 'hermes',
                status TEXT NOT NULL DEFAULT 'pending',
                input_snapshot TEXT,
                output_text TEXT,
                model TEXT,
                reasoning TEXT,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                error TEXT
            );
            """
        )
        count = conn.execute("SELECT COUNT(*) AS c FROM spaces").fetchone()["c"]
        if count == 0:
            ts = now_iso()
            conn.executemany(
                """
                INSERT INTO spaces (id, name, type, icon, sort_order, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [(new_id(), name, typ, icon, order, ts, ts) for name, typ, icon, order in DEFAULT_SPACES],
            )


def dumps_json(value: object) -> str:
    return json.dumps(value if value is not None else [], ensure_ascii=False)


def loads_json(text: str | None) -> object:
    if not text:
        return []
    return json.loads(text)
