from fastapi import APIRouter, HTTPException

from backend.app.models.advisor import AdvisorRequest, AdvisorResponse
from backend.app.services.advisor_service import explain_skill
from rag.generator import GeneratorTimeoutError, GeneratorUnavailableError

router = APIRouter(prefix="/advisor", tags=["advisor"])


@router.post("/explain", response_model=AdvisorResponse)
async def explain_skill_endpoint(request: AdvisorRequest) -> AdvisorResponse:
    try:
        return explain_skill(request)
    except GeneratorTimeoutError as error:
        raise HTTPException(status_code=504, detail=str(error)) from error
    except GeneratorUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error