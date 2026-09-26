"""Tests for /internal/v1/health endpoint."""

import datetime
from backend.api.schemas import HealthResponse
from backend.config import get_settings


def test_health_endpoint_success(client, valid_headers):
    """GET /internal/v1/health returns status 200 and expected schema keys."""
    response = client.get("/internal/v1/health", headers=valid_headers)
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "service" in data
    assert "version" in data
    assert "timestamp" in data

    assert data["status"] == "ok"
    assert data["service"] == get_settings().SERVICE_NAME
    assert data["version"] == get_settings().SERVICE_VERSION

    # Validate that payload conforms strictly to HealthResponse schema
    validated = HealthResponse.model_validate(data)
    assert validated.status == "ok"
    assert validated.service == get_settings().SERVICE_NAME


def test_health_timestamp_is_valid_iso(client, valid_headers):
    """Health endpoint must return a valid ISO 8601 timestamp."""
    response = client.get("/internal/v1/health", headers=valid_headers)
    assert response.status_code == 200
    data = response.json()
    ts = data["timestamp"]
    parsed_date = datetime.datetime.fromisoformat(ts)
    assert parsed_date is not None


def test_coordinacion_backends_schemas_validation():
    """Verify that all schemas match the specification payloads in COORDINACION_BACKENDS.md."""
    from backend.api.schemas import (
        AnalyzeRequest,
        AnalyzeResponse,
        AnalyzeSummary,
        FileAnalysisResult,
        RefactorRequest,
        RefactorResponse,
        UserSpecs,
    )

    # 1. AnalyzeRequest
    req_payload = {
        "repoPath": "/tmp/repos/user_project_123",
        "targetFiles": ["scripts/legacy_module.py"],
        "scope": "file",
    }
    analyze_req = AnalyzeRequest.model_validate(req_payload)
    assert analyze_req.repoPath == "/tmp/repos/user_project_123"
    assert analyze_req.targetFiles == ["scripts/legacy_module.py"]
    assert analyze_req.scope == "file"

    # 2. AnalyzeResponse
    resp_payload = {
        "success": True,
        "summary": {
            "overallRisk": 87,
            "riskLevel": "high",
            "totalFiles": 1,
            "highRiskFilesCount": 1,
        },
        "files": [
            {
                "filePath": "scripts/legacy_module.py",
                "riskScore": 87,
                "riskLevel": "high",
                "dependencies": 14,
                "coverage": "12%",
                "age": "4.2 años",
                "blockers": [
                    "Alto acoplamiento con 14 módulos críticos",
                    "Sin tests unitarios automatizados detectados",
                    "Uso de variables globales no resueltas",
                ],
                "safeToRefactorDirectly": False,
                "recommendation": "Generar suite de tests de caracterización antes de refactorizar.",
            }
        ],
    }
    analyze_resp = AnalyzeResponse.model_validate(resp_payload)
    assert analyze_resp.success is True
    assert analyze_resp.summary.overallRisk == 87
    assert analyze_resp.summary.riskLevel == "high"
    assert len(analyze_resp.files) == 1
    assert analyze_resp.files[0].safeToRefactorDirectly is False

    # 3. RefactorRequest
    refactor_req_payload = {
        "filePath": "scripts/legacy_module.py",
        "originalCode": "def calculate_price(base_price, customer_type='regular'):\n    if customer_type == 'premium':\n        return round(base_price * 0.85, 2)\n    return round(base_price, 2)",
        "userSpecs": {
            "targetLanguage": "python",
            "targetVersion": "3.12",
            "framework": "standard",
            "customInstructions": "Agregar tipado estricto (PEP 484), dataclasses y docstrings Google-style.",
        },
        "generateTests": True,
    }
    refactor_req = RefactorRequest.model_validate(refactor_req_payload)
    assert refactor_req.filePath == "scripts/legacy_module.py"
    assert refactor_req.userSpecs.targetLanguage == "python"
    assert refactor_req.generateTests is True

    # 4. RefactorResponse
    refactor_resp_payload = {
        "success": True,
        "filePath": "scripts/legacy_module.py",
        "refactoredCode": "from typing import Literal\n\ndef calculate_price(base_price: float, customer_type: Literal['regular', 'premium'] = 'regular') -> float:\n    return round(base_price * 0.85, 2)\n",
        "generatedTests": "import pytest\n",
        "diff": "--- scripts/legacy_module.py (original)\n+++ scripts/legacy_module.py (modernizado)\n",
        "changesSummary": [
            "Tipado estricto PEP 484 añadido",
            "Docstring descriptivo incorporado",
        ],
    }
    refactor_resp = RefactorResponse.model_validate(refactor_resp_payload)
    assert refactor_resp.success is True
    assert len(refactor_resp.changesSummary) == 2

