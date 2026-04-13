"""Structured chat metadata task generation."""

from __future__ import annotations

import os
from typing import Mapping, TypeVar

from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from src.logger import get_logger

from src.api.models import Message
from src.config import OPENAI_COMPATIBLE_PROVIDERS, build_chat_model, get_model_registry

logger = get_logger(__name__)
StructuredResultT = TypeVar("StructuredResultT", bound=BaseModel)
TASK_MODEL_ID_ENV = "ETHOS_TASK_MODEL_ID"
TITLE_HISTORY_LIMIT = 4
FOLLOW_UP_HISTORY_LIMIT = 4
TITLE_MAX_TOKENS = 32
FOLLOW_UP_MAX_TOKENS = 96


TITLE_TASK_PROMPT = """### Task:
Generate a concise 3-5 word title summarizing this conversation.

### Guidelines:
- Focus on the user's actual task or question.
- Prefer clarity over cleverness.
- Return a JSON object matching this schema exactly:
  {{"title":"Short title"}}

### Chat History:
<chat_history>
{chat_history}
</chat_history>
"""

FOLLOW_UP_TASK_PROMPT = """### Task:
Suggest 3 relevant follow-up prompts the user might naturally ask next.

### Guidelines:
- Write from the user's point of view.
- Keep each follow-up concise and directly related to the conversation.
- Do not repeat questions that were already answered.
- Return a JSON object matching this schema exactly:
  {{"follow_ups":["Question 1?","Question 2?","Question 3?"]}}

### Chat History:
<chat_history>
{chat_history}
</chat_history>
"""


class TitleTaskResult(BaseModel):
    title: str = Field(min_length=1, max_length=120)


class FollowUpsTaskResult(BaseModel):
    follow_ups: list[str] = Field(default_factory=list, max_length=3)


def render_chat_history(messages: list[Message], limit: int) -> str:
    filtered = [message for message in messages if message.role != "system"]
    selected = filtered[-limit:] if limit > 0 else filtered
    lines: list[str] = []
    for message in selected:
        content = message.content.strip()
        if not content:
            continue
        lines.append(f"{message.role.upper()}: {content}")
    return "\n".join(lines).strip()


def resolve_task_model_spec(model_id: str):
    registry = {spec.id: spec for spec in get_model_registry()}
    configured = os.getenv(TASK_MODEL_ID_ENV, "").strip()
    task_model_id = configured or ("ethos" if "ethos" in registry else model_id)
    return registry.get(task_model_id) or registry[model_id]


def fallback_title(messages: list[Message]) -> str:
    for message in messages:
        if message.role == "user" and message.content.strip():
            return " ".join(message.content.split())[:56] or "New conversation"
    return "New conversation"


def normalize_follow_ups(items: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = " ".join(item.split()).strip()
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(text)
        if len(cleaned) >= 3:
            break
    return cleaned


def preferred_structured_output_method(provider: str) -> str:
    normalized = provider.strip().lower()
    if normalized in OPENAI_COMPATIBLE_PROVIDERS:
        return "json_mode"
    return "function_calling"


def structured_output_methods(provider: str) -> list[str]:
    preferred = preferred_structured_output_method(provider)
    methods = [preferred]
    for method in ("function_calling", "json_schema", "json_mode"):
        if method not in methods:
            methods.append(method)
    return methods


async def invoke_structured_task(
    *,
    provider: str,
    model_name: str,
    api_keys: Mapping[str, str] | None,
    schema: type[StructuredResultT],
    prompt: str,
    task_name: str,
    max_tokens: int,
) -> StructuredResultT:
    last_error: Exception | None = None
    methods = structured_output_methods(provider)

    for method in methods:
        try:
            model = build_chat_model(provider, model_name, api_keys=api_keys).bind(
                max_tokens=max_tokens
            ).with_structured_output(
                schema,
                method=method,
            )
            return await model.ainvoke([HumanMessage(content=prompt)])
        except Exception as exc:
            last_error = exc
            logger.warning(
                "Structured output task failed; trying fallback if available (task=%s, provider=%s, model=%s, method=%s, error=%s)",
                task_name,
                provider,
                model_name,
                method,
                exc,
            )

    assert last_error is not None
    raise last_error


async def generate_title_task(
    *,
    model_id: str,
    messages: list[Message],
    api_keys: Mapping[str, str] | None = None,
) -> TitleTaskResult:
    spec = resolve_task_model_spec(model_id)
    prompt = TITLE_TASK_PROMPT.format(chat_history=render_chat_history(messages, TITLE_HISTORY_LIMIT))
    return await invoke_structured_task(
        provider=spec.provider,
        model_name=spec.model,
        api_keys=api_keys,
        schema=TitleTaskResult,
        prompt=prompt,
        task_name="title",
        max_tokens=TITLE_MAX_TOKENS,
    )


async def generate_follow_ups_task(
    *,
    model_id: str,
    messages: list[Message],
    api_keys: Mapping[str, str] | None = None,
) -> FollowUpsTaskResult:
    spec = resolve_task_model_spec(model_id)
    prompt = FOLLOW_UP_TASK_PROMPT.format(chat_history=render_chat_history(messages, FOLLOW_UP_HISTORY_LIMIT))
    result = await invoke_structured_task(
        provider=spec.provider,
        model_name=spec.model,
        api_keys=api_keys,
        schema=FollowUpsTaskResult,
        prompt=prompt,
        task_name="follow_ups",
        max_tokens=FOLLOW_UP_MAX_TOKENS,
    )
    return FollowUpsTaskResult(follow_ups=normalize_follow_ups(result.follow_ups))
