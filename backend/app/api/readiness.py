from fastapi import APIRouter

from backend.app.models.readiness import ReadinessRequest, ReadinessResult
from backend.app.services.readiness_service import calculate_readiness


router = APIRouter(prefix="/readiness", tags=["readiness"])


@router.post("", response_model=ReadinessResult)
async def calculate_readiness_endpoint(request: ReadinessRequest) -> ReadinessResult:
    return calculate_readiness(request.match_report)