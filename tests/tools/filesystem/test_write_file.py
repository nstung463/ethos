# tests/tools/filesystem/test_write_file.py
"""Tests for write_file tool."""
from __future__ import annotations

import pytest
from pathlib import Path
from src.tools.filesystem.write_file import build_write_file_tool


def test_write_creates_new_file(workspace: Path) -> None:
    tool = build_write_file_tool(workspace)
    tool.invoke({"path": "new.txt", "content": "hello"})
    assert (workspace / "new.txt").read_text() == "hello"


def test_write_creates_parent_dirs(workspace: Path) -> None:
    tool = build_write_file_tool(workspace)
    tool.invoke({"path": "a/b/c.txt", "content": "deep"})
    assert (workspace / "a" / "b" / "c.txt").exists()


def test_write_overwrites_existing(workspace: Path) -> None:
    (workspace / "f.txt").write_text("old")
    tool = build_write_file_tool(workspace)
    tool.invoke({"path": "f.txt", "content": "new"})
    assert (workspace / "f.txt").read_text() == "new"


def test_write_reports_line_count(workspace: Path) -> None:
    tool = build_write_file_tool(workspace)
    result = tool.invoke({"path": "lines.txt", "content": "a\nb\nc"})
    assert "3 lines" in result


def test_write_rejects_traversal(workspace: Path) -> None:
    tool = build_write_file_tool(workspace)
    with pytest.raises(PermissionError):
        tool.invoke({"path": "../escape.txt", "content": "bad"})


def test_write_requires_permission_in_default_mode(workspace: Path) -> None:
    from src.ai.permissions.context import build_default_permission_context
    tool = build_write_file_tool(workspace, permission_context=build_default_permission_context(workspace))
    result = tool.invoke({"path": "blocked.txt", "content": "hello"})
    assert "permission" in result.lower()
    assert "ask" in result.lower()


def test_write_allowed_in_accept_edits_mode(workspace: Path) -> None:
    from src.ai.permissions.context import build_default_permission_context
    from src.ai.permissions.types import PermissionMode
    tool = build_write_file_tool(workspace, permission_context=build_default_permission_context(workspace, mode=PermissionMode.ACCEPT_EDITS))
    result = tool.invoke({"path": "ok.txt", "content": "hello"})
    assert "written" in result.lower()
