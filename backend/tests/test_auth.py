"""Tests for X-Internal-Secret authentication middleware and security dependency."""

import pytest
from fastapi import HTTPException
from backend.main import verify_internal_secret


def test_auth_missing_header_returns_401(client):
    """Requests to /internal/v1/* without X-Internal-Secret header must return 401."""
    response = client.get("/internal/v1/health")
    assert response.status_code == 401
    data = response.json()
    assert data == {"detail": "Missing or invalid X-Internal-Secret header"}


def test_auth_invalid_header_returns_401(client, invalid_headers):
    """Requests with incorrect X-Internal-Secret header must return 401."""
    response = client.get("/internal/v1/health", headers=invalid_headers)
    assert response.status_code == 401
    data = response.json()
    assert data == {"detail": "Missing or invalid X-Internal-Secret header"}


def test_auth_empty_header_returns_401(client):
    """Requests with empty X-Internal-Secret header must return 401."""
    response = client.get("/internal/v1/health", headers={"X-Internal-Secret": ""})
    assert response.status_code == 401
    data = response.json()
    assert data == {"detail": "Missing or invalid X-Internal-Secret header"}


def test_auth_valid_header_returns_200(client, valid_headers):
    """Requests with valid X-Internal-Secret header must succeed with 200."""
    response = client.get("/internal/v1/health", headers=valid_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_verify_internal_secret_dependency_valid(valid_secret):
    """Dependency verify_internal_secret returns secret if valid."""
    result = verify_internal_secret(valid_secret)
    assert result == valid_secret


def test_verify_internal_secret_dependency_invalid():
    """Dependency verify_internal_secret raises HTTPException 401 if invalid."""
    with pytest.raises(HTTPException) as exc_info:
        verify_internal_secret("wrong_token_123")
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Missing or invalid X-Internal-Secret header"


def test_verify_internal_secret_dependency_none():
    """Dependency verify_internal_secret raises HTTPException 401 if None."""
    with pytest.raises(HTTPException) as exc_info:
        verify_internal_secret(None)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Missing or invalid X-Internal-Secret header"
