"""OpenAI-compatible v1 API endpoints."""

import json
import time
import uuid
from pathlib import Path
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from api.deps import get_file_store, get_open_terminal_api_key, get_open_terminal_base_url
from src.config import build_chat_model, get_model_registry
from src.backends.open_terminal import OpenTerminalSandbox
from src.graph import create_ethos_agent
from src.logger import get_logger

from api.models import ChatRequest, Message

logger = get_logger(__name__)
router = APIRouter(prefix="/v1", tags=["v1"])

# ── Agent factory (one compiled graph per model id, cached) ───────────────────
_agent_by_id: dict[str, object] = {}


def _resolve_model_id(model_id: str) -> str:
    """Map client ``model`` to a registry id.

    Open WebUI often caches the default name ``ethos``. If the registry was trimmed
    to a single model (e.g. only OpenRouter after Azure 401), accept that sole model
    instead of 404.
    """
    specs = get_model_registry()
    registry = {s.id: s for s in specs}
    if model_id in registry:
        return model_id
    if len(specs) == 1:
        sole = specs[0].id
        logger.warning(
            "Requested model %r not in registry; using only configured model %r",
            model_id,
            sole,
        )
        return sole
    raise HTTPException(
        status_code=404,
        detail=f"Unknown model: {model_id!r}. Available: {sorted(registry.keys())}",
    )


def _get_agent(model_id: str) -> object:
    """Return compiled agent for ``model_id``."""
    registry = {s.id: s for s in get_model_registry()}
    if model_id not in registry:
        raise HTTPException(
            status_code=500,
            detail=f"Internal: unresolved model id {model_id!r}",
        )
    if model_id not in _agent_by_id:
        spec = registry[model_id]
        m = build_chat_model(spec.provider, spec.model)
        _agent_by_id[model_id] = create_ethos_agent(model=m)
        logger.info("Ethos agent compiled (model_id=%s)", model_id)
    return _agent_by_id[model_id]


logger.info(
    "Ethos API model registry: %s",
    [s.id for s in get_model_registry()],
)


# ── Helper functions ──────────────────────────────────────────────────────────

def _to_lc_messages(messages: list[Message]):
    """Convert OpenAI-format messages to LangChain messages."""
    result = []
    for m in messages:
        if m.role == "system":
            result.append(SystemMessage(content=m.content))
        elif m.role == "assistant":
            result.append(AIMessage(content=m.content))
        else:
            result.append(HumanMessage(content=m.content))
    return result


def _parse_content(content) -> tuple[str, str]:
    """Parse LangChain content into (text, thinking) strings.

    Handles:
    - str: plain text (may contain inline <think> tags)
    - list[dict]: structured blocks with type "text" or "thinking"

    Returns (text, thinking) where thinking goes to reasoning_content.
    """
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
        btype = block.get("type", "")
        if btype == "thinking":
            thinking_parts.append(block.get("thinking", ""))
        elif btype == "text":
            text_parts.append(block.get("text", ""))

    return "".join(text_parts), "".join(thinking_parts)


def _extract_text(content) -> str:
    """Extract plain text only."""
    text, _ = _parse_content(content)
    return text


def _pick_edit_target(request: ChatRequest) -> str | None:
    metadata = request.metadata or {}
    if isinstance(metadata.get("target_file_id"), str):
        return metadata["target_file_id"]
    if isinstance(metadata.get("edit_target_file_id"), str):
        return metadata["edit_target_file_id"]
    return request.file_ids[0] if request.file_ids else None


