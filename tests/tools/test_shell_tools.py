from __future__ import annotations

from src.backends.protocol import ExecuteResponse
from src.backends.sandbox import BaseSandbox


class _FakeBackend(BaseSandbox):
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
    from src.tools.shell.bash import build_bash_tool

    backend = _FakeBackend({"bash"})
    tool = build_bash_tool(backend)

    result = tool.invoke({"command": "echo hello", "timeout": 7})

    assert result == "ok"
    assert backend.calls == [("bash -lc 'echo hello'", 7)]


def test_bash_tool_rejects_unsupported_backend() -> None:
    from src.tools.shell.bash import build_bash_tool

    tool = build_bash_tool(_FakeBackend({"powershell"}))

    result = tool.invoke({"command": "echo hello"})

    assert "not supported" in result.lower()


def test_powershell_tool_encodes_command() -> None:
    from src.tools.shell.powershell import build_powershell_tool

    backend = _FakeBackend({"powershell"})
    tool = build_powershell_tool(backend)

    result = tool.invoke({"command": "Get-ChildItem", "timeout": 3})

    assert result == "ok"
    command, timeout = backend.calls[0]
    assert command.startswith("powershell -NoProfile -EncodedCommand ")
    assert timeout == 3


def test_powershell_tool_rejects_background() -> None:
    from src.tools.shell.powershell import build_powershell_tool

    tool = build_powershell_tool(_FakeBackend({"powershell"}))

    result = tool.invoke({"command": "Get-ChildItem", "background": True})

    assert "background" in result.lower()
