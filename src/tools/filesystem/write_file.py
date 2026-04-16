"""write_file tool — create or overwrite a file."""

from pathlib import Path

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.ai.permissions.evaluator import PermissionEvaluator
from src.ai.permissions.filesystem_policy import FilesystemPolicy
from src.ai.permissions.types import PermissionBehavior, PermissionContext, PermissionSubject
from src.tools.filesystem._sandbox import resolve


class WriteFileInput(BaseModel):
    path: str = Field(description="File path to write (relative to workspace root). Parent directories are created automatically.")
    content: str = Field(description="Full content to write to the file.")


def _write_file(root: Path, path: str, content: str) -> str:
    target = resolve(root, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    lines = content.count("\n") + 1
    return f"Written {len(content)} characters ({lines} lines) to '{path}'."


def build_write_file_tool(root: Path, permission_context: PermissionContext | None = None) -> StructuredTool:
    policy = FilesystemPolicy()
    evaluator = PermissionEvaluator()

    def _tool(path: str, content: str) -> str:
        target = resolve(root, path)
        if permission_context is not None:
            decision = evaluator.evaluate(
                context=permission_context,
                subject=PermissionSubject.EDIT,
                candidate=path,
                policy_decision=policy.check_edit(context=permission_context, target=target),
            )
            if decision.behavior is not PermissionBehavior.ALLOW:
                return f"Permission {decision.behavior.value}: {decision.reason}"
        return _write_file(root, path, content)

    return StructuredTool.from_function(
        name="write_file",
        func=_tool,
        description=(
            "Write content to a file, creating it and parent directories if needed. "
            "Prefer edit_file for modifying existing files — use write_file for new files "
            "or complete rewrites."
        ),
        args_schema=WriteFileInput,
    )
