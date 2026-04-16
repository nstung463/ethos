"""powershell tool - run PowerShell commands inside a supported backend."""

from __future__ import annotations

import base64

from langchain_core.tools import StructuredTool
from langgraph.types import interrupt
from pydantic import BaseModel, Field

from src.backends.protocol import SandboxProtocol
from src.ai.permissions.evaluator import PermissionEvaluator
from src.ai.permissions.shell_policy import ShellPolicy
from src.ai.permissions.types import PermissionBehavior, PermissionContext, PermissionMode, PermissionSubject


class PowerShellInput(BaseModel):
    command: str = Field(
        description=(
            "PowerShell command to execute inside the backend workspace. "
            "Examples: 'Get-ChildItem', 'pytest -q', 'Get-Content file.txt'."
        )
    )
    timeout: int | None = Field(
        default=None,
        description="Maximum seconds to wait. Uses backend default when omitted.",
    )
    background: bool = Field(
        default=False,
        description="Reserved for future parity. Background execution is not supported in Ethos v1.",
    )


def _encode_powershell(command: str) -> str:
    return base64.b64encode(command.encode("utf-16le")).decode("ascii")


def build_powershell_tool(
    backend: SandboxProtocol,
    permission_context: PermissionContext | None = None,
) -> StructuredTool:
    """Build the PowerShell tool when the backend supports it."""
    policy = ShellPolicy()
    evaluator = PermissionEvaluator()

    def _powershell(command: str, timeout: int | None = None, background: bool = False) -> str:
        if "powershell" not in backend.supported_shells:
            return "Error: powershell is not supported by the active backend."
        if background:
            return "Error: background execution is not supported by the powershell tool yet."

        if permission_context is not None:
            decision = evaluator.evaluate(
                context=permission_context,
                subject=PermissionSubject.POWERSHELL,
                candidate=command,
                policy_decision=policy.check_powershell(context=permission_context, command=command),
            )
            if decision.behavior is PermissionBehavior.DENY:
                return f"Permission denied: {decision.reason}"

            if decision.behavior is PermissionBehavior.ASK:
                user_decision = interrupt({
                    "behavior": "ask",
                    "reason": decision.reason,
                    "subject": "powershell",
                    "command": command,
                    "suggested_mode": PermissionMode.BYPASS_PERMISSIONS.value,
                })
                if not user_decision.get("approved", False):
                    return "Permission denied by user."

        encoded = _encode_powershell(command)
        wrapped = f"powershell -NoProfile -EncodedCommand {encoded}"
        result = backend.execute(wrapped, timeout=timeout)
        output = result.output.strip()
        if result.exit_code != 0:
            return f"Exit code: {result.exit_code}\n{output}" if output else f"Command failed (exit {result.exit_code})"
        return output or "(no output)"

    return StructuredTool.from_function(
        name="powershell",
        func=_powershell,
        description=(
            "Execute a PowerShell command inside a Windows-compatible backend workspace. "
            "Use for Windows-native shell tasks and scripts."
        ),
        args_schema=PowerShellInput,
    )
