"""Shared pytest fixtures for ethos tool tests."""
from __future__ import annotations

import pytest
from pathlib import Path


@pytest.fixture()
def workspace(tmp_path: Path) -> Path:
    """Return a fresh temporary workspace root for each test."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    return ws
