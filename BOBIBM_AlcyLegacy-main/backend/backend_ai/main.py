"""Core FastAPI application and authentication middleware for BOB Backend."""

import importlib.util
import os
import secrets
import sys
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse

# ---------------------------------------------------------------------------
# Setup sys.path and alias so standalone execution works seamlessly
# ---------------------------------------------------------------------------
_PKG_DIR = Path(__file__).resolve().parent
for _p in [str(_PKG_DIR), str(_PKG_DIR.parent)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

if "backend" not in sys.modules:
    _spec = importlib.util.spec_from_file_location(
        "backend",
        str(_PKG_DIR / "__init__.py"),
        submodule_search_locations=[str(_PKG_DIR)],
    )
    if _spec and _spec.loader:
        _mod = importlib.util.module_from_spec(_spec)
        sys.modules["backend"] = _mod
        _spec.loader.exec_module(_mod)

from backend.api.routes_analyze import router as analyze_router
from backend.api.routes_health import router as health_router
from backend.api.routes_refactor import router as refactor_router
from backend.config import get_settings


def verify_internal_secret(
    x_internal_secret: Optional[str] = Header(None, alias="X-Internal-Secret")
) -> str:
    """Dependency enforcing the X-Internal-Secret header."""
    settings = get_settings()
    if not x_internal_secret or not secrets.compare_digest(
        x_internal_secret.encode("utf-8"), settings.INTERNAL_API_SECRET.encode("utf-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid X-Internal-Secret header",
        )
    return x_internal_secret


def create_app() -> FastAPI:
    """Application factory for BOB Backend."""
    app = FastAPI(
        title="BOB Backend (Alcy Legacy)",
        description="Internal microservice for static risk diagnostics and modernization with IBM watsonx.ai",
        version="1.0.0",
    )

    @app.middleware("http")
    async def internal_secret_auth_middleware(request: Request, call_next):
        """Enforces X-Internal-Secret authentication on all /internal/v1/* requests."""
        if request.url.path.startswith("/internal/v1"):
            secret_header = request.headers.get("X-Internal-Secret")
            settings = get_settings()
            if not secret_header or not secrets.compare_digest(
                secret_header.encode("utf-8"), settings.INTERNAL_API_SECRET.encode("utf-8")
            ):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Missing or invalid X-Internal-Secret header"},
                )
        return await call_next(request)

    # Register internal API routers
    app.include_router(health_router, prefix="/internal/v1")
    app.include_router(analyze_router, prefix="/internal/v1")
    app.include_router(refactor_router, prefix="/internal/v1")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"Starting BOB Backend AI server on http://{host}:{port} ...")
    uvicorn.run("main:app", host=host, port=port, reload=True)
