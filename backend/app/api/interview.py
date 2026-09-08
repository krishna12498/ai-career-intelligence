from fastapi import APIRouter

from backend.app.models.interview import (
    InterviewEvaluation,
    InterviewEvaluationRequest,
    InterviewQuestionsRequest,
    InterviewQuestionsResponse,
)
from backend.app.services.interview_service import (
    evaluate_interview_answer,
    generate_interview_questions,
)

router = APIRouter(prefix="/interview", tags=["interview"])


@router.post("/questions", response_model=InterviewQuestionsResponse)
async def interview_questions(request: InterviewQuestionsRequest) -> InterviewQuestionsResponse:
    """Generate grounded technical, resume, behavioral, and gap questions."""
    return generate_interview_questions(
        request.resume_text,
        request.job_description,
        questions_per_category=request.questions_per_category,
        use_semantic=request.use_semantic,
    )


@router.post("/evaluate", response_model=InterviewEvaluation)
async def evaluate_answer(request: InterviewEvaluationRequest) -> InterviewEvaluation:
    """Evaluate answer structure against the evidence attached to a question."""
    return evaluate_interview_answer(request)
