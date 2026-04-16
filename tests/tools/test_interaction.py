"""Tests for user interaction tools."""
from __future__ import annotations

import json


def test_ask_user_single_select() -> None:
    from src.ai.tools.interaction.ask_user import build_ask_user_tool

    tool = build_ask_user_tool(input_fn=lambda q: "0")
    result = json.loads(tool.invoke({
        "questions": [{
            "question": "Pick one?",
            "header": "Choice",
            "options": [
                {"label": "A", "description": "Option A"},
                {"label": "B", "description": "Option B"},
            ]
        }]
    }))
    assert result["answers"]["Pick one?"] == "A"


def test_ask_user_multi_select() -> None:
    from src.ai.tools.interaction.ask_user import build_ask_user_tool

    tool = build_ask_user_tool(input_fn=lambda q: "0,1")
    result = json.loads(tool.invoke({
        "questions": [{
            "question": "Pick all?",
            "header": "Multi",
            "options": [
                {"label": "X", "description": "Option X"},
                {"label": "Y", "description": "Option Y"},
                {"label": "Z", "description": "Option Z"},
            ],
            "multi_select": True,
        }]
    }))
    assert result["answers"]["Pick all?"] == "X,Y"


def test_structured_output_returns_json_string() -> None:
    from src.ai.tools.interaction.structured_output import structured_output_tool
    data = {"name": "test", "value": 42}
    result = structured_output_tool.invoke(data)
    assert json.loads(result) == data


def test_structured_output_nested() -> None:
    from src.ai.tools.interaction.structured_output import structured_output_tool
    data = {"items": [1, 2, 3], "meta": {"count": 3}}
    result = structured_output_tool.invoke(data)
    assert json.loads(result)["items"] == [1, 2, 3]


def test_send_user_message_returns_ack() -> None:
    from src.ai.tools.interaction.send_user_message import build_send_user_message_tool

    received = []
    tool = build_send_user_message_tool(output_fn=received.append)
    result = tool.invoke({"message": "Hello from agent"})
    assert received == ["Hello from agent"]
    assert result == "Message sent."

