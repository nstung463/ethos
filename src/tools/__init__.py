"""Ethos tools.

Filesystem tools are sandboxed to the workspace root.
Web tools require TAVILY_API_KEY (search) or httpx (fetch).

Usage pattern:
    store = ToolStore()
    tools = [
        *build_filesystem_tools(),
        tavily_search, think_tool, web_fetch_tool,
        build_todo_write_tool(store),
        build_task_create_tool(store),
        ...
    ]
"""

# State store
from src.tools._store import TaskRecord, TaskStatus, ToolStore

# Filesystem
from src.tools.filesystem import build_filesystem_tools, build_notebook_edit_tool

# Web
from src.tools.web import tavily_search, think_tool, web_fetch_tool

# Todo
from src.tools.todo import build_todo_write_tool

# Task management
from src.tools.task import (
    build_task_create_tool,
    build_task_get_tool,
    build_task_list_tool,
    build_task_output_tool,
    build_task_stop_tool,
    build_task_update_tool,
)

# User interaction
from src.tools.interaction import (
    build_ask_user_tool,
    build_send_user_message_tool,
    structured_output_tool,
)

# Session utilities
from src.tools.session import build_config_tool, build_tool_search_tool, sleep_tool

# Agent orchestration
from src.tools.orchestration import (
    build_send_message_tool,
    build_skill_tool,
    build_team_create_tool,
    build_team_delete_tool,
)

__all__ = [
    # State store
    "ToolStore",
    "TaskStatus",
    "TaskRecord",
    # Filesystem
    "build_filesystem_tools",
    "build_notebook_edit_tool",
    # Web
    "tavily_search",
    "think_tool",
    "web_fetch_tool",
    # Todo
    "build_todo_write_tool",
    # Task management
    "build_task_create_tool",
    "build_task_get_tool",
    "build_task_list_tool",
    "build_task_output_tool",
    "build_task_stop_tool",
    "build_task_update_tool",
    # User interaction
    "build_ask_user_tool",
    "build_send_user_message_tool",
    "structured_output_tool",
    # Session utilities
    "sleep_tool",
    "build_config_tool",
    "build_tool_search_tool",
    # Orchestration
    "build_skill_tool",
    "build_send_message_tool",
    "build_team_create_tool",
    "build_team_delete_tool",
]
