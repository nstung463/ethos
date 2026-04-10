# tests/tools/web/test_think.py
"""Tests for think tool."""
from src.tools.web.think import think_tool


def test_think_returns_thought_unchanged() -> None:
    result = think_tool.invoke({"thought": "my reasoning here"})
    assert result == "my reasoning here"


def test_think_empty_thought() -> None:
    result = think_tool.invoke({"thought": ""})
    assert result == ""
