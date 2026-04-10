"""Ethos agent factory.

Two modes:
  - Local (default): filesystem tools use pathlib.
  - Sandbox (Daytona or LocalSandbox): filesystem + shell tools delegate
    to the backend; all file operations happen inside the sandbox.

Usage:
    # Local mode (default)
    agent = create_ethos_agent()

    # Daytona sandbox mode
    from daytona import Daytona, CreateSandboxParams
    from src.backends.daytona import DaytonaSandbox

    sandbox = Daytona().create(CreateSandboxParams(language="python"))
    agent = create_ethos_agent(backend=DaytonaSandbox(sandbox=sandbox))

    # Local sandbox mode (subprocess execution)
    from src.backends.local import LocalSandbox
    agent = create_ethos_agent(backend=LocalSandbox(root_dir="./workspace"))
"""

from langchain.agents import create_agent
from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.memory import MemorySaver

from src.backends.sandbox import BaseSandbox
from src.config import get_mcp_servers, get_model, get_workspace
from src.middleware import MemoryMiddleware, SkillsMiddleware
from src.logger import get_logger
from src.prompts import BASE_SYSTEM_PROMPT
from src.subagents import DEFAULT_SUBAGENTS, build_task_tool
from src.tools.filesystem import build_filesystem_tools
from src.tools.mcp import build_mcp_tools
from src.tools.shell import build_bash_tool, build_powershell_tool
from src.tools.web import tavily_search, web_fetch_tool

logger = get_logger(__name__)


def _build_default_middleware(root_dir: str) -> list[AgentMiddleware]:
    """Create a fresh middleware stack for an Ethos agent instance."""
    return [
        SkillsMiddleware(skills_dir=f"{root_dir}/skills"),
        MemoryMiddleware(agents_md_path=f"{root_dir}/AGENTS.md"),
    ]


def create_ethos_agent(
    root_dir: str | None = None,
    backend: BaseSandbox | None = None,
    model: BaseChatModel | None = None,
) -> object:
    """Create and return a compiled Ethos agent.

    Args:
        root_dir: Workspace root directory (local mode only).
                  Defaults to ETHOS_WORKSPACE env var or './workspace'.
        backend: Optional sandbox backend (LocalSandbox or DaytonaSandbox).
                 When provided, all filesystem and shell operations run inside
                 the sandbox instead of the local machine.

    Returns:
        A compiled agent graph ready to invoke.
    """
    if root_dir is None:
        root_dir = get_workspace()

    if model is None:
        model = get_model()
    logger.info("Creating Ethos agent (backend=%s, workspace=%s)", "sandbox" if backend else "local", root_dir)

    # ── Tools ──────────────────────────────────────────────────────────────────
    if backend is not None:
        # Sandbox mode: filesystem tools + shell tools delegating to backend
        from src.tools.filesystem.sandbox_tools import build_sandbox_filesystem_tools

        fs_tools = build_sandbox_filesystem_tools(backend)
        extra_tools = []
        if "bash" in backend.supported_shells:
            extra_tools.append(build_bash_tool(backend))
        if "powershell" in backend.supported_shells:
            extra_tools.append(build_powershell_tool(backend))
    else:
        # Local mode: pathlib-based filesystem tools, no shell tool
        fs_tools = build_filesystem_tools(root_dir)
        extra_tools = []

    web_tools = [tavily_search, web_fetch_tool]
    mcp_tools = build_mcp_tools(get_mcp_servers())
    task_tool = build_task_tool(
        model=model,
        subagents=DEFAULT_SUBAGENTS,
        base_tools=fs_tools + extra_tools + web_tools + mcp_tools,
        default_middleware=_build_default_middleware(root_dir),
    )
    all_tools = fs_tools + extra_tools + web_tools + mcp_tools + [task_tool]
    logger.debug("Agent tools prepared (count=%d)", len(all_tools))

    # ── Middleware stack ───────────────────────────────────────────────────────
    middleware = _build_default_middleware(root_dir)

    # ── Agent ──────────────────────────────────────────────────────────────────
    return create_agent(
        model=model,
        tools=all_tools,
        system_prompt=BASE_SYSTEM_PROMPT,
        middleware=middleware,
        checkpointer=MemorySaver(),
        name="ethos",
    )
