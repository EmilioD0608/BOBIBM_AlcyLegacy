"""Comprehensive unit and integration tests for Modernization & Safety Engine (M3)."""

import ast
import os
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from backend.api.schemas import RefactorRequest, RefactorResponse, UserSpecs
from backend.refactor.diff_generator import (
    extract_changes_summary,
    generate_unified_diff,
)
from backend.refactor.engine import RefactorEngine, refactor_code
from backend.refactor.provider import (
    BaseWatsonxProvider,
    MockWatsonxProvider,
    WatsonxProvider,
    get_watsonx_provider,
)
from backend.refactor.safety_harness import (
    generate_characterization_tests,
    generate_safety_harness,
)
from backend.refactor.validator import (
    strip_markdown_code_blocks,
    validate_python_syntax,
)


# =========================================================================
# 1. Tests for Validator (Syntax & Compilation)
# =========================================================================
class TestSyntaxValidator:
    """Tests for ast.parse and compile syntax validator."""

    def test_valid_python_code(self):
        code = "def add(a: int, b: int) -> int:\n    return a + b\n"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None

    def test_strip_markdown_fences(self):
        fenced_code = "```python\ndef greet(name: str) -> str:\n    return f'Hello, {name}'\n```"
        clean = strip_markdown_code_blocks(fenced_code)
        assert not clean.startswith("```")
        assert not clean.endswith("```")
        is_valid, error = validate_python_syntax(fenced_code)
        assert is_valid is True
        assert error is None

    def test_invalid_syntax_detection(self):
        bad_code = "def broken_func(:\n    return 42"
        is_valid, error = validate_python_syntax(bad_code)
        assert is_valid is False
        assert error is not None
        assert "SyntaxError" in error

    def test_empty_string_is_valid_python(self):
        is_valid, error = validate_python_syntax("")
        assert is_valid is True
        assert error is None


# =========================================================================
# 2. Tests for Diff Generator & Changes Summary
# =========================================================================
class TestDiffGenerator:
    """Tests for standard unified git diff generation and summary extraction."""

    def test_unified_diff_headers_and_chunks(self):
        orig = "def foo():\n    return 1\n"
        refact = "def foo() -> int:\n    return 1\n"
        diff = generate_unified_diff("scripts/my_mod.py", orig, refact)
        assert "--- scripts/my_mod.py (original)" in diff
        assert "+++ scripts/my_mod.py (modernizado)" in diff
        assert "@@" in diff
        assert "-def foo():" in diff
        assert "+def foo() -> int:" in diff

    def test_unified_diff_identical_code_empty(self):
        code = "x = 42\n"
        diff = generate_unified_diff("test.py", code, code)
        assert diff == ""

    def test_extract_changes_summary_type_hints_and_docstrings(self):
        orig = "def calc(x):\n    return x * 2\n"
        refact = 'def calc(x: int) -> int:\n    """Multiplies x by 2."""\n    return x * 2\n'
        summary = extract_changes_summary(orig, refact, generated_tests="def test_foo(): pass")
        assert any("Tipado" in s for s in summary)
        assert any("Docstring" in s for s in summary)
        assert any("tests" in s for s in summary)


