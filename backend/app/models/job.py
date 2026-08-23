from typing import Optional

from pydantic import BaseModel, Field


class JobDescriptionRequest(BaseModel):
    description: str = Field(..., min_length=30, description="Full job description text")
    use_semantic: bool = Field(
        default=True,
        description="Enable sentence-embedding skill detection for implicit mentions",
    )


class JobDescriptionResponse(BaseModel):
    job_title: str
    required_skills: list[str]
    preferred_skills: list[str]
    technologies: list[str]
    ai_ml_skills: list[str]
    experience_level: str
    extraction_metadata: dict = Field(default_factory=dict)
