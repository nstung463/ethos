from __future__ import annotations

from types import MappingProxyType

from src.ai.permissions.types import (
    PermissionBehavior,
    PermissionContext,
    PermissionDecision,
    PermissionMode,
)


class ShellPolicy:
    # Command prefixes by class
    _READ_ONLY_PREFIXES = (
        "pwd",
        "ls",
        "ls ",
        "cat ",
        "rg ",
        "rg\t",
        "git status",
        "git log",
        "git diff",
        "git show",
        "Get-ChildItem",
        "Get-Content ",
        "Get-Item ",
        "Get-Location",
        "echo ",
        "type ",  # bare echo without redirect → read-only
    )
    _NETWORK_PREFIXES = (
        "curl ",
        "wget ",
        "Invoke-WebRequest",
        "Invoke-RestMethod",
        "pip install",
        "pip3 install",
        "npm install",
        "npm ci",
        "uv add",
        "uv sync",
        "apt ",
        "apt-get ",
        "brew ",
    )
    _DESTRUCTIVE_PREFIXES = (
        "rm ",
        "rm\t",
        "del ",
        "Remove-Item",
        "git reset --hard",
        "git clean ",
        "format ",
        "mkfs",
        "dd ",
    )
    _PRIVILEGED_PREFIXES = (
        "sudo ",
        "su ",
        "su\t",
        "chmod ",
        "chown ",
        "chgrp ",
        "Invoke-Expression",
        "iex ",
        "iex\t",
        "eval ",
        "exec ",
        "Start-Process",
        "runas ",
    )
    # Markers that indicate write to file (must appear in command, not just as prefix)
    _REDIRECT_MARKERS = (" >", " >>", ">", ">>")
    _WRITE_COMMAND_PREFIXES = (
        "Set-Content",
        "Out-File",
        "Add-Content",
        "tee ",
        "mkdir ",
        "touch ",
        "cp ",
        "mv ",
        "copy ",
        "move ",
    )

    def _classify(self, command: str) -> str:
        stripped = command.strip()

        # Privileged/escape check first (highest risk)
        if stripped.startswith(self._PRIVILEGED_PREFIXES):
            return "privileged_or_escape"

        # Network check
        if stripped.startswith(self._NETWORK_PREFIXES):
            return "networked"

        # Destructive check
        if stripped.startswith(self._DESTRUCTIVE_PREFIXES):
            return "destructive"

        # Read-only check (before write checks)
        if stripped.startswith(self._READ_ONLY_PREFIXES):
            # But if read-only prefix has a redirect, it's actually a write
            if any(marker in stripped for marker in self._REDIRECT_MARKERS):
                return "workspace_write"
            return "read_only"

        # Write command prefixes
        if stripped.startswith(self._WRITE_COMMAND_PREFIXES):
            return "workspace_write"

        # Redirect markers (e.g., `python script.py > output.txt`)
        if any(marker in stripped for marker in self._REDIRECT_MARKERS):
            return "workspace_write"

        # Default: unknown → conservative workspace_write
        return "workspace_write"

    def check_bash(self, *, context: PermissionContext, command: str) -> PermissionDecision:
        return self._check(context=context, command=command, shell_name="bash")

    def check_powershell(self, *, context: PermissionContext, command: str) -> PermissionDecision:
        return self._check(context=context, command=command, shell_name="powershell")

    def _check(
        self, *, context: PermissionContext, command: str, shell_name: str
    ) -> PermissionDecision:
        classification = self._classify(command)

        if classification == "read_only":
            return PermissionDecision(
                behavior=PermissionBehavior.ALLOW,
                reason=f"{shell_name} read-only command",
                metadata=MappingProxyType({"classification": classification}),
            )

        if classification == "privileged_or_escape":
            # privileged commands ask even in bypass_permissions
            return PermissionDecision(
                behavior=PermissionBehavior.ASK,
                reason=f"{shell_name} command classified as {classification}",
                metadata=MappingProxyType({"classification": classification}),
            )

        if classification in ("networked", "destructive"):
            return PermissionDecision(
                behavior=PermissionBehavior.ASK,
                reason=f"{shell_name} command classified as {classification}",
                metadata=MappingProxyType({"classification": classification}),
            )

        # workspace_write
        if context.mode is PermissionMode.ACCEPT_EDITS:
            return PermissionDecision(
                behavior=PermissionBehavior.ALLOW,
                reason=f"{shell_name} workspace write allowed by accept_edits",
                metadata=MappingProxyType({"classification": classification}),
            )

        return PermissionDecision(
            behavior=PermissionBehavior.ASK,
            reason=f"{shell_name} command classified as {classification}",
            metadata=MappingProxyType({"classification": classification}),
        )
