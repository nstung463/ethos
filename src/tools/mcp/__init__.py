"""MCP tools and builders."""

from __future__ import annotations

from src.config import MCPServerSpec
from src.tools.mcp.auth import build_auth_tools
from src.tools.mcp.client import MCPRuntime
from src.tools.mcp.mcp_tool import build_mcp_tool
from src.tools.mcp.resources import (
    build_list_mcp_resources_tool,
    build_read_mcp_resource_tool,
)


def build_mcp_tools(servers: list[MCPServerSpec] | None = None) -> list:
    runtime = MCPRuntime(servers or [])
    return [
        build_mcp_tool(runtime),
        build_list_mcp_resources_tool(runtime),
        build_read_mcp_resource_tool(runtime),
        *build_auth_tools(runtime),
    ]


__all__ = [
    "MCPRuntime",
    "build_mcp_tool",
    "build_list_mcp_resources_tool",
    "build_read_mcp_resource_tool",
    "build_auth_tools",
    "build_mcp_tools",
]
