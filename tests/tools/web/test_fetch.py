"""Tests for web_fetch tool — uses httpx mock."""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock


def _make_response(status=200, text="<html><body><p>Hello world</p></body></html>", headers=None):
    resp = MagicMock()
    resp.status_code = status
    resp.reason_phrase = "OK" if status == 200 else "Not Found"
    resp.text = text
    resp.content = text.encode()
    resp.headers = headers or {"content-type": "text/html"}
    return resp


def test_fetch_returns_content() -> None:
    with patch("src.tools.web.fetch.httpx") as mock_httpx:
        mock_httpx.get.return_value = _make_response()
        from src.tools.web.fetch import web_fetch_tool
        result = web_fetch_tool.invoke({"url": "https://example.com", "prompt": "what is this?"})
        assert "Hello world" in result
        mock_httpx.get.assert_called_once()


def test_fetch_http_error() -> None:
    with patch("src.tools.web.fetch.httpx") as mock_httpx:
        mock_httpx.get.return_value = _make_response(status=404, text="Not Found")
        from src.tools.web.fetch import web_fetch_tool
        result = web_fetch_tool.invoke({"url": "https://example.com/missing", "prompt": "content"})
        assert "404" in result


def test_fetch_network_error() -> None:
    import httpx as real_httpx
    with patch("src.tools.web.fetch.httpx") as mock_httpx:
        mock_httpx.get.side_effect = Exception("refused")
        from src.tools.web.fetch import web_fetch_tool
        result = web_fetch_tool.invoke({"url": "https://example.com", "prompt": "x"})
        assert "error" in result.lower() or "failed" in result.lower() or "refused" in result.lower()


def test_fetch_includes_prompt_hint() -> None:
    with patch("src.tools.web.fetch.httpx") as mock_httpx:
        mock_httpx.get.return_value = _make_response(text="<html><body>Content</body></html>")
        from src.tools.web.fetch import web_fetch_tool
        result = web_fetch_tool.invoke({"url": "https://example.com", "prompt": "find the title"})
        assert "find the title" in result


def test_strip_html_removes_tags() -> None:
    from src.tools.web.fetch import _strip_html
    result = _strip_html("<h1>Title</h1><p>Body text</p>")
    assert "Title" in result
    assert "Body text" in result
    assert "<h1>" not in result
    assert "<p>" not in result


def test_strip_html_removes_scripts() -> None:
    from src.tools.web.fetch import _strip_html
    result = _strip_html("<script>alert('x')</script><p>Hello</p>")
    assert "alert" not in result
    assert "Hello" in result


def test_strip_html_decodes_entities() -> None:
    from src.tools.web.fetch import _strip_html
    result = _strip_html("&amp; &lt; &gt; &nbsp;")
    assert "&" in result
    assert "<" in result
    assert ">" in result
