"""Tests for notebook_edit tool."""
from __future__ import annotations

from pathlib import Path
import pytest

try:
    import nbformat
    HAS_NBFORMAT = True
except ImportError:
    HAS_NBFORMAT = False

pytestmark = pytest.mark.skipif(not HAS_NBFORMAT, reason="nbformat not installed")


def _make_notebook(workspace: Path, cells: list[dict]) -> str:
    nb = nbformat.v4.new_notebook()
    nb.cells = [
        nbformat.v4.new_code_cell(c["source"]) if c["type"] == "code"
        else nbformat.v4.new_markdown_cell(c["source"])
        for c in cells
    ]
    path = workspace / "test.ipynb"
    nbformat.write(nb, str(path))
    return "test.ipynb"


def test_notebook_edit_replaces_cell_source(workspace: Path) -> None:
    nb_path = _make_notebook(workspace, [
        {"type": "code", "source": "x = 1"},
        {"type": "markdown", "source": "# Header"},
    ])
    from src.ai.tools.filesystem.notebook_edit import build_notebook_edit_tool
    tool = build_notebook_edit_tool(workspace)
    result = tool.invoke({"path": nb_path, "cell_index": 0, "new_source": "x = 99"})
    assert "edited" in result.lower()
    nb = nbformat.read(str(workspace / nb_path), as_version=4)
    assert nb.cells[0].source == "x = 99"


def test_notebook_edit_out_of_range_index(workspace: Path) -> None:
    nb_path = _make_notebook(workspace, [{"type": "code", "source": "pass"}])
    from src.ai.tools.filesystem.notebook_edit import build_notebook_edit_tool
    tool = build_notebook_edit_tool(workspace)
    result = tool.invoke({"path": nb_path, "cell_index": 99, "new_source": "x = 1"})
    assert "out of range" in result.lower() or "error" in result.lower()


def test_notebook_edit_missing_file(workspace: Path) -> None:
    from src.ai.tools.filesystem.notebook_edit import build_notebook_edit_tool
    tool = build_notebook_edit_tool(workspace)
    result = tool.invoke({"path": "ghost.ipynb", "cell_index": 0, "new_source": "x"})
    assert "does not exist" in result or "error" in result.lower()


def test_notebook_edit_non_notebook(workspace: Path) -> None:
    (workspace / "code.py").write_text("x = 1")
    from src.ai.tools.filesystem.notebook_edit import build_notebook_edit_tool
    tool = build_notebook_edit_tool(workspace)
    result = tool.invoke({"path": "code.py", "cell_index": 0, "new_source": "y = 2"})
    assert "error" in result.lower() or "notebook" in result.lower()

