from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "mattermost_hermes_bridge.py"
spec = importlib.util.spec_from_file_location("mattermost_hermes_bridge", SCRIPT_PATH)
assert spec is not None
bridge = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bridge
assert spec.loader is not None
spec.loader.exec_module(bridge)


def test_parse_hermes_prompt_with_slash_prefix():
    assert bridge.parse_hermes_prompt("/hermes summarize this") == "summarize this"
    assert bridge.parse_hermes_prompt("/ask what changed") == "what changed"
    assert bridge.parse_hermes_prompt("/home check service") == "check service"


def test_parse_hermes_prompt_without_prefix():
    assert bridge.parse_hermes_prompt("summarize this thread") == "summarize this thread"


def test_strip_hermes_mentions():
    assert bridge.strip_bot_mention("@Hermes /ask hello", ["@Hermes"]) == "/ask hello"


def test_should_process_post_in_hermes_channel_without_mention():
    post = {"id": "p1", "user_id": "u1", "message": "summarize this"}
    assert bridge.should_process_post(post, bot_user_id="bot", bot_mentions=["@Hermes"], hermes_channel_mode=True)


def test_should_not_process_own_or_empty_posts():
    assert not bridge.should_process_post({"user_id": "bot", "message": "hello"}, "bot", ["@Hermes"], True)
    assert not bridge.should_process_post({"user_id": "u1", "message": "   "}, "bot", ["@Hermes"], True)
