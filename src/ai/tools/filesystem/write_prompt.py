from __future__ import annotations

DESCRIPTION = "Write a file to the local filesystem."


def render_write_tool_description() -> str:
    return (
        "Writes a file to the local filesystem.\n\n"
        "Usage:\n"
        "- This tool will overwrite the existing file if there is one at the provided path.\n"
        "- If this is an existing file, you MUST use the read_file tool first to read the file's contents. "
        "This tool will fail if you did not read the file first.\n"
        "- Prefer the edit_file tool for modifying existing files - it only sends the diff. "
        "Only use this tool to create new files or for complete rewrites.\n"
        "- NEVER create documentation files (*.md) or README files unless explicitly requested by the User.\n"
        "- Only use emojis if the user explicitly requests it. Avoid writing emojis to files unless asked."
    )


__all__ = ["DESCRIPTION", "render_write_tool_description"]
