"""send_user_message tool — send a message to the user.

Mirrors BriefTool (legacy alias SendUserMessage) from claude-code-source.
"""
from __future__ import annotations

from typing import Callable, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class SendUserMessageInput(BaseModel):
    message: str = Field(description="The message to display to the user.")


def build_send_user_message_tool(
    output_fn: Optional[Callable[[str], None]] = None,
) -> StructuredTool:
    """Build send_user_message tool. Provide output_fn for testing (default: print)."""
    fn = output_fn or print

    def _send(message: str) -> str:
        fn(message)
        return "Message sent."

    return StructuredTool.from_function(
        name="send_user_message",
        func=_send,
        description=(
            "Send a message or update to the user outside of the normal response flow. "
            "Use for progress updates, warnings, or notifications during long tasks."
        ),
        args_schema=SendUserMessageInput,
    )
