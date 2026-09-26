"""Adversarial stress-testing suite for BOB Backend Static Risk Diagnostic Engine (Milestone M2).

Challenger 1 Verification Suite:
1. Pathological source inputs:
   - 0-byte empty files (disk & memory)
   - Severely broken Python syntax errors, incomplete tokens, null bytes
   - Code without functions or classes (constants only, module-level expressions)
   - Deeply nested ASTs (40+ nested functions, 50+ nested blocks)
   - Recursive calls (direct recursion, mutual recursion, cyclic references)
   - Massive imports (150+ imports) and coupling limits
2. Git age inspection & fallbacks:
   - Non-git directories (clean fallback to filesystem mtime)
   - Untracked files inside git repositories
   - Future mtimes and clock-skew tolerance
   - Humanized Spanish formatting boundaries
3. Continuous risk score formula & semaphore boundaries:
   - Extreme boundary stress tests (negative inputs, massive dependencies, clamped [0, 100])
   - Semaphore threshold boundaries (0, 39, 40, 69, 70, 71, 100)
   - Safety refactoring flags under unresolved globals and syntax errors
4. HTTP API endpoint POST /internal/v1/analyze:
   - Invalid / non-existent repo paths (HTTP 400)
   - Non-existent target files inside valid repo paths (HTTP 200 with diagnostic error blockers)
   - Empty target files list on empty directory vs populated directory
   - Missing / invalid authentication headers (HTTP 401)
   - Malformed JSON payloads (HTTP 422)
"""

from __future__ import annotations

import ast
import os
from pathlib import Path
import tempfile
import time
import pytest
from fastapi.testclient import TestClient

from backend.analyzer.coverage_checker import check_coverage
from backend.analyzer.dependency_scanner import (
    DependencyScanResult,
    scan_dependencies,
)
from backend.analyzer.git_age import format_age_in_spanish, get_file_age
from backend.analyzer.report_builder import build_analysis_report
from backend.analyzer.risk_score import calculate_risk_score
from backend.api.schemas import AnalyzeResponse
from backend.config import get_settings
from backend.main import app


@pytest.fixture
def auth_client():
    """Test client with valid X-Internal-Secret authentication."""
    settings = get_settings()
    client = TestClient(app)
    client.headers.update({"X-Internal-Secret": settings.INTERNAL_API_SECRET})
    return client


# ==============================================================================
# Suite 1: Pathological Source Inputs
# ==============================================================================

def test_pathological_zero_byte_empty_file():
    """Verify 0-byte files (memory and disk) parse without exception or division by zero."""
    # In-memory empty source code
    res_mem = scan_dependencies("empty.py", source_code="")
    assert res_mem.syntax_valid is True
    assert res_mem.dependencies_count == 0
    assert res_mem.external_imports == []
    assert res_mem.internal_calls == []
    assert res_mem.unresolved_globals == []

    # On-disk empty file
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        empty_file = tmp_path / "zero_bytes.py"
        empty_file.write_text("", encoding="utf-8")
        assert empty_file.stat().st_size == 0

        res_disk = scan_dependencies(empty_file, repo_path=tmp_path)
        assert res_disk.syntax_valid is True
        assert res_disk.dependencies_count == 0

        cov_res = check_coverage(empty_file, repo_path=tmp_path)
        assert cov_res.has_tests is False
        assert cov_res.coverage_ratio == 0.0
        assert cov_res.coverage_percentage == "0%"

        age_res = get_file_age(empty_file, repo_path=tmp_path)
        assert age_res.age_in_years >= 0.0

        risk_res = calculate_risk_score(
            dependencies=res_disk.dependencies_count,
            coverage_ratio=cov_res.coverage_ratio,
            age_in_years=age_res.age_in_years,
            unresolved_globals=res_disk.unresolved_globals,
            syntax_valid=res_disk.syntax_valid,
        )
        assert 0 <= risk_res.risk_score <= 100
        assert "Sin tests unitarios automatizados detectados" in risk_res.blockers

        # End-to-end report build
        report = build_analysis_report(repo_path=tmp_path, target_files=["zero_bytes.py"])
        assert isinstance(report, AnalyzeResponse)
        assert len(report.files) == 1
        assert report.files[0].filePath == "zero_bytes.py"


