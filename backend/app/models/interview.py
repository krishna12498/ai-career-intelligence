from pydantic import BaseModel, Field


class InterviewQuestion(BaseModel):
    id: str
    category: str
    question: str
    evidence: list[str] = Field(default_factory=list)
    grounding_note: str


class InterviewQuestionsRequest(BaseModel):
    resume_text: str = Field(..., min_length=50)
    job_description: str = Field(..., min_length=30)
    use_semantic: bool = True
    questions_per_category: int = Field(default=2, ge=1, le=5)


class InterviewQuestionsResponse(BaseModel):
    questions: list[InterviewQuestion] = Field(default_factory=list)
    grounding_policy: str


class InterviewEvaluationRequest(BaseModel):
    question: InterviewQuestion
    answer: str = Field(..., min_length=1, max_length=5000)


class InterviewEvaluation(BaseModel):
    question_id: str
    score: int = Field(ge=0, le=100)
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    feedback: str
    grounding_note: str
