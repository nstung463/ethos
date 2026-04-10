from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.backends.daytona import DaytonaSandbox, create_daytona_sandbox


class _ExecResult:
    def __init__(self, result: str = "", exit_code: int = 0) -> None:
        self.result = result
        self.exit_code = exit_code


class _FakeProcess:
    def __init__(self, *, ready_exit_code: int = 0) -> None:
        self._ready_exit_code = ready_exit_code
        self.calls: list[tuple[str, int | None]] = []

    def exec(self, command: str, timeout: int | None = None) -> _ExecResult:
        self.calls.append((command, timeout))
        if command == "echo ready":
            return _ExecResult("ready", self._ready_exit_code)
        return _ExecResult("ok", 0)


class _FakeSandbox:
    def __init__(self, *, sid: str = "sb-1", ready_exit_code: int = 0) -> None:
        self.id = sid
        self.process = _FakeProcess(ready_exit_code=ready_exit_code)
        self.deleted = False

    def delete(self) -> None:
        self.deleted = True


def _install_fake_daytona(monkeypatch: pytest.MonkeyPatch, sandbox: _FakeSandbox) -> None:
    module = types.ModuleType("daytona")
    errors_module = types.ModuleType("daytona.common.errors")

    class DaytonaError(Exception):
        pass

    class DaytonaConfig:
        def __init__(self, api_key: str) -> None:
            self.api_key = api_key

    class CreateSandboxBaseParams:
        def __init__(self, name: str, auto_delete_interval: int) -> None:
            self.name = name
            self.auto_delete_interval = auto_delete_interval

    class Daytona:
        def __init__(self, _config: DaytonaConfig) -> None:
            self.sandbox = sandbox

        def create(self, params: CreateSandboxBaseParams) -> _FakeSandbox:
            assert params.name
            return self.sandbox

        def get(self, sandbox_id_or_name: str) -> _FakeSandbox:
            assert sandbox_id_or_name
            return self.sandbox

    module.Daytona = Daytona
    module.DaytonaConfig = DaytonaConfig
    module.CreateSandboxBaseParams = CreateSandboxBaseParams
    errors_module.DaytonaError = DaytonaError

    monkeypatch.setitem(sys.modules, "daytona", module)
    monkeypatch.setitem(sys.modules, "daytona.common.errors", errors_module)


def test_execute_uses_default_timeout() -> None:
    sandbox = _FakeSandbox()
    backend = DaytonaSandbox(sandbox=sandbox, timeout=123)

    result = backend.execute("pwd")

    assert result.exit_code == 0
    assert result.output == "ok"
    assert sandbox.process.calls == [("pwd", 123)]


def test_execute_returns_error_response_on_exception() -> None:
    class _BrokenProcess:
        def exec(self, _command: str, timeout: int | None = None):  # noqa: ARG002
            raise RuntimeError("boom")

    fake = types.SimpleNamespace(id="sb-2", process=_BrokenProcess())
    backend = DaytonaSandbox(sandbox=fake)

    result = backend.execute("ls")

    assert result.exit_code == 1
    assert "Daytona exec failed: boom" in result.output


def test_create_daytona_sandbox_requires_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DAYTONA_API_KEY", raising=False)

    with pytest.raises(ValueError, match="DAYTONA_API_KEY"):
        with create_daytona_sandbox(conversation_id="conv-1"):
            pass


def test_create_daytona_sandbox_yields_backend_and_cleans_up(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sandbox = _FakeSandbox()
    _install_fake_daytona(monkeypatch, sandbox)
    monkeypatch.setenv("DAYTONA_API_KEY", "test-key")

    with create_daytona_sandbox(conversation_id="conv-2") as backend:
        assert isinstance(backend, DaytonaSandbox)
        assert backend.id == "sb-1"
        # readiness probe should run before yielding
        assert ("echo ready", 5) in sandbox.process.calls
        assert sandbox.deleted is False

    assert sandbox.deleted is True
