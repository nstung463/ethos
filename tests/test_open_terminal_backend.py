"""Tests for OpenTerminalBackend."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
import httpx
import pytest

from src.backends.open_terminal import OpenTerminalBackend, _join_output


# ── Helper: Create proper responses ────────────────────────────────────────


def _make_response(
    status_code: int,
    json_data: dict | None = None,
    content: bytes | None = None,
    headers: dict | None = None,
) -> httpx.Response:
    """Create a proper httpx.Response object for testing."""
    request = httpx.Request("POST", "http://localhost:8000/test")
    response = httpx.Response(
        status_code,
        request=request,
        json=json_data,
        content=content,
        headers=headers or {},
    )
    return response


# ── Tests: _join_output() ──────────────────────────────────────────────────


def test_join_output_single_entry():
    """Test joining a single log entry."""
    entries = [{"type": "stdout", "data": "hello"}]
    assert _join_output(entries) == "hello"


def test_join_output_multiple_entries():
    """Test joining multiple log entries."""
    entries = [
        {"type": "stdout", "data": "line1\n"},
        {"type": "stdout", "data": "line2\n"},
    ]
    assert _join_output(entries) == "line1\nline2\n"


def test_join_output_mixed_types():
    """Test joining stdout and stderr."""
    entries = [
        {"type": "stdout", "data": "out"},
        {"type": "stderr", "data": "err"},
    ]
    assert _join_output(entries) == "outerr"


def test_join_output_empty_list():
    """Test joining empty list of entries."""
    assert _join_output([]) == ""


def test_join_output_missing_data_field():
    """Test handling of entries without 'data' field."""
    entries = [
        {"type": "stdout"},
        {"type": "stderr", "data": "error"},
    ]
    assert _join_output(entries) == "error"


# ── Tests: Backend initialization ──────────────────────────────────────────


def test_backend_initialization():
    """Test OpenTerminalBackend initialization."""
    with patch("src.backends.open_terminal.httpx.Client"):
        backend = OpenTerminalBackend(
            base_url="http://localhost:8000",
            api_key="test-key",
        )
        assert backend._api_key == "test-key"
        assert backend._base_url == "http://localhost:8000"
        assert "open-terminal" in backend.id


def test_backend_with_user_id():
    """Test that user_id is passed to headers."""
    with patch("src.backends.open_terminal.httpx.Client") as mock_client_class:
        backend = OpenTerminalBackend(
            base_url="http://localhost:8000",
            api_key="key",
            user_id="user-123",
        )
        # Check that Client was initialized with X-User-Id header
        call_kwargs = mock_client_class.call_args[1]
        assert "X-User-Id" in call_kwargs["headers"]
        assert call_kwargs["headers"]["X-User-Id"] == "user-123"


def test_backend_id_stable():
    """Test that backend ID is stable."""
    with patch("src.backends.open_terminal.httpx.Client"):
        backend = OpenTerminalBackend(api_key="key")
        id1 = backend.id
        id2 = backend.id
        assert id1 == id2
        assert "open-terminal" in id1


# ── Tests: execute() ──────────────────────────────────────────────────────


def test_execute_success():
    """Test successful command execution."""
    with patch("src.backends.open_terminal.httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock successful execution
        mock_client.post.return_value = _make_response(
            200,
            json_data={
                "id": "proc-1",
                "status": "done",
                "exit_code": 0,
                "output": [{"type": "stdout", "data": "hello world"}],
                "truncated": False,
                "next_offset": 1,
            },
        )

        backend = OpenTerminalBackend(api_key="key")
        backend._client = mock_client
        result = backend.execute("echo hello")

        assert result.exit_code == 0
        assert "hello world" in result.output
        assert result.truncated is False


def test_execute_with_timeout():
    """Test execute with custom timeout."""
    with patch("src.backends.open_terminal.httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.post.return_value = _make_response(
            200,
            json_data={
                "id": "proc",
                "status": "done",
                "exit_code": 0,
                "output": [],
                "truncated": False,
                "next_offset": 0,
            },
        )

        backend = OpenTerminalBackend(api_key="key")
        backend._client = mock_client
        result = backend.execute("test", timeout=60)

        assert result.exit_code == 0
        # Verify timeout was passed to post
        call_kwargs = mock_client.post.call_args[1]
        assert call_kwargs["params"]["wait"] == 60


def test_execute_max_timeout_capped():
    """Test that timeout is capped at 300."""
    with patch("src.backends.open_terminal.httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.post.return_value = _make_response(
            200,
            json_data={
                "id": "proc",
                "status": "done",
                "exit_code": 0,
                "output": [],
                "truncated": False,
                "next_offset": 0,
            },
        )

        backend = OpenTerminalBackend(api_key="key")
        backend._client = mock_client
        backend.execute("test", timeout=400)

        # Should use 300, not 400
        call_kwargs = mock_client.post.call_args[1]
        assert call_kwargs["params"]["wait"] == 300


def test_execute_polls_when_running():
    """Test that execute polls when process is still running."""
    with patch("src.backends.open_terminal.httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # First call: running
        mock_client.post.return_value = _make_response(
            200,
            json_data={
                "id": "proc-slow",
                "status": "running",
                "exit_code": None,
                "output": [{"type": "stdout", "data": "part1\n"}],
                "truncated": False,
                "next_offset": 1,
            },
        )

        # Polling call: done
        mock_client.get.return_value = _make_response(
            200,
            json_data={
                "id": "proc-slow",
                "status": "done",
                "exit_code": 0,
                "output": [{"type": "stdout", "data": "part2\n"}],
                "truncated": False,
                "next_offset": 2,
            },
        )

        backend = OpenTerminalBackend(api_key="key")
        backend._client = mock_client
        result = backend.execute("slow_cmd")

        assert result.exit_code == 0
        assert "part1" in result.output
        assert "part2" in result.output
        assert mock_client.get.called  # Should have polled


def test_execute_timeout_error():
    """Test execute handles timeout errors."""
    with patch("src.backends.open_terminal.httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.post.side_effect = httpx.TimeoutException("timeout")

        backend = OpenTerminalBackend(api_key="key")
        backend._client = mock_client
        result = backend.execute("test")

        assert result.exit_code == 1
        assert "timed out" in result.output.lower()


def test_execute_http_error():
    """Test execute handles HTTP errors."""
    with patch("src.backends.open_terminal.httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        request = httpx.Request("POST", "http://test")
        mock_client.post.side_effect = httpx.HTTPStatusError(
            "403",
            request=request,
            response=_make_response(403),
        )

        backend = OpenTerminalBackend(api_key="key")
        backend._client = mock_client
        result = backend.execute("test")

        assert result.exit_code == 1
        assert "HTTP" in result.output or "error" in result.output.lower()


# ── Tests: upload_files() ──────────────────────────────────────────────────


def test_upload_files_success():
    """Test successful file upload."""
    with patch("src.backends.open_terminal.httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.post.return_value = _make_response(
            200,
            json_data={"path": "/test.txt", "size": 11},
        )

        backend = OpenTerminalBackend(api_key="key")
        backend._client = mock_client

        responses = backend.upload_files([("/test.txt", b"hello world")])

        assert len(responses) == 1
        assert responses[0].path == "/test.txt"
        assert responses[0].error is None


def test_upload_files_error():
    """Test file upload error handling."""
    with patch("src.backends.open_terminal.httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        request = httpx.Request("POST", "http://test")
        mock_client.post.side_effect = httpx.HTTPStatusError(
            "500",
            request=request,
            response=_make_response(500),
        )

        backend = OpenTerminalBackend(api_key="key")
        backend._client = mock_client

        responses = backend.upload_files([("/test.txt", b"data")])

        assert len(responses) == 1
        assert responses[0].error is not None


def test_upload_files_binary_content():
    """Test that binary content is safely decoded."""
    with patch("src.backends.open_terminal.httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.post.return_value = _make_response(
            200,
            json_data={"path": "/test", "size": 5},
        )

        backend = OpenTerminalBackend(api_key="key")
        backend._client = mock_client

        # Non-UTF8 bytes should be handled gracefully
        responses = backend.upload_files([("/test", b"\x80\x81\x82")])

        assert len(responses) == 1
        assert responses[0].error is None


# ── Tests: download_files() ────────────────────────────────────────────────


def test_download_files_success():
    """Test successful file download."""
    with patch("src.backends.open_terminal.httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get.return_value = _make_response(
            200,
            json_data={"path": "/test.txt", "content": "hello"},
            headers={"content-type": "application/json"},
        )

        backend = OpenTerminalBackend(api_key="key")
        backend._client = mock_client

        responses = backend.download_files(["/test.txt"])

        assert len(responses) == 1
        assert responses[0].path == "/test.txt"
        assert responses[0].content == b"hello"
        assert responses[0].error is None


def test_download_files_not_found():
    """Test handling of missing files."""
    with patch("src.backends.open_terminal.httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get.return_value = _make_response(404)

        backend = OpenTerminalBackend(api_key="key")
        backend._client = mock_client

        responses = backend.download_files(["/missing.txt"])

        assert len(responses) == 1
        assert responses[0].error == "file_not_found"
        assert responses[0].content is None


def test_download_files_binary():
    """Test handling of binary file responses."""
    with patch("src.backends.open_terminal.httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        png_bytes = b"\x89PNG\r\n\x1a\n"
        mock_client.get.return_value = _make_response(
            200,
            content=png_bytes,
            headers={"content-type": "image/png"},
        )

        backend = OpenTerminalBackend(api_key="key")
        backend._client = mock_client

        responses = backend.download_files(["/image.png"])

        assert len(responses) == 1
        assert responses[0].content == png_bytes
        assert responses[0].error is None


def test_download_files_http_error():
    """Test error handling when download fails."""
    with patch("src.backends.open_terminal.httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        request = httpx.Request("GET", "http://test")
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "500",
            request=request,
            response=_make_response(500),
        )

        backend = OpenTerminalBackend(api_key="key")
        backend._client = mock_client

        responses = backend.download_files(["/test.txt"])

        assert len(responses) == 1
        assert responses[0].error is not None


# ── Tests: Cleanup ─────────────────────────────────────────────────────────


def test_backend_closes_client():
    """Test that HTTP client is closed on deletion."""
    with patch("src.backends.open_terminal.httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        backend = OpenTerminalBackend(api_key="key")
        del backend

        mock_client.close.assert_called()
