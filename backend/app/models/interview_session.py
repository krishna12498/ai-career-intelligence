from datetime import datetime

from pydantic import BaseModel, Field

from backend.app.models.interview import InterviewEvaluation, InterviewQuestion


class InterviewSessionCreateRequest(BaseModel):
    resume_text: str = Field(..., min_length=50)
    job_description: str = Field(..., min_length=30)
    questions_per_category: int = Field(default=2, ge=1, le=5)


class InterviewSessionSummary(BaseModel):
    overall_structure_coverage: float = Field(ge=0, le=100)
    category_structure_coverage: dict[str, float] = Field(default_factory=dict)
    recurring_feedback_themes: list[str] = Field(default_factory=list)
    answered: int = Field(ge=0)
    total_questions: int = Field(ge=0)
    completion_status: str


class InterviewSessionCreateResponse(BaseModel):
    session_id: str
    status: str
    questions: list[InterviewQuestion]
    created_at: datetime
    grounding_policy: str


class InterviewAnswerRequest(BaseModel):
    question_id: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1, max_length=5000)


class InterviewAnswerResponse(BaseModel):
    question_id: str
    evaluation: InterviewEvaluation
    submitted_at: datetime
    answered: int = Field(ge=0)
    total_questions: int = Field(ge=0)
    progress_percent: float = Field(ge=0, le=100)


class InterviewSessionAnswer(BaseModel):
    question_id: str
    answer: str
    evaluation: InterviewEvaluation
    submitted_at: datetime


class InterviewSessionResponse(BaseModel):
    session_id: str
    status: str
    questions: list[InterviewQuestion]
    answers: list[InterviewSessionAnswer] = Field(default_factory=list)
    created_at: datetime
    grounding_policy: str
    progress_percent: float = Field(ge=0, le=100)
    summary: InterviewSessionSummary | None = None


class InterviewSessionCompleteResponse(InterviewSessionResponse):
    summary: InterviewSessionSummary