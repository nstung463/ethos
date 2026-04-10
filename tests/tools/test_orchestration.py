"""Tests for orchestration tools: skill, send_message, team_create, team_delete."""
from __future__ import annotations

import json


def test_skill_invokes_registered_skill() -> None:
    from src.tools.orchestration.skill import build_skill_tool
    tool = build_skill_tool(skill_runner=lambda name, args: f"ran:{name}:{args}")
    result = tool.invoke({"skill": "my-skill", "args": "some args"})
    assert result == "ran:my-skill:some args"


def test_skill_missing_skill() -> None:
    from src.tools.orchestration.skill import build_skill_tool
    def failing_runner(name: str, args: str) -> str:
        raise FileNotFoundError(f"Skill '{name}' not found")
    tool = build_skill_tool(skill_runner=failing_runner)
    result = tool.invoke({"skill": "nope", "args": ""})
    assert "not found" in result.lower() or "error" in result.lower()


def test_send_message_delivers_to_recipient() -> None:
    from src.tools.orchestration.send_message import build_send_message_tool
    mailbox: dict[str, list] = {}
    def deliver(to: str, content: str) -> None:
        mailbox.setdefault(to, []).append(content)
    tool = build_send_message_tool(deliver_fn=deliver)
    result = json.loads(tool.invoke({"to": "agent-2", "content": "hello there"}))
    assert result["delivered"] is True
    assert mailbox["agent-2"] == ["hello there"]


def test_send_message_returns_ack() -> None:
    from src.tools.orchestration.send_message import build_send_message_tool
    tool = build_send_message_tool(deliver_fn=lambda to, content: None)
    result = json.loads(tool.invoke({"to": "team-lead", "content": "done"}))
    assert "delivered" in result


def test_team_create_registers_team() -> None:
    from src.tools.orchestration.team_create import build_team_create_tool
    registry: dict = {}
    tool = build_team_create_tool(registry=registry)
    result = json.loads(tool.invoke({"name": "my-team", "description": "A research team"}))
    assert result["created"] is True
    assert "my-team" in registry


def test_team_delete_removes_team() -> None:
    from src.tools.orchestration.team_delete import build_team_delete_tool
    registry = {"my-team": {"name": "my-team"}}
    tool = build_team_delete_tool(registry=registry)
    result = json.loads(tool.invoke({"name": "my-team"}))
    assert result["deleted"] is True
    assert "my-team" not in registry


def test_team_delete_missing_team() -> None:
    from src.tools.orchestration.team_delete import build_team_delete_tool
    tool = build_team_delete_tool(registry={})
    result = tool.invoke({"name": "ghost-team"})
    assert "not found" in result.lower()
