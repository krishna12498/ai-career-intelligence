from fastapi import APIRouter, HTTPException

from backend.app.models.job import JobDescriptionRequest, JobDescriptionResponse
from backend.app.services.job_analyzer import analyze_job_description

router = APIRouter(prefix="/job", tags=["job"])


@router.post("/analyze", response_model=JobDescriptionResponse)
async def analyze_job(request: JobDescriptionRequest) -> JobDescriptionResponse:
    if len(request.description.strip()) < 30:
        raise HTTPException(status_code=400, detail="Job description too short (min 30 characters)")

    return analyze_job_description(
        request.description,
        use_semantic=request.use_semantic,
    )
