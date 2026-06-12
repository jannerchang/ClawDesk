from __future__ import annotations

import os
import re
import subprocess
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
    status: str


class HermesAdapterError(RuntimeError):
    pass


class HermesAdapter:
    """Hermes invocation adapter.

    Modes:
    - stub: deterministic local response for tests and offline dev.
    - cli: invokes `hermes chat -q <prompt> --profile <profile>` via subprocess.
    - auto (default): tries cli first, then falls back to stub unless disabled.
    """

    def __init__(self, mode: str | None = None, timeout_seconds: int | None = None) -> None:
        self.mode = (mode or os.getenv("CLAWDESK_HERMES_MODE") or "auto").strip().lower()
        raw_timeout = os.getenv("CLAWDESK_HERMES_TIMEOUT_SECONDS")
        self.timeout_seconds = timeout_seconds or int(raw_timeout or "120")
        self.fallback_to_stub = os.getenv("CLAWDESK_HERMES_FALLBACK_TO_STUB", "1") != "0"

    def invoke(self, request: HermesRequest) -> HermesResponse:
        if self.mode == "stub":
            return self._invoke_stub(request)
        if self.mode == "cli":
            return self._invoke_cli(request)
        if self.mode == "auto":
            try:
                return self._invoke_cli(request)
            except HermesAdapterError:
                if not self.fallback_to_stub:
                    raise
                return self._invoke_stub(request)
        raise HermesAdapterError(f"Unsupported CLAWDESK_HERMES_MODE: {self.mode}")

    def _invoke_stub(self, request: HermesRequest) -> HermesResponse:
        return HermesResponse(text=f"[Hermes stub] 收到：{request.prompt}", status="stubbed")

    def _invoke_cli(self, request: HermesRequest) -> HermesResponse:
        command = ["hermes", "chat", "-q", request.prompt, "--profile", request.profile, "--quiet"]
        if request.model:
            command.extend(["--model", request.model])
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise HermesAdapterError(f"Hermes CLI timed out after {self.timeout_seconds}s") from exc
        except OSError as exc:
            raise HermesAdapterError(f"Failed to start Hermes CLI: {exc}") from exc

        stdout = completed.stdout.strip()
        stderr = completed.stderr.strip()
        if completed.returncode != 0:
            detail = stderr or stdout or f"exit code {completed.returncode}"
            raise HermesAdapterError(f"Hermes CLI failed: {detail}")
        return HermesResponse(text=self._clean_cli_output(stdout), status="succeeded")

    def _clean_cli_output(self, text: str) -> str:
        lines = [line for line in text.splitlines() if not re.match(r"^session_id:\s*\S+\s*$", line)]
        cleaned = "\n".join(lines).strip()
        return cleaned or text.strip()
