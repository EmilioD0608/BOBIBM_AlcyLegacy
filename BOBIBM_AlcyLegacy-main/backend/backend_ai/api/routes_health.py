"""Health check endpoint for BOB Backend."""

import datetime
from fastapi import APIRouter
from backend.api.schemas import HealthResponse
from backend.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return service health and operational status."""
    settings = get_settings()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return HealthResponse(
        status="ok",
        service=settings.SERVICE_NAME,
        version=settings.SERVICE_VERSION,
        timestamp=now_iso,
    )
