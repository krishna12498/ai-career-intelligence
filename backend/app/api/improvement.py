from fastapi import APIRouter

from backend.app.models.improvement import ImprovementRequest, ImprovementResponse
from backend.app.services.improvement_service import build_improvement_report

router = APIRouter(prefix="/improvement", tags=["improvement"])


@router.post("", response_model=ImprovementResponse)
async def improve_resume(request: ImprovementRequest) -> ImprovementResponse:
    """Return grounded resume improvement suggestions for a target job."""
    return build_improvement_report(
        request.resume_text,
        request.job_description,
        use_semantic=request.use_semantic,
    )
