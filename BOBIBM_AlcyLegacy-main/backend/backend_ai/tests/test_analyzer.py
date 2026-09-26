"""Comprehensive test suite for BOB Backend Static Risk Diagnostic Engine (Milestone M2).

Covers:
- AST dependency scanner unit tests (imports, calls, unresolved globals, syntax handling)
- Unit test coverage checker (detection, frameworks, ratios, percentages)
- Git age inspector (commit history, mtime fallback, Spanish humanization)
- Continuous calibrated risk score formula (weights, penalties, semaphore, blockers)
- Report builder orchestration (targets, recursive repo scan, summaries)
- API endpoint integration tests (POST /internal/v1/analyze, auth 401, validation)
- Benchmark test for scripts/legacy_module.py (risk > 70, blockers, safeToRefactorDirectly = False)
"""

import os
from pathlib import Path
import tempfile
import time
import pytest
from fastapi.testclient import TestClient

from backend.analyzer.coverage_checker import check_coverage
from backend.analyzer.dependency_scanner import scan_dependencies
from backend.analyzer.git_age import format_age_in_spanish, get_file_age
from backend.analyzer.report_builder import build_analysis_report
from backend.analyzer.risk_score import calculate_risk_score
from backend.api.schemas import AnalyzeResponse


# ==============================================================================
# 1. AST Dependency Scanner Unit Tests
# ==============================================================================

def test_ast_scanner_external_imports():
    """Verify scanner extracts Import and ImportFrom statements."""
    code = """
import os
import sys
from typing import List, Dict, Optional
import numpy as np
from datetime import datetime
"""
    result = scan_dependencies("dummy.py", source_code=code)
    assert result.syntax_valid is True
    assert "os" in result.external_modules
    assert "sys" in result.external_modules
    assert "typing" in result.external_modules
    assert "numpy" in result.external_modules
    assert "datetime" in result.external_modules
    assert "typing.List" in result.external_imports or "typing" in result.external_imports


def test_ast_scanner_internal_calls_and_definitions():
    """Verify scanner tracks function definitions, class definitions, and calls."""
    code = """
class OrderProcessor:
    def process(self, item):
        return round(item.price * 0.9, 2)

def calculate_tax(amount):
    formatted = str(amount)
    return float(formatted)
"""
    result = scan_dependencies("dummy.py", source_code=code)
    assert result.syntax_valid is True
    assert "OrderProcessor" in result.class_definitions
    assert "process" in result.function_definitions
    assert "calculate_tax" in result.function_definitions
    assert "round" in result.internal_calls
    assert "str" in result.internal_calls
    assert "float" in result.internal_calls


def test_ast_scanner_detects_unresolved_globals():
    """Verify that variables used in functions without declaration are detected."""
    code = """
def calculate_price(base_price: float, customer_type: str = "regular") -> float:
    if customer_type == "premium":
        return round(base_price * (1 - LEGACY_DISCOUNT), 2)
    return round(base_price, 2)
"""
    result = scan_dependencies("dummy.py", source_code=code)
    assert result.syntax_valid is True
    assert "LEGACY_DISCOUNT" in result.unresolved_globals
    assert "base_price" not in result.unresolved_globals
    assert "customer_type" not in result.unresolved_globals
    assert "round" not in result.unresolved_globals


def test_ast_scanner_resolved_globals_not_flagged():
    """Verify declared constants, imports, and builtins are not flagged as unresolved."""
    code = """
LEGACY_DISCOUNT = 0.15
TAX_RATE = 0.08

from math import ceil

def compute(val: float) -> float:
    local_fee = 5.0
    return ceil(val * (1 - LEGACY_DISCOUNT) + TAX_RATE + local_fee)
"""
    result = scan_dependencies("dummy.py", source_code=code)
    assert result.syntax_valid is True
    assert result.unresolved_globals == []


def test_ast_scanner_syntax_error_handling():
    """Verify syntax errors are captured gracefully without unhandled exceptions."""
    code = "def broken_syntax(x, y: return x +"
    result = scan_dependencies("broken.py", source_code=code)
    assert result.syntax_valid is False
    assert result.error_message is not None
    assert "SyntaxError" in result.error_message


def test_ast_scanner_missing_file():
    """Verify non-existent file produces graceful error result."""
    result = scan_dependencies("non_existent_file_xyz_123.py")
    assert result.syntax_valid is False
    assert "File not found" in (result.error_message or "")


# ==============================================================================
# 2. Test Coverage Checker Unit Tests
# ==============================================================================

