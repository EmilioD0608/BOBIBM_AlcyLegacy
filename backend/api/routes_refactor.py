"""Modernization and refactoring endpoint for BOB Backend."""

from fastapi import APIRouter, HTTPException, status

from backend.api.schemas import RefactorRequest, RefactorResponse
from backend.refactor.engine import refactor_code

router = APIRouter(tags=["refactor"])


@router.post("/refactor", response_model=RefactorResponse)
def refactor_source_code(request: RefactorRequest) -> RefactorResponse:
    """Modernizes legacy source code using IBM watsonx.ai provider.

    Applies requested user specifications, generates automated characterization
    tests if requested or risk is high, produces standard unified git diff,
    and validates syntax integrity.
    """
    try:
        response = refactor_code(request)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Refactoring engine failed: {str(e)}",
        )
