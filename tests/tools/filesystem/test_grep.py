# tests/tools/filesystem/test_grep.py
"""Tests for grep tool."""
from __future__ import annotations

from pathlib import Path
from src.ai.tools.filesystem.grep import build_grep_tool


def test_grep_content_mode_returns_matching_lines(workspace: Path) -> None:
    (workspace / "f.py").write_text("hello world\ngoodbye world\n")
    tool = build_grep_tool(workspace)
    result = tool.invoke({"pattern": "hello", "output_mode": "content"})
    assert "hello world" in result
    assert "goodbye" not in result


def test_grep_files_with_matches_mode(workspace: Path) -> None:
    (workspace / "yes.py").write_text("match here")
    (workspace / "no.py").write_text("nothing")
    tool = build_grep_tool(workspace)
    result = tool.invoke({"pattern": "match", "output_mode": "files_with_matches"})
    assert "yes.py" in result
    assert "no.py" not in result


def test_grep_count_mode(workspace: Path) -> None:
    (workspace / "c.py").write_text("x\nx\ny\n")
    tool = build_grep_tool(workspace)
    result = tool.invoke({"pattern": "x", "output_mode": "count"})
    assert "c.py: 2" in result


def test_grep_glob_filter(workspace: Path) -> None:
    (workspace / "a.py").write_text("find me")
    (workspace / "b.txt").write_text("find me")
    tool = build_grep_tool(workspace)
    result = tool.invoke({"pattern": "find me", "glob": "*.py", "output_mode": "files_with_matches"})
    assert "a.py" in result
    assert "b.txt" not in result


def test_grep_invalid_regex(workspace: Path) -> None:
    tool = build_grep_tool(workspace)
    result = tool.invoke({"pattern": "[invalid"})
    assert "invalid regex" in result


def test_grep_no_matches(workspace: Path) -> None:
    (workspace / "f.py").write_text("nothing here")
    tool = build_grep_tool(workspace)
    result = tool.invoke({"pattern": "zzznomatch"})
    assert "No matches" in result

