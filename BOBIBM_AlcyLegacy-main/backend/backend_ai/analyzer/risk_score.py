"""Continuous calibrated risk scoring engine for BOB Backend.

Calculates weighted risk score (0-100), risk semaphore (high, medium, low),
architectural blockers, and refactoring recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, Union


RiskLevel = Literal["low", "medium", "high"]


@dataclass
class RiskScoreResult:
    """Calculated risk assessment result."""

    risk_score: int
    risk_level: RiskLevel
    safe_to_refactor_directly: bool
    recommendation: str
    blockers: List[str] = field(default_factory=list)
    dependencies: int = 0
    coverage_ratio: float = 0.0
    age_in_years: float = 0.0
    penalties: float = 0.0

    def to_dict(self) -> Dict[str, Union[int, str, bool, List[str], float]]:
        """Convert result to dictionary representation."""
        return {
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "safe_to_refactor_directly": self.safe_to_refactor_directly,
            "recommendation": self.recommendation,
            "blockers": self.blockers,
            "dependencies": self.dependencies,
            "coverage_ratio": self.coverage_ratio,
            "age_in_years": self.age_in_years,
            "penalties": self.penalties,
        }


def calculate_risk_score(
    dependencies: int,
    coverage_ratio: float,
    age_in_years: float,
    unresolved_globals: Optional[List[str]] = None,
    syntax_valid: bool = True,
    error_message: Optional[str] = None,
) -> RiskScoreResult:
    """Computes the continuous calibrated risk score and blockers.

    Formula:
        score = round(
            0.30 * min(100, deps * 6) +
            0.35 * (100 * (1 - cov)) +
            0.20 * min(100, age_years * 20) +
            penalties
        )
        penalties: +15 if unresolved_globals, +10 if coverage == 0, +30 if syntax invalid.
        Bounded between 0 and 100.

    Args:
        dependencies: Total coupling / dependencies count.
        coverage_ratio: Unit test coverage ratio (0.0 to 1.0).
        age_in_years: Elapsed time since last modification in years.
        unresolved_globals: List of unresolved global variable names.
        syntax_valid: Whether the source code parsed cleanly.
        error_message: Optional syntax or parser error message.

    Returns:
        RiskScoreResult with calibrated score, level, blockers, and recommendation.
    """
    unresolved = unresolved_globals or []
    cov = max(0.0, min(1.0, float(coverage_ratio)))
    deps = max(0, int(dependencies))
    age_yrs = max(0.0, float(age_in_years))

    # Calculate weighted components
    deps_component = min(100.0, deps * 6.0)
    cov_component = 100.0 * (1.0 - cov)
    age_component = min(100.0, age_yrs * 20.0)

    # Penalties
    penalties = 0.0
    if len(unresolved) > 0:
        penalties += 15.0
    if cov == 0.0:
        penalties += 10.0
    if not syntax_valid:
        penalties += 30.0

    raw_score = (
        0.30 * deps_component
        + 0.35 * cov_component
        + 0.20 * age_component
        + penalties
    )

    risk_score = max(0, min(100, int(round(raw_score))))

    # Semaphore classification:
    # > 70: "high" (or >= 70)
    # 40 to 69: "medium"
    # < 40: "low"
    if risk_score >= 70:
        risk_level: RiskLevel = "high"
    elif risk_score >= 40:
        risk_level = "medium"
    else:
        risk_level = "low"

    # Blockers generation
    blockers: List[str] = []
    if deps > 10:
        blockers.append(f"Alto acoplamiento con {deps} módulos críticos")
    if cov < 0.20:
        blockers.append("Sin tests unitarios automatizados detectados")
    if len(unresolved) > 0:
        blockers.append("Uso de variables globales no resueltas")
    if not syntax_valid and error_message:
        blockers.append(f"Error de sintaxis en el archivo: {error_message}")

    # safeToRefactorDirectly logic
    if risk_score >= 70 or len(unresolved) > 0 or not syntax_valid:
        safe_to_refactor = False
        recommendation = "Generar suite de tests de caracterización antes de refactorizar."
    elif risk_level == "medium":
        safe_to_refactor = True
        recommendation = "Proceder con modernización estándar con revisión recomendada."
    else:
        safe_to_refactor = True
        recommendation = "Código seguro para refactorización directa."

    return RiskScoreResult(
        risk_score=risk_score,
        risk_level=risk_level,
        safe_to_refactor_directly=safe_to_refactor,
        recommendation=recommendation,
        blockers=blockers,
        dependencies=deps,
        coverage_ratio=cov,
        age_in_years=age_yrs,
        penalties=penalties,
    )
