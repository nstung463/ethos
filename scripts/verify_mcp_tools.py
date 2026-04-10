"""Utility script to verify Ethos MCP tool wiring.

Examples:
  python scripts/verify_mcp_tools.py --print-example-env
  python scripts/verify_mcp_tools.py --print-memory-filesystem-env
  python scripts/verify_mcp_tools.py --print-memory-filesystem-env --allowed-path W:\\panus
  python scripts/verify_mcp_tools.py --show-agent-tools
  python scripts/verify_mcp_tools.py --list
  python scripts/verify_mcp_tools.py --server memory --list
  python scripts/verify_mcp_tools.py --server filesystem --tool read_file --args '{"path":"README.md"}'
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

from src.config import get_mcp_servers  # noqa: E402
from src.tools.mcp import build_mcp_tools  # noqa: E402


EXAMPLE_MCP_SERVERS = {
    "docs": {
        "transport": "streamable_http",
        "url": "https://your-server.example.com/mcp",
        "auth_url": "https://your-server.example.com/login",
        "headers": {
            "Authorization": "Bearer YOUR_TOKEN"
        },
    }
}


def _memory_filesystem_example(allowed_path: str) -> dict[str, dict]:
    return {
        "memory": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-memory"],
        },
        "filesystem": {
            "transport": "stdio",
            "command": "npx",
            "args": [
                "-y",
                "@modelcontextprotocol/server-filesystem",
                allowed_path,
            ],
        },
    }


def _tool_map() -> dict[str, object]:
    return {tool.name: tool for tool in build_mcp_tools(get_mcp_servers())}


def _print_example_env() -> None:
    print("Add this to your .env or shell environment:\n")
    print("ETHOS_MCP_SERVERS=" + json.dumps(EXAMPLE_MCP_SERVERS, ensure_ascii=False))
    print("\nThen run one of these:")
    print("  python scripts/verify_mcp_tools.py --list")
    print("  python scripts/verify_mcp_tools.py --server docs --read-uri mcp://docs/one")
    print("  python scripts/verify_mcp_tools.py --server docs --tool ping --args '{\"x\": 1}'")


def _print_memory_filesystem_env(allowed_path: str) -> None:
    config = _memory_filesystem_example(allowed_path)
    print("Add this MCP config to your .env or shell environment:\n")
    print("ETHOS_MCP_SERVERS=" + json.dumps(config, ensure_ascii=False))
    print("\nNotes:")
    print("  - `memory` uses @modelcontextprotocol/server-memory via npx")
    print(f"  - `filesystem` is restricted to: {allowed_path}")
    print("\nThen verify with:")
    print("  python scripts/verify_mcp_tools.py --show-agent-tools")
    print("  python scripts/verify_mcp_tools.py --server memory --list")
    print("  python scripts/verify_mcp_tools.py --server filesystem --list")


def _set_memory_filesystem_env(allowed_path: str) -> None:
    os.environ["ETHOS_MCP_SERVERS"] = json.dumps(
        _memory_filesystem_example(allowed_path),
        ensure_ascii=False,
    )


def _show_agent_tools() -> None:
    from langchain_core.language_models.fake_chat_models import FakeListChatModel

    from src.graph import create_ethos_agent

    agent = create_ethos_agent(model=FakeListChatModel(responses=["ok"]))
    graph = agent.get_graph()
    tools_node = graph.nodes["tools"].data
    names = sorted(tools_node._tools_by_name.keys())

    print("Ethos agent tools:")
    for name in names:
        print(f"  - {name}")

    mcp_names = [name for name in names if name == "mcp" or "mcp" in name]
    print("\nMCP-related tools detected:")
    if mcp_names:
        for name in mcp_names:
            print(f"  - {name}")
    else:
        print("  (none)")


def _invoke_and_print(tool: object, payload: dict) -> None:
    try:
        print(tool.invoke(payload))  # type: ignore[union-attr]
    except Exception as exc:
        print(f"Tool call failed: {type(exc).__name__}: {exc}")
        if "WinError 5" in str(exc):
            print(
                "Hint: this Windows environment denied stdio subprocess pipes for the MCP server. "
                "Try running the script in a less restricted terminal or use an HTTP/SSE MCP server instead of stdio."
            )
        raise SystemExit(1) from exc


def _require_servers() -> None:
    if os.getenv("ETHOS_MCP_SERVERS", "").strip():
        return
    print("ETHOS_MCP_SERVERS is not set.")
    print("Run: python scripts/verify_mcp_tools.py --print-example-env")
    raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify Ethos MCP tools")
    parser.add_argument("--print-example-env", action="store_true", help="Print example ETHOS_MCP_SERVERS config")
    parser.add_argument(
        "--print-memory-filesystem-env",
        action="store_true",
        help="Print ETHOS_MCP_SERVERS for the stdio memory + filesystem MCP servers",
    )
    parser.add_argument(
        "--use-memory-filesystem-example",
        action="store_true",
        help="Temporarily use the stdio memory + filesystem MCP config for this run",
    )
    parser.add_argument(
        "--allowed-path",
        default=str(ROOT),
        help="Allowed path for the filesystem MCP server example",
    )
    parser.add_argument(
        "--show-agent-tools",
        action="store_true",
        help="Build an Ethos agent with a fake model and print tool names loaded into the agent",
    )
    parser.add_argument("--server", help="MCP server name to target")
    parser.add_argument("--list", action="store_true", help="List MCP resources")
    parser.add_argument("--read-uri", help="Read one MCP resource URI")
    parser.add_argument("--tool", help="Invoke an MCP tool by name")
    parser.add_argument("--args", default="{}", help="JSON object passed to --tool")
    parser.add_argument(
        "--auth",
        action="store_true",
        help="Call the dynamic auth tool for --server if configured",
    )
    args = parser.parse_args()

    if args.print_example_env:
        _print_example_env()
        return

    if args.print_memory_filesystem_env:
        _print_memory_filesystem_env(args.allowed_path)
        return

    if args.use_memory_filesystem_example:
        _set_memory_filesystem_env(args.allowed_path)

    if args.show_agent_tools:
        _require_servers()
        _show_agent_tools()
        return

    _require_servers()
    tools = _tool_map()

    if args.auth:
        if not args.server:
            raise SystemExit("--auth requires --server")
        auth_tool_name = f"mcp__{args.server}__authenticate"
        tool = tools.get(auth_tool_name)
        if tool is None:
            raise SystemExit(f"No auth tool configured for server '{args.server}'")
        _invoke_and_print(tool, {})
        return

    if args.list:
        payload = {"server": args.server} if args.server else {}
        _invoke_and_print(tools["list_mcp_resources"], payload)
        return

    if args.read_uri:
        if not args.server:
            raise SystemExit("--read-uri requires --server")
        _invoke_and_print(
            tools["read_mcp_resource"],
            {"server": args.server, "uri": args.read_uri},
        )
        return

    if args.tool:
        if not args.server:
            raise SystemExit("--tool requires --server")
        try:
            tool_args = json.loads(args.args)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"--args must be valid JSON: {exc}") from exc
        if not isinstance(tool_args, dict):
            raise SystemExit("--args must decode to a JSON object")
        _invoke_and_print(
            tools["mcp"],
            {"server": args.server, "tool": args.tool, "arguments": tool_args},
        )
        return

    print("Nothing to do. Use one of: --print-example-env, --list, --read-uri, --tool, --auth")


if __name__ == "__main__":
    main()
