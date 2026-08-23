from fastapi import APIRouter

from backend.app.models.match import (
    FullMatchRequest,
    MatchReport,
    SkillMatchRequest,
    SkillMatchResponse,
    TextMatchRequest,
)
from backend.app.services.match_service import (
    generate_match_report,
    match_from_text,
    match_skills_only,
)

router = APIRouter(prefix="/match", tags=["match"])


@router.post("/skills", response_model=SkillMatchResponse)
async def match_skills(request: SkillMatchRequest) -> SkillMatchResponse:
    """Match candidate skill list against required/preferred job skills."""
    return match_skills_only(request)


@router.post("", response_model=MatchReport)
async def match_resume_to_job(request: FullMatchRequest) -> MatchReport:
    """Full match report from structured resume + job analysis (Phase 1 + 2 output)."""
    return generate_match_report(
        request.resume,
        request.job,
        job_description=request.job_description,
    )


@router.post("/from-text", response_model=MatchReport)
async def match_from_text_endpoint(request: TextMatchRequest) -> MatchReport:
    """End-to-end: resume text + job description → full match report."""
    return match_from_text(
        request.resume_text,
        request.job_description,
        use_semantic=request.use_semantic,
    )
