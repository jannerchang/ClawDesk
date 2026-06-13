from __future__ import annotations

import importlib.util
from pathlib import Path


import sys

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "mattermost_local_agent_bridge.py"
spec = importlib.util.spec_from_file_location("mattermost_local_agent_bridge", SCRIPT_PATH)
assert spec is not None
bridge = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bridge
assert spec.loader is not None
spec.loader.exec_module(bridge)


def test_parse_local_command_with_explicit_agent():
    command = bridge.parse_local_command("/codex review the staged diff")
    assert command.agent == "codex"
    assert command.prompt == "review the staged diff"


def test_parse_local_command_defaults_to_shell():
    command = bridge.parse_local_command("printf hello")
    assert command.agent == "shell"
    assert command.prompt == "printf hello"


def test_strip_bot_mentions():
    assert bridge.strip_bot_mention("@LocalAgent /shell pwd", ["@LocalAgent"]) == "/shell pwd"
    assert bridge.strip_bot_mention("please run @localagent /grok build", ["@LocalAgent", "@localagent"]) == "please run  /grok build"


def test_should_process_post_in_local_work_channel_without_mention():
    post = {"id": "p1", "user_id": "u1", "message": "printf ok"}
    assert bridge.should_process_post(post, bot_user_id="bot", bot_mentions=["@LocalAgent"], local_work_channel_mode=True)


def test_should_not_process_own_or_empty_posts():
    assert not bridge.should_process_post({"user_id": "bot", "message": "hello"}, "bot", ["@LocalAgent"], True)
    assert not bridge.should_process_post({"user_id": "u1", "message": "   "}, "bot", ["@LocalAgent"], True)
