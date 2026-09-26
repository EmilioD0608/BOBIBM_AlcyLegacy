"""Risk diagnostic endpoint for BOB Backend."""

import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, status

from backend.analyzer.report_builder import build_analysis_report
from backend.api.schemas import AnalyzeRequest, AnalyzeResponse

router = APIRouter(tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_codebase(request: AnalyzeRequest) -> AnalyzeResponse:
    """Performs static code risk analysis on a repository or target files.

    Inspects AST dependencies, test coverage, git commit age, and computes
    calibrated risk scores without executing untrusted code.
    """
    repo_path = Path(request.repoPath)
    if not repo_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Repository path not found: {request.repoPath}",
        )

    try:
        report = build_analysis_report(
            repo_path=request.repoPath,
            target_files=request.targetFiles,
            scope=request.scope,
        )
        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )
