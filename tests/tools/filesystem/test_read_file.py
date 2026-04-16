# tests/tools/filesystem/test_read_file.py
"""Tests for read_file tool."""
from __future__ import annotations

from pathlib import Path
from src.ai.tools.filesystem.read_file import build_read_file_tool


def test_read_file_returns_numbered_lines(workspace: Path) -> None:
    (workspace / "hello.txt").write_text("line1\nline2\nline3")
    tool = build_read_file_tool(workspace)
    result = tool.invoke({"path": "hello.txt"})
    assert "     1\tline1" in result
    assert "     2\tline2" in result
    assert "     3\tline3" in result


def test_read_file_missing_file(workspace: Path) -> None:
    tool = build_read_file_tool(workspace)
    result = tool.invoke({"path": "missing.txt"})
    assert "does not exist" in result


def test_read_file_directory(workspace: Path) -> None:
    (workspace / "d").mkdir()
    tool = build_read_file_tool(workspace)
    result = tool.invoke({"path": "d"})
    assert "directory" in result


def test_read_file_pagination_offset(workspace: Path) -> None:
    lines = "\n".join(f"line{i}" for i in range(1, 11))
    (workspace / "big.txt").write_text(lines)
    tool = build_read_file_tool(workspace)
    result = tool.invoke({"path": "big.txt", "offset": 5, "limit": 3})
    assert "line6" in result
    assert "line7" in result
    assert "line8" in result
    assert "line5" not in result
    assert "line9" not in result


def test_read_file_empty(workspace: Path) -> None:
    (workspace / "empty.txt").write_text("")
    tool = build_read_file_tool(workspace)
    result = tool.invoke({"path": "empty.txt"})
    assert result == "(empty file)"


def test_read_file_offset_past_end(workspace: Path) -> None:
    (workspace / "short.txt").write_text("a\nb")
    tool = build_read_file_tool(workspace)
    result = tool.invoke({"path": "short.txt", "offset": 100})
    assert "past the end" in result


def test_read_file_shows_truncation_hint(workspace: Path) -> None:
    lines = "\n".join(f"line{i}" for i in range(1, 250))
    (workspace / "long.txt").write_text(lines)
    tool = build_read_file_tool(workspace)
    result = tool.invoke({"path": "long.txt", "limit": 5})
    assert "Showing lines" in result or "offset=" in result

