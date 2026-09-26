"""Pytest fixtures and configuration for BOB Backend test suite."""

import importlib.util
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Path Setup
# ---------------------------------------------------------------------------
# Directory layout after rename:
#   BOBIBM_AlcyLegacy-main/
#     backend/
#       backend_ai/          ← this package (was called "backend")
#         tests/
#           conftest.py      ← this file
#     scripts/
#
BACKEND_AI_DIR = Path(__file__).resolve().parent.parent   # .../backend/backend_ai
ROOT_SCRIPTS_DIR = BACKEND_AI_DIR.parent.parent.parent / "scripts"  # Monorepo root scripts
WS_SCRIPTS_DIR = BACKEND_AI_DIR.parent.parent / "scripts"           # BOBIBM_AlcyLegacy-main/scripts

for p in [str(BACKEND_AI_DIR.parent), str(ROOT_SCRIPTS_DIR), str(WS_SCRIPTS_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ---------------------------------------------------------------------------
# Module alias: expose backend_ai as `backend` so all existing test imports
# (`from backend.main import ...`) continue to work without modification.
# ---------------------------------------------------------------------------
if "backend" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "backend",
        str(BACKEND_AI_DIR / "__init__.py"),
        submodule_search_locations=[str(BACKEND_AI_DIR)],
    )
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules["backend"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]

from backend.main import create_app  # noqa: E402
from backend.config import get_settings  # noqa: E402


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

