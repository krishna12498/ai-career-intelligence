from pydantic import BaseModel, Field

from backend.app.models.match import MatchReport, MatchStatus


class ReadinessBlocker(BaseModel):
    skill: str
    status: MatchStatus
    reason: str


class ReadinessResult(BaseModel):
    readiness_score: float = Field(ge=0, le=100)
    required_skill_coverage: float = Field(ge=0, le=100)
    experience_evidence: float = Field(ge=0, le=100)
    project_evidence: float = Field(ge=0, le=100)
    blockers: list[ReadinessBlocker] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    scope_note: str


class ReadinessRequest(BaseModel):
    match_report: MatchReport