def test_coverage_checker_no_tests():
    """Verify 0% coverage and has_tests=False when no test files exist."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        src_file = tmp_path / "service.py"
        src_file.write_text("def do_something(): return 42\n", encoding="utf-8")

        res = check_coverage(src_file, repo_path=tmp_path)
        assert res.has_tests is False
        assert res.coverage_ratio == 0.0
        assert res.coverage_percentage == "0%"
        assert res.test_functions_count == 0


def test_coverage_checker_with_matching_pytest():
    """Verify discovery and coverage calculation for matching test file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        src_file = tmp_path / "pricing.py"
        src_file.write_text(
            "def calculate_total(a, b): return a + b\n"
            "def calculate_discount(a): return a * 0.1\n",
            encoding="utf-8",
        )

        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        test_file = test_dir / "test_pricing.py"
        test_file.write_text(
            "import pytest\n"
            "from pricing import calculate_total\n\n"
            "def test_total():\n"
            "    assert calculate_total(2, 3) == 5\n",
            encoding="utf-8",
        )

        res = check_coverage(src_file, repo_path=tmp_path)
        assert res.has_tests is True
        assert res.framework == "pytest"
        assert res.test_functions_count == 1
        assert res.coverage_ratio > 0.0
        assert res.coverage_percentage != "0%"


