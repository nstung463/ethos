# tests/tools/filesystem/test_glob.py
"""Tests for glob tool."""
from __future__ import annotations

from pathlib import Path
from src.ai.tools.filesystem.glob import build_glob_tool


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



def test_glob_hides_denied_paths(workspace: Path) -> None:
    from src.ai.permissions.context import build_default_permission_context
    from src.ai.permissions.types import PermissionBehavior, PermissionRule, PermissionSource, PermissionSubject
    (workspace / "a.py").write_text("")
    (workspace / "secret.py").write_text("")
    ctx = build_default_permission_context(
        workspace,
        rules=(PermissionRule(subject=PermissionSubject.READ, behavior=PermissionBehavior.DENY, source=PermissionSource.SESSION, matcher="secret.py"),)
    )
    tool = build_glob_tool(workspace, permission_context=ctx)
    result = tool.invoke({"pattern": "*.py"})
    assert "a.py" in result
    assert "secret.py" not in result
