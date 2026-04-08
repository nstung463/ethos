"""TodosMiddleware — manages a todo list in agent state and injects it into the system prompt.

Pattern mirrors deepagents TodoListMiddleware:
- self.tools exposes the write_todos tool to the agent
- modify_request injects the current todos list into the system message before each LLM call
- state_schema registers the `todos` key so create_agent knows about it
"""

from collections.abc import Awaitable, Callable
from typing import Any, NotRequired

from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
    ContextT,
    ModelRequest,
    ModelResponse,
    ResponseT,
)
from langchain_core.tools import StructuredTool
from langgraph.types import Command
from pydantic import BaseModel, Field

from src.middleware._utils import append_to_system_message


# ── State ──────────────────────────────────────────────────────────────────────

class TodosState(AgentState):
    """Extends AgentState with a todos list."""

    todos: NotRequired[list[str]]


# ── Tool ───────────────────────────────────────────────────────────────────────

class WriteTodosInput(BaseModel):
    todos: list[str] = Field(
        description=(
            "The COMPLETE updated todo list. Each item is a short, actionable task description. "
            "Pass an empty list to clear all todos. This replaces the current list entirely."
        )
    )


def _write_todos(todos: list[str]) -> Command:
    """Update todos in agent state."""
    return Command(update={"todos": todos})


_WRITE_TODOS_TOOL = StructuredTool.from_function(
    name="write_todos",
    func=_write_todos,
    description=(
        "Manage your task list. Use at the start of complex tasks to plan steps, "
        "and update as you complete them. Pass the COMPLETE updated list each call — "
        "it replaces the current todos entirely. Pass [] to clear."
    ),
    args_schema=WriteTodosInput,
)


# ── Middleware ─────────────────────────────────────────────────────────────────

class TodosMiddleware(AgentMiddleware[TodosState, ContextT, ResponseT]):
    """Injects the current todo list into the system prompt before each model call.

    Also exposes the ``write_todos`` tool so the agent can update the list.

    Placement: put this early in the middleware stack so other middleware
    (memory, skills) can see the todo-augmented system message.
    """

    state_schema = TodosState

    def __init__(self) -> None:
        self.tools = [_WRITE_TODOS_TOOL]

    def modify_request(self, request: ModelRequest[ContextT]) -> ModelRequest[ContextT]:
        todos: list[str] = request.state.get("todos") or []
        if not todos:
            return request

        items = "\n".join(f"- [ ] {t}" for t in todos)
        section = f"\n\n## Current Todos\n\n{items}"
        new_sys = append_to_system_message(request.system_message, section)
        return request.override(system_message=new_sys)

    def wrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], ModelResponse[ResponseT]],
    ) -> ModelResponse[ResponseT]:
        return handler(self.modify_request(request))

    async def awrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], Awaitable[ModelResponse[ResponseT]]],
    ) -> ModelResponse[ResponseT]:
        return await handler(self.modify_request(request))
