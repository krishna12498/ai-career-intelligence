from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from backend.app.models.job import JobDescriptionResponse
from backend.app.models.resume import StructuredResume


class MatchStatus(str, Enum):
    STRONG = "Strong Match"
    PARTIAL = "Partial Match"
    MISSING = "Missing"


class SkillMatchResult(BaseModel):
    job_skill: str
    candidate_skill: Optional[str] = None
    similarity: float
    match_type: str  # required | preferred
    status: MatchStatus
    score_percent: int


class MatchReport(BaseModel):
    overall_match: float
    skills_match: float
    project_relevance: float
    experience_relevance: float
    education_match: float
    semantic_similarity: float
    matches: list[SkillMatchResult] = Field(default_factory=list)
    strong_skills: list[str] = Field(default_factory=list)
    partial_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    recommended_priority: list[str] = Field(default_factory=list)


class SkillMatchRequest(BaseModel):
    candidate_skills: list[str] = Field(..., min_length=1)
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)


class SkillMatchResponse(BaseModel):
    overall_match: float
    matches: list[SkillMatchResult]


class FullMatchRequest(BaseModel):
    resume: StructuredResume
    job: JobDescriptionResponse
    job_description: Optional[str] = Field(
        None,
        description="Original JD text for semantic/project/experience scoring",
    )


class TextMatchRequest(BaseModel):
    resume_text: str = Field(..., min_length=50)
    job_description: str = Field(..., min_length=30)
    use_semantic: bool = True
