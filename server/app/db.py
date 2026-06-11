from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.utils import new_id, now_iso

DEFAULT_USERS = [
    ("user_janner", "Janner", "human", "J", None),
    ("bot_hermes", "Hermes", "bot", "H", "Hermes / OpenClaw"),
]

DEFAULT_SPACES = [
    ("Inbox / 随手聊", "inbox", "tray", 10),
    ("技佐", "tech", "wrench", 20),
    ("合议庭", "case", "scale", 30),
    ("课题研究室", "research", "books", 40),
    ("个人知识库", "knowledge", "archivebox", 50),
    ("归档", "archive", "archive", 60),
]

DEFAULT_CHANNELS_BY_SPACE_TYPE = {
    "inbox": [
        ("随手聊", "temporary", "chat", "无目的入口：随手发一句、语音转文字、稍后整理。", ["inbox"]),
    ],
    "tech": [
        ("技术聊天", "tech", "mixed", "技佐入口：技术闲聊、排障、工具开发，可从聊天生成子频道。", ["技佐", "技术"]),
        ("Hermes / OpenClaw", "tech", "mixed", "Hermes、OpenClaw、Gateway、模型与 agent 工作流。", ["Hermes", "OpenClaw"]),
    ],
    "case": [
        ("案件入口", "case", "mixed", "合议庭案件讨论入口。", ["案件"]),
        ("已沉淀", "case", "forum", "已沉淀案件、规则卡与案例候选。", ["已沉淀"]),
    ],
    "research": [
        ("研究聊天", "research", "mixed", "课题研究的自由讨论与问题生长区。", ["研究"]),
        ("文献与案例", "research", "forum", "文献、案例、理论问题与章节素材。", ["文献", "案例"]),
    ],
    "knowledge": [
        ("碎片整理", "normal", "mixed", "个人知识库入口：碎片、待整理想法与长期知识。", ["知识库"]),
    ],
    "archive": [
        ("归档索引", "normal", "forum", "低频查阅与已完成内容索引。", ["归档"]),
    ],
}


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
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                kind TEXT NOT NULL DEFAULT 'human',
                avatar TEXT,
                description TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

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

            CREATE TABLE IF NOT EXISTS channel_members (
                channel_id TEXT NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                role TEXT NOT NULL DEFAULT 'member',
                created_at TEXT NOT NULL,
                PRIMARY KEY (channel_id, user_id)
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

            CREATE TABLE IF NOT EXISTS attachments (
                id TEXT PRIMARY KEY,
                message_id TEXT NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
                kind TEXT NOT NULL,
                original_name TEXT NOT NULL,
                local_path TEXT NOT NULL,
                mime_type TEXT,
                size INTEGER NOT NULL,
                created_at TEXT NOT NULL
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
        seed_default_users(conn)
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
        seed_default_channels(conn)
        seed_default_channel_members(conn)


def seed_default_users(conn: sqlite3.Connection) -> None:
    ts = now_iso()
    for user_id, name, kind, avatar, description in DEFAULT_USERS:
        conn.execute(
            """
            INSERT OR IGNORE INTO users (id, name, kind, avatar, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, name, kind, avatar, description, ts, ts),
        )


def seed_default_channel_members(conn: sqlite3.Connection) -> None:
    ts = now_iso()
    channels = conn.execute("SELECT id FROM channels").fetchall()
    for channel in channels:
        for user_id, role in (("user_janner", "owner"), ("bot_hermes", "bot")):
            conn.execute(
                """
                INSERT OR IGNORE INTO channel_members (channel_id, user_id, role, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (channel["id"], user_id, role, ts),
            )


def seed_default_channels(conn: sqlite3.Connection) -> None:
    ts = now_iso()
    spaces = conn.execute("SELECT id, type FROM spaces").fetchall()
    for space in spaces:
        for name, channel_type, mode, description, tags in DEFAULT_CHANNELS_BY_SPACE_TYPE.get(space["type"], []):
            existing = conn.execute(
                "SELECT id FROM channels WHERE space_id = ? AND parent_channel_id IS NULL AND name = ?",
                (space["id"], name),
            ).fetchone()
            if existing:
                continue
            conn.execute(
                """
                INSERT INTO channels (
                    id, space_id, parent_channel_id, name, type, mode, status, description,
                    tags, agent_config_id, source_message_ids, created_at, updated_at
                ) VALUES (?, ?, NULL, ?, ?, ?, 'active', ?, ?, NULL, '[]', ?, ?)
                """,
                (new_id(), space["id"], name, channel_type, mode, description, dumps_json(tags), ts, ts),
            )


def dumps_json(value: object) -> str:
    return json.dumps(value if value is not None else [], ensure_ascii=False)


def loads_json(text: str | None) -> object:
    if not text:
        return []
    return json.loads(text)
