from typing import Literal
from pydantic import BaseModel, Field


class TargetActionStep(BaseModel):
    step_number: int = Field(ge=1)
    priority: Literal["immediate", "short_term", "medium_term"]
    skill: str
    action_type: Literal["resume_polish", "evidence_strengthening", "interview_prep", "skill_upskilling"]
    title: str
    description: str
    resource_title: str | None = None
    resource_url: str | None = None
    grounding_note: str


class TargetInterviewQuestion(BaseModel):
    topic_id: str
    category: str
    question_type: Literal["technical_deep_dive", "project_experience", "gap_defense"]
    question: str
    target_skill: str
    recommended_focus: str
    grounding_note: str


class TargetResumeTailoringGuidance(BaseModel):
    target_skill: str
    requirement_type: Literal["required", "preferred"]
    current_gap_status: Literal["missing", "partial", "strong_match"]
    section: str = "Experience / Projects"
    current_evidence: str | None = None
    recommended_action: str
    risk_warning: str | None = None
    grounding_note: str


class TargetActionPackageResponse(BaseModel):
    status: Literal["action_package_generated", "no_completed_jobs"]
    target_job_id: str | None = None
    target_label: str | None = None
    reason_codes: list[str] = Field(default_factory=list)
    action_plan: list[TargetActionStep] = Field(default_factory=list)
    interview_blueprint: list[TargetInterviewQuestion] = Field(default_factory=list)
    resume_tailoring: list[TargetResumeTailoringGuidance] = Field(default_factory=list)
    scope_note: str

