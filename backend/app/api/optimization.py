from fastapi import APIRouter

from backend.app.models.optimization import OptimizationRequest, OptimizationResponse
from backend.app.services.optimization_service import build_optimization_suggestions


router = APIRouter(prefix="/resume/optimization", tags=["resume optimization"])


@router.post("/suggestions", response_model=OptimizationResponse)
async def optimization_suggestions(request: OptimizationRequest) -> OptimizationResponse:
    return build_optimization_suggestions(request)