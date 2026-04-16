"""Shared path sandboxing — prevents traversal outside the workspace root."""

from pathlib import Path


def resolve(root: Path, path: str) -> Path:
    """Resolve `path` relative to `root`, rejecting any `../` traversal attempts.

    Args:
        root: Absolute workspace root path.
        path: Relative (or absolute) path supplied by the agent.

    Returns:
        Resolved absolute path guaranteed to be inside `root`.

    Raises:
        PermissionError: If the resolved path escapes the workspace root.
    """
    resolved = (root / path.lstrip("/")).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        raise PermissionError(
            f"Path '{path}' resolves outside the workspace root '{root}'. "
            "Access denied."
        )
    return resolved
