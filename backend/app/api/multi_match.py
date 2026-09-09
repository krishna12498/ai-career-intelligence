from fastapi import APIRouter

from backend.app.models.multi_match import MultiMatchRequest, MultiMatchResponse
from backend.app.services.multi_match_service import analyze_multiple_jobs


router = APIRouter(prefix="/match", tags=["match"])


@router.post("/multi", response_model=MultiMatchResponse)
async def match_multiple_jobs(request: MultiMatchRequest) -> MultiMatchResponse:
    return analyze_multiple_jobs(request)