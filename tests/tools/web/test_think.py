# tests/tools/web/test_think.py
"""Tests for think tool."""
from src.ai.tools.web.think import think_tool


def test_think_records_reflection() -> None:
    result = think_tool.invoke({"reflection": "my reasoning here"})
    assert result == "Reflection recorded: my reasoning here"


def test_think_empty_reflection() -> None:
    result = think_tool.invoke({"reflection": ""})
    assert result == "Reflection recorded: "

