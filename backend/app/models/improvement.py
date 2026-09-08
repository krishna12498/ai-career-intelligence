from pydantic import BaseModel, Field


class ImprovementRequest(BaseModel):
    resume_text: str = Field(..., min_length=50)
    job_description: str = Field(..., min_length=30)
    use_semantic: bool = True


class ImprovementSuggestion(BaseModel):
    category: str
    priority: str
    title: str
    action: str
    evidence: list[str] = Field(default_factory=list)
    grounding_note: str


class ImprovementResponse(BaseModel):
    missing_required_skills: list[str] = Field(default_factory=list)
    missing_preferred_skills: list[str] = Field(default_factory=list)
    suggestions: list[ImprovementSuggestion] = Field(default_factory=list)
    grounding_policy: str
