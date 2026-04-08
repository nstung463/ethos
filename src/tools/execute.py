"""execute tool — run shell commands inside the sandbox.

Only available when the agent has a sandbox backend (LocalSandbox or DaytonaSandbox).
The tool is NOT exposed when running in pure local-pathlib mode without a backend.
"""

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.backends.sandbox import BaseSandbox


class ExecuteInput(BaseModel):
    command: str = Field(
        description=(
            "Shell command to execute inside the sandbox. "
            "The command runs in the workspace root directory. "
            "Examples: 'ls -la', 'python main.py', 'pip install requests', 'cat file.txt'"
        )
    )
    timeout: int | None = Field(
        default=None,
        description=(
            "Maximum seconds to wait for the command. "
            "Uses backend default if not specified. "
            "Use 0 for no timeout (long-running processes)."
        ),
    )


def build_execute_tool(backend: BaseSandbox) -> StructuredTool:
    """Build the execute tool backed by a sandbox."""

    def _execute(command: str, timeout: int | None = None) -> str:
        result = backend.execute(command, timeout=timeout)
        output = result.output.strip()
        if result.exit_code != 0:
            return f"Exit code: {result.exit_code}\n{output}" if output else f"Command failed (exit {result.exit_code})"
        return output or "(no output)"

    return StructuredTool.from_function(
        name="execute",
        func=_execute,
        description=(
            "Execute a shell command inside the sandbox. "
            "Use for running scripts, installing packages, compiling code, "
            "running tests, or any task requiring a real shell. "
            "The command runs in the workspace root directory."
        ),
        args_schema=ExecuteInput,
    )
