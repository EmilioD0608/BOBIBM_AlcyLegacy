from pathlib import Path
from typing import Optional

from backend.api.schemas import RefactorRequest, RefactorResponse
from backend.refactor.diff_generator import extract_changes_summary, generate_unified_diff
from backend.refactor.provider import BaseWatsonxProvider, get_watsonx_provider
from backend.refactor.safety_harness import generate_safety_harness
from backend.refactor.validator import validate_python_syntax


class RefactorEngine:
    """Orchestrates code modernization pipeline."""

    def __init__(self, provider: Optional[BaseWatsonxProvider] = None) -> None:
        self.provider = provider or get_watsonx_provider()

    def refactor(
        self,
        request: RefactorRequest,
        risk_score: Optional[int] = None,
    ) -> RefactorResponse:
        """Executes full modernization workflow for a RefactorRequest.

        1. Syntax verification of original code.
        2. Effective risk score evaluation from request or disk.
        3. Safety harness generation if generateTests is True or effective_risk > 70.
        4. Code modernization via IBM watsonx / mock provider.
        5. Syntax and compilation validation of generated code.
        6. Unified diff calculation.
        7. Change summary assembly into RefactorResponse.
        """
        # 1. Validate original code syntax
        orig_valid, orig_err = validate_python_syntax(
            code=request.originalCode,
            file_path=request.filePath,
        )
        if not orig_valid:
            raise ValueError(
                f"Original legacy code failed Python syntax verification: {orig_err}"
            )

        # 2. Determine effective risk score
        effective_risk = 0
        if request.riskScore is not None:
            effective_risk = request.riskScore
        elif risk_score is not None:
            effective_risk = risk_score
        else:
            file_path_obj = Path(request.filePath)
            if file_path_obj.exists() and file_path_obj.is_file():
                try:
                    from backend.analyzer.coverage_checker import check_coverage
                    from backend.analyzer.dependency_scanner import scan_dependencies
                    from backend.analyzer.git_age import get_file_age
                    from backend.analyzer.risk_score import calculate_risk_score

                    dep_res = scan_dependencies(file_path_obj)
                    cov_res = check_coverage(file_path_obj)
                    age_res = get_file_age(file_path_obj)
                    risk_res = calculate_risk_score(
                        dependencies=dep_res.dependencies_count,
                        coverage_ratio=cov_res.coverage_ratio,
                        age_in_years=age_res.age_in_years,
                        unresolved_globals=dep_res.unresolved_globals,
                        syntax_valid=dep_res.syntax_valid,
                        error_message=dep_res.error_message,
                    )
                    effective_risk = risk_res.risk_score
                except Exception:
                    effective_risk = 80 if request.generateTests else 0
            else:
                effective_risk = 80 if request.generateTests else 0

        # 3. Generate safety harness (characterization tests) if requested or high risk
        should_generate_tests = request.generateTests or effective_risk > 70
        generated_tests = ""
        if should_generate_tests:
            generated_tests = generate_safety_harness(
                file_path=request.filePath,
                original_code=request.originalCode,
                risk_score=effective_risk,
                force=request.generateTests,
            )

        # 2. Modernize code using the configured watsonx provider
        refactored_code, provider_changes = self.provider.generate_refactoring(
            original_code=request.originalCode,
            user_specs=request.userSpecs,
            file_path=request.filePath,
        )

        # 3. Syntax and bytecode compilation validation
        is_valid, error_msg = validate_python_syntax(
            code=refactored_code,
            file_path=request.filePath,
        )
        if not is_valid:
            raise ValueError(
                f"Generated modernized code failed Python syntax verification: {error_msg}"
            )

        # 4. Generate standard unified git diff
        diff_text = generate_unified_diff(
            file_path=request.filePath,
            original_code=request.originalCode,
            refactored_code=refactored_code,
        )

        # 5. Extract comprehensive change summary
        changes_summary = extract_changes_summary(
            original_code=request.originalCode,
            refactored_code=refactored_code,
            diff_text=diff_text,
            generated_tests=generated_tests,
        )

        # Merge any specific items from provider that add valuable context
        for item in provider_changes:
            if item not in changes_summary:
                changes_summary.append(item)

        return RefactorResponse(
            success=True,
            filePath=request.filePath,
            refactoredCode=refactored_code,
            generatedTests=generated_tests,
            diff=diff_text,
            changesSummary=changes_summary,
        )


def refactor_code(
    request: RefactorRequest,
    risk_score: Optional[int] = None,
) -> RefactorResponse:
    """Convenience functional interface for running RefactorEngine."""
    engine = RefactorEngine()
    return engine.refactor(request=request, risk_score=risk_score)
