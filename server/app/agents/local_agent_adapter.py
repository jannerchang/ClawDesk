from __future__ import annotations

import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class LocalAgentRequest:
    prompt: str
    agent: str = "shell"
    workspace: str | None = None
    timeout_seconds: int | None = None


@dataclass(slots=True)
class LocalAgentResponse:
    text: str
    status: str
    command: list[str]
    workspace: str


class LocalAgentAdapterError(RuntimeError):
    pass


class LocalAgentAdapter:
    """Thin current-machine runner for the LocalAgent bot.

    This is intentionally not a Hermes wrapper. It runs only explicit local
    tools from an allowlist and always from a bounded workspace directory.
    """

    AGENT_COMMANDS: dict[str, list[str]] = {
        "codex": ["codex"],
        "antigravity": ["agy"],
        "agy": ["agy"],
        "grok": ["grok"],
        "grok-build": ["grok"],
        "shell": ["/bin/bash", "-lc"],
    }

    def __init__(self, mode: str | None = None, timeout_seconds: int | None = None) -> None:
        self.mode = (mode or os.getenv("CLAWDESK_LOCAL_AGENT_MODE") or "stub").strip().lower()
        raw_timeout = os.getenv("CLAWDESK_LOCAL_AGENT_TIMEOUT_SECONDS")
        self.timeout_seconds = timeout_seconds or int(raw_timeout or "120")
        self.workspace_root = Path(os.getenv("CLAWDESK_LOCAL_AGENT_WORKSPACE_ROOT", str(Path.home()))).expanduser().resolve()

    def invoke(self, request: LocalAgentRequest) -> LocalAgentResponse:
        workspace = self._resolve_workspace(request.workspace)
        agent = request.agent.strip().lower()
        if agent not in self.AGENT_COMMANDS:
            raise LocalAgentAdapterError(f"Unsupported local agent: {request.agent}")
        timeout = request.timeout_seconds or self.timeout_seconds
        if timeout < 1 or timeout > 600:
            raise LocalAgentAdapterError("timeout_seconds must be between 1 and 600")

        command = self._build_command(agent, request.prompt)
        if self.mode == "stub":
            return LocalAgentResponse(
                text=f"[LocalAgent stub] agent={agent} workspace={workspace}\n收到：{request.prompt}",
                status="stubbed",
                command=command,
                workspace=str(workspace),
            )
        if self.mode == "exec":
            return self._invoke_exec(command, workspace, timeout)
        raise LocalAgentAdapterError(f"Unsupported CLAWDESK_LOCAL_AGENT_MODE: {self.mode}")

    def _resolve_workspace(self, raw: str | None) -> Path:
        candidate = Path(raw).expanduser() if raw else self.workspace_root
        if not candidate.is_absolute():
            candidate = self.workspace_root / candidate
        resolved = candidate.resolve()
        if not resolved.exists() or not resolved.is_dir():
            raise LocalAgentAdapterError(f"Workspace does not exist or is not a directory: {resolved}")
        try:
            resolved.relative_to(self.workspace_root)
        except ValueError as exc:
            raise LocalAgentAdapterError(f"Workspace must be under {self.workspace_root}: {resolved}") from exc
        return resolved

    def _build_command(self, agent: str, prompt: str) -> list[str]:
        base = self.AGENT_COMMANDS[agent]
        if agent == "shell":
            return [*base, prompt]
        return [*base, prompt]

    def _invoke_exec(self, command: list[str], workspace: Path, timeout: int) -> LocalAgentResponse:
        try:
            completed = subprocess.run(
                command,
                cwd=str(workspace),
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise LocalAgentAdapterError(f"Local agent timed out after {timeout}s") from exc
        except OSError as exc:
            printable = " ".join(shlex.quote(part) for part in command)
            raise LocalAgentAdapterError(f"Failed to start local agent command `{printable}`: {exc}") from exc

        stdout = completed.stdout.strip()
        stderr = completed.stderr.strip()
        combined = "\n".join(part for part in (stdout, stderr) if part).strip()
        if completed.returncode != 0:
            detail = combined or f"exit code {completed.returncode}"
            raise LocalAgentAdapterError(f"Local agent failed: {detail}")
        return LocalAgentResponse(
            text=combined or "Local agent command completed with no output.",
            status="succeeded",
            command=command,
            workspace=str(workspace),
        )
