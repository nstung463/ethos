"""Shared pytest fixtures for ethos tool tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.app.core.settings import get_settings
from src.app.dependencies import get_auth_repository, get_file_store, get_rate_limiter, get_thread_store


@pytest.fixture(autouse=True)
def isolate_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ETHOS_SECURITY_STATE_DIR", str(tmp_path / "security"))
    monkeypatch.setenv("ETHOS_MANAGED_FILES_DIR", str(tmp_path / "managed_files"))
    get_settings.cache_clear()
    get_auth_repository.cache_clear()
    get_thread_store.cache_clear()
    get_file_store.cache_clear()
    get_rate_limiter.cache_clear()


@pytest.fixture()
def workspace(tmp_path: Path) -> Path:
    """Return a fresh temporary workspace root for each test."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    return ws
