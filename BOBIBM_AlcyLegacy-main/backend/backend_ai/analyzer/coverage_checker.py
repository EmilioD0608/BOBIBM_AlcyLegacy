"""Test coverage detection and estimation for BOB Backend.

Detects existing automated unit tests (pytest / unittest) associated with target files.
Calculates coverage ratio (0.0 to 1.0) and formatted percentage string (e.g. "12%", "0%").
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Union


@dataclass
class CoverageCheckResult:
    """Result of unit test coverage checking."""

    file_path: str
    has_tests: bool
    test_file_path: Optional[str] = None
    test_files: List[str] = field(default_factory=list)
    test_functions_count: int = 0
    target_functions_count: int = 0
    coverage_ratio: float = 0.0  # 0.0 to 1.0
    coverage_percentage: str = "0%"  # e.g. "12%", "0%"
    framework: Optional[str] = None  # "pytest" or "unittest"

    def to_dict(self) -> Dict[str, Union[str, int, float, bool, List[str], Optional[str]]]:
        """Convert result to dictionary representation."""
        return {
            "file_path": self.file_path,
            "has_tests": self.has_tests,
            "test_file_path": self.test_file_path,
            "test_files": self.test_files,
            "test_functions_count": self.test_functions_count,
            "target_functions_count": self.target_functions_count,
            "coverage_ratio": self.coverage_ratio,
            "coverage_percentage": self.coverage_percentage,
            "framework": self.framework,
        }


def _count_target_functions(target_file: Path) -> Set[str]:
    """Counts public functions and methods defined in the target file."""
    if not target_file.exists() or not target_file.is_file():
        return set()

    functions: Set[str] = set()
    try:
        with open(target_file, "r", encoding="utf-8", errors="replace") as f:
            tree = ast.parse(f.read(), filename=str(target_file))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("_"):
                    functions.add(node.name)
    except Exception:
        pass
    return functions


def _inspect_test_file(
    test_file: Path, target_stem: str, target_functions: Set[str]
) -> tuple[int, Set[str], Optional[str]]:
    """Inspects a candidate test file.

    Returns:
        (test_functions_count, invoked_target_functions, detected_framework)
    """
    test_count = 0
    invoked: Set[str] = set()
    framework: Optional[str] = None

    try:
        with open(test_file, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        tree = ast.parse(content, filename=str(test_file))
    except Exception:
        return 0, set(), None

    imported_target = False
    imported_names: Set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if "pytest" in alias.name:
                    framework = framework or "pytest"
                elif "unittest" in alias.name:
                    framework = "unittest"
                if alias.name == target_stem or alias.name.endswith(f".{target_stem}"):
                    imported_target = True
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if "pytest" in mod:
                framework = framework or "pytest"
            elif "unittest" in mod:
                framework = "unittest"
            if mod == target_stem or mod.endswith(f".{target_stem}"):
                imported_target = True
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name)

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_") or node.name.endswith("_test"):
                test_count += 1
                # Inspect calls inside test function
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            if child.func.id in target_functions:
                                invoked.add(child.func.id)
                        elif isinstance(child.func, ast.Attribute):
                            if child.func.attr in target_functions:
                                invoked.add(child.func.attr)

        elif isinstance(node, ast.ClassDef):
            for base in node.bases:
                if isinstance(base, ast.Attribute) and base.attr == "TestCase":
                    framework = "unittest"
                elif isinstance(base, ast.Name) and base.id == "TestCase":
                    framework = "unittest"

    if framework is None and test_count > 0:
        framework = "pytest"

    return test_count, invoked, framework


def check_coverage(
    file_path: Union[str, Path],
    repo_path: Optional[Union[str, Path]] = None,
) -> CoverageCheckResult:
    """Detects unit tests associated with the target file and computes coverage metrics.

    Args:
        file_path: Path or relative path to the Python file.
        repo_path: Optional repository root directory.

    Returns:
        CoverageCheckResult with test presence, counts, ratio, and percentage string.
    """
    file_path_str = str(file_path).replace("\\", "/")
    target_path = Path(file_path)

    if repo_path and not target_path.is_absolute():
        full_target_path = Path(repo_path) / target_path
    else:
        full_target_path = target_path

    target_stem = target_path.stem
    target_functions = _count_target_functions(full_target_path)
    target_count = max(1, len(target_functions))

    # Candidate locations to find tests
    candidate_paths: List[Path] = []
    parent_dir = full_target_path.parent
    candidate_paths.append(parent_dir / f"test_{target_stem}.py")
    candidate_paths.append(parent_dir / f"{target_stem}_test.py")

    search_roots: List[Path] = []
    if repo_path:
        r_path = Path(repo_path)
        search_roots.append(r_path)
    search_roots.append(parent_dir)

    for s_root in search_roots:
        if s_root.exists() and s_root.is_dir():
            for t_dir_name in ["tests", "test", "testing"]:
                td = s_root / t_dir_name
                if td.exists() and td.is_dir():
                    candidate_paths.append(td / f"test_{target_stem}.py")
                    candidate_paths.append(td / f"{target_stem}_test.py")

    # Discover and inspect matching test files
    discovered_tests: List[Path] = []
    total_test_functions = 0
    all_invoked_target_funcs: Set[str] = set()
    detected_framework: Optional[str] = None

    # Check direct name matches
    for cand in candidate_paths:
        if cand.exists() and cand.is_file() and cand not in discovered_tests:
            try:
                if cand.resolve() == full_target_path.resolve():
                    continue
            except (OSError, RuntimeError):
                pass
            discovered_tests.append(cand)

    # If no direct name matches, search test folders for files importing target
    if not discovered_tests and repo_path:
        r_path = Path(repo_path)
        excluded_dirs = {".git", ".venv", "venv", "node_modules", "__pycache__", "backend", ".agents"}
        for root, dirs, files in os.walk(r_path):
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            rel_root = os.path.relpath(root, r_path).lower()
            is_test_dir = "test" in rel_root
            for file_name in files:
                if file_name.endswith(".py") and (is_test_dir or file_name.startswith("test_")):
                    test_cand = Path(root) / file_name
                    try:
                        if test_cand.resolve() == full_target_path.resolve():
                            continue
                    except (OSError, RuntimeError):
                        pass
                    # Check if test file imports target
                    t_count, invoked, fw = _inspect_test_file(test_cand, target_stem, target_functions)
                    if t_count > 0 and (invoked or f"import {target_stem}" in test_cand.read_text(errors="ignore")):
                        discovered_tests.append(test_cand)

    # Aggregate test counts
    for t_file in discovered_tests:
        t_count, invoked, fw = _inspect_test_file(t_file, target_stem, target_functions)
        total_test_functions += t_count
        all_invoked_target_funcs.update(invoked)
        if fw and not detected_framework:
            detected_framework = fw

    has_tests = len(discovered_tests) > 0 and total_test_functions > 0

    if not has_tests:
        return CoverageCheckResult(
            file_path=file_path_str,
            has_tests=False,
            test_file_path=None,
            test_files=[],
            test_functions_count=0,
            target_functions_count=len(target_functions),
            coverage_ratio=0.0,
            coverage_percentage="0%",
            framework=None,
        )

    # Calculate coverage ratio
    if all_invoked_target_funcs:
        coverage_ratio = min(1.0, len(all_invoked_target_funcs) / float(target_count))
    else:
        # Fallback heuristic based on test count relative to target function count
        coverage_ratio = min(0.8, total_test_functions / float(target_count * 2.0))

    coverage_percentage = f"{int(round(coverage_ratio * 100))}%"
    primary_test_path = (
        str(discovered_tests[0].relative_to(repo_path)).replace("\\", "/")
        if repo_path and discovered_tests[0].is_relative_to(Path(repo_path))
        else str(discovered_tests[0]).replace("\\", "/")
    )
    test_files_list = [
        str(p.relative_to(repo_path)).replace("\\", "/")
        if repo_path and p.is_relative_to(Path(repo_path))
        else str(p).replace("\\", "/")
        for p in discovered_tests
    ]

    return CoverageCheckResult(
        file_path=file_path_str,
        has_tests=True,
        test_file_path=primary_test_path,
        test_files=test_files_list,
        test_functions_count=total_test_functions,
        target_functions_count=len(target_functions),
        coverage_ratio=coverage_ratio,
        coverage_percentage=coverage_percentage,
        framework=detected_framework or "pytest",
    )
