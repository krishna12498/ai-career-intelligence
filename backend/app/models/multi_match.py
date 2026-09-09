from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from backend.app.models.job import JobDescriptionResponse
from backend.app.models.match import MatchReport


class MultiJobInput(BaseModel):
    job_id: str = Field(..., min_length=1, max_length=100)
    label: str | None = Field(default=None, max_length=200)
    description: str = Field(..., min_length=30)


class MultiMatchRequest(BaseModel):
    resume_text: str = Field(..., min_length=50)
    jobs: list[MultiJobInput] = Field(..., min_length=1, max_length=10)
    use_semantic: bool = True

    @model_validator(mode="after")
    def validate_unique_job_ids(self):
        job_ids = [job.job_id for job in self.jobs]
        if len(job_ids) != len(set(job_ids)):
            raise ValueError("job_id values must be unique")
        return self


class MultiMatchJobResult(BaseModel):
    job_id: str
    label: str | None = None
    job: JobDescriptionResponse | None = None
    match_report: MatchReport | None = None
    status: Literal["completed", "failed"]
    errors: list[str] = Field(default_factory=list)


class MultiMatchSummary(BaseModel):
    requested: int = Field(ge=0)
    completed: int = Field(ge=0)
    failed: int = Field(ge=0)


class MultiMatchResponse(BaseModel):
    analysis_id: UUID
    results: list[MultiMatchJobResult]
    summary: MultiMatchSummary