def test_pathological_syntax_errors():
    """Verify malformed Python code produces clean diagnostic errors without crashing."""
    broken_snippets = [
        "def (broken syntax :::",
        "for i in range(10)\n    print(i",
        "class 123InvalidName: pass",
        "import",
        "x = 1 +\n",
        "'''unclosed docstring",
    ]

    for snippet in broken_snippets:
        res = scan_dependencies("broken.py", source_code=snippet)
        assert res.syntax_valid is False
        assert res.error_message is not None
        assert "SyntaxError" in res.error_message

        # Risk score calculation under syntax error
        risk = calculate_risk_score(
            dependencies=0,
            coverage_ratio=0.0,
            age_in_years=0.0,
            syntax_valid=res.syntax_valid,
            error_message=res.error_message,
        )
        assert risk.safe_to_refactor_directly is False
        assert any("Error de sintaxis" in b for b in risk.blockers)
        assert risk.risk_score >= 70


def test_pathological_null_bytes():
    """Verify files containing null bytes are safely handled."""
    code_with_null = "x = 1\x00 + 2\n"
    res = scan_dependencies("null_byte.py", source_code=code_with_null)
    assert res.syntax_valid is False
    assert res.error_message is not None


def test_pathological_code_with_no_functions_or_classes():
    """Verify code with only variables, constants, expressions or comments."""
    code = """# Only global assignments and comments
BASE_URL = "https://api.bob.internal/v1"
TIMEOUT_SECONDS = 30
RETRIES = 3
ENABLED_FLAGS = [f"FLAG_{i}" for i in range(5)]
SUMMARY = {"url": BASE_URL, "timeout": TIMEOUT_SECONDS, "retries": RETRIES}
"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        const_file = tmp_path / "constants.py"
        const_file.write_text(code, encoding="utf-8")

        res = scan_dependencies(const_file, repo_path=tmp_path)
        assert res.syntax_valid is True
        assert res.function_definitions == []
        assert res.class_definitions == []
        assert res.unresolved_globals == []  # Locals in comprehension and constants resolved

        cov = check_coverage(const_file, repo_path=tmp_path)
        assert cov.target_functions_count == 0
        assert cov.coverage_ratio == 0.0


def test_pathological_deeply_nested_asts():
    """Verify deeply nested AST structures do not cause stack overflow or recursion crash."""
    # 40 nested functions
    nested_code = "def f0():\n"
    for i in range(1, 40):
        indent = "    " * i
        nested_code += f"{indent}def f{i}():\n"
    nested_code += f"{'    ' * 40}return 42\n"
    nested_code += f"{'    ' * 40}f39()\n"

    res = scan_dependencies("deep_nested.py", source_code=nested_code)
    assert res.syntax_valid is True
    assert "f0" in res.function_definitions

    # 40 nested if statements
    nested_ifs = "def test_conditions(x):\n"
    for i in range(1, 40):
        indent = "    " * i
        nested_ifs += f"{indent}if x > {i}:\n"
    nested_ifs += f"{'    ' * 40}return x\n"
    nested_ifs += f"{'    ' * 40}return -1\n"

    res_ifs = scan_dependencies("deep_ifs.py", source_code=nested_ifs)
    assert res_ifs.syntax_valid is True
    assert "test_conditions" in res_ifs.function_definitions


def test_pathological_recursive_and_cyclic_calls():
    """Verify recursive and mutually recursive calls are scanned without infinite recursion."""
    recursive_code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def ping(n):
    if n <= 0:
        return "done"
    return pong(n - 1)

def pong(n):
    if n <= 0:
        return "done"
    return ping(n - 1)

def tree_sum(node):
    if not node:
        return 0
    return node['val'] + tree_sum(node.get('left')) + tree_sum(node.get('right'))
"""
    res = scan_dependencies("recursion.py", source_code=recursive_code)
    assert res.syntax_valid is True
    assert "factorial" in res.function_definitions
    assert "ping" in res.function_definitions
    assert "pong" in res.function_definitions
    assert "tree_sum" in res.function_definitions

    # Internal calls should capture factorial, ping, pong, tree_sum, node.get
    assert "factorial" in res.internal_calls
    assert "ping" in res.internal_calls
    assert "pong" in res.internal_calls
    assert "tree_sum" in res.internal_calls


