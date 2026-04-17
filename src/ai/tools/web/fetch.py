"""web_fetch tool — fetch URL content and return as plain text.

Mirrors WebFetchTool from claude-code-source:
  - Input: url (validated URL), prompt (extraction hint shown to agent)
  - Output: plain-text content (HTML stripped) or error message

Unlike the TypeScript version, we return raw extracted text directly.
The calling agent applies its own reasoning rather than a second LLM call.
"""
from __future__ import annotations

import time
import re
from typing import Optional

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

MAX_CONTENT_LENGTH = 100_000  # chars — mirrors TS maxResultSizeChars


class WebFetchInput(BaseModel):
    url: str = Field(description="The URL to fetch content from.")
    prompt: str = Field(
        description=(
            "Describe what information you want to extract from this page. "
            "Example: 'List all API endpoints', 'Summarize the main points'."
        )
    )


def _strip_html(html: str) -> str:
    """Remove HTML tags and decode common entities."""
    # Remove script and style blocks
    html = re.sub(r"<(script|style)[^>]*>.*?</(script|style)>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Remove all tags
    text = re.sub(r"<[^>]+>", " ", html)
    # Decode common entities
    for entity, char in [("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                          ("&nbsp;", " "), ("&quot;", '"'), ("&#39;", "'")]:
        text = text.replace(entity, char)
    # Collapse whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _fetch(url: str, prompt: str) -> str:
    if httpx is None:
        return "Error: httpx not installed. Run: pip install httpx"

    start = time.monotonic()
    try:
        response = httpx.get(
            url,
            follow_redirects=True,
            timeout=30.0,
            headers={"User-Agent": "Mozilla/5.0 (compatible; EthosAgent/1.0)"},
        )
    except Exception as exc:
        return f"Fetch error: {exc}"

    elapsed_ms = int((time.monotonic() - start) * 1000)
    code = response.status_code

    if code >= 400:
        return (
            f"HTTP {code} {response.reason_phrase} fetching {url}\n"
            f"(elapsed: {elapsed_ms}ms)"
        )

    content_type = response.headers.get("content-type", "")
    raw = response.text

    if "html" in content_type or raw.lstrip().startswith("<"):
        text = _strip_html(raw)
    else:
        text = raw  # JSON, plain text, etc.

    if len(text) > MAX_CONTENT_LENGTH:
        text = text[:MAX_CONTENT_LENGTH] + f"\n\n[Truncated: content exceeded {MAX_CONTENT_LENGTH} chars]"

    return (
        f"URL: {url}\n"
        f"Status: {code} {response.reason_phrase}\n"
        f"Size: {len(response.content)} bytes\n"
        f"Elapsed: {elapsed_ms}ms\n"
        f"Prompt hint: {prompt}\n\n"
        f"{text}"
    )


web_fetch_tool = StructuredTool.from_function(
    name="web_fetch",
    func=_fetch,
    description=(
        "Fetch and extract text content from a URL. "
        "Use for reading documentation, web pages, or any URL the agent needs to inspect. "
        "HTML is stripped to plain text. Content is truncated at 100K chars."
    ),
    args_schema=WebFetchInput,
)
