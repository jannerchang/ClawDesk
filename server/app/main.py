from __future__ import annotations

import os

from fastapi import FastAPI

from app.api import agents, attachments, channels, messages, spaces
from app.db import init_db

app = FastAPI(title="ClawDesk Server", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, bool | str]:
    return {"ok": True, "hermes_mode": os.getenv("CLAWDESK_HERMES_MODE", "auto")}


app.include_router(spaces.router)
app.include_router(channels.router)
app.include_router(messages.router)
app.include_router(attachments.router)
app.include_router(agents.router)
