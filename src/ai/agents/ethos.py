"""Primary Ethos agent factory."""

from pathlib import Path

from langchain.agents import create_agent
from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver

from src.ai.permissions import PermissionContext
from src.ai.agents.subagents import DEFAULT_SUBAGENTS, build_task_tool
from src.ai.middleware import MemoryMiddleware, SkillsMiddleware
from src.ai.prompts.catalog import BASE_SYSTEM_PROMPT
from src.backends.protocol import SandboxProtocol as FilesystemBackendProtocol
from src.config import get_mcp_servers, get_model, get_workspace
from src.logger import get_logger
from src.ai.tools.filesystem import build_filesystem_tools
from src.ai.tools.mcp import build_mcp_tools
from src.ai.tools.shell import build_bash_tool, build_powershell_tool
from src.ai.tools.web import tavily_search, web_fetch_tool

logger = get_logger(__name__)


def _build_default_middleware(root_dir: str) -> list[AgentMiddleware]:
    """Create a fresh middleware stack for an Ethos agent instance."""
    return [
        SkillsMiddleware(skills_dir=f"{root_dir}/skills"),
        MemoryMiddleware(agents_md_path=f"{root_dir}/AGENTS.md"),
    ]


def create_ethos_agent(
    root_dir: str | None = None,
    backend: FilesystemBackendProtocol | None = None,
    model: BaseChatModel | None = None,
    permission_context: PermissionContext | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
) -> object:
    """Create and return a compiled Ethos agent."""
    raw_backend_root = getattr(backend, "root", None) if backend is not None else None
    if root_dir is None:
        backend_root = raw_backend_root
        if isinstance(backend_root, Path):
            root_dir = str(backend_root.resolve())
        elif isinstance(backend_root, str) and backend_root.strip():
            root_dir = backend_root.strip()
        else:
            root_dir = get_workspace()
    if model is None:
        model = get_model()
    logger.info("Creating Ethos agent (backend=%s, workspace=%s)", "sandbox" if backend else "local", root_dir)

    fs_tools = build_filesystem_tools(
        root_dir=root_dir,
        backend=backend,
        permission_context=permission_context,
    )
    extra_tools = []
    if backend is not None:
        if "bash" in backend.supported_shells:
            extra_tools.append(build_bash_tool(backend, permission_context=permission_context))
        if "powershell" in backend.supported_shells:
            extra_tools.append(build_powershell_tool(backend, permission_context=permission_context))

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

    # CLI / non-API callers get a fresh in-memory checkpointer per session.
    # The API path always injects the shared app.state checkpointer.
    if checkpointer is None:
        checkpointer = MemorySaver()
    middleware = _build_default_middleware(root_dir)
    return create_agent(
        model=model,
        tools=all_tools,
        system_prompt=BASE_SYSTEM_PROMPT,
        middleware=middleware,
        checkpointer=checkpointer,
        name="ethos",
    )
