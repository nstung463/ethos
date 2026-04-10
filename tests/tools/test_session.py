"""Tests for session utility tools: sleep, config, tool_search."""
from __future__ import annotations

import json
import time


def test_sleep_pauses_execution() -> None:
    from src.tools.session.sleep import sleep_tool
    start = time.monotonic()
    sleep_tool.invoke({"duration_ms": 100})
    elapsed = time.monotonic() - start
    assert elapsed >= 0.09


def test_sleep_zero_duration() -> None:
    from src.tools.session.sleep import sleep_tool
    result = sleep_tool.invoke({"duration_ms": 0})
    assert "slept" in result.lower() or "0ms" in result.lower()


def test_config_set_and_get() -> None:
    from src.tools.session.config import build_config_tool
    store: dict = {}
    tool = build_config_tool(config_store=store)
    tool.invoke({"action": "set", "key": "theme", "value": "dark"})
    result = json.loads(tool.invoke({"action": "get", "key": "theme"}))
    assert result["value"] == "dark"


def test_config_get_missing_key() -> None:
    from src.tools.session.config import build_config_tool
    tool = build_config_tool(config_store={})
    result = tool.invoke({"action": "get", "key": "no_such_key"})
    assert "not found" in result.lower()


def test_config_list_all_keys() -> None:
    from src.tools.session.config import build_config_tool
    store = {"a": "1", "b": "2"}
    tool = build_config_tool(config_store=store)
    result = json.loads(tool.invoke({"action": "list"}))
    assert set(result["keys"]) == {"a", "b"}


def test_config_delete_key() -> None:
    from src.tools.session.config import build_config_tool
    store = {"x": "val"}
    tool = build_config_tool(config_store=store)
    tool.invoke({"action": "delete", "key": "x"})
    assert "x" not in store


def test_tool_search_finds_by_keyword() -> None:
    from langchain_core.tools import StructuredTool
    from src.tools.session.tool_search import build_tool_search_tool
    from pydantic import BaseModel

    class DummyInput(BaseModel):
        pass

    file_tool = StructuredTool.from_function(
        name="read_file", func=lambda: "", description="Read a file from the filesystem", args_schema=DummyInput,
    )
    tool = build_tool_search_tool(available_tools=[file_tool])
    result = json.loads(tool.invoke({"query": "file", "max_results": 5}))
    names = [m["name"] for m in result["matches"]]
    assert "read_file" in names


def test_tool_search_select_by_name() -> None:
    from langchain_core.tools import StructuredTool
    from src.tools.session.tool_search import build_tool_search_tool
    from pydantic import BaseModel

    class DummyInput(BaseModel):
        pass

    t = StructuredTool.from_function(name="my_tool", func=lambda: "", description="Does things", args_schema=DummyInput)
    tool = build_tool_search_tool(available_tools=[t])
    result = json.loads(tool.invoke({"query": "select:my_tool"}))
    assert result["matches"][0]["name"] == "my_tool"


def test_tool_search_no_matches() -> None:
    from src.tools.session.tool_search import build_tool_search_tool
    tool = build_tool_search_tool(available_tools=[])
    result = json.loads(tool.invoke({"query": "zzznomatch"}))
    assert result["matches"] == []
