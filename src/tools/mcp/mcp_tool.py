"""Generic MCP tool invocation wrapper."""

from __future__ import annotations

from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.tools.mcp.client import MCPRuntime


class MCPToolInput(BaseModel):
    server: str = Field(description="Configured MCP server name.")
    tool: str = Field(description="MCP tool name exposed by the target server.")
    arguments: dict[str, Any] | None = Field(
        default=None,
        description="JSON object of arguments passed to the MCP tool.",
    )


def build_mcp_tool(runtime: MCPRuntime) -> StructuredTool:
    def _mcp(server: str, tool: str, arguments: dict[str, Any] | None = None) -> str:
        return runtime.invoke_tool(server=server, tool=tool, arguments=arguments)

    return StructuredTool.from_function(
        name="mcp",
        func=_mcp,
        description=(
            "Invoke a tool exposed by a configured MCP server. "
            "Use when a capability already exists behind MCP instead of rebuilding it natively."
        ),
        args_schema=MCPToolInput,
    )
