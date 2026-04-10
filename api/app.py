"""FastAPI app initialization and middleware configuration."""

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.logger import setup_logging

from api.routes import files_router, terminals_router, v1_router

load_dotenv()
setup_logging()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Ethos API",
        version="1.0.0",
        description="OpenAI-compatible API for Ethos LangGraph agent",
    )

    # ── CORS middleware ────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routes ────────────────────────────────────────────────────────────
    app.include_router(v1_router)
    app.include_router(files_router)
    app.include_router(terminals_router)

    return app
