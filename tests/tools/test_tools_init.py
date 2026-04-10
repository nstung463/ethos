"""Smoke test: all tool builders importable from src.tools."""
from __future__ import annotations


def test_all_tools_importable() -> None:
    from src.tools import (
        # Store
        ToolStore, TaskStatus, TaskRecord,
        # Filesystem
        build_filesystem_tools, build_notebook_edit_tool,
        # Web
        tavily_search, think_tool, web_fetch_tool,
        # Todo
        build_todo_write_tool,
        # Task
        build_task_create_tool, build_task_get_tool, build_task_list_tool,
        build_task_output_tool, build_task_stop_tool, build_task_update_tool,
        # Interaction
        build_ask_user_tool, build_send_user_message_tool, structured_output_tool,
        # Session
        sleep_tool, build_config_tool, build_tool_search_tool,
        # Orchestration
        build_skill_tool, build_send_message_tool, build_team_create_tool, build_team_delete_tool,
    )
    # If we got here, all imports succeeded
    assert True


def test_build_all_stateful_tools() -> None:
    from src.tools import (
        ToolStore,
        build_todo_write_tool,
        build_task_create_tool, build_task_get_tool, build_task_list_tool,
        build_task_output_tool, build_task_stop_tool, build_task_update_tool,
        build_config_tool, build_tool_search_tool,
    )

    store = ToolStore()
    tools = [
        build_todo_write_tool(store),
        build_task_create_tool(store),
        build_task_get_tool(store),
        build_task_list_tool(store),
        build_task_update_tool(store),
        build_task_stop_tool(store),
        build_task_output_tool(store),
        build_config_tool(),
        build_tool_search_tool([]),
    ]
    assert len(tools) == 9
    for t in tools:
        assert t.name is not None


def test_web_fetch_importable_from_root() -> None:
    from src.tools import web_fetch_tool
    assert web_fetch_tool.name == "web_fetch"


def test_store_importable_from_root() -> None:
    from src.tools import ToolStore, TaskStatus
    store = ToolStore()
    task = store.create_task(subject="Test", description="desc")
    assert task.status == TaskStatus.PENDING
