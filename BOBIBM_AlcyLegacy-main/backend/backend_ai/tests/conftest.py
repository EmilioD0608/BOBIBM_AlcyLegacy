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
SCRIPTS_DIR = BACKEND_AI_DIR.parent.parent / "scripts"    # .../BOBIBM_AlcyLegacy-main/scripts

for p in [str(BACKEND_AI_DIR.parent), str(SCRIPTS_DIR)]:
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


@pytest.fixture(scope="session", autouse=True)
def configure_test_sandbox():
    """Set ALLOWED_REPO_ROOT to the monorepo root for tests.

    The B-02 sandbox check validates that repoPath is inside ALLOWED_REPO_ROOT.
    In production this is /tmp/repos; in tests we allow the full monorepo so
    test fixtures using local paths are accepted.
    """
    import os
    from backend.api import routes_analyze

    monorepo_root = str(BACKEND_AI_DIR.parent.parent.parent)  # .../BOBIBM_AlcyLegacy
    os.environ.setdefault("ALLOWED_REPO_ROOT", monorepo_root)

    # Reload the module-level ALLOWED_ROOT constant to reflect the env override
    from pathlib import Path as _Path
    routes_analyze.ALLOWED_ROOT = _Path(monorepo_root).resolve()
    yield
    # Cleanup: restore to default after session
    routes_analyze.ALLOWED_ROOT = _Path(
        os.environ.get("ALLOWED_REPO_ROOT", "/tmp/repos")
    ).resolve()
