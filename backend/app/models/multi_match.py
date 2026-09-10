from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from backend.app.models.application_strategy import ApplicationStrategyResponse
from backend.app.models.job import JobDescriptionResponse
from backend.app.models.match import MatchReport, MatchStatus
from backend.app.models.target_action_package import TargetActionPackageResponse


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
    rank: int | None = None
    ranking_score: float | None = None
    ranking_metadata: "RankingMetadata | None" = None


class RankingMetadata(BaseModel):
    overall_match: float
    skills_match: float
    readiness_score: float
    required_skill_coverage: float
    required_skill_count: int = Field(ge=0)
    preferred_skill_count: int = Field(ge=0)
    provisional: bool
    input_position: int = Field(ge=0)


class CrossJobGapOccurrence(BaseModel):
    job_id: str
    label: str | None = None
    input_position: int = Field(ge=0)
    rank: int | None = None
    status: MatchStatus
    candidate_skill: str | None = None
    similarity: float
    score_percent: int


class CrossJobGap(BaseModel):
    skill: str
    normalized_skill: str
    match_type: Literal["required", "preferred"]
    job_count: int = Field(ge=0)
    missing_count: int = Field(ge=0)
    partial_count: int = Field(ge=0)
    strong_count: int = Field(ge=0)
    missing_job_ids: list[str] = Field(default_factory=list)
    partial_job_ids: list[str] = Field(default_factory=list)
    strong_job_ids: list[str] = Field(default_factory=list)
    occurrences: list[CrossJobGapOccurrence] = Field(default_factory=list)


class CrossJobGapAnalysis(BaseModel):
    completed_job_ids: list[str] = Field(default_factory=list)
    gaps: list[CrossJobGap] = Field(default_factory=list)
    required_gap_count: int = Field(default=0, ge=0)
    preferred_gap_count: int = Field(default=0, ge=0)
    missing_occurrence_count: int = Field(default=0, ge=0)
    partial_occurrence_count: int = Field(default=0, ge=0)


class TargetRecommendation(BaseModel):
    status: Literal["recommended", "no_completed_jobs"]
    selected_job_id: str | None = None
    selected_label: str | None = None
    selected_rank: int | None = None
    selected_score: float | None = None
    selected_readiness_score: float | None = None
    selected_required_skill_coverage: float | None = None
    provisional: bool = False
    reason_codes: list[str] = Field(default_factory=list)
    tied_job_ids: list[str] = Field(default_factory=list)
    completed_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    scope_note: str


class MultiMatchSummary(BaseModel):
    requested: int = Field(ge=0)
    completed: int = Field(ge=0)
    failed: int = Field(ge=0)


class MultiMatchResponse(BaseModel):
    analysis_id: UUID
    results: list[MultiMatchJobResult]
    summary: MultiMatchSummary
    ranked_job_ids: list[str] = Field(default_factory=list)
    gap_analysis: CrossJobGapAnalysis
    target_recommendation: TargetRecommendation
    application_strategy: ApplicationStrategyResponse | None = None
    target_action_package: TargetActionPackageResponse | None = None