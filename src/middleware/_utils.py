"""Shared middleware utilities."""

from langchain_core.messages import BaseMessage, SystemMessage


def append_to_system_message(sys_msg: BaseMessage | None, text: str) -> SystemMessage:
    """Append text to a system message, creating one if needed.

    Handles both string content and content-block lists (e.g. Anthropic cache blocks).
    """
    if sys_msg is None:
        return SystemMessage(content=text)

    content = sys_msg.content
    if isinstance(content, str):
        return SystemMessage(content=content + "\n\n" + text)

    # Content-block list — append a new text block
    return SystemMessage(content=[*content, {"type": "text", "text": "\n\n" + text}])
