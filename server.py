"""OpenAI-compatible API server for Ethos LangGraph agent.

Usage:
    uv run python server.py
    # → http://localhost:8000

Endpoints:
    GET  /v1/models               — list available models
    POST /v1/chat/completions     — chat (streaming + non-streaming)

Connect OpenWebUI:
    Admin → Settings → Connections → OpenAI API
    URL: http://localhost:8000/v1   Key: dummy

Streaming features:
    - Text tokens → streamed as `delta.content`
    - Thinking blocks (Claude extended thinking) → `delta.reasoning_content`
    - Inline <think> tags (Qwen, DeepSeek) → passed through in content, OpenWebUI renders natively
    - Tool calls → shown in `delta.reasoning_content` as status updates
"""

import json
import time
import uuid
from typing import AsyncIterator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel

load_dotenv()

# ── Build agent once at startup ────────────────────────────────────────────────
from src.graph import create_ethos_agent

_agent = create_ethos_agent()

# ── FastAPI app ────────────────────────────────────────────────────────────────
app = FastAPI(title="Ethos API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request models ─────────────────────────────────────────────────────────────

class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str = "ethos"
    messages: list[Message]
    stream: bool = False

    model_config = {"extra": "allow"}  # ignore unknown OpenWebUI fields


# ── Helpers ────────────────────────────────────────────────────────────────────

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
    - str: plain text (may contain inline <think> tags — passed as-is)
    - list[dict]: Anthropic structured blocks with type "text" or "thinking"

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
        # skip "tool_use" blocks — tool calls are handled via on_tool_start

    return "".join(text_parts), "".join(thinking_parts)


def _extract_text(content) -> str:
    """Extract plain text only (for non-streaming responses)."""
    text, _ = _parse_content(content)
    return text


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


async def _stream(messages: list[Message], model: str) -> AsyncIterator[str]:
    """Stream agent response as OpenAI SSE chunks.

    Event mapping:
        on_chat_model_stream  text content      → delta.content
        on_chat_model_stream  thinking block    → delta.reasoning_content
        on_tool_start                           → delta.reasoning_content  (tool status)
    """
    lc_messages = _to_lc_messages(messages)
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    async for event in _agent.astream_events(
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

            # Summarise args — avoid dumping huge payloads
            if isinstance(tool_input, dict):
                args_preview = ", ".join(
                    f"{k}={repr(v)[:60]}" for k, v in list(tool_input.items())[:3]
                )
            else:
                args_preview = repr(tool_input)[:120]

            status = f"Using tool `{tool_name}`({args_preview})\n"
            yield _sse({"reasoning_content": status}, model)

    yield _sse({}, model, finish_reason="stop")
    yield "data: [DONE]\n\n"


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [{
            "id": "ethos",
            "object": "model",
            "created": int(time.time()),
            "owned_by": "local",
        }],
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    if request.stream:
        return StreamingResponse(
            _stream(request.messages, request.model),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # Non-streaming: collect full result
    lc_messages = _to_lc_messages(request.messages)
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    result = await _agent.ainvoke({"messages": lc_messages}, config=config)
    last = result["messages"][-1]
    content = _extract_text(last.content)

    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": content},
            "finish_reason": "stop",
        }],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=False)