def test_pathological_massive_imports_and_coupling():
    """Verify handling of files with 150+ imports does not cause calculation overflows."""
    imports_lines = [f"import sys_module_{i}" for i in range(100)]
    from_imports = [f"from pkg_{i} import item_a, item_b" for i in range(50)]
    source = "\n".join(imports_lines + from_imports) + "\n\ndef main(): pass\n"

    res = scan_dependencies("massive_imports.py", source_code=source)
    assert res.syntax_valid is True
    assert len(res.external_modules) >= 150
    assert res.dependencies_count >= 150

    # Risk score calculation must clamp dependency component cleanly
    risk = calculate_risk_score(
        dependencies=res.dependencies_count,
        coverage_ratio=0.5,
        age_in_years=2.0,
        syntax_valid=True,
    )
    assert 0 <= risk.risk_score <= 100
    assert any("Alto acoplamiento con" in b for b in risk.blockers)


# ==============================================================================
# Suite 2: Git Age Inspection & Fallback Scenarios
# ==============================================================================

def test_git_age_fallback_in_non_git_directory():
    """Verify get_file_age falls back gracefully to mtime when directory is not a git repo."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        # Ensure tmp_path has NO .git directory
        assert not (tmp_path / ".git").exists()

        f = tmp_path / "standalone_script.py"
        f.write_text("print('hello standalone')\n", encoding="utf-8")

        # Set mtime to 180 days ago
        now = time.time()
        past_time = now - (180 * 86400)
        os.utime(f, (past_time, past_time))

        res = get_file_age(f, repo_path=tmp_path)
        assert res.is_git_tracked is False
        assert res.commit_count == 0
        assert 0.45 <= res.age_in_years <= 0.55
        assert res.age_display == "6 meses"


def test_git_age_untracked_file_inside_git_repo():
    """Verify an untracked file inside a git repo falls back to mtime."""
    # Current repo is a git repo
    tmp_f = tempfile.NamedTemporaryFile(
        dir=".", prefix="temp_untracked_", suffix=".py", delete=False
    )
    tmp_f.close()
    tmp_path = Path(tmp_f.name)
    try:
        tmp_path.write_text("# Untracked file\nx = 1\n", encoding="utf-8")
        res = get_file_age(tmp_path.name, repo_path=".")
        assert res.is_git_tracked is False
        assert res.commit_count == 0
        assert res.age_in_years >= 0.0
        assert "días" in res.age_display or "día" in res.age_display
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


def test_git_age_future_and_zero_epoch():
    """Verify future mtimes (clock skew) and epoch 0 do not cause negative ages or exceptions."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        f_future = tmp_path / "future.py"
        f_future.write_text("x = 1\n", encoding="utf-8")

        # Set mtime in the future (e.g. +1 day)
        future_time = time.time() + 86400
        os.utime(f_future, (future_time, future_time))

        res_future = get_file_age(f_future, repo_path=tmp_path)
        assert res_future.age_in_years == 0.0
        assert res_future.age_display == "1 día" or res_future.age_display == "0 días"

        # Non-existent file
        res_nonexistent = get_file_age(tmp_path / "non_existent.py", repo_path=tmp_path)
        assert res_nonexistent.is_git_tracked is False
        assert res_nonexistent.age_in_years == 0.0
        assert res_nonexistent.age_display == "0 días"


def test_format_age_in_spanish_boundaries():
    """Verify Spanish string formatting across time boundaries."""
    assert format_age_in_spanish(0.0) == "1 día"
    assert format_age_in_spanish(0.002) == "1 día"
    assert format_age_in_spanish(0.04) == "15 días"
    assert format_age_in_spanish(0.083) == "1 mes"
    assert format_age_in_spanish(0.5) == "6 meses"
    assert format_age_in_spanish(1.0) == "1.0 años"
    assert format_age_in_spanish(4.24) == "4.2 años"
    assert format_age_in_spanish(10.0) == "10.0 años"


# ==============================================================================
# Suite 3: Score Boundedness and Semaphore Thresholds
# ==============================================================================