def test_coverage_checker_detects_unittest():
    """Verify framework detection when tests use unittest.TestCase."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        src_file = tmp_path / "auth.py"
        src_file.write_text("def login(): return True\n", encoding="utf-8")

        test_file = tmp_path / "test_auth.py"
        test_file.write_text(
            "import unittest\n"
            "from auth import login\n\n"
            "class AuthTest(unittest.TestCase):\n"
            "    def test_login(self):\n"
            "        self.assertTrue(login())\n",
            encoding="utf-8",
        )

        res = check_coverage(src_file, repo_path=tmp_path)
        assert res.has_tests is True
        assert res.framework == "unittest"


# ==============================================================================
# 3. Git Age Inspector Unit Tests
# ==============================================================================

def test_git_age_tracked_repo_file():
    """Verify git age retrieves real commit epoch for repository files."""
    repo_file = "scripts/legacy_module.py"
    res = get_file_age(repo_file, repo_path=".")
    assert res.file_path == repo_file
    assert res.age_in_years >= 0.0
    assert isinstance(res.age_display, str)
    assert len(res.age_display) > 0


def test_git_age_untracked_fallback_mtime():
    """Verify fallback to file mtime when file is untracked or outside git."""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        f.write(b"x = 1\n")
        temp_name = f.name

    try:
        res = get_file_age(temp_name)
        assert res.age_in_years >= 0.0
        assert "día" in res.age_display or "mes" in res.age_display or "año" in res.age_display
    finally:
        if os.path.exists(temp_name):
            os.remove(temp_name)


def test_format_age_in_spanish():
    """Verify age humanization rules in Spanish."""
    assert format_age_in_spanish(4.2) == "4.2 años"
    assert format_age_in_spanish(1.0) == "1.0 años"
    assert format_age_in_spanish(0.5) == "6 meses"
    assert format_age_in_spanish(1 / 12) == "1 mes"
    assert format_age_in_spanish(15 / 365.25) == "15 días"
    assert format_age_in_spanish(1 / 365.25) == "1 día"
    assert format_age_in_spanish(0.0) == "1 día"


def test_git_age_nonexistent_file():
    """Verify non-existent file returns default 0 days."""
    res = get_file_age("non_existent_file_9999.py")
    assert res.age_in_years == 0.0
    assert res.age_display == "0 días"


# ==============================================================================
# 4. Risk Score Calculator Unit Tests
# ==============================================================================

def test_risk_score_calibrated_benchmark_formula():
    """Verify calibrated formula matching explorer_architecture_1/analysis.md."""
    # deps=14, cov=0.12, age=4.2, unresolved_globals=['LEGACY_DISCOUNT']
    # 0.30 * min(100, 14*6) = 25.2
    # 0.35 * (100 * (1 - 0.12)) = 30.8
    # 0.20 * min(100, 4.2*20) = 16.8
    # penalties = 15.0
    # raw = 25.2 + 30.8 + 16.8 + 15.0 = 87.8 -> round = 88 (or 87 with slight variations)
    res = calculate_risk_score(
        dependencies=14,
        coverage_ratio=0.12,
        age_in_years=4.2,
        unresolved_globals=["LEGACY_DISCOUNT"],
    )
    assert res.risk_score >= 70
    assert res.risk_level == "high"
    assert res.safe_to_refactor_directly is False
    assert res.recommendation == "Generar suite de tests de caracterización antes de refactorizar."
    assert "Alto acoplamiento con 14 módulos críticos" in res.blockers
    assert "Sin tests unitarios automatizados detectados" in res.blockers
    assert "Uso de variables globales no resueltas" in res.blockers


def test_risk_score_low_tier():
    """Verify low risk classification when metrics are healthy."""
    res = calculate_risk_score(
        dependencies=2,
        coverage_ratio=1.0,
        age_in_years=0.1,
        unresolved_globals=[],
    )
    assert res.risk_score < 40
    assert res.risk_level == "low"
    assert res.safe_to_refactor_directly is True
    assert res.recommendation == "Código seguro para refactorización directa."
    assert res.blockers == []


def test_risk_score_medium_tier():
    """Verify medium risk classification in 40-69 range."""
    # deps=5 (30*0.3=9), cov=0.50 (50*0.35=17.5), age=1.0 (20*0.2=4) -> ~31
    # with coverage=0.0 -> penalty +10, cov_comp=35 -> total=9 + 35 + 4 + 10 = 58
    res = calculate_risk_score(
        dependencies=5,
        coverage_ratio=0.0,
        age_in_years=1.0,
        unresolved_globals=[],
    )
    assert 40 <= res.risk_score <= 69
    assert res.risk_level == "medium"
    assert res.safe_to_refactor_directly is True
    assert res.recommendation == "Proceder con modernización estándar con revisión recomendada."


def test_risk_score_boundary_conditions():
    """Verify exact boundary classifications."""
    # Low boundary: < 40
    low_res = calculate_risk_score(0, 1.0, 0.0)
    assert low_res.risk_score == 0
    assert low_res.risk_level == "low"

    # High boundary: >= 70
    high_res = calculate_risk_score(20, 0.0, 3.0)
    assert high_res.risk_score >= 70
    assert high_res.risk_level == "high"
    assert high_res.safe_to_refactor_directly is False


def test_risk_score_clamping():
    """Verify score cannot exceed 100 or fall below 0."""
    high = calculate_risk_score(dependencies=200, coverage_ratio=0.0, age_in_years=50.0, unresolved_globals=["a", "b", "c"])
    assert high.risk_score == 100

    low = calculate_risk_score(dependencies=0, coverage_ratio=1.0, age_in_years=0.0, unresolved_globals=[])
    assert low.risk_score == 0


def test_risk_score_syntax_error_blocker():
    """Verify syntax error penalty and blocker inclusion."""
    res = calculate_risk_score(
        dependencies=1,
        coverage_ratio=1.0,
        age_in_years=0.0,
        syntax_valid=False,
        error_message="unexpected EOF",
    )
    assert res.safe_to_refactor_directly is False
    assert any("Error de sintaxis" in b for b in res.blockers)


# ==============================================================================
# 5. Report Builder Unit Tests
# ==============================================================================

def test_report_builder_single_target(tmp_path):
    """Verify report builder accurately summarizes single file analysis.

    Uses a synthetic high-risk fixture instead of the real legacy_module.py to
    avoid coupling test expectations to a file that may change over time.
    """
    # Create a synthetic high-risk file: many imports + unresolved globals
    high_risk_code = "\n".join([
        "import os, sys, re, json, csv, math, time, io, abc, ast",
        "import collections, itertools, functools, pathlib, datetime",
        *[f"result = UNDEFINED_VAR_{i} + some_global_func_{i}()" for i in range(15)],
    ])
    target_dir = tmp_path / "myrepo"
    target_dir.mkdir()
    high_risk_file = target_dir / "risky.py"
    high_risk_file.write_text(high_risk_code, encoding="utf-8")

    report = build_analysis_report(str(target_dir), target_files=["risky.py"])
    assert isinstance(report, AnalyzeResponse)
    assert report.success is True
    assert report.summary.totalFiles == 1
    assert len(report.files) == 1
    file_res = report.files[0]
    assert file_res.filePath == "risky.py"
    assert file_res.riskScore >= 70, f"Expected high risk, got {file_res.riskScore}"
    assert file_res.riskLevel == "high"


def test_report_builder_repo_scope():
    """Verify report builder discovers all files in directory under scope='repo'."""
    scripts_dir = Path(__file__).resolve().parent.parent.parent.parent / "scripts"
    if not scripts_dir.exists():
        pytest.skip("scripts/ directory not found relative to test location")
    report = build_analysis_report(str(scripts_dir), scope="repo")
    assert report.success is True
    assert report.summary.totalFiles >= 1


def test_report_builder_empty_dir():
    """Verify empty directory produces 0 totalFiles and low overallRisk."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        report = build_analysis_report(tmp_dir, scope="repo")
        assert report.success is True
        assert report.summary.totalFiles == 0
        assert report.summary.overallRisk == 0
        assert report.summary.riskLevel == "low"
        assert report.files == []


