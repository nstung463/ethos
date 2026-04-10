# tests/tools/web/test_search.py
"""Tests for tavily_search tool — stubs only (no real API)."""
from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock, patch


def test_search_missing_api_key(monkeypatch) -> None:
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    from src.tools.web.search import tavily_search
    result = tavily_search.invoke({"query": "test"})
    assert "TAVILY_API_KEY" in result


def test_search_no_results(monkeypatch) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "fake-key")
    fake_client = MagicMock()
    fake_client.search.return_value = {"results": []}
    fake_tavily = types.ModuleType("tavily")
    fake_tavily.TavilyClient = MagicMock(return_value=fake_client)
    with patch.dict(sys.modules, {"tavily": fake_tavily}):
        from importlib import reload
        import src.tools.web.search as m
        reload(m)
        result = m._search("nothing")
        assert "No results" in result
