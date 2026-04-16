"""Dynamic MCP auth tools."""

from __future__ import annotations

import json

from langchain_core.tools import StructuredTool
from pydantic import BaseModel

from src.ai.tools.mcp.client import MCPRuntime


class _NoArgs(BaseModel):
    pass


def build_auth_tools(runtime: MCPRuntime) -> list[StructuredTool]:
    tools: list[StructuredTool] = []
    for server in runtime.server_names:
        auth_url = runtime.auth_url_for(server)
        if not auth_url:
            continue

        def _authenticate(_server: str = server, _auth_url: str = auth_url) -> str:
            return json.dumps(
                {
                    "server": _server,
                    "auth_url": _auth_url,
                    "status": "authentication_required",
                }
            )

        tools.append(
            StructuredTool.from_function(
                name=f"mcp__{server}__authenticate",
                func=_authenticate,
                description=f"Return the authentication URL for MCP server '{server}'.",
                args_schema=_NoArgs,
            )
        )
    return tools