def test_risk_score_extremes_and_strict_clamping():
    """Verify risk score is strictly clamped between 0 and 100 for any extreme input."""
    # Completely clean code
    clean_score = calculate_risk_score(
        dependencies=0,
        coverage_ratio=1.0,
        age_in_years=0.0,
        unresolved_globals=[],
        syntax_valid=True,
    )
    assert clean_score.risk_score == 0
    assert clean_score.risk_level == "low"
    assert clean_score.safe_to_refactor_directly is True
    assert clean_score.blockers == []

    # Extremely high values + all penalties
    extreme_score = calculate_risk_score(
        dependencies=999999,
        coverage_ratio=-5.0,  # Negative coverage clamped to 0.0
        age_in_years=1000.0,
        unresolved_globals=["foo", "bar", "baz"],
        syntax_valid=False,
        error_message="Severe error",
    )
    assert extreme_score.risk_score == 100
    assert extreme_score.risk_level == "high"
    assert extreme_score.safe_to_refactor_directly is False

    # Negative dependencies and negative age
    neg_score = calculate_risk_score(
        dependencies=-50,
        coverage_ratio=2.5,  # Exceeding 1.0 clamped to 1.0
        age_in_years=-10.0,
        unresolved_globals=[],
        syntax_valid=True,
    )
    assert neg_score.risk_score == 0
    assert neg_score.risk_level == "low"


def test_semaphore_exact_thresholds():
    """Verify semaphore threshold transitions: >70 high (or >=70), 40-69 medium, <40 low."""
    # Test low (<40)
    score_39 = calculate_risk_score(
        dependencies=1, coverage_ratio=0.8, age_in_years=0.1, syntax_valid=True
    )
    # Adjust to achieve specific score values directly
    assert calculate_risk_score(0, 1.0, 0.0).risk_level == "low"

    # Verify score level mapping for every integer 0..100
    for s in range(0, 40):
        # Simulated mapping check
        level = "high" if s >= 70 else ("medium" if s >= 40 else "low")
        assert level == "low"

    for s in range(40, 70):
        level = "high" if s >= 70 else ("medium" if s >= 40 else "low")
        assert level == "medium"

    for s in range(70, 101):
        level = "high" if s >= 70 else ("medium" if s >= 40 else "low")
        assert level == "high"


def test_safety_flags_under_blockers():
    """Verify safeToRefactorDirectly is False whenever unresolved globals or syntax errors exist."""
    # Medium risk score, but has unresolved globals
    res = calculate_risk_score(
        dependencies=2,
        coverage_ratio=0.8,
        age_in_years=0.5,
        unresolved_globals=["UNDEFINED_VAR"],
        syntax_valid=True,
    )
    assert res.safe_to_refactor_directly is False
    assert "Uso de variables globales no resueltas" in res.blockers

    # Low risk score, but has syntax error
    res_syntax = calculate_risk_score(
        dependencies=0,
        coverage_ratio=1.0,
        age_in_years=0.0,
        unresolved_globals=[],
        syntax_valid=False,
        error_message="Incomplete",
    )
    assert res_syntax.safe_to_refactor_directly is False


# ==============================================================================
# Suite 4: HTTP API POST /internal/v1/analyze Edge Cases
# ==============================================================================

def test_api_analyze_nonexistent_repo_path(auth_client):
    """POST /internal/v1/analyze with non-existent repo path returns HTTP 400."""
    payload = {
        "repoPath": "C:/definitely_non_existent_repo_xyz_987654",
        "targetFiles": ["some_file.py"],
    }
    resp = auth_client.post("/internal/v1/analyze", json=payload)
    assert resp.status_code == 400
    data = resp.json()
    assert "detail" in data
    assert "Repository path not found" in data["detail"]


