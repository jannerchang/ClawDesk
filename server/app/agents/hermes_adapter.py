from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class HermesRequest:
    prompt: str
    profile: str = "default"
    model: str | None = None
    reasoning: str | None = None


@dataclass(slots=True)
class HermesResponse:
    text: str
    status: str = "stubbed"


class HermesAdapter:
    """Placeholder adapter for future Hermes CLI/API integration.

    Real Hermes invocation is intentionally not wired in Phase 0 so basic CRUD can
    be validated without triggering model calls.
    """

    def invoke(self, request: HermesRequest) -> HermesResponse:
        return HermesResponse(text=f"[Hermes stub] 收到：{request.prompt}")
