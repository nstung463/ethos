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


def set_mode(context: PermissionContext, mode: PermissionMode) -> PermissionContext:
    return PermissionContext(
        mode=mode,
        workspace_root=context.workspace_root,
        working_directories=context.working_directories,
        rules=context.rules,
        headless=context.headless,
    )


def add_working_directory(context: PermissionContext, path: Path) -> PermissionContext:
    resolved = path.resolve()
    directories = tuple(dict.fromkeys((*context.working_directories, resolved)))
    return PermissionContext(
        mode=context.mode,
        workspace_root=context.workspace_root,
        working_directories=directories,
        rules=context.rules,
        headless=context.headless,
    )


def add_rule(context: PermissionContext, rule: PermissionRule) -> PermissionContext:
    return PermissionContext(
        mode=context.mode,
        workspace_root=context.workspace_root,
        working_directories=context.working_directories,
        rules=(*context.rules, rule),
        headless=context.headless,
    )