# =========================================================================
# 3. Tests for Safety Harness Generator (Characterization Tests)
# =========================================================================
class TestSafetyHarness:
    """Tests for automatic pytest characterization test suite generation."""

    def test_safety_harness_triggered_on_high_risk(self):
        code = (
            "def calculate_price(base_price, customer_type='regular'):\n"
            "    if customer_type == 'premium':\n"
            "        return round(base_price * 0.85, 2)\n"
            "    return round(base_price, 2)\n"
        )
        tests = generate_safety_harness(
            file_path="scripts/legacy_module.py",
            original_code=code,
            risk_score=87,
            force=False,
        )
        assert "import pytest" in tests
        assert "test_regular_customer" in tests
        assert "test_premium_customer" in tests

    def test_safety_harness_skipped_on_low_risk_without_force(self):
        code = "def simple(): return 1\n"
        tests = generate_safety_harness(
            file_path="scripts/legacy_module.py",
            original_code=code,
            risk_score=35,
            force=False,
        )
        assert tests == ""

    def test_safety_harness_forced_on_low_risk(self):
        code = "def calculate_price(base_price, customer_type='regular'):\n    return base_price\n"
        tests = generate_safety_harness(
            file_path="scripts/legacy_module.py",
            original_code=code,
            risk_score=20,
            force=True,
        )
        assert "import pytest" in tests
        assert "calculate_price" in tests

    def test_generated_tests_are_valid_and_executable(self):
        import inspect
        import legacy_module
        code = inspect.getsource(legacy_module)
        tests = generate_characterization_tests("scripts/legacy_module.py", code)
        is_valid, error = validate_python_syntax(tests)
        assert is_valid is True, f"Generated test failed syntax: {error}"

        # Execute characterization assertions directly in namespace with legacy_module
        namespace = {"pytest": pytest, "calculate_price": legacy_module.calculate_price}
        exec(compile(tests, "<test>", "exec"), namespace)
        # Call the generated test functions
        namespace["test_regular_customer"]()
        namespace["test_premium_customer"]()

    def test_generic_function_characterization(self):
        code = "def process_order(order_id, amount):\n    return True\n"
        tests = generate_characterization_tests("orders.py", code)
        is_valid, error = validate_python_syntax(tests)
        assert is_valid is True
        assert "def test_process_order_characterization():" in tests


# =========================================================================
# 4. Tests for Watsonx Providers (Real and Mock)
# =========================================================================
class TestWatsonxProvider:
    """Tests for IBM watsonx.ai client and Mock fallback provider."""

    def test_mock_provider_legacy_pricing_benchmark(self):
        provider = MockWatsonxProvider()
        specs = UserSpecs(
            targetLanguage="python",
            targetVersion="3.12",
            customInstructions="PEP 484 and docstrings",
        )
        code = (
            "def calculate_price(base_price, customer_type='regular'):\n"
            "    if customer_type == 'premium':\n"
            "        return round(base_price * 0.85, 2)\n"
            "    return round(base_price, 2)\n"
        )
        refactored, changes = provider.generate_refactoring(code, specs, "scripts/legacy_module.py")

        assert "from typing import Literal" in refactored
        assert "Literal['regular', 'premium']" in refactored
        assert "base_price: float" in refactored
        assert "-> float:" in refactored
        assert '"""Calcula el precio final aplicando descuentos según el tipo de cliente."""' in refactored
        is_valid, error = validate_python_syntax(refactored)
        assert is_valid is True

        # Test functional behavior matches legacy module
        local_scope = {}
        exec(refactored, local_scope)
        modern_fn = local_scope["calculate_price"]
        assert modern_fn(100.0, "regular") == 100.0
        assert modern_fn(100.0, "premium") == 85.0

    def test_mock_provider_generic_python_code(self):
        provider = MockWatsonxProvider()
        specs = UserSpecs()
        code = "def compute_tax(amount, rate):\n    return amount * rate\n"
        refactored, changes = provider.generate_refactoring(code, specs, "tax.py")
        is_valid, error = validate_python_syntax(refactored)
        assert is_valid is True
        assert "amount: float" in refactored
        assert "rate: float" in refactored
        assert len(changes) > 0

    def test_watsonx_provider_init(self):
        provider = WatsonxProvider(
            api_key="mock-api-key",
            project_id="mock-project-id",
            url="https://us-south.ml.cloud.ibm.com",
            model_id="ibm/granite-3-8b-instruct",
        )
        assert provider.api_key == "mock-api-key"
        assert provider.project_id == "mock-project-id"
        assert provider.model_id == "ibm/granite-3-8b-instruct"

    @patch("requests.post")
    def test_watsonx_provider_mock_api_call(self, mock_post):
        # 1st call: IAM token exchange
        # 2nd call: Watsonx text generation
        mock_iam_resp = MagicMock()
        mock_iam_resp.json.return_value = {"access_token": "mock-iam-bearer-token", "expires_in": 3600}
        mock_iam_resp.raise_for_status = MagicMock()

        mock_watsonx_resp = MagicMock()
        mock_watsonx_resp.json.return_value = {
            "results": [
                {
                    "generated_text": "```python\ndef modernized(val: int) -> int:\n    \"\"\"Modernized docstring.\"\"\"\n    return val * 2\n```"
                }
            ]
        }
        mock_watsonx_resp.raise_for_status = MagicMock()

        mock_post.side_effect = [mock_iam_resp, mock_watsonx_resp]

        provider = WatsonxProvider(
            api_key="test-key",
            project_id="test-proj",
            url="https://us-south.ml.cloud.ibm.com",
        )
        specs = UserSpecs()
        refactored, changes = provider.generate_refactoring("def modernized(val): return val * 2\n", specs)

        assert "val: int" in refactored
        assert "Modernized docstring." in refactored
        assert any("watsonx" in c for c in changes)

    def test_get_watsonx_provider_factory(self, monkeypatch):
        # When BOB_MOCK_WATSONX is True -> returns MockWatsonxProvider
        monkeypatch.setenv("BOB_MOCK_WATSONX", "true")
        provider = get_watsonx_provider()
        assert isinstance(provider, MockWatsonxProvider)

        # When API key is unset -> returns MockWatsonxProvider
        monkeypatch.setenv("BOB_MOCK_WATSONX", "false")
        monkeypatch.delenv("WATSONX_APIKEY", raising=False)
        monkeypatch.delenv("IBM_CLOUD_API_KEY", raising=False)
        provider2 = get_watsonx_provider()
        assert isinstance(provider2, MockWatsonxProvider)


