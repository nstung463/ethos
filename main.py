"""Ethos entry point.

Modes:
  python main.py               — local pathlib mode (default)
  python main.py --sandbox     — LocalSandbox mode (subprocess + pathlib via shell)
  python main.py --daytona     — Daytona remote sandbox mode

Or as a LangGraph deployment:
  langgraph dev                — exposes the graph for LangGraph Studio / OpenWebUI
"""

import argparse
import os
import uuid

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

load_dotenv()


def _build_agent(mode: str):
    """Build the agent in the requested mode."""
    from src.graph import create_ethos_agent

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

    # Default: local pathlib mode
    return create_ethos_agent()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ethos AI Agent")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--daytona", action="store_true", help="Use Daytona remote sandbox")
    group.add_argument("--sandbox", action="store_true", help="Use LocalSandbox (subprocess mode)")
    args = parser.parse_args()

    mode = "daytona" if args.daytona else ("sandbox" if args.sandbox else "local")
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
