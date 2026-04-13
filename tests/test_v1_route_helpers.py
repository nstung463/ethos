from __future__ import annotations

from src.api.models.chat import ChatRequest, Message
from src.api.routes.v1 import _extract_file_ids, _extract_user_api_keys, _resolve_session_id


def test_extract_file_ids_supports_openwebui_files_shape() -> None:
    request = ChatRequest(
        model="ethos",
        messages=[Message(role="user", content="hi")],
        file_ids=["a"],
        files=[
            {"id": "b"},
            {"file": {"id": "c"}},
            {"id": "a"},
        ],
        metadata={"file_ids": ["d", "c"]},
    )

    assert _extract_file_ids(request) == ["a", "b", "c", "d"]


def test_resolve_session_id_prefers_session_id_then_chat_id_then_metadata() -> None:
    request = ChatRequest(
        model="ethos",
        messages=[Message(role="user", content="hi")],
        session_id="session-1",
        chat_id="chat-1",
        metadata={"conversation_id": "conv-1"},
    )
    assert _resolve_session_id(request) == "session-1"

    request = ChatRequest(
        model="ethos",
        messages=[Message(role="user", content="hi")],
        chat_id="chat-2",
    )
    assert _resolve_session_id(request) == "chat-2"

    request = ChatRequest(
        model="ethos",
        messages=[Message(role="user", content="hi")],
        metadata={"conversation_id": "conv-3"},
    )
    assert _resolve_session_id(request) == "conv-3"


def test_extract_user_api_keys_reads_only_expected_string_values() -> None:
    request = ChatRequest(
        model="ethos",
        messages=[Message(role="user", content="hi")],
        metadata={
            "user_api_keys": {
                "openrouter": " sk-or-v1-test ",
                "anthropic": "sk-ant-test",
                "openai": 123,
                "ignored": "value",
            }
        },
    )

    assert _extract_user_api_keys(request) == {
        "openrouter": "sk-or-v1-test",
        "anthropic": "sk-ant-test",
    }
