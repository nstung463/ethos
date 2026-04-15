# tests/tools/filesystem/test_sandbox.py
"""Tests for path sandboxing in _sandbox.py."""
from __future__ import annotations

import pytest
from pathlib import Path
from src.ai.tools.filesystem._sandbox import resolve


def test_resolve_relative_path(workspace: Path) -> None:
    result = resolve(workspace, "foo/bar.txt")
    assert result == workspace / "foo" / "bar.txt"


def test_resolve_strips_leading_slash(workspace: Path) -> None:
    result = resolve(workspace, "/foo.txt")
    assert result == workspace / "foo.txt"


def test_resolve_rejects_traversal(workspace: Path) -> None:
    with pytest.raises(PermissionError, match="outside the workspace root"):
        resolve(workspace, "../secret.txt")


def test_resolve_rejects_absolute_escape(workspace: Path) -> None:
    # Leading slashes are stripped and joined to workspace root, so /etc/passwd
    # becomes workspace/etc/passwd (inside workspace). Traversal via .. is what
    # actually escapes, so we test a direct parent traversal here.
    with pytest.raises(PermissionError):
        resolve(workspace, "../../escape.txt")


def test_resolve_dot_stays_at_root(workspace: Path) -> None:
    result = resolve(workspace, ".")
    assert result == workspace

