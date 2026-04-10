# tests/tools/filesystem/test_glob.py
"""Tests for glob tool."""
from __future__ import annotations

from pathlib import Path
from src.tools.filesystem.glob import build_glob_tool


def test_glob_finds_matching_files(workspace: Path) -> None:
    (workspace / "a.py").write_text("")
    (workspace / "b.py").write_text("")
    (workspace / "c.txt").write_text("")
    tool = build_glob_tool(workspace)
    result = tool.invoke({"pattern": "*.py"})
    assert "a.py" in result
    assert "b.py" in result
    assert "c.txt" not in result


def test_glob_recursive_pattern(workspace: Path) -> None:
    sub = workspace / "sub"
    sub.mkdir()
    (sub / "deep.py").write_text("")
    tool = build_glob_tool(workspace)
    result = tool.invoke({"pattern": "**/*.py"})
    assert "deep.py" in result


def test_glob_no_matches(workspace: Path) -> None:
    tool = build_glob_tool(workspace)
    result = tool.invoke({"pattern": "*.rs"})
    assert "No files matched" in result


def test_glob_nonexistent_path(workspace: Path) -> None:
    tool = build_glob_tool(workspace)
    result = tool.invoke({"pattern": "*.py", "path": "nope"})
    assert "does not exist" in result
