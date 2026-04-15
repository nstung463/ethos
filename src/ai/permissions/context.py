from __future__ import annotations

from pathlib import Path

from src.ai.permissions.types import PermissionContext, PermissionMode, PermissionRule


def build_default_permission_context(
    workspace_root: Path,
    *,
    mode: PermissionMode = PermissionMode.DEFAULT,
    rules: tuple[PermissionRule, ...] = (),
) -> PermissionContext:
    root = workspace_root.resolve()
    return PermissionContext(
        mode=mode,
        workspace_root=root,
        working_directories=(root,),
        rules=rules,
    )