# =========================================================================
# 5. Tests for Refactor Engine Pipeline
# =========================================================================
class TestRefactorEngine:
    """Tests for RefactorEngine orchestrator."""

    def test_refactor_engine_full_pipeline(self):
        engine = RefactorEngine(provider=MockWatsonxProvider())
        req = RefactorRequest(
            filePath="scripts/legacy_module.py",
            originalCode=(
                "def calculate_price(base_price, customer_type='regular'):\n"
                "    if customer_type == 'premium':\n"
                "        return round(base_price * 0.85, 2)\n"
                "    return round(base_price, 2)\n"
            ),
            userSpecs=UserSpecs(
                targetLanguage="python",
                targetVersion="3.12",
                customInstructions="Add PEP 484 and docstrings",
            ),
            generateTests=True,
        )
        res = engine.refactor(req, risk_score=87)

        assert res.success is True
        assert res.filePath == "scripts/legacy_module.py"
        assert "from typing import Literal" in res.refactoredCode
        assert "def test_regular_customer():" in res.generatedTests
        assert "--- scripts/legacy_module.py (original)" in res.diff
        assert len(res.changesSummary) >= 2

    def test_refactor_engine_syntax_error_rejection(self):
        mock_provider = MagicMock(spec=BaseWatsonxProvider)
        mock_provider.generate_refactoring.return_value = ("def broken(:\n    pass", ["Broken syntax"])
        engine = RefactorEngine(provider=mock_provider)

        req = RefactorRequest(
            filePath="scripts/module.py",
            originalCode="x = 1\n",
            generateTests=False,
        )
        with pytest.raises(ValueError, match="failed Python syntax verification"):
            engine.refactor(req)


