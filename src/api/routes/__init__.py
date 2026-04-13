"""API route modules."""

from src.api.routes.files import router as files_router
from src.api.routes.terminals import router as terminals_router
from src.api.routes.v1 import router as v1_router

__all__ = ["v1_router", "files_router", "terminals_router"]
