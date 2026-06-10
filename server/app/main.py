from __future__ import annotations

from fastapi import FastAPI

from app.api import agents, channels, messages, spaces
from app.db import init_db

app = FastAPI(title="ClawDesk Server", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


app.include_router(spaces.router)
app.include_router(channels.router)
app.include_router(messages.router)
app.include_router(agents.router)
