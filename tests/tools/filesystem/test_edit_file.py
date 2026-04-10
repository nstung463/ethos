# tests/tools/filesystem/test_edit_file.py
"""Tests for edit_file tool."""
from __future__ import annotations

from pathlib import Path
from src.tools.filesystem.edit_file import build_edit_file_tool


def test_edit_replaces_unique_string(workspace: Path) -> None:
    (workspace / "code.py").write_text("x = 1\ny = 2\n")
    tool = build_edit_file_tool(workspace)
    tool.invoke({"path": "code.py", "old_string": "x = 1", "new_string": "x = 99"})
    assert (workspace / "code.py").read_text() == "x = 99\ny = 2\n"


def test_edit_fails_if_old_string_not_found(workspace: Path) -> None:
    (workspace / "f.py").write_text("hello")
    tool = build_edit_file_tool(workspace)
    result = tool.invoke({"path": "f.py", "old_string": "xyz", "new_string": "abc"})
    assert "not found" in result


def test_edit_fails_if_old_string_not_unique(workspace: Path) -> None:
    (workspace / "dup.py").write_text("x = 1\nx = 1\n")
    tool = build_edit_file_tool(workspace)
    result = tool.invoke({"path": "dup.py", "old_string": "x = 1", "new_string": "x = 0"})
    assert "2 times" in result


def test_edit_replace_all(workspace: Path) -> None:
    (workspace / "dup.py").write_text("x = 1\nx = 1\n")
    tool = build_edit_file_tool(workspace)
    tool.invoke({"path": "dup.py", "old_string": "x = 1", "new_string": "x = 0", "replace_all": True})
    assert (workspace / "dup.py").read_text() == "x = 0\nx = 0\n"


def test_edit_missing_file(workspace: Path) -> None:
    tool = build_edit_file_tool(workspace)
    result = tool.invoke({"path": "ghost.py", "old_string": "a", "new_string": "b"})
    assert "does not exist" in result
