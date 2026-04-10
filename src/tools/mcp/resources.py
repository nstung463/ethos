"""MCP resource tools."""

from __future__ import annotations

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.tools.mcp.client import MCPRuntime


class ListMCPResourcesInput(BaseModel):
    server: str | None = Field(
        default=None,
        description="Optional MCP server name. When omitted, list resources across all configured servers.",
    )


class ReadMCPResourceInput(BaseModel):
    server: str = Field(description="Configured MCP server name.")
    uri: str = Field(description="Resource URI to read from the MCP server.")


def build_list_mcp_resources_tool(runtime: MCPRuntime) -> StructuredTool:
    def _list(server: str | None = None) -> str:
        return runtime.list_resources(server=server)

    return StructuredTool.from_function(
        name="list_mcp_resources",
        func=_list,
        description="List resources available from configured MCP servers.",
        args_schema=ListMCPResourcesInput,
    )


def build_read_mcp_resource_tool(runtime: MCPRuntime) -> StructuredTool:
    def _read(server: str, uri: str) -> str:
        return runtime.read_resource(server=server, uri=uri)

    return StructuredTool.from_function(
        name="read_mcp_resource",
        func=_read,
        description="Read a resource from a configured MCP server.",
        args_schema=ReadMCPResourceInput,
    )
