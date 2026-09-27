from __future__ import annotations

import ast
import logging
import os
from pathlib import Path
from typing import List, Optional, Union

from backend.analyzer.coverage_checker import check_coverage
from backend.analyzer.dependency_scanner import scan_dependencies
from backend.analyzer.git_age import get_file_age
from backend.analyzer.risk_score import calculate_risk_score
from backend.api.schemas import (
    AnalyzeResponse,
    AnalyzeSummary,
    FileAnalysisResult,
    FileDocumentation,
)

logger = logging.getLogger(__name__)

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".agents",
}


def _discover_python_files(repo_root: Path) -> List[str]:
    """Recursively discovers all Python files in repository, returning relative paths."""
    discovered: List[str] = []

    if not repo_root.exists() or not repo_root.is_dir():
        return discovered

    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        for f in files:
            if f.endswith(".py"):
                full_p = Path(root) / f

                try:
                    rel_p = str(
                        full_p.relative_to(repo_root)
                    ).replace("\\", "/")
                except ValueError:
                    rel_p = str(full_p).replace("\\", "/")

                discovered.append(rel_p)

    return sorted(discovered)


def _extract_file_documentation(
    file_path: Path,
) -> FileDocumentation:
    """
    Extract structural documentation from a Python source file.

    Detects:
    - Functions
    - Async functions
    - Classes
    - Imports
    - Total source lines
    """

    try:
        source = file_path.read_text(
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, UnicodeError) as exc:
        logger.warning(
            "Could not read %s for documentation extraction: %s",
            file_path,
            exc,
        )
        return FileDocumentation()

    # Number of source lines
    lines = len(source.splitlines())

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        logger.warning(
            "Could not parse %s for documentation extraction: %s",
            file_path,
            exc,
        )

        # We can still return the line count even if the
        # Python source contains a syntax error.
        return FileDocumentation(
            lines=lines,
        )

    functions: List[str] = []
    classes: List[str] = []
    imports: List[str] = []

    for node in ast.walk(tree):

        # Normal and asynchronous functions
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ):
            functions.append(node.name)

        # Classes
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)

        # import package
        elif isinstance(node, ast.Import):
            names = ", ".join(
                alias.name
                for alias in node.names
            )

            imports.append(
                f"import {names}"
            )

        # from package import something
        elif isinstance(node, ast.ImportFrom):
            module = (
                "." * node.level
                + (node.module or "")
            )

            names = ", ".join(
                alias.name
                for alias in node.names
            )

            imports.append(
                f"from {module} import {names}"
            )

    # Remove duplicates while preserving order
    unique_functions = list(
        dict.fromkeys(functions)
    )

    unique_classes = list(
        dict.fromkeys(classes)
    )

    unique_imports = list(
        dict.fromkeys(imports)
    )

    return FileDocumentation(
        functions=unique_functions,
        classes=unique_classes,
        imports=unique_imports[:15],
        lines=lines,
    )


def build_analysis_report(
    repo_path: Union[str, Path],
    target_files: Optional[List[str]] = None,
    scope: str = "file",
) -> AnalyzeResponse:
    """
    Orchestrates risk diagnostic analysis across
    target files or repository.

    Args:
        repo_path:
            Root filesystem path of the repository
            (already sandboxed by the route).

        target_files:
            Optional list of relative file paths
            to inspect.

        scope:
            Scope of analysis:
            "file", "folder", or "repo".

    Returns:
        AnalyzeResponse with overall summary
        and per-file metrics.
    """

    repo_root = Path(repo_path).resolve()

    files_to_analyze: List[str] = []

    if target_files and len(target_files) > 0:
        files_to_analyze = [
            f.replace("\\", "/")
            for f in target_files
        ]

    elif scope == "repo" or not target_files:
        files_to_analyze = (
            _discover_python_files(repo_root)
        )

    file_results: List[FileAnalysisResult] = []

    for rel_path_str in files_to_analyze:

        target_p = Path(rel_path_str)


        full_file_path = (
            repo_root / target_p
        ).resolve()

        try:
            full_file_path.relative_to(
                repo_root
            )

        except ValueError:
            logger.warning(
                (
                    "B-02: Skipping targetFile outside "
                    "repo sandbox: %s (resolved: %s)"
                ),
                rel_path_str,
                full_file_path,
            )
            continue

        dep_res = scan_dependencies(
            full_file_path,
            repo_path=repo_root,
        )


        cov_res = check_coverage(
            full_file_path,
            repo_path=repo_root,
        )


        age_res = get_file_age(
            full_file_path,
            repo_path=repo_root,
        )

        documentation = (
            _extract_file_documentation(
                full_file_path
            )
        )

        risk_res = calculate_risk_score(
            dependencies=(
                dep_res.dependencies_count
            ),
            coverage_ratio=(
                cov_res.coverage_ratio
            ),
            age_in_years=(
                age_res.age_in_years
            ),
            unresolved_globals=(
                dep_res.unresolved_globals
            ),
            syntax_valid=(
                dep_res.syntax_valid
            ),
            error_message=(
                dep_res.error_message
            ),
        )

        if (
            repo_root.exists()
            and full_file_path.exists()
        ):
            try:
                display_path = str(
                    full_file_path
                    .resolve()
                    .relative_to(
                        repo_root.resolve()
                    )
                ).replace("\\", "/")

            except (
                ValueError,
                RuntimeError,
            ):
                display_path = rel_path_str

        else:
            display_path = rel_path_str


        file_results.append(
            FileAnalysisResult(
                filePath=display_path,

                riskScore=(
                    risk_res.risk_score
                ),

                riskLevel=(
                    risk_res.risk_level
                ),

                dependencies=(
                    dep_res.dependencies_count
                ),

                coverage=(
                    cov_res.coverage_percentage
                ),

                age=(
                    age_res.age_display
                ),

                blockers=(
                    risk_res.blockers
                ),

                safeToRefactorDirectly=(
                    risk_res.safe_to_refactor_directly
                ),

                recommendation=(
                    risk_res.recommendation
                ),

                # NEW:
                # Documentation extracted by BOB
                documentation=documentation,
            )
        )

    total_files = len(
        file_results
    )

    high_risk_files = sum(
        1
        for f in file_results
        if f.riskScore >= 70
    )

    if total_files > 0:

        overall_risk = max(
            f.riskScore
            for f in file_results
        )

        if overall_risk >= 70:
            overall_level = "high"

        elif overall_risk >= 40:
            overall_level = "medium"

        else:
            overall_level = "low"

    else:
        overall_risk = 0
        overall_level = "low"

    summary = AnalyzeSummary(
        overallRisk=overall_risk,
        riskLevel=overall_level,
        totalFiles=total_files,
        highRiskFilesCount=(
            high_risk_files
        ),
    )

    return AnalyzeResponse(
        success=True,
        summary=summary,
        files=file_results,
    )