from fastapi import APIRouter

from backend.app.models.roadmap import RoadmapRequest, RoadmapResult
from backend.app.services.roadmap_service import build_roadmap


router = APIRouter(prefix="/roadmap", tags=["roadmap"])


@router.post("", response_model=RoadmapResult)
async def build_roadmap_endpoint(request: RoadmapRequest) -> RoadmapResult:
    return build_roadmap(request)