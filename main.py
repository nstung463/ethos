"""Ethos API server.

OpenAI-compatible API server for Ethos LangGraph agent.

Usage:
    python main.py
    # → http://localhost:8080

Endpoints:
    GET  /v1/models               — list available models
    POST /v1/chat/completions     — chat (streaming + non-streaming)

Connect OpenWebUI:
    Admin → Settings → Connections → OpenAI API
    URL: http://localhost:8080/v1   Key: dummy

Multiple models:
    Set ``ETHOS_MODEL_REGISTRY`` in ``.env`` (JSON array of {id, provider, model}).
    In Open WebUI, pick the model from the chat model dropdown.

Streaming features:
    - Text tokens → streamed as `delta.content`
    - Thinking blocks (Claude extended thinking) → `delta.reasoning_content`
    - Tool calls → shown as status updates in `delta.reasoning_content`
"""

import uvicorn
from api import create_app


def main() -> None:
    """Run the API server."""
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=False)


if __name__ == "__main__":
    main()
