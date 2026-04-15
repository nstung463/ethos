from __future__ import annotations
from pathlib import Path
from src.ai.permissions.types import PermissionSuggestion


def suggest_mode(mode_name: str) -> PermissionSuggestion:
    return PermissionSuggestion(kind="set_mode", value=mode_name)


def suggest_directory(path: Path) -> PermissionSuggestion:
    return PermissionSuggestion(kind="add_working_directory", value=str(path))
