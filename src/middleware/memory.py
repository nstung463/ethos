"""MemoryMiddleware — loads AGENTS.md once per session and injects it into the system prompt.

Pattern mirrors deepagents MemoryMiddleware:
- before_agent loads the file into state (runs once per session, skips if already loaded)
- modify_request wraps the content in <agent_memory> tags and appends to system message
- PrivateStateAttr marks memory_contents as private (not propagated to subagents)
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Annotated, NotRequired, TypedDict

from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
    ContextT,
    ModelRequest,
    ModelResponse,
    PrivateStateAttr,
    ResponseT,
)
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime

from src.middleware._utils import append_to_system_message

logger = logging.getLogger(__name__)

MEMORY_TEMPLATE = """<agent_memory>
{content}
</agent_memory>

<memory_guidelines>
The above <agent_memory> was loaded from AGENTS.md in your workspace.
It defines your role, rules, and accumulated knowledge.

- When the user asks you to remember something, update AGENTS.md immediately using
  edit_file or write_file — before responding.
- Capture WHY feedback was given, not just the surface correction.
- Never store API keys or credentials in memory files.
</memory_guidelines>"""


# ── State ──────────────────────────────────────────────────────────────────────

class MemoryState(AgentState):
    """Extends AgentState with loaded memory content.

    Marked Private so it is not propagated to subagents — each subagent
    should load its own memory if needed.
    """

    memory_contents: NotRequired[Annotated[str | None, PrivateStateAttr]]


class MemoryStateUpdate(TypedDict):
    memory_contents: str | None


# ── Middleware ─────────────────────────────────────────────────────────────────

class MemoryMiddleware(AgentMiddleware[MemoryState, ContextT, ResponseT]):
    """Loads AGENTS.md once per session and injects it into the system prompt.

    Placement: put this after SkillsMiddleware in the stack,
    so memory appears last in the system prompt (closest to the model call).
    """

    state_schema = MemoryState

    def __init__(self, agents_md_path: str = "./AGENTS.md") -> None:
        self.agents_md_path = agents_md_path

    def _load(self) -> str | None:
        path = Path(self.agents_md_path)
        if not path.exists():
            logger.debug("AGENTS.md not found at %s", self.agents_md_path)
            return None
        content = path.read_text(encoding="utf-8").strip()
        return content or None

    # ── Hooks ──────────────────────────────────────────────────────────────────

    def before_agent(  # type: ignore[override]
        self,
        state: MemoryState,
        runtime: Runtime,
        config: RunnableConfig,
    ) -> MemoryStateUpdate | None:
        """Load AGENTS.md into state (runs once; skips if already loaded)."""
        if "memory_contents" in state:
            return None
        content = self._load()
        if content:
            logger.debug("Loaded AGENTS.md from %s", self.agents_md_path)
        return MemoryStateUpdate(memory_contents=content)

    async def abefore_agent(  # type: ignore[override]
        self,
        state: MemoryState,
        runtime: Runtime,
        config: RunnableConfig,
    ) -> MemoryStateUpdate | None:
        if "memory_contents" in state:
            return None
        content = self._load()
        return MemoryStateUpdate(memory_contents=content)

    def modify_request(self, request: ModelRequest[ContextT]) -> ModelRequest[ContextT]:
        content: str | None = request.state.get("memory_contents")
        if not content:
            return request
        section = MEMORY_TEMPLATE.format(content=content)
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
