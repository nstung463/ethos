"""OpenAI-compatible v1 API endpoints."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.api.deps import get_daytona_session_manager, get_file_store
from src.api.models import ChatRequest, Message
from src.api.services.chat_tasks import fallback_title, generate_follow_ups_task, generate_title_task
from src.api.services.daytona_manager import DaytonaSessionManager
from src.config import build_chat_model, get_model_registry
from src.graph import create_ethos_agent
from src.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/v1", tags=["v1"])
_SANDBOX_ATTACHMENTS_ROOT = "/tmp/ethos/attachments"


def _resolve_model_id(model_id: str) -> str:
    specs = get_model_registry()
    registry = {spec.id: spec for spec in specs}
    if model_id in registry:
        return model_id
    if len(specs) == 1:
        sole = specs[0].id
        logger.warning("Requested model %r not in registry; using only configured model %r", model_id, sole)
        return sole
    raise HTTPException(
        status_code=404,
        detail=f"Unknown model: {model_id!r}. Available: {sorted(registry.keys())}",
    )


def _to_lc_messages(messages: list[Message]):
    result = []
    for message in messages:
        if message.role == "system":
            result.append(SystemMessage(content=message.content))
        elif message.role == "assistant":
            result.append(AIMessage(content=message.content))
        else:
            result.append(HumanMessage(content=message.content))
    return result


def _parse_content(content) -> tuple[str, str]:
    if isinstance(content, str):
        return content, ""
    if not isinstance(content, list):
        return str(content), ""

    text_parts: list[str] = []
    thinking_parts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            text_parts.append(str(block))
            continue
        block_type = block.get("type", "")
        if block_type == "thinking":
            thinking_parts.append(block.get("thinking", ""))
        elif block_type == "text":
            text_parts.append(block.get("text", ""))

    return "".join(text_parts), "".join(thinking_parts)


def _extract_text(content) -> str:
    text, _ = _parse_content(content)
    return text


def _extract_file_ids(request: ChatRequest) -> list[str]:
    file_ids: list[str] = []
    seen: set[str] = set()

    def add_file_id(value: Any) -> None:
        if not isinstance(value, str) or not value or value in seen:
            return
        seen.add(value)
        file_ids.append(value)

    for file_id in request.file_ids:
        add_file_id(file_id)

    for item in request.files:
        add_file_id(item.get("id"))
        nested = item.get("file")
        if isinstance(nested, dict):
            add_file_id(nested.get("id"))

    metadata = request.metadata or {}
    extra_ids = metadata.get("file_ids")
    if isinstance(extra_ids, list):
        for file_id in extra_ids:
            add_file_id(file_id)

    return file_ids


def _pick_edit_target(request: ChatRequest, file_ids: list[str]) -> str | None:
    metadata = request.metadata or {}
    for key in ("target_file_id", "edit_target_file_id"):
        value = metadata.get(key)
        if isinstance(value, str):
            return value
    return file_ids[0] if file_ids else None


def _extract_user_api_keys(request: ChatRequest) -> dict[str, str]:
    metadata = request.metadata or {}
    raw_keys = metadata.get("user_api_keys")
    if not isinstance(raw_keys, dict):
        return {}

    result: dict[str, str] = {}
    for provider in ("openrouter", "anthropic", "openai"):
        value = raw_keys.get(provider)
        if isinstance(value, str) and value.strip():
            result[provider] = value.strip()
    return result


_VALID_PROVIDERS = frozenset(
    {"openrouter", "anthropic", "openai", "azure_openai", "openai_compatible",
     "deepseek", "together", "groq", "xai", "fireworks", "perplexity",
     "google_genai", "bedrock"}
)


def _extract_profile(request: ChatRequest) -> dict | None:
    """Extract a provider profile from request metadata, if present and valid."""
    metadata = request.metadata or {}
    raw = metadata.get("profile")
    if not isinstance(raw, dict):
        return None
    provider = str(raw.get("provider", "")).strip().lower()
    model = str(raw.get("model", "")).strip()
    if not provider or not model:
        return None
    if provider not in _VALID_PROVIDERS:
        logger.warning("Unknown provider in profile: %r — falling back to registry", provider)
        return None
    api_key = str(raw.get("api_key", "")).strip()
    base_url = str(raw.get("base_url", "")).strip() or None
    deployment = str(raw.get("deployment", "")).strip() or None
    api_version = str(raw.get("api_version", "")).strip() or None
    return {
        "provider": provider,
        "model": model,
        "api_key": api_key,
        "base_url": base_url,
        "deployment": deployment,
        "api_version": api_version,
    }


def _resolve_session_id(request: ChatRequest) -> str:
    if request.session_id:
        return request.session_id.strip()
    if request.chat_id:
        return request.chat_id.strip()
    metadata = request.metadata or {}
    for key in ("session_id", "chat_id", "conversation_id", "thread_id"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return str(uuid.uuid4())


def _sandbox_attachment_path(file_id: str, filename: str) -> str:
    safe_name = Path(filename).name or file_id
    return f"{_SANDBOX_ATTACHMENTS_ROOT}/{file_id}/{safe_name}"


def _stage_attached_files(
    *,
    request: ChatRequest,
    backend,
    file_ids: list[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, str], str | None, list[Message]]:
    store = get_file_store()
    records: dict[str, dict[str, Any]] = {}
    sandbox_paths: dict[str, str] = {}

    for file_id in file_ids:
        record = store.get_file(file_id)
        if not record:
            raise HTTPException(status_code=404, detail=f"Attached file not found: {file_id}")

        filename = record.get("filename", file_id)
        sandbox_path = _sandbox_attachment_path(file_id, filename)
        upload_response = backend.upload_files([(sandbox_path, Path(record["path"]).read_bytes())])
        if not upload_response or upload_response[0].error:
            error = upload_response[0].error if upload_response else "no response from sandbox"
            raise HTTPException(status_code=502, detail=f"Failed to stage file into sandbox: {error}")

        records[file_id] = record
        sandbox_paths[file_id] = sandbox_path

    target_file_id = _pick_edit_target(request, file_ids)
    target_path = sandbox_paths.get(target_file_id) if target_file_id else None
    attached_lines = [
        f"- {records[file_id].get('filename', file_id)} -> {sandbox_paths[file_id]}"
        for file_id in file_ids
    ]
    instruction = (
        "The user's attached files have been staged into the sandbox.\n"
        "Use sandbox filesystem tools such as read_file, edit_file, write_file, glob, and grep.\n"
        "Do not say the file is missing until you have checked the staged sandbox paths below.\n"
        "Attached files in sandbox:\n"
        + "\n".join(attached_lines)
    )
    if target_path:
        instruction += (
            "\n\nPrimary edit target:\n"
            f"- {target_path}\n"
            "If the user asks to modify the uploaded file, edit this file in place and keep it valid."
        )

    staged_messages = [Message(role="system", content=instruction), *request.messages]
    return records, sandbox_paths, target_file_id, staged_messages


def _publish_edited_file(source_record: dict[str, Any], backend, sandbox_path: str) -> dict[str, Any]:
    store = get_file_store()
    downloads = backend.download_files([sandbox_path])
    if not downloads or downloads[0].error or downloads[0].content is None:
        error = downloads[0].error if downloads else "no response from sandbox"
        raise HTTPException(status_code=502, detail=f"Failed to read edited sandbox file: {error}")

    source_name = source_record.get("filename", "edited.py")
    stem = Path(source_name).stem
    suffix = Path(source_name).suffix or ".py"
    output_name = f"{stem}.edited{suffix}"
    return store.import_bytes(
        filename=output_name,
        content=downloads[0].content,
        content_type=source_record.get("meta", {}).get("content_type"),
    )


def _sse(delta: dict[str, Any], model: str, finish_reason: str | None = None) -> str:
    payload = {
        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{
            "index": 0,
            "delta": delta,
            "finish_reason": finish_reason,
        }],
    }
    return f"data: {json.dumps(payload)}\n\n"


async def _stream_response(
    *,
    agent: object,
    messages: list[Message],
    model: str,
    thread_id: str,
    backend,
    source_records: dict[str, dict[str, Any]] | None = None,
    sandbox_paths: dict[str, str] | None = None,
    target_file_id: str | None = None,
) -> AsyncIterator[str]:
    lc_messages = _to_lc_messages(messages)
    config = {"configurable": {"thread_id": thread_id}}
    logger.info("Streaming chat request started (model=%s, session_id=%s, messages=%d)", model, thread_id, len(messages))

    async for event in agent.astream_events({"messages": lc_messages}, config=config, version="v2"):
        kind = event["event"]

        if kind == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            text, thinking = _parse_content(chunk.content)
            if thinking:
                yield _sse({"reasoning_content": thinking}, model)
            if text:
                yield _sse({"content": text}, model)
        elif kind == "on_tool_start":
            tool_name = event.get("name", "tool")
            tool_input = event["data"].get("input", {})
            if isinstance(tool_input, dict):
                args_preview = ", ".join(f"{key}={repr(value)[:60]}" for key, value in list(tool_input.items())[:3])
            else:
                args_preview = repr(tool_input)[:120]
            yield _sse({"reasoning_content": f"Using tool `{tool_name}`({args_preview})\n"}, model)

    if (
        source_records
        and sandbox_paths
        and target_file_id
        and target_file_id in source_records
        and target_file_id in sandbox_paths
        and source_records[target_file_id].get("filename", "").lower().endswith(".py")
    ):
        try:
            output_file = _publish_edited_file(
                source_records[target_file_id],
                backend,
                sandbox_paths[target_file_id],
            )
            yield _sse(
                {
                    "output_file": output_file,
                    "sandbox_path": sandbox_paths[target_file_id],
                },
                model,
            )
        except Exception as exc:
            logger.exception("Failed to publish streamed output file")
            yield _sse(
                {"reasoning_content": f"Edited file was created in sandbox but publishing failed: {exc}"},
                model,
            )

    logger.info("Streaming chat request finished (model=%s, session_id=%s)", model, thread_id)
    yield _sse({}, model, finish_reason="stop")
    yield "data: [DONE]\n\n"


@router.get("/models")
async def list_models():
    now = int(time.time())
    return {
        "object": "list",
        "data": [
            {
                "id": spec.id,
                "object": "model",
                "created": now,
                "owned_by": "ethos",
                "info": {
                    "meta": {
                        "capabilities": {
                            "file_upload": True,
                            "file_context": True,
                            "vision": True,
                            "web_search": True,
                            "image_generation": False,
                            "code_interpreter": True,
                            "citations": True,
                            "status_updates": True,
                        }
                    }
                },
            }
            for spec in get_model_registry()
        ],
    }


@router.post("/chat/completions")
async def chat_completions(
    request: ChatRequest,
    http_request: Request,
    daytona_manager: DaytonaSessionManager = Depends(get_daytona_session_manager),
):
    session_id = _resolve_session_id(request)
    file_ids = _extract_file_ids(request)
    backend = daytona_manager.get_backend(session_id)

    source_records = None
    sandbox_paths = None
    target_file_id = None
    effective_messages = request.messages

    if file_ids:
        source_records, sandbox_paths, target_file_id, effective_messages = _stage_attached_files(
            request=request,
            backend=backend,
            file_ids=file_ids,
        )

    profile = _extract_profile(request)
    if profile:
        # Profile path: bypass registry; build model directly from profile config
        resolved_model = profile["model"]
        model = build_chat_model(
            profile["provider"],
            profile["model"],
            api_keys={"api_key": profile["api_key"]},
            base_url=profile["base_url"],
            api_version=profile["api_version"],
            deployment=profile["deployment"],
        )
    else:
        # Registry path: existing behaviour unchanged
        resolved_model = _resolve_model_id(request.model)
        user_api_keys = _extract_user_api_keys(request)
        registry = {spec.id: spec for spec in get_model_registry()}
        spec = registry[resolved_model]
        model = build_chat_model(spec.provider, spec.model, api_keys=user_api_keys)

    agent = create_ethos_agent(model=model, backend=backend)

    logger.info(
        "Chat completion request received (model=%s -> %s, session_id=%s, stream=%s, messages=%d, files=%d, client=%s)",
        request.model,
        resolved_model,
        session_id,
        request.stream,
        len(effective_messages),
        len(file_ids),
        http_request.client.host if http_request.client else "unknown",
    )

    if request.stream:
        return StreamingResponse(
            _stream_response(
                agent=agent,
                messages=effective_messages,
                model=resolved_model,
                thread_id=session_id,
                backend=backend,
                source_records=source_records,
                sandbox_paths=sandbox_paths,
                target_file_id=target_file_id,
            ),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    lc_messages = _to_lc_messages(effective_messages)
    config = {"configurable": {"thread_id": session_id}}
    result = await agent.ainvoke({"messages": lc_messages}, config=config)
    last = result["messages"][-1]
    content = _extract_text(last.content)

    output_file = None
    if (
        source_records
        and sandbox_paths
        and target_file_id
        and target_file_id in source_records
        and target_file_id in sandbox_paths
        and source_records[target_file_id].get("filename", "").lower().endswith(".py")
    ):
        output_file = _publish_edited_file(
            source_records[target_file_id],
            backend,
            sandbox_paths[target_file_id],
        )

    response = {
        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": resolved_model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": content},
            "finish_reason": "stop",
        }],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "session_id": session_id,
    }
    if output_file and sandbox_paths and target_file_id:
        response["output_file"] = output_file
        response["sandbox_path"] = sandbox_paths[target_file_id]

    logger.info("Chat completion request finished (model=%s, session_id=%s)", resolved_model, session_id)
    return response


@router.post("/tasks/title")
async def generate_title(request: ChatRequest):
    profile = _extract_profile(request)
    try:
        if profile:
            result = await generate_title_task(
                model_id=profile["model"],
                messages=request.messages,
                api_keys={"api_key": profile["api_key"]},
                profile_provider=profile["provider"],
                profile_model=profile["model"],
                profile_base_url=profile["base_url"],
                profile_api_version=profile["api_version"],
                profile_deployment=profile["deployment"],
            )
        else:
            resolved_model = _resolve_model_id(request.model)
            user_api_keys = _extract_user_api_keys(request)
            result = await generate_title_task(
                model_id=resolved_model,
                messages=request.messages,
                api_keys=user_api_keys,
            )
    except Exception:
        logger.exception("Title generation failed")
        return {"title": fallback_title(request.messages)}

    title = result.title.strip() or fallback_title(request.messages)
    return {"title": title}


@router.post("/tasks/follow-ups")
async def generate_follow_ups(request: ChatRequest):
    profile = _extract_profile(request)
    try:
        if profile:
            result = await generate_follow_ups_task(
                model_id=profile["model"],
                messages=request.messages,
                api_keys={"api_key": profile["api_key"]},
                profile_provider=profile["provider"],
                profile_model=profile["model"],
                profile_base_url=profile["base_url"],
                profile_api_version=profile["api_version"],
                profile_deployment=profile["deployment"],
            )
        else:
            resolved_model = _resolve_model_id(request.model)
            user_api_keys = _extract_user_api_keys(request)
            result = await generate_follow_ups_task(
                model_id=resolved_model,
                messages=request.messages,
                api_keys=user_api_keys,
            )
    except Exception:
        logger.exception("Follow-up generation failed")
        return {"follow_ups": []}

    return {"follow_ups": result.follow_ups}
