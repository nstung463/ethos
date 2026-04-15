"""edit_file tool — exact string replacement in a file."""

from pathlib import Path

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.ai.permissions.evaluator import PermissionEvaluator
from src.ai.permissions.filesystem_policy import FilesystemPolicy
from src.ai.permissions.types import PermissionBehavior, PermissionContext, PermissionSubject
from src.tools.filesystem._sandbox import resolve


class EditFileInput(BaseModel):
    path: str = Field(description="File path to edit (relative to workspace root).")
    old_string: str = Field(
        description=(
            "Exact string to find and replace. Must appear exactly once in the file "
            "unless replace_all=True. Include enough surrounding context to make it unique."
        )
    )
    new_string: str = Field(description="Replacement string. Must be different from old_string.")
    replace_all: bool = Field(
        default=False,
        description="If True, replace all occurrences. If False (default), old_string must be unique.",
    )


def _edit_file(root: Path, path: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
    target = resolve(root, path)
    if not target.exists():
        return f"Error: '{path}' does not exist. Read the file before editing."

    content = target.read_text(encoding="utf-8")
    count = content.count(old_string)

    if count == 0:
        return (
            f"Error: old_string not found in '{path}'. "
            "Make sure the string matches exactly (including indentation and whitespace)."
        )
    if count > 1 and not replace_all:
        return (
            f"Error: old_string appears {count} times in '{path}'. "
            "Provide more surrounding context to make it unique, or set replace_all=True."
        )

    new_content = content.replace(old_string, new_string)
    target.write_text(new_content, encoding="utf-8")
    replaced = count if replace_all else 1
    return f"Edited '{path}': replaced {replaced} occurrence(s)."


def build_edit_file_tool(root: Path, permission_context: PermissionContext | None = None) -> StructuredTool:
    policy = FilesystemPolicy()
    evaluator = PermissionEvaluator()

    def _tool(path: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
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
        return _edit_file(root, path, old_string, new_string, replace_all)

    return StructuredTool.from_function(
        name="edit_file",
        func=_tool,
        description=(
            "Replace an exact string in a file. "
            "You MUST read the file first. "
            "old_string must be unique in the file (or use replace_all=True). "
            "Preserve exact indentation from the read output."
        ),
        args_schema=EditFileInput,
    )
