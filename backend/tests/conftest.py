"""Pytest fixtures and configuration for BOB Backend test suite."""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure repo root and scripts directory are in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

for p in [str(REPO_ROOT), str(SCRIPTS_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.main import create_app
from backend.config import get_settings


@pytest.fixture(scope="session")
def app():
    """Create FastAPI application instance for testing."""
    return create_app()


@pytest.fixture(scope="session")
def client(app):
    """TestClient instance for making test HTTP requests."""
    return TestClient(app)


@pytest.fixture(scope="session")
def valid_secret() -> str:
    """Return the configured valid internal API secret."""
    return get_settings().INTERNAL_API_SECRET


@pytest.fixture(scope="session")
def valid_headers(valid_secret: str) -> dict:
    """Return HTTP headers with valid authentication secret."""
    return {
        "X-Internal-Secret": valid_secret,
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="session")
def invalid_headers() -> dict:
    """Return HTTP headers with an invalid authentication secret."""
    return {
        "X-Internal-Secret": "invalid_unauthorized_token_xyz_999",
        "Content-Type": "application/json",
    }
