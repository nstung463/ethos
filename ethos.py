"""Ethos CLI entry point.

Modes:
  python ethos.py               — local pathlib mode (default)
  python ethos.py --sandbox     — LocalSandbox mode (subprocess + pathlib via shell)
  python ethos.py --daytona     — Daytona remote sandbox mode
  python ethos.py --open-terminal — OpenTerminal HTTP backend mode

Or as a LangGraph deployment:
  langgraph dev                — exposes the graph for LangGraph Studio
"""

import argparse
import os
import uuid
from contextlib import nullcontext

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from src.logger import get_logger, setup_logging

load_dotenv()
setup_logging()
logger = get_logger(__name__)


def _build_agent(mode: str):
    """Build the agent in the requested mode."""
    from src.graph import create_ethos_agent
    logger.info("Building agent in mode=%s", mode)

    if mode == "daytona":
        try:
            from daytona import CreateSandboxParams, Daytona
            from src.backends.daytona import DaytonaSandbox
        except ImportError:
            print("Error: daytona package not installed. Run: pip install 'ethos[daytona]'")
            raise

        api_key = os.getenv("DAYTONA_API_KEY")
        if not api_key:
            raise ValueError("DAYTONA_API_KEY environment variable not set.")

        print("Creating Daytona sandbox...")
        sandbox = Daytona(api_key=api_key).create(CreateSandboxParams(language="python"))
        backend = DaytonaSandbox(sandbox=sandbox)
        print(f"Sandbox ready: {backend.id}")
        return create_ethos_agent(backend=backend)

    if mode == "sandbox":
        from src.backends.local import LocalSandbox
        from src.config import get_workspace
        backend = LocalSandbox(root_dir=get_workspace())
        return create_ethos_agent(backend=backend)

    if mode == "open_terminal":
        try:
            from src.backends.open_terminal import OpenTerminalSandbox
        except ImportError:
            print("Error: httpx package not installed. Run: pip install 'ethos[open-terminal]'")
            raise

        base_url = os.getenv("OPEN_TERMINAL_URL", "http://localhost:8000")
        api_key = os.getenv("OPEN_TERMINAL_API_KEY")
        if not api_key:
            raise ValueError("OPEN_TERMINAL_API_KEY environment variable not set.")

        user_id = os.getenv("OPEN_TERMINAL_USER_ID")
        print(f"Connecting to Open Terminal at {base_url}...")
        backend = OpenTerminalSandbox(base_url=base_url, api_key=api_key, user_id=user_id)
        print(f"Backend ready: {backend.id}")
        return create_ethos_agent(backend=backend)

    # Default: local pathlib mode
    return create_ethos_agent()


def main() -> None:
    """Run the Ethos CLI agent."""
    parser = argparse.ArgumentParser(description="Ethos AI Agent")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--daytona", action="store_true", help="Use Daytona remote sandbox")
    group.add_argument("--sandbox", action="store_true", help="Use LocalSandbox (subprocess mode)")
    group.add_argument("--open-terminal", action="store_true", help="Use OpenTerminal HTTP backend", default=True)
    args = parser.parse_args()

    mode = "daytona" if args.daytona else ("sandbox" if args.sandbox else ("open_terminal" if args.open_terminal else "local"))
    logger.info("Starting Ethos CLI with mode=%s", mode)
    sandbox_ctx = nullcontext()
    print(f"Mode: {mode}")
    if mode == "daytona":
        from src.backends.daytona import create_daytona_sandbox

        sandbox_ctx = create_daytona_sandbox(conversation_id=f"ethos-{uuid.uuid4().hex[:8]}")

    with sandbox_ctx as backend:
        if mode == "daytona":
            from src.graph import create_ethos_agent

            agent = create_ethos_agent(backend=backend)
            logger.info("Daytona backend ready (sandbox_id=%s)", backend.id)
        else:
            agent = _build_agent(mode)

        print(f"Ethos AI Agent [{mode} mode] — type 'exit' to quit\n")
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye.")
                break

            if not user_input or user_input.lower() in ("exit", "quit"):
                print("Goodbye.")
                break

            result = agent.invoke(
                {"messages": [HumanMessage(content=user_input)]},
                config=config,
            )
            logger.debug("Agent invocation completed (thread_id=%s)", thread_id)

            last = result["messages"][-1]
            content = getattr(last, "content", "")
            if isinstance(content, list):
                content = "".join(
                    b.get("text", "") if isinstance(b, dict) else str(b) for b in content
                )
            print(f"\nEthos: {content}\n")


# Graph exported for langgraph dev / LangGraph Studio
def create_graph():
    from src.graph import create_ethos_agent
    return create_ethos_agent()

graph = create_graph()


if __name__ == "__main__":
    main()
