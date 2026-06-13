from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from app.agents.hermes_adapter import HermesAdapter, HermesAdapterError, HermesRequest
from app.agents.local_agent_adapter import LocalAgentAdapter, LocalAgentAdapterError, LocalAgentRequest
from app.db import get_conn
from app.schemas import HermesInvokeCreate, HermesInvokeOut, LocalAgentInvokeCreate, LocalAgentInvokeOut, agent_run_from_row
from app.utils import new_id, now_iso

router = APIRouter(prefix="/channels/{channel_id}/agent", tags=["agents"])


def _ensure_channel(conn, channel_id: str) -> None:
    row = conn.execute("SELECT id FROM channels WHERE id = ?", (channel_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Channel not found")


def _build_prompt(conn, channel_id: str, payload: HermesInvokeCreate) -> str:
    if payload.prompt and payload.prompt.strip():
        return payload.prompt.strip()
    rows = conn.execute(
        """
        SELECT sender_name, content
        FROM messages
        WHERE channel_id = ?
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (channel_id, payload.max_context_messages),
    ).fetchall()
    ordered = list(reversed(rows))
    if not ordered:
        return "请查看当前空频道，并简要说明可以如何开始。"
    return "\n".join(f"{row['sender_name']}: {row['content']}" for row in ordered)


@router.post("/hermes", response_model=HermesInvokeOut)
def invoke_hermes(channel_id: str, payload: HermesInvokeCreate) -> dict:
    started_at = now_iso()
    run_id = new_id()
    with get_conn() as conn:
        _ensure_channel(conn, channel_id)
        prompt = _build_prompt(conn, channel_id, payload)
        input_snapshot = json.dumps(
            {
                "prompt": prompt,
                "max_context_messages": payload.max_context_messages,
                "profile": payload.profile,
                "model": payload.model,
                "reasoning": payload.reasoning,
            },
            ensure_ascii=False,
        )
        conn.execute(
            """
            INSERT INTO agent_runs (
                id, channel_id, agent_config_id, agent, status, input_snapshot,
                output_text, model, reasoning, started_at, finished_at, error
            ) VALUES (?, ?, NULL, 'hermes', 'running', ?, NULL, ?, ?, ?, NULL, NULL)
            """,
            (run_id, channel_id, input_snapshot, payload.model, payload.reasoning, started_at),
        )

        try:
            response = HermesAdapter().invoke(
                HermesRequest(
                    prompt=prompt,
                    profile=payload.profile,
                    model=payload.model,
                    reasoning=payload.reasoning,
                )
            )
        except HermesAdapterError as exc:
            finished_at = now_iso()
            conn.execute(
                """
                UPDATE agent_runs
                SET status = 'failed', finished_at = ?, error = ?
                WHERE id = ?
                """,
                (finished_at, str(exc), run_id),
            )
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        finished_at = now_iso()
        message_id = new_id()
        conn.execute(
            """
            INSERT INTO messages (
                id, channel_id, sender_type, sender_name, content, content_type,
                reply_to_id, source_message_id, created_at, updated_at
            ) VALUES (?, ?, 'hermes', 'Hermes', ?, 'text', NULL, NULL, ?, ?)
            """,
            (message_id, channel_id, response.text, finished_at, finished_at),
        )
        conn.execute(
            """
            UPDATE agent_runs
            SET status = ?, output_text = ?, finished_at = ?, error = NULL
            WHERE id = ?
            """,
            ("succeeded" if response.status != "stubbed" else "stubbed", response.text, finished_at, run_id),
        )
        run = conn.execute("SELECT * FROM agent_runs WHERE id = ?", (run_id,)).fetchone()
        message = conn.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()
        return {"agent_run": agent_run_from_row(dict(run)).model_dump(), "message": dict(message)}


@router.post("/local", response_model=LocalAgentInvokeOut)
def invoke_local_agent(channel_id: str, payload: LocalAgentInvokeCreate) -> dict:
    started_at = now_iso()
    run_id = new_id()
    with get_conn() as conn:
        _ensure_channel(conn, channel_id)
        input_snapshot = json.dumps(
            {
                "prompt": payload.prompt,
                "agent": payload.agent,
                "workspace": payload.workspace,
                "timeout_seconds": payload.timeout_seconds,
            },
            ensure_ascii=False,
        )
        conn.execute(
            """
            INSERT INTO agent_runs (
                id, channel_id, agent_config_id, agent, status, input_snapshot,
                output_text, model, reasoning, started_at, finished_at, error
            ) VALUES (?, ?, NULL, 'local-agent', 'running', ?, NULL, ?, NULL, ?, NULL, NULL)
            """,
            (run_id, channel_id, input_snapshot, payload.agent, started_at),
        )

        try:
            response = LocalAgentAdapter().invoke(
                LocalAgentRequest(
                    prompt=payload.prompt,
                    agent=payload.agent,
                    workspace=payload.workspace,
                    timeout_seconds=payload.timeout_seconds,
                )
            )
        except LocalAgentAdapterError as exc:
            finished_at = now_iso()
            conn.execute(
                """
                UPDATE agent_runs
                SET status = 'failed', finished_at = ?, error = ?
                WHERE id = ?
                """,
                (finished_at, str(exc), run_id),
            )
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        finished_at = now_iso()
        message_id = new_id()
        conn.execute(
            """
            INSERT INTO messages (
                id, channel_id, sender_type, sender_name, content, content_type,
                reply_to_id, source_message_id, created_at, updated_at
            ) VALUES (?, ?, 'local-agent', 'LocalAgent', ?, 'text', NULL, NULL, ?, ?)
            """,
            (message_id, channel_id, response.text, finished_at, finished_at),
        )
        conn.execute(
            """
            UPDATE agent_runs
            SET status = ?, output_text = ?, finished_at = ?, error = NULL
            WHERE id = ?
            """,
            ("succeeded" if response.status != "stubbed" else "stubbed", response.text, finished_at, run_id),
        )
        run = conn.execute("SELECT * FROM agent_runs WHERE id = ?", (run_id,)).fetchone()
        message = conn.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()
        return {
            "agent_run": agent_run_from_row(dict(run)).model_dump(),
            "message": dict(message),
            "command": response.command,
            "workspace": response.workspace,
        }
