from typing import Literal
from pydantic import BaseModel, Field


class StrategyPillar(BaseModel):
    category: Literal["resume_tailoring", "quick_win_skills", "project_focus", "interview_preparation"]
    title: str
    description: str
    items: list[str] = Field(default_factory=list)


class ApplicationStrategyResponse(BaseModel):
    status: Literal["strategy_generated", "no_completed_jobs"]
    primary_target_job_id: str | None = None
    primary_target_label: str | None = None
    timeline_status: Literal["apply_now", "polish_and_apply", "skill_up_first", "no_target_resume_overhaul"]
    headline: str
    reason_codes: list[str] = Field(default_factory=list)
    pillars: list[StrategyPillar] = Field(default_factory=list)
    scope_note: str

