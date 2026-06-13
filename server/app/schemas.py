from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SpaceCreate(BaseModel):
    name: str
    type: str = "normal"
    icon: str | None = None
    sort_order: int = 0


class SpaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    type: str
    icon: str | None = None
    sort_order: int
    created_at: str
    updated_at: str


class ChannelCreate(BaseModel):
    space_id: str
    parent_channel_id: str | None = None
    name: str
    type: str = "normal"
    mode: Literal["chat", "forum", "mixed"] = "mixed"
    status: str = "active"
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    source_message_ids: list[str] = Field(default_factory=list)


class ChannelOut(BaseModel):
    id: str
    space_id: str
    parent_channel_id: str | None = None
    name: str
    type: str
    mode: str
    status: str
    description: str | None = None
    tags: list[str]
    agent_config_id: str | None = None
    source_message_ids: list[str]
    created_at: str
    updated_at: str


class UserOut(BaseModel):
    id: str
    name: str
    kind: str
    avatar: str | None = None
    description: str | None = None
    role: str | None = None
    created_at: str
    updated_at: str


class ChannelBotBindingCreate(BaseModel):
    user_id: str
    bot_kind: Literal["hermes", "local-agent"]
    session_key: str | None = None
    listen_mode: Literal["mention", "channel", "manual"] = "mention"
    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)


class ChannelBotBindingUpdate(BaseModel):
    session_key: str | None = None
    listen_mode: Literal["mention", "channel", "manual"] | None = None
    enabled: bool | None = None
    config: dict[str, Any] | None = None


class ChannelBotBindingOut(BaseModel):
    id: str
    channel_id: str
    user_id: str
    user_name: str | None = None
    bot_kind: str
    session_key: str
    listen_mode: str
    enabled: bool
    config: dict[str, Any]
    created_at: str
    updated_at: str


class MessageCreate(BaseModel):
    sender_type: str = "user"
    sender_name: str = "Janner"
    content: str
    content_type: str = "text"
    reply_to_id: str | None = None
    source_message_id: str | None = None


class MessageOut(BaseModel):
    id: str
    channel_id: str
    sender_type: str
    sender_name: str
    content: str
    content_type: str
    reply_to_id: str | None = None
    source_message_id: str | None = None
    created_at: str
    updated_at: str


class AttachmentOut(BaseModel):
    id: str
    message_id: str
    kind: str
    original_name: str
    local_path: str
    mime_type: str | None = None
    size: int
    created_at: str


class SubchannelFromMessagesCreate(BaseModel):
    name: str
    type: str = "normal"
    mode: Literal["chat", "forum", "mixed"] = "mixed"
    status: str = "active"
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    source_message_ids: list[str]


class AgentRunOut(BaseModel):
    id: str
    channel_id: str | None = None
    agent_config_id: str | None = None
    agent: str
    status: str
    input_snapshot: str | None = None
    output_text: str | None = None
    model: str | None = None
    reasoning: str | None = None
    started_at: str
    finished_at: str | None = None
    error: str | None = None


class HermesInvokeCreate(BaseModel):
    prompt: str | None = None
    max_context_messages: int = Field(default=20, ge=1, le=100)
    profile: str = "default"
    model: str | None = None
    reasoning: str | None = None


class HermesInvokeOut(BaseModel):
    agent_run: AgentRunOut
    message: MessageOut


class LocalAgentInvokeCreate(BaseModel):
    prompt: str
    agent: Literal["codex", "antigravity", "agy", "grok", "grok-build", "shell"] = "shell"
    workspace: str | None = None
    timeout_seconds: int = Field(default=120, ge=1, le=600)


class LocalAgentInvokeOut(BaseModel):
    agent_run: AgentRunOut
    message: MessageOut
    command: list[str]
    workspace: str


def agent_run_from_row(row: dict[str, Any]) -> AgentRunOut:
    return AgentRunOut(**dict(row))

def channel_from_row(row: dict[str, Any]) -> ChannelOut:
    from app.db import loads_json

    data = dict(row)
    data["tags"] = loads_json(data.get("tags"))
    data["source_message_ids"] = loads_json(data.get("source_message_ids"))
    return ChannelOut(**data)


def bot_binding_from_row(row: dict[str, Any]) -> ChannelBotBindingOut:
    from app.db import loads_json

    data = dict(row)
    data["enabled"] = bool(data.get("enabled"))
    data["config"] = loads_json(data.get("config"))
    return ChannelBotBindingOut(**data)
