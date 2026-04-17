"""send_message tool — send a message to another agent or teammate."""
from __future__ import annotations

import json
from typing import Callable

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class SendMessageInput(BaseModel):
    to: str = Field(description="Recipient agent ID or team name.")
    content: str = Field(description="Message content to send.")


def build_send_message_tool(deliver_fn: Callable[[str, str], None]) -> StructuredTool:
    def _send(to: str, content: str) -> str:
        try:
            deliver_fn(to, content)
            return json.dumps({"delivered": True, "to": to})
        except Exception as exc:
            return json.dumps({"delivered": False, "error": str(exc)})

    return StructuredTool.from_function(
        name="send_message", func=_send,
        description="Send a message to another agent or teammate by ID.",
        args_schema=SendMessageInput,
    )