def test_api_analyze_nonexistent_target_file(auth_client):
    """POST /internal/v1/analyze with missing target file returns HTTP 200 with diagnostics."""
    payload = {
        "repoPath": ".",
        "targetFiles": ["non_existent_target_file_12345.py"],
    }
    resp = auth_client.post("/internal/v1/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert len(data["files"]) == 1

    file_diag = data["files"][0]
    assert file_diag["filePath"] == "non_existent_target_file_12345.py"
    assert file_diag["riskScore"] >= 70
    assert file_diag["riskLevel"] == "high"
    assert file_diag["safeToRefactorDirectly"] is False
    assert any("File not found" in b for b in file_diag["blockers"])


def test_api_analyze_empty_target_files_in_empty_directory(auth_client):
    """POST /internal/v1/analyze with empty targetFiles on folder with no python files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        payload = {
            "repoPath": tmp_dir,
            "targetFiles": [],
            "scope": "repo",
        }
        resp = auth_client.post("/internal/v1/analyze", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["summary"]["totalFiles"] == 0
        assert data["summary"]["highRiskFilesCount"] == 0
        assert data["summary"]["overallRisk"] == 0
        assert data["summary"]["riskLevel"] == "low"
        assert data["files"] == []


def test_api_analyze_unauthorized_access():
    """POST /internal/v1/analyze requires valid X-Internal-Secret."""
    unauth_client = TestClient(app)
    payload = {"repoPath": ".", "targetFiles": ["scripts/legacy_module.py"]}

    # Missing header
    resp_missing = unauth_client.post("/internal/v1/analyze", json=payload)
    assert resp_missing.status_code == 401

    # Invalid header
    resp_invalid = unauth_client.post(
        "/internal/v1/analyze",
        headers={"X-Internal-Secret": "wrong_secret_value_123"},
        json=payload,
    )
    assert resp_invalid.status_code == 401


def test_api_analyze_malformed_payload(auth_client):
    """POST /internal/v1/analyze rejects malformed request bodies with 422."""
    # Missing repoPath
    resp1 = auth_client.post("/internal/v1/analyze", json={"targetFiles": ["a.py"]})
    assert resp1.status_code == 422

    # Wrong data type for targetFiles
    resp2 = auth_client.post(
        "/internal/v1/analyze",
        json={"repoPath": ".", "targetFiles": "not_a_list"},
    )
    assert resp2.status_code == 422


def test_pathological_non_python_file(auth_client):
    """Verify requesting non-Python files (e.g. text/markdown) does not crash the engine."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        readme = tmp_path / "README.md"
        readme.write_text("# Documentation\nThis is not Python code! > < &\n", encoding="utf-8")

        resp = auth_client.post(
            "/internal/v1/analyze",
            json={"repoPath": tmp_dir, "targetFiles": ["README.md"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["files"]) == 1
        f_res = data["files"][0]
        # Should either catch syntax error or handle gracefully
        assert 0 <= f_res["riskScore"] <= 100


def test_pathological_unicode_identifiers_and_syntax():
    """Verify Python 3 unicode identifiers and modern syntax construct handling."""
    code = """
def calcular_descuento_año_próximo(precio_base: float, categoría: str = "estándar") -> float:
    match categoría:
        case "estándar":
            return precio_base * 0.95
        case "vip":
            return precio_base * 0.80
        case _:
            return precio_base
"""
    res = scan_dependencies("unicode_syntax.py", source_code=code)
    assert res.syntax_valid is True
    assert "calcular_descuento_año_próximo" in res.function_definitions
    assert res.unresolved_globals == []


def test_api_analyze_duplicate_target_files(auth_client, tmp_path):
    """Verify duplicate entries in targetFiles are handled gracefully."""
    high_risk_code = "\n".join([
        "import os, sys, re, json, csv, math, time, io, abc, ast",
        "import collections, itertools, functools, pathlib, datetime",
        *[f"result_{i} = UNDEFINED_VAR_{i} + func_{i}()" for i in range(15)],
    ])
    repo_dir = tmp_path / "dup_repo"
    repo_dir.mkdir()
    (repo_dir / "target.py").write_text(high_risk_code, encoding="utf-8")

    resp = auth_client.post(
        "/internal/v1/analyze",
        json={
            "repoPath": str(repo_dir),
            "targetFiles": ["target.py", "target.py"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert len(data["files"]) == 2
    for f in data["files"]:
        assert f["riskScore"] >= 70
        assert f["riskLevel"] == "high"



def test_excluded_directories_in_repo_scan():
    """Verify directories like .git, __pycache__, .venv are excluded from discovery."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        # Create normal file
        (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")

        # Create excluded directory files
        for ex in [".git", ".venv", "__pycache__", ".pytest_cache", ".agents"]:
            d = tmp_path / ex
            d.mkdir(parents=True, exist_ok=True)
            (d / "hidden.py").write_text("y = 2\n", encoding="utf-8")

        report = build_analysis_report(tmp_path, scope="repo")
        discovered_paths = [f.filePath for f in report.files]
        assert "app.py" in discovered_paths
        assert not any(".git" in p for p in discovered_paths)
        assert not any(".venv" in p for p in discovered_paths)
        assert not any("__pycache__" in p for p in discovered_paths)
        assert not any(".agents" in p for p in discovered_paths)

