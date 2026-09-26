"""Pydantic v2 schemas matching COORDINACION_BACKENDS.md contracts."""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------
# Health Check Schemas
# ---------------------------------------------------------
class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = "ok"
    service: str = "bob-backend"
    version: str = "1.0.0"
    timestamp: Optional[str] = None


# ---------------------------------------------------------
# Analyze (Static Risk Diagnostic) Schemas
# ---------------------------------------------------------
class AnalyzeRequest(BaseModel):
    """Payload for POST /internal/v1/analyze."""

    repoPath: str = Field(
        ...,
        max_length=500,
        description="Root path of the repository to analyze",
    )
    targetFiles: List[str] = Field(
        default_factory=list,
        max_length=200,
        description="List of relative file paths to inspect within repoPath (max 200 files)",
    )
    scope: str = Field(
        default="file",
        description="Scope of analysis: 'file', 'folder', or 'repo'",
    )


class FileAnalysisResult(BaseModel):
    """Analysis metrics and risk score for an individual file."""

    filePath: str = Field(..., description="Relative path of the analyzed file")
    riskScore: int = Field(..., ge=0, le=100, description="Calculated risk score (0-100)")
    riskLevel: Literal["low", "medium", "high"] = Field(
        ..., description="Risk category: low (<40), medium (40-69), high (>=70)"
    )
    dependencies: int = Field(
        ..., ge=0, description="Coupling count and imported dependency count"
    )
    coverage: str = Field(..., description="Test coverage string, e.g. '12%'")
    age: str = Field(..., description="Stagnation age string, e.g. '4.2 años'")
    blockers: List[str] = Field(
        default_factory=list,
        description="List of identified architectural/safety blockers",
    )
    safeToRefactorDirectly: bool = Field(
        ..., description="True if low/medium risk without critical blockers"
    )
    recommendation: str = Field(
        ..., description="Actionable recommendation before or for refactoring"
    )


class AnalyzeSummary(BaseModel):
    """Summary metrics across all analyzed files in request."""

    overallRisk: int = Field(..., ge=0, le=100, description="Overall risk score")
    riskLevel: Literal["low", "medium", "high"] = Field(
        ..., description="Overall risk level category"
    )
    totalFiles: int = Field(..., ge=0, description="Total count of analyzed files")
    highRiskFilesCount: int = Field(
        ..., ge=0, description="Count of files classified as high risk"
    )


class AnalyzeResponse(BaseModel):
    """Response payload for POST /internal/v1/analyze."""

    success: bool = True
    summary: AnalyzeSummary
    files: List[FileAnalysisResult]


# ---------------------------------------------------------
# Refactor (Modernization Engine) Schemas
# ---------------------------------------------------------
class UserSpecs(BaseModel):
    """User specifications for code modernization."""

    targetLanguage: str = Field(default="python", description="Target programming language")
    targetVersion: str = Field(default="3.12", description="Target language version")
    framework: str = Field(default="standard", description="Target framework or standard")
    customInstructions: Optional[str] = Field(
        default="",
        max_length=1_000,
        description="Additional customization instructions (max 1,000 chars)",
    )


class RefactorRequest(BaseModel):
    """Payload for POST /internal/v1/refactor."""

    filePath: str = Field(
        ...,
        max_length=500,
        description="Relative path of file to modernize",
    )
    originalCode: str = Field(
        ...,
        max_length=50_000,
        description="Original legacy source code (max 50,000 chars)",
    )
    userSpecs: UserSpecs = Field(
        default_factory=UserSpecs, description="Modernization specifications"
    )
    generateTests: bool = Field(
        default=True, description="Whether to generate characterization test suite"
    )
    riskScore: Optional[int] = Field(
        default=None, ge=0, le=100, description="Risk score of the file (0-100)"
    )


class RefactorResponse(BaseModel):
    """Response payload for POST /internal/v1/refactor."""

    success: bool = True
    filePath: str = Field(..., description="Relative path of refactored file")
    refactoredCode: str = Field(..., description="Modernized source code")
    generatedTests: str = Field(..., description="Pytest test suite code")
    diff: str = Field(..., description="Unified git diff patch")
    changesSummary: List[str] = Field(
        default_factory=list, description="List of key changes applied"
    )