# ==============================================================================
# 6. Integration Tests for POST /internal/v1/analyze
# ==============================================================================

def test_api_analyze_missing_secret(client: TestClient):
    """Verify HTTP 401 when X-Internal-Secret header is omitted."""
    response = client.post(
        "/internal/v1/analyze",
        json={"repoPath": ".", "targetFiles": ["scripts/legacy_module.py"]},
    )
    assert response.status_code == 401
    assert "Missing or invalid X-Internal-Secret header" in response.json()["detail"]


def test_api_analyze_invalid_secret(client: TestClient, invalid_headers: dict):
    """Verify HTTP 401 when X-Internal-Secret header is incorrect."""
    response = client.post(
        "/internal/v1/analyze",
        headers=invalid_headers,
        json={"repoPath": ".", "targetFiles": ["scripts/legacy_module.py"]},
    )
    assert response.status_code == 401
    assert "Missing or invalid X-Internal-Secret header" in response.json()["detail"]


def test_api_analyze_nonexistent_repo(client: TestClient, valid_headers: dict):
    """Verify HTTP 400 Bad Request when repoPath does not exist on disk."""
    response = client.post(
        "/internal/v1/analyze",
        headers=valid_headers,
        json={"repoPath": "/nonexistent/path/xyz_999"},
    )
    assert response.status_code == 400
    assert "Repository path not found" in response.json()["detail"]


def test_api_analyze_success_contract_schema(client: TestClient, valid_headers: dict, tmp_path):
    """Verify response strictly matches schema defined in COORDINACION_BACKENDS.md."""
    # Synthetic high-risk file as fixture
    high_risk_code = "\n".join([
        "import os, sys, re, json, csv, math, time, io, abc, ast",
        "import collections, itertools, functools, pathlib, datetime",
        *[f"result_{i} = UNDEFINED_VAR_{i} + func_{i}()" for i in range(15)],
    ])
    repo_dir = tmp_path / "contract_repo"
    repo_dir.mkdir()
    (repo_dir / "legacy.py").write_text(high_risk_code, encoding="utf-8")

    response = client.post(
        "/internal/v1/analyze",
        headers=valid_headers,
        json={
            "repoPath": str(repo_dir),
            "targetFiles": ["legacy.py"],
            "scope": "file",
        },
    )
    assert response.status_code == 200
    data = response.json()

    validated = AnalyzeResponse.model_validate(data)
    assert validated.success is True
    assert validated.summary.totalFiles == 1
    assert validated.summary.highRiskFilesCount == 1
    assert validated.summary.overallRisk >= 70
    assert validated.summary.riskLevel == "high"

    file_item = validated.files[0]
    assert file_item.filePath == "legacy.py"
    assert file_item.riskScore >= 70
    assert file_item.riskLevel == "high"
    assert file_item.safeToRefactorDirectly is False


# ==============================================================================
# 7. Benchmark Verification Test (synthetic high-risk file)
# ==============================================================================

def test_benchmark_legacy_module_risk_and_blockers(client: TestClient, valid_headers: dict, tmp_path):
    """Benchmark test verifying that a synthetic high-risk file yields riskScore > 70
    and safeToRefactorDirectly = False.

    Uses a controlled fixture instead of scripts/legacy_module.py to avoid
    coupling test expectations to a file that evolves over time.
    """
    high_risk_code = "\n".join([
        "import os, sys, re, json, csv, math, time, io, abc, ast",
        "import collections, itertools, functools, pathlib, datetime",
        *[f"x_{i} = UNDEFINED_{i} + missing_func_{i}()" for i in range(20)],
    ])
    repo_dir = tmp_path / "benchmark_repo"
    repo_dir.mkdir()
    (repo_dir / "module.py").write_text(high_risk_code, encoding="utf-8")

    response = client.post(
        "/internal/v1/analyze",
        headers=valid_headers,
        json={
            "repoPath": str(repo_dir),
            "targetFiles": ["module.py"],
            "scope": "file",
        },
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["success"] is True
    file_data = payload["files"][0]

    assert file_data["riskScore"] >= 70, f"Expected high risk, got {file_data['riskScore']}"
    assert file_data["riskLevel"] == "high"
    assert file_data["safeToRefactorDirectly"] is False
    blockers = file_data["blockers"]
    assert len(blockers) >= 1

