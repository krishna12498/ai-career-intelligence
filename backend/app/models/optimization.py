from typing import Literal

from pydantic import BaseModel, Field


EvidenceSupport = Literal["explicit", "inferred", "missing"]
SuggestionStatus = Literal["supported", "verify_before_use", "learning_gap"]
SuggestionOperation = Literal["add", "replace", "reorder", "remove"]


class OptimizationEvidence(BaseModel):
    source_type: Literal["resume", "job_match"]
    source_text: str
    source_section: str | None = None
    support: EvidenceSupport


class OptimizationSuggestion(BaseModel):
    id: str
    section: str
    operation: SuggestionOperation
    original_text: str | None = None
    proposed_text: str
    evidence: list[OptimizationEvidence] = Field(default_factory=list)
    status: SuggestionStatus
    risk_flags: list[str] = Field(default_factory=list)
    grounding_note: str


class OptimizationRequest(BaseModel):
    master_resume_text: str = Field(..., min_length=50)
    job_description: str = Field(..., min_length=30)
    base_version_id: str = Field(default="master", min_length=1, max_length=100)
    use_semantic: bool = False


class OptimizationResponse(BaseModel):
    base_version_id: str
    target_role: str
    grounding_policy: str
    suggestions: list[OptimizationSuggestion] = Field(default_factory=list)