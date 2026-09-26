"""Modernization and refactoring endpoint for BOB Backend."""

import logging

from fastapi import APIRouter, HTTPException, status

from backend.api.schemas import RefactorRequest, RefactorResponse
from backend.refactor.engine import refactor_code

router = APIRouter(tags=["refactor"])
logger = logging.getLogger(__name__)


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
        # B-05: ValueError represents client-safe validation errors (e.g., empty code)
        logger.warning("Refactor validation error for '%s': %s", request.filePath, e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        # B-05: log full detail internally, return generic message to client
        logger.error(
            "Refactoring engine failed for '%s': %s", request.filePath, e, exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Refactoring failed. Please try again or contact support.",
        )
