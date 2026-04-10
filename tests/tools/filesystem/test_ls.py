# tests/tools/filesystem/test_ls.py
"""Tests for ls tool."""
from __future__ import annotations

from pathlib import Path
from src.tools.filesystem.ls import build_ls_tool


def test_ls_root_shows_files_and_dirs(workspace: Path) -> None:
    (workspace / "file.txt").write_text("hi")
    (workspace / "subdir").mkdir()
    tool = build_ls_tool(workspace)
    result = tool.invoke({"path": "."})
    assert "subdir/" in result
    assert "file.txt" in result


def test_ls_dirs_sorted_before_files(workspace: Path) -> None:
    (workspace / "z_file.txt").write_text("z")
    (workspace / "a_dir").mkdir()
    tool = build_ls_tool(workspace)
    result = tool.invoke({"path": "."})
    lines = result.strip().split("\n")
    assert lines[0] == "a_dir/"
    assert "z_file.txt" in lines[1]


def test_ls_nonexistent_path(workspace: Path) -> None:
    tool = build_ls_tool(workspace)
    result = tool.invoke({"path": "nope"})
    assert "does not exist" in result


def test_ls_empty_dir(workspace: Path) -> None:
    (workspace / "empty").mkdir()
    tool = build_ls_tool(workspace)
    result = tool.invoke({"path": "empty"})
    assert result == "(empty directory)"


def test_ls_single_file(workspace: Path) -> None:
    (workspace / "solo.txt").write_text("solo")
    tool = build_ls_tool(workspace)
    result = tool.invoke({"path": "solo.txt"})
    assert "solo.txt" in result
