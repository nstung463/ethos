from __future__ import annotations

from src.backends.protocol import ExecuteResponse
from src.backends.sandbox import CommandBackedBackend


class _FakeBackend(CommandBackedBackend):
    def __init__(self, shells: set[str]) -> None:
        self._shells = shells
        self.calls: list[tuple[str, int | None]] = []

    @property
    def id(self) -> str:
        return "fake"

    @property
    def supported_shells(self) -> set[str]:
        return self._shells

    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        self.calls.append((command, timeout))
        return ExecuteResponse(output="ok", exit_code=0, truncated=False)

    def upload_files(self, files: list[tuple[str, bytes]]):  # pragma: no cover - not used here
        return []

    def download_files(self, paths: list[str]):  # pragma: no cover - not used here
        return []


def test_bash_tool_wraps_command_for_bash() -> None:
    from src.ai.tools.shell.bash import build_bash_tool

    backend = _FakeBackend({"bash"})
    tool = build_bash_tool(backend)

    result = tool.invoke({"command": "echo hello", "timeout": 7})

    assert result == "ok"
    assert backend.calls == [("bash -lc 'echo hello'", 7)]


def test_bash_tool_rejects_unsupported_backend() -> None:
    from src.ai.tools.shell.bash import build_bash_tool

    tool = build_bash_tool(_FakeBackend({"powershell"}))

    result = tool.invoke({"command": "echo hello"})

    assert "not supported" in result.lower()


def test_powershell_tool_encodes_command() -> None:
    from src.ai.tools.shell.powershell import build_powershell_tool

    backend = _FakeBackend({"powershell"})
    tool = build_powershell_tool(backend)

    result = tool.invoke({"command": "Get-ChildItem", "timeout": 3})

    assert result == "ok"
    command, timeout = backend.calls[0]
    assert command.startswith("powershell -NoProfile -EncodedCommand ")
    assert timeout == 3


def test_powershell_tool_rejects_background() -> None:
    from src.ai.tools.shell.powershell import build_powershell_tool

    tool = build_powershell_tool(_FakeBackend({"powershell"}))

    result = tool.invoke({"command": "Get-ChildItem", "background": True})

    assert "background" in result.lower()



def test_bash_blocks_network_command_in_default_mode(tmp_path):
    from unittest.mock import patch

    from src.ai.permissions.context import build_default_permission_context
    from src.ai.tools.shell.bash import build_bash_tool

    backend = _FakeBackend({"bash"})
    tool = build_bash_tool(backend, permission_context=build_default_permission_context(tmp_path))
    with patch("src.ai.tools.shell.bash.interrupt", return_value={"approved": False}):
        result = tool.invoke({"command": "curl https://example.com"})
    assert "permission" in result.lower()
    assert backend.calls == []


def test_bash_allows_read_only_command_in_default_mode(tmp_path):
    from src.ai.permissions.context import build_default_permission_context
    from src.ai.tools.shell.bash import build_bash_tool

    backend = _FakeBackend({"bash"})
    tool = build_bash_tool(backend, permission_context=build_default_permission_context(tmp_path))
    result = tool.invoke({"command": "pwd"})
    assert result == "ok"
    assert len(backend.calls) == 1


def test_bash_calls_interrupt_on_network_command(tmp_path) -> None:
    """bash tool must call interrupt() for networked commands, not return a string."""
    from pathlib import Path
    from unittest.mock import patch

    from src.ai.permissions.context import build_default_permission_context
    from src.ai.tools.shell.bash import build_bash_tool

    backend = _FakeBackend({"bash"})
    ctx = build_default_permission_context(workspace_root=tmp_path)
    tool = build_bash_tool(backend, permission_context=ctx)

    interrupted: list[dict] = []

    def _fake_interrupt(payload):
        interrupted.append(payload)
        return {"approved": False}

    with patch("src.ai.tools.shell.bash.interrupt", side_effect=_fake_interrupt):
        result = tool.invoke({"command": "curl https://example.com"})

    assert len(interrupted) == 1
    assert interrupted[0]["behavior"] == "ask"
    assert interrupted[0]["subject"] == "bash"
    assert not backend.calls  # command was NOT executed


def test_bash_proceeds_after_interrupt_approval(tmp_path) -> None:
    from unittest.mock import patch

    from src.ai.permissions.context import build_default_permission_context
    from src.ai.tools.shell.bash import build_bash_tool

    backend = _FakeBackend({"bash"})
    ctx = build_default_permission_context(workspace_root=tmp_path)
    tool = build_bash_tool(backend, permission_context=ctx)

    with patch("src.ai.tools.shell.bash.interrupt", return_value={"approved": True}):
        result = tool.invoke({"command": "curl https://example.com"})

    assert backend.calls  # command WAS executed after approval
    assert "denied" not in result.lower()  # not a denial message


def test_bash_calls_interrupt_on_code_execution(tmp_path) -> None:
    """code_execution commands (python, node) must call interrupt() even in accept_edits mode."""
    from unittest.mock import patch

    from src.ai.permissions.context import build_default_permission_context
    from src.ai.permissions.types import PermissionMode
    from src.ai.tools.shell.bash import build_bash_tool

    backend = _FakeBackend({"bash"})
    ctx = build_default_permission_context(workspace_root=tmp_path, mode=PermissionMode.ACCEPT_EDITS)
    tool = build_bash_tool(backend, permission_context=ctx)

    interrupted: list[dict] = []

    def _fake_interrupt(payload):
        interrupted.append(payload)
        return {"approved": False}

    with patch("src.ai.tools.shell.bash.interrupt", side_effect=_fake_interrupt):
        tool.invoke({"command": "python script.py"})

    assert len(interrupted) == 1
    assert interrupted[0]["behavior"] == "ask"
    assert not backend.calls


def test_powershell_calls_interrupt_on_network_command(tmp_path) -> None:
    from unittest.mock import patch

    from src.ai.permissions.context import build_default_permission_context
    from src.ai.tools.shell.powershell import build_powershell_tool

    backend = _FakeBackend({"powershell"})
    ctx = build_default_permission_context(workspace_root=tmp_path)
    tool = build_powershell_tool(backend, permission_context=ctx)

    interrupted: list[dict] = []

    def _fake_interrupt(payload):
        interrupted.append(payload)
        return {"approved": False}

    with patch("src.ai.tools.shell.powershell.interrupt", side_effect=_fake_interrupt):
        result = tool.invoke({"command": "Invoke-WebRequest https://example.com"})

    assert len(interrupted) == 1
    assert interrupted[0]["behavior"] == "ask"
    assert interrupted[0]["subject"] == "powershell"
    assert not backend.calls
