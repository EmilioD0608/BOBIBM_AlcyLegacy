"""Risk diagnostic endpoint for BOB Backend."""

import logging
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from backend.analyzer.report_builder import build_analysis_report
from backend.api.schemas import AnalyzeRequest, AnalyzeResponse

router = APIRouter(tags=["analyze"])
logger = logging.getLogger(__name__)

# B-02: Raíz de repositorios permitida — configurable vía env, default /tmp/repos.
# Cualquier repoPath que no sea hijo de esta raíz será rechazado.
_DEFAULT_ALLOWED_ROOT = os.path.join(os.sep + "tmp", "repos")
ALLOWED_ROOT = Path(os.getenv("ALLOWED_REPO_ROOT", _DEFAULT_ALLOWED_ROOT)).resolve()


def _validate_repo_path(raw_path: str) -> Path:
    """Resolve and validate that repoPath is inside ALLOWED_ROOT.

    Rejects absolute paths pointing outside the sandbox, relative path traversal
    (../../etc/passwd), symlinks escaping the sandbox, and non-existent directories.

    Raises:
        HTTPException 400: if path is invalid, unsafe, or does not exist.
    """
    try:
        resolved = Path(raw_path).resolve()
    except (OSError, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid repository path.")

    # B-02: enforce containment inside ALLOWED_ROOT
    try:
        resolved.relative_to(ALLOWED_ROOT)
    except ValueError:
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
