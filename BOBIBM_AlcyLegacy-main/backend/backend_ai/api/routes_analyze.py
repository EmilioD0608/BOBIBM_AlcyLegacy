"""Risk diagnostic endpoint for BOB Backend."""

import logging
import os
import tempfile
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, status

from backend.analyzer.report_builder import build_analysis_report
from backend.api.schemas import AnalyzeRequest, AnalyzeResponse

router = APIRouter(tags=["analyze"])
logger = logging.getLogger(__name__)


def _get_allowed_roots() -> List[Path]:
    """Return all allowed base roots for repository sandbox validation.

    Allows:
    1. Directory configured via ALLOWED_REPO_ROOT (e.g. /tmp/repos in production).
    2. System temporary directory (for dynamically cloned repos / test suites).
    3. Current working directory and workspace root (for relative analysis).
    """
    roots: List[Path] = []

    # 1. Configured environment variable (can be multiple separated by pathsep)
    env_root = os.getenv("ALLOWED_REPO_ROOT")
    if env_root:
        for p in env_root.split(os.pathsep):
            if p.strip():
                try:
                    roots.append(Path(p.strip()).resolve())
                except Exception:
                    pass

    # 2. System temporary directory
    try:
        roots.append(Path(tempfile.gettempdir()).resolve())
    except Exception:
        pass

    # 3. Current working directory and workspace monorepo parent
    try:
        roots.append(Path.cwd().resolve())
        # backend_ai -> backend -> BOBIBM_AlcyLegacy-main -> monorepo root
        module_root = Path(__file__).resolve().parent.parent.parent.parent
        roots.append(module_root)
    except Exception:
        pass

    return roots


def _validate_repo_path(raw_path: str) -> Path:
    """Resolve and validate that repoPath is contained within an allowed sandbox.

    Rejects absolute paths pointing outside the allowed sandbox (e.g., /etc, C:\\Windows),
    path traversal attempts (../../etc/passwd), and non-existent directories.

    Raises:
        HTTPException 400: if path is invalid, unsafe, or does not exist.
    """
    try:
        resolved = Path(raw_path).resolve()
    except (OSError, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid repository path.")

    # B-02: verify containment within at least one allowed root
    allowed_roots = _get_allowed_roots()
    is_safe = False
    for root in allowed_roots:
        try:
            resolved.relative_to(root)
            is_safe = True
            break
        except (ValueError, RuntimeError):
            continue

    if not is_safe:
        logger.warning("B-02: Rejected path outside sandbox: %s (resolved: %s)", raw_path, resolved)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository path not found or not accessible.",
        )

    if not resolved.exists():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Repository path not found.")

    if not resolved.is_dir():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Repository path must be a directory.")

    return resolved


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_codebase(request: AnalyzeRequest) -> AnalyzeResponse:
    """Performs static code risk analysis on a repository or target files.

    Inspects AST dependencies, test coverage, git commit age, and computes
    calibrated risk scores without executing untrusted code.
    """
    # B-02: validate and sandbox the repository path
    repo_path = _validate_repo_path(request.repoPath)

    try:
        report = build_analysis_report(
            repo_path=repo_path,
            target_files=request.targetFiles,
            scope=request.scope,
        )
        return report
    except Exception as e:
        # B-05: log full detail internally, return generic message to client
        logger.error("Analysis failed for path '%s': %s", repo_path, e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis failed. Please try again or contact support.",
        )
