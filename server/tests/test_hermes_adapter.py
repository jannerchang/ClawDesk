from __future__ import annotations

from app.agents.hermes_adapter import HermesAdapter, HermesRequest


def test_stub_mode_returns_deterministic_response() -> None:
    response = HermesAdapter(mode="stub").invoke(HermesRequest(prompt="ping"))

    assert response.status == "stubbed"
    assert response.text == "[Hermes stub] 收到：ping"


def test_clean_cli_output_removes_session_id_line() -> None:
    adapter = HermesAdapter(mode="stub")

    cleaned = adapter._clean_cli_output("session_id: 20260612_153405_ff6ac7\nCLAWDESK_HERMES_OK")

    assert cleaned == "CLAWDESK_HERMES_OK"