def _stage_attached_files(
    request: ChatRequest,
) -> tuple[OpenTerminalSandbox, dict[str, dict], dict[str, str], str | None, list[Message]] | None:
    if not request.file_ids:
        return None

    store = get_file_store()
    sandbox = OpenTerminalSandbox(
        base_url=get_open_terminal_base_url(),
        api_key=get_open_terminal_api_key(),
    )
    records: dict[str, dict] = {}
    sandbox_paths: dict[str, str] = {}

    for file_id in request.file_ids:
        record = store.get_file(file_id)
        if not record:
            raise HTTPException(status_code=404, detail=f"Attached file not found: {file_id}")
        filename = record.get("filename", "")
        file_bytes = Path(record["path"]).read_bytes()
        sandbox_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
        sandbox_path = f"/home/user/workspace/{sandbox_filename}"
        upload_response = sandbox.upload_files([(sandbox_path, file_bytes)])
        if not upload_response or upload_response[0].error:
            error = upload_response[0].error if upload_response else "no response from sandbox"
            raise HTTPException(status_code=502, detail=f"Failed to stage file into sandbox: {error}")
        records[file_id] = record
        sandbox_paths[file_id] = sandbox_path

    target_file_id = _pick_edit_target(request)
    target_path = sandbox_paths.get(target_file_id) if target_file_id else None

    attached_lines = [
        f"- {records[file_id].get('filename', file_id)} -> {sandbox_paths[file_id]}"
        for file_id in request.file_ids
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
    return sandbox, records, sandbox_paths, target_file_id, staged_messages


def _publish_edited_file(source_record: dict, sandbox: OpenTerminalSandbox, sandbox_path: str) -> dict:
    store = get_file_store()
    downloads = sandbox.download_files([sandbox_path])
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


def _sse(delta: dict, model: str, finish_reason: str | None = None) -> str:
    """Format a single SSE line with an arbitrary delta dict."""
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


async def _stream(agent: object, messages: list[Message], model: str) -> AsyncIterator[str]:
    """Stream agent response as OpenAI SSE chunks.

    Event mapping:
        on_chat_model_stream  text content      → delta.content
        on_chat_model_stream  thinking block    → delta.reasoning_content
        on_tool_start                           → delta.reasoning_content
    """
    lc_messages = _to_lc_messages(messages)
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    logger.info("Streaming chat request started (model=%s, messages=%d)", model, len(messages))

    async for event in agent.astream_events(
        {"messages": lc_messages}, config=config, version="v2"
    ):
        kind = event["event"]

        # ── LLM token stream ──────────────────────────────────────────────────
        if kind == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            text, thinking = _parse_content(chunk.content)

            if thinking:
                yield _sse({"reasoning_content": thinking}, model)
            if text:
                yield _sse({"content": text}, model)

        # ── Tool invocation start ─────────────────────────────────────────────
        elif kind == "on_tool_start":
            tool_name = event.get("name", "tool")
            tool_input = event["data"].get("input", {})

            if isinstance(tool_input, dict):
                args_preview = ", ".join(
                    f"{k}={repr(v)[:60]}" for k, v in list(tool_input.items())[:3]
                )
            else:
                args_preview = repr(tool_input)[:120]

            status = f"Using tool `{tool_name}`({args_preview})\n"
            logger.info("Tool started during stream (tool=%s)", tool_name)
            yield _sse({"reasoning_content": status}, model)

    logger.info("Streaming chat request finished (model=%s)", model)
    yield _sse({}, model, finish_reason="stop")
    yield "data: [DONE]\n\n"


async def _stream_with_context(
    agent: object,
    messages: list[Message],
    model: str,
    *,
    sandbox: OpenTerminalSandbox | None = None,
    source_records: dict[str, dict] | None = None,
    sandbox_paths: dict[str, str] | None = None,
    target_file_id: str | None = None,
) -> AsyncIterator[str]:
    """Stream chat events and publish edited output file at the end when applicable."""
    lc_messages = _to_lc_messages(messages)
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    logger.info("Streaming chat request started (model=%s, messages=%d)", model, len(messages))

    async for event in agent.astream_events(
        {"messages": lc_messages}, config=config, version="v2"
    ):
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
                args_preview = ", ".join(
                    f"{k}={repr(v)[:60]}" for k, v in list(tool_input.items())[:3]
                )
            else:
                args_preview = repr(tool_input)[:120]

            status = f"Using tool `{tool_name}`({args_preview})\n"
            logger.info("Tool started during stream (tool=%s)", tool_name)
            yield _sse({"reasoning_content": status}, model)

    if (
        sandbox
        and source_records
        and sandbox_paths
        and target_file_id
        and target_file_id in source_records
        and target_file_id in sandbox_paths
        and source_records[target_file_id].get("filename", "").lower().endswith(".py")
    ):
        try:
            output_file = _publish_edited_file(
                source_records[target_file_id],
                sandbox,
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
                {
                    "reasoning_content": f"Edited file was created in sandbox but publishing failed: {exc}",
                },
                model,
            )

    logger.info("Streaming chat request finished (model=%s)", model)
    yield _sse({}, model, finish_reason="stop")
    yield "data: [DONE]\n\n"


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/models")
async def list_models():
    """List available models."""
    logger.debug("List models endpoint called")
    now = int(time.time())
    data = [
        {
            "id": spec.id,
            "object": "model",
            "created": now,
            "owned_by": "ethos",
        }
        for spec in get_model_registry()
    ]
    return {"object": "list", "data": data}


@router.post("/chat/completions")
async def chat_completions(request: ChatRequest):
    """OpenAI-compatible chat completion endpoint."""
    resolved_model = _resolve_model_id(request.model)
    staged = _stage_attached_files(request)
    if staged:
        sandbox, source_records, sandbox_paths, target_file_id, effective_messages = staged
        registry = {s.id: s for s in get_model_registry()}
        spec = registry[resolved_model]
        model = build_chat_model(spec.provider, spec.model)
        agent = create_ethos_agent(model=model, backend=sandbox)
    else:
        sandbox = None
        source_records = None
        sandbox_paths = None
        target_file_id = None
        effective_messages = request.messages
        agent = _get_agent(resolved_model)
    logger.info(
        "Chat completion request received (model=%s -> %s, stream=%s, messages=%d)",
        request.model,
        resolved_model,
        request.stream,
        len(effective_messages),
    )
    if request.stream:
        return StreamingResponse(
            _stream_with_context(
                agent,
                effective_messages,
                resolved_model,
                sandbox=sandbox,
                source_records=source_records,
                sandbox_paths=sandbox_paths,
                target_file_id=target_file_id,
            ),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # Non-streaming: collect full result
    lc_messages = _to_lc_messages(effective_messages)
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    result = await agent.ainvoke({"messages": lc_messages}, config=config)
    last = result["messages"][-1]
    content = _extract_text(last.content)
    output_file = None
    if (
        sandbox
        and source_records
        and sandbox_paths
        and target_file_id
        and target_file_id in source_records
        and target_file_id in sandbox_paths
        and source_records[target_file_id].get("filename", "").lower().endswith(".py")
    ):
        output_file = _publish_edited_file(source_records[target_file_id], sandbox, sandbox_paths[target_file_id])
    logger.info(
        "Chat completion request finished (model=%s, stream=%s)",
        resolved_model,
        request.stream,
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
    }
    if output_file:
        response["output_file"] = output_file
        response["sandbox_path"] = sandbox_paths[target_file_id]
    return response
