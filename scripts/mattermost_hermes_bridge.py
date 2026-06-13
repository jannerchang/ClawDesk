#!/usr/bin/env python3
"""Poll a Mattermost channel and route explicit messages to ClawDesk Hermes.

This is the home-side twin of mattermost_local_agent_bridge.py. It keeps
Mattermost as the shared communication surface while ClawDesk/Hermes handle
assistant replies through the existing /agent/hermes endpoint.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


def strip_bot_mention(message: str, bot_mentions: list[str]) -> str:
    text = message.strip()
    for mention in bot_mentions:
        pattern = re.compile(rf"(^|\s){re.escape(mention)}(?=\s|$)", re.IGNORECASE)
        text = pattern.sub(" ", text).strip()
    return text


def parse_hermes_prompt(message: str) -> str:
    text = message.strip()
    match = re.match(r"^/(hermes|ask|home)\b\s*(.*)$", text, re.IGNORECASE | re.DOTALL)
    if match:
        text = match.group(2).strip()
    if not text:
        raise ValueError("Hermes prompt is empty")
    return text


class HTTPClient:
    def __init__(self, base_url: str, token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        data = None
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = resp.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code} {url}: {detail}") from exc
        if not body:
            return None
        return json.loads(body.decode("utf-8"))


def discover_clawdesk_hermes_channel(clawdesk: HTTPClient) -> str:
    spaces = clawdesk.request("GET", "spaces")
    tech = next((space for space in spaces if space.get("type") == "tech"), None)
    if not tech:
        raise RuntimeError("Could not find ClawDesk tech space")
    channels = clawdesk.request("GET", f"spaces/{tech['id']}/channels")
    hermes = next((channel for channel in channels if channel.get("name") == "Hermes / OpenClaw"), None)
    if not hermes:
        raise RuntimeError("Could not find ClawDesk Hermes / OpenClaw channel")
    return hermes["id"]


def fetch_recent_posts(mm: HTTPClient, channel_id: str, per_page: int = 20) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode({"page": 0, "per_page": per_page})
    data = mm.request("GET", f"api/v4/channels/{channel_id}/posts?{query}")
    order = data.get("order", [])
    posts = data.get("posts", {})
    return [posts[post_id] for post_id in reversed(order) if post_id in posts]


def post_mattermost(mm: HTTPClient, channel_id: str, message: str, root_id: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"channel_id": channel_id, "message": message}
    if root_id:
        payload["root_id"] = root_id
    return mm.request("POST", "api/v4/posts", payload)


def run_hermes(clawdesk: HTTPClient, channel_id: str, prompt: str, max_context_messages: int) -> dict[str, Any]:
    clawdesk.request("POST", f"channels/{channel_id}/messages", {"content": prompt})
    return clawdesk.request(
        "POST",
        f"channels/{channel_id}/agent/hermes",
        {"prompt": prompt, "max_context_messages": max_context_messages},
    )


def format_reply(result: dict[str, Any]) -> str:
    run = result.get("agent_run", {})
    message = result.get("message", {})
    status = run.get("status", "unknown")
    content = message.get("content", "")
    if len(content) > 3500:
        content = content[:3500] + "\n…(truncated)"
    return f"**Hermes {status}**\n\n{content}"


def should_process_post(post: dict[str, Any], bot_user_id: str | None, bot_mentions: list[str], hermes_channel_mode: bool) -> bool:
    if bot_user_id and post.get("user_id") == bot_user_id:
        return False
    if post.get("delete_at"):
        return False
    message = (post.get("message") or "").strip()
    if not message:
        return False
    if hermes_channel_mode:
        return True
    lowered = message.lower()
    return any(mention.lower() in lowered for mention in bot_mentions)


def process_post(
    post: dict[str, Any],
    mm: HTTPClient,
    clawdesk: HTTPClient,
    mm_channel_id: str,
    clawdesk_channel_id: str,
    bot_mentions: list[str],
    max_context_messages: int,
) -> None:
    raw_message = post.get("message") or ""
    cleaned = strip_bot_mention(raw_message, bot_mentions)
    try:
        prompt = parse_hermes_prompt(cleaned)
        result = run_hermes(clawdesk, clawdesk_channel_id, prompt, max_context_messages)
        reply = format_reply(result)
    except Exception as exc:  # keep bridge alive and report failure in-channel
        reply = f"**Hermes failed**\n\n```text\n{exc}\n```"
    post_mattermost(mm, mm_channel_id, reply, root_id=post.get("root_id") or post.get("id"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Mattermost to ClawDesk Hermes bridge")
    parser.add_argument("--once", action="store_true", help="Process currently visible new posts once and exit")
    parser.add_argument("--process-existing", action="store_true", help="Process recent posts present at startup")
    args = parser.parse_args()

    mm_url = os.environ["MATTERMOST_URL"].rstrip("/")
    mm_token = os.environ["MATTERMOST_TOKEN"]
    mm_channel_id = os.environ["MATTERMOST_HERMES_CHANNEL_ID"]
    clawdesk_url = os.getenv("CLAWDESK_URL", "http://127.0.0.1:8000").rstrip("/")
    clawdesk_channel_id = os.getenv("CLAWDESK_HERMES_CHANNEL_ID")
    poll_seconds = float(os.getenv("HERMES_BRIDGE_POLL_SECONDS", "3"))
    max_context_messages = int(os.getenv("HERMES_BRIDGE_MAX_CONTEXT_MESSAGES", "20"))
    bot_mentions = [item.strip() for item in os.getenv("HERMES_BOT_MENTIONS", "@Hermes,@hermes").split(",") if item.strip()]
    hermes_channel_mode = os.getenv("HERMES_BRIDGE_REQUIRE_MENTION", "0") != "1"

    mm = HTTPClient(mm_url, mm_token)
    clawdesk = HTTPClient(clawdesk_url)
    bot_user_id = None
    try:
        bot_user_id = mm.request("GET", "api/v4/users/me").get("id")
    except Exception as exc:
        print(f"warning: could not resolve Mattermost bot user id: {exc}", file=sys.stderr)

    if not clawdesk_channel_id:
        clawdesk_channel_id = discover_clawdesk_hermes_channel(clawdesk)

    seen = {post["id"] for post in fetch_recent_posts(mm, mm_channel_id)}
    print(f"Hermes bridge ready: mattermost_channel={mm_channel_id} clawdesk_channel={clawdesk_channel_id}", flush=True)

    if args.process_existing:
        seen = set()

    while True:
        posts = fetch_recent_posts(mm, mm_channel_id)
        for post in posts:
            post_id = post["id"]
            if post_id in seen:
                continue
            seen.add(post_id)
            if should_process_post(post, bot_user_id, bot_mentions, hermes_channel_mode):
                process_post(post, mm, clawdesk, mm_channel_id, clawdesk_channel_id, bot_mentions, max_context_messages)
        if args.once:
            return 0
        time.sleep(poll_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
