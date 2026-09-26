"""Analyzer package for BOB Backend static risk diagnostics.

Provides AST dependency scanning, unit test coverage checking, git age inspection,
and calibrated risk score assessment.
"""

from backend.analyzer.coverage_checker import (
    CoverageCheckResult,
    check_coverage,
)
from backend.analyzer.dependency_scanner import (
    DependencyScanResult,
    scan_dependencies,
)
from backend.analyzer.git_age import (
    GitAgeResult,
    format_age_in_spanish,
    get_file_age,
)
from backend.analyzer.report_builder import (
    build_analysis_report,
)
from backend.analyzer.risk_score import (
    RiskScoreResult,
    calculate_risk_score,
)

__all__ = [
    "scan_dependencies",
    "DependencyScanResult",
    "check_coverage",
    "CoverageCheckResult",
    "get_file_age",
    "GitAgeResult",
    "format_age_in_spanish",
    "calculate_risk_score",
    "RiskScoreResult",
    "build_analysis_report",
]
