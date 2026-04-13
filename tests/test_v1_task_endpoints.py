"""Tests for POST /v1/tasks/title and POST /v1/tasks/follow-ups."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from starlette.testclient import TestClient

from src.api.app import create_app
from src.api.services.chat_tasks import FollowUpsTaskResult, TitleTaskResult


@pytest.fixture()
def client() -> TestClient:
    with TestClient(create_app()) as c:
        yield c


def _chat_body(*, model: str = "ethos") -> dict:
    return {
        "model": model,
        "messages": [
            {"role": "user", "content": "How do I reset my password?"},
        ],
    }


def test_tasks_title_returns_model_title(client: TestClient) -> None:
    with patch(
        "src.api.routes.v1.generate_title_task",
        new_callable=AsyncMock,
        return_value=TitleTaskResult(title="Password reset help"),
    ):
        r = client.post("/v1/tasks/title", json=_chat_body())
    assert r.status_code == 200
    assert r.json() == {"title": "Password reset help"}


def test_tasks_title_strips_whitespace(client: TestClient) -> None:
    with patch(
        "src.api.routes.v1.generate_title_task",
        new_callable=AsyncMock,
        return_value=TitleTaskResult(title="  Trimmed title  "),
    ):
        r = client.post("/v1/tasks/title", json=_chat_body())
    assert r.status_code == 200
    assert r.json() == {"title": "Trimmed title"}


def test_tasks_title_fallback_on_empty_title(client: TestClient) -> None:
    with patch(
        "src.api.routes.v1.generate_title_task",
        new_callable=AsyncMock,
        return_value=TitleTaskResult(title="   "),
    ):
        r = client.post("/v1/tasks/title", json=_chat_body())
    assert r.status_code == 200
    body = r.json()
    assert "title" in body
    assert body["title"] == "How do I reset my password?"


def test_tasks_title_fallback_on_exception(client: TestClient) -> None:
    with patch(
        "src.api.routes.v1.generate_title_task",
        new_callable=AsyncMock,
        side_effect=RuntimeError("LLM unavailable"),
    ):
        r = client.post("/v1/tasks/title", json=_chat_body())
    assert r.status_code == 200
    assert r.json() == {"title": "How do I reset my password?"}


def test_tasks_follow_ups_returns_list(client: TestClient) -> None:
    follow_ups = ["What about 2FA?", "Can I use SSO?", "Where are logs?"]
    with patch(
        "src.api.routes.v1.generate_follow_ups_task",
        new_callable=AsyncMock,
        return_value=FollowUpsTaskResult(follow_ups=follow_ups),
    ):
        r = client.post("/v1/tasks/follow-ups", json=_chat_body())
    assert r.status_code == 200
    assert r.json() == {"follow_ups": follow_ups}


def test_tasks_follow_ups_empty_on_exception(client: TestClient) -> None:
    with patch(
        "src.api.routes.v1.generate_follow_ups_task",
        new_callable=AsyncMock,
        side_effect=RuntimeError("LLM unavailable"),
    ):
        r = client.post("/v1/tasks/follow-ups", json=_chat_body())
    assert r.status_code == 200
    assert r.json() == {"follow_ups": []}


def test_tasks_unknown_model_404(client: TestClient) -> None:
    body = _chat_body(model="nonexistent-model-xyz")
    r = client.post("/v1/tasks/title", json=body)
    assert r.status_code == 404


def test_tasks_forward_user_api_keys_from_metadata(client: TestClient) -> None:
    body = _chat_body()
    body["metadata"] = {
        "user_api_keys": {
            "openrouter": "sk-or-v1-test",
            "anthropic": "sk-ant-test",
            "openai": "sk-openai-test",
        }
    }

    with patch(
        "src.api.routes.v1.generate_title_task",
        new_callable=AsyncMock,
        return_value=TitleTaskResult(title="Password reset help"),
    ) as mocked_task:
        r = client.post("/v1/tasks/title", json=body)

    assert r.status_code == 200
    _, kwargs = mocked_task.await_args
    assert kwargs["model_id"] == "ethos"
    assert [message.model_dump() for message in kwargs["messages"]] == body["messages"]
    assert kwargs["api_keys"] == {
        "openrouter": "sk-or-v1-test",
        "anthropic": "sk-ant-test",
        "openai": "sk-openai-test",
    }
