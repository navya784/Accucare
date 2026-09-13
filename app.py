"""Compatibility entry point for `uvicorn app:app`.

The real FastAPI application lives in `backend.app.main`.
"""

from backend.app.main import app
