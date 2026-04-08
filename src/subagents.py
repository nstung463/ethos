"""Subagent specs and task tool builder.

Each subagent is a plain TypedDict-compatible dict:
  {name, description, system_prompt, tools?}

build_task_tool() compiles them into agents via create_agent and
exposes a single `task` tool for the main agent to delegate work.

Pattern mirrors deepagents SubAgentMiddleware but implemented from scratch
using create_agent + ToolRuntime + Command.
"""

from typing import Any

from langchain.agents import create_agent
from langchain.tools import ToolRuntime
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import BaseTool, StructuredTool
from langgraph.types import Command
from pydantic import BaseModel, Field

from src.prompts import ANALYST_PROMPT, CODER_PROMPT, PLANNER_PROMPT, RESEARCHER_PROMPT
from src.tools.web import tavily_search, think_tool


# ── Subagent specs ─────────────────────────────────────────────────────────────

PLANNER: dict[str, Any] = {
    "name": "planner",
    "description": (
        "Break down a complex task into clear, ordered, actionable steps. "
        "Use before acting on multi-part requests."
    ),
    "system_prompt": PLANNER_PROMPT,
    "tools": [],
}

RESEARCHER: dict[str, Any] = {
    "name": "researcher",
    "description": (
        "Gather current, accurate information from the web on a specific topic. "
        "Use for research requiring up-to-date knowledge outside the codebase."
    ),
    "system_prompt": RESEARCHER_PROMPT,
    "tools": [tavily_search, think_tool],
}

CODER: dict[str, Any] = {
    "name": "coder",
    "description": (
        "Implement, debug, or refactor code in isolation. "
        "Use for focused coding tasks that would bloat the main context."
    ),
    "system_prompt": CODER_PROMPT,
    # tools=None → inherits base_tools (filesystem + web) from build_task_tool
}

ANALYST: dict[str, Any] = {
    "name": "analyst",
    "description": (
        "Analyze code, data, logs, or documents and return structured insights. "
        "Use when you need a thorough analysis report."
    ),
    "system_prompt": ANALYST_PROMPT,
    "tools": [think_tool],
}

DEFAULT_SUBAGENTS: list[dict[str, Any]] = [PLANNER, RESEARCHER, CODER, ANALYST]


# ── Task tool ──────────────────────────────────────────────────────────────────

TASK_DESCRIPTION = """Launch an ephemeral subagent to handle a complex, isolated task.

Available subagent types:
{available_agents}

Usage notes:
- Provide ALL context in the description — subagents are stateless.
- Launch multiple in parallel when tasks are independent (send multiple tool calls in one message).
- The subagent returns a single final message. Summarize it for the user.
- Use for tasks that are complex, multi-step, or that benefit from isolated context."""


class TaskInput(BaseModel):
    description: str = Field(
        description=(
            "Detailed task description for the subagent. "
            "Include all necessary context and specify the expected output format."
        )
    )
    subagent_type: str = Field(
        description="Subagent to use. Must be one of the available types listed above."
    )


def build_task_tool(
    model: BaseChatModel,
    subagents: list[dict[str, Any]],
    base_tools: list[BaseTool] | None = None,
) -> StructuredTool:
    """Compile subagent specs into agents and return a `task` tool.

    Args:
        model: LLM shared across all subagents (can be overridden per spec).
        subagents: List of subagent spec dicts.
        base_tools: Default tools given to subagents that don't specify their own.
    """
    base_tools = base_tools or []

    # Compile each spec into a runnable agent
    agents: dict[str, Any] = {}
    for spec in subagents:
        tools = spec.get("tools", base_tools)
        subagent_model = spec.get("model", model)
        agents[spec["name"]] = create_agent(
            model=subagent_model,
            tools=tools,
            system_prompt=spec["system_prompt"],
            name=spec["name"],
        )

    agents_desc = "\n".join(f"- {s['name']}: {s['description']}" for s in subagents)
    description = TASK_DESCRIPTION.format(available_agents=agents_desc)

    def task(
        description: str,
        subagent_type: str,
        runtime: ToolRuntime,
    ) -> Command:
        tool_call_id = runtime.tool_call_id or "unknown"

        if subagent_type not in agents:
            allowed = ", ".join(f"`{k}`" for k in agents)
            return Command(
                update={
                    "messages": [
                        ToolMessage(
                            content=f"Unknown subagent '{subagent_type}'. Allowed: {allowed}",
                            tool_call_id=tool_call_id,
                        )
                    ]
                }
            )

        result = agents[subagent_type].invoke(
            {"messages": [HumanMessage(content=description)]}
        )

        last = result["messages"][-1]
        content = getattr(last, "content", str(last))
        if isinstance(content, list):
            content = " ".join(
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in content
            ).strip()

        return Command(
            update={"messages": [ToolMessage(content=content, tool_call_id=tool_call_id)]}
        )

    return StructuredTool.from_function(
        name="task",
        func=task,
        description=description,
        args_schema=TaskInput,
    )