# =========================================================================
# 6. Tests for POST /internal/v1/refactor API Endpoint
# =========================================================================
class TestRefactorAPIEndpoint:
    """Integration tests for the /internal/v1/refactor endpoint."""

    def test_refactor_endpoint_valid_auth(self, client: TestClient, valid_headers: dict):
        payload = {
            "filePath": "scripts/legacy_module.py",
            "originalCode": (
                "def calculate_price(base_price, customer_type='regular'):\n"
                "    if customer_type == 'premium':\n"
                "        return round(base_price * 0.85, 2)\n"
                "    return round(base_price, 2)"
            ),
            "userSpecs": {
                "targetLanguage": "python",
                "targetVersion": "3.12",
                "framework": "standard",
                "customInstructions": "Agregar tipado estricto (PEP 484), dataclasses y docstrings Google-style.",
            },
            "generateTests": True,
        }

        response = client.post("/internal/v1/refactor", json=payload, headers=valid_headers)
        assert response.status_code == 200
        data = response.json()

        # Validate exact schema match with COORDINACION_BACKENDS.md
        parsed_response = RefactorResponse(**data)
        assert parsed_response.success is True
        assert parsed_response.filePath == "scripts/legacy_module.py"
        assert "from typing import Literal" in parsed_response.refactoredCode
        assert "def test_regular_customer():" in parsed_response.generatedTests
        assert "--- scripts/legacy_module.py (original)" in parsed_response.diff
        assert "+++ scripts/legacy_module.py (modernizado)" in parsed_response.diff
        assert len(parsed_response.changesSummary) > 0

    def test_refactor_endpoint_missing_secret_returns_401(self, client: TestClient):
        payload = {
            "filePath": "scripts/legacy_module.py",
            "originalCode": "def foo(): pass",
        }
        response = client.post("/internal/v1/refactor", json=payload)
        assert response.status_code == 401
        assert "detail" in response.json()

    def test_refactor_endpoint_invalid_secret_returns_401(
        self, client: TestClient, invalid_headers: dict
    ):
        payload = {
            "filePath": "scripts/legacy_module.py",
            "originalCode": "def foo(): pass",
        }
        response = client.post("/internal/v1/refactor", json=payload, headers=invalid_headers)
        assert response.status_code == 401
        assert "detail" in response.json()

    def test_refactor_endpoint_coordinacion_backends_exact_contract(
        self, client: TestClient, valid_headers: dict
    ):
        """Validates exact payload and response match against COORDINACION_BACKENDS.md."""
        exact_request_payload = {
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

        response = client.post(
            "/internal/v1/refactor",
            json=exact_request_payload,
            headers=valid_headers,
        )
        assert response.status_code == 200
        data = response.json()

        # Contract checks:
        assert data["success"] is True
        assert data["filePath"] == "scripts/legacy_module.py"
        assert "def calculate_price(base_price: float" in data["refactoredCode"]
        assert "import pytest" in data["generatedTests"]
        assert "--- scripts/legacy_module.py (original)" in data["diff"]
        assert isinstance(data["changesSummary"], list)
        assert len(data["changesSummary"]) >= 2

    def test_refactor_endpoint_validation_error_missing_fields(
        self, client: TestClient, valid_headers: dict
    ):
        """Verifies 422 Unprocessable Entity when required fields are missing."""
        bad_payload = {"userSpecs": {}}
        response = client.post("/internal/v1/refactor", json=bad_payload, headers=valid_headers)
        assert response.status_code == 422

    def test_safety_harness_empty_code(self):
        """Verifies empty code yields importable fallback test."""
        tests = generate_safety_harness("empty.py", "", force=True)
        assert "import pytest" in tests
        assert "empty" in tests

    def test_mock_provider_with_classes(self):
        """Verifies mock provider handles class methods and docstrings."""
        code = (
            "class Calculator:\n"
            "    def multiply(self, factor_a, factor_b):\n"
            "        return factor_a * factor_b\n"
        )
        provider = MockWatsonxProvider()
        specs = UserSpecs()
        refactored, changes = provider.generate_refactoring(code, specs, "calc.py")
        is_valid, _ = validate_python_syntax(refactored)
        assert is_valid is True
        assert "def multiply(self" in refactored

    @patch("requests.post")
    def test_watsonx_provider_network_error_raises_exception(self, mock_post):
        """Verifies WatsonxProvider surfaces network errors."""
        mock_post.side_effect = Exception("Connection refused by IBM endpoint")
        provider = WatsonxProvider(api_key="key", project_id="proj")
        with pytest.raises(Exception, match="Connection refused"):
            provider.generate_refactoring("def foo(): pass", UserSpecs())


# =========================================================================
# 7. Remediation Tests for Reviewer M3 Findings
# =========================================================================
class TestRemediationM3:
    """Verifies all remediation fixes required by reviewer_m3_1 handoff."""

    def test_mock_provider_preserves_custom_vip_logic(self):
        """Reviewer Challenge 1: Custom business logic in calculate_price must be preserved."""
        code = (
            "def calculate_price(base_price, customer_type='regular'):\n"
            "    if customer_type == 'vip':\n"
            "        return round(base_price * 0.50, 2)\n"
            "    return round(base_price, 2)\n"
        )
        provider = MockWatsonxProvider()
        refactored, changes = provider.generate_refactoring(code, UserSpecs(), "scripts/pricing.py")

        is_valid, err = validate_python_syntax(refactored)
        assert is_valid is True, f"Failed syntax: {err}"
        assert "vip" in refactored
        assert "0.5" in refactored or "0.50" in refactored

        # Execute modernized code to verify functional logic is intact
        scope = {}
        exec(refactored, scope)
        fn = scope["calculate_price"]
        assert fn(100.0, "vip") == 50.0
        assert fn(100.0, "regular") == 100.0

    def test_safety_harness_no_tautological_assertions(self):
        """Reviewer Finding 2: Tautological assertions must be eliminated."""
        code = "def multiply(x, y):\n    return x * y\n"
        tests = generate_characterization_tests("math_tool.py", code)
        is_valid, err = validate_python_syntax(tests)
        assert is_valid is True, f"Failed syntax: {err}"
        assert "assert result is not None or result is None" not in tests
        assert "assert multiply(2, 2) == 4" in tests or "assert multiply" in tests

        # Execute tests against function
        import sys, types
        mod = types.ModuleType("math_tool")
        mod.multiply = lambda x, y: x * y
        sys.modules["math_tool"] = mod
        try:
            scope = {}
            exec(compile(tests, "<test>", "exec"), scope)
            assert callable(scope["test_multiply_characterization"])
            scope["test_multiply_characterization"]()
        finally:
            sys.modules.pop("math_tool", None)

    def test_safety_harness_hyphenated_file_path(self):
        """Reviewer Finding 4: Hyphenated filenames must not cause SyntaxError."""
        code = "def calculate_price(base_price, customer_type='regular'): return base_price\n"
        tests = generate_characterization_tests("legacy-pricing-tool.py", code)
        is_valid, err = validate_python_syntax(tests)
        assert is_valid is True, f"Hyphenated module generated invalid syntax: {err}"
        assert "import legacy-pricing-tool" not in tests

    def test_risk_score_in_refactor_request_triggers_safety_harness(self):
        """Reviewer Finding 3: riskScore in request must trigger harness if >70 even if generateTests is False."""
        engine = RefactorEngine(provider=MockWatsonxProvider())

        # 1. High risk (>70) with generateTests=False MUST still generate tests
        high_risk_req = RefactorRequest(
            filePath="scripts/module.py",
            originalCode="def calculate_price(base_price, customer_type='regular'): return base_price\n",
            generateTests=False,
            riskScore=85,
        )
        res_high = engine.refactor(high_risk_req)
        assert res_high.success is True
        assert len(res_high.generatedTests) > 0
        assert "import pytest" in res_high.generatedTests

        # 2. Low risk (<=70) with generateTests=False MUST NOT generate tests
        low_risk_req = RefactorRequest(
            filePath="scripts/module.py",
            originalCode="def calculate_price(base_price, customer_type='regular'): return base_price\n",
            generateTests=False,
            riskScore=30,
        )
        res_low = engine.refactor(low_risk_req)
        assert res_low.success is True
        assert res_low.generatedTests == ""

    def test_bob_api_key_configuration_precedence(self, monkeypatch):
        """Parent Directive: BOB_API_KEY must be recognized and prioritized."""
        from backend.config import Settings, get_settings

        monkeypatch.setenv("BOB_API_KEY", "bob-priority-key")
        monkeypatch.setenv("IBM_API_KEY", "ibm-fallback-key")
        monkeypatch.setenv("WATSONX_APIKEY", "watsonx-fallback-key")
        monkeypatch.setenv("BOB_PROJECT_ID", "bob-proj-id")

        settings = Settings()
        assert settings.WATSONX_APIKEY == "bob-priority-key"
        assert settings.WATSONX_PROJECT_ID == "bob-proj-id"

        # Check get_settings with reload
        reloaded = get_settings(reload=True)
        assert reloaded.WATSONX_APIKEY == "bob-priority-key"
        assert reloaded.WATSONX_PROJECT_ID == "bob-proj-id"

