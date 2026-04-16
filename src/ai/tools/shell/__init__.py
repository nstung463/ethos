"""Shell tools exposed according to backend platform support."""

from src.ai.tools.shell.bash import build_bash_tool
from src.ai.tools.shell.powershell import build_powershell_tool

__all__ = ["build_bash_tool", "build_powershell_tool"]

