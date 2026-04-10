"""Chat completion request and message models."""

from typing import Any

from pydantic import BaseModel, Field
from src.config import get_model_registry


class Message(BaseModel):
    """OpenAI-compatible message."""
    role: str
    content: str


def _default_openai_model_id() -> str:
    """Default ``model`` field: first id in registry."""
    return get_model_registry()[0].id


class ChatRequest(BaseModel):
    """OpenAI-compatible chat completion request."""
    model: str = Field(default_factory=_default_openai_model_id)
    messages: list[Message]
    stream: bool = False
    file_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] | None = None

    model_config = {"extra": "allow"}  # ignore unknown OpenWebUI fields
