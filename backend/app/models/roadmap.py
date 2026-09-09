from pydantic import BaseModel, Field

from backend.app.models.match import MatchReport, MatchStatus


class RoadmapResource(BaseModel):
    skill: str
    title: str
    summary: str
    resource_type: str
    level: str
    url: str
    source: str


class RoadmapItem(BaseModel):
    order: int = Field(ge=1)
    horizon: str
    skill: str
    priority: str
    status: MatchStatus | None = None
    reason: str
    resource: RoadmapResource | None = None
    grounding_note: str


class RoadmapResult(BaseModel):
    items: list[RoadmapItem] = Field(default_factory=list)
    source: str
    grounding_policy: str


class RoadmapRequest(BaseModel):
    match_report: MatchReport
    candidate_context: str = Field(default="", max_length=4000)
    max_items: int = Field(default=6, ge=1, le=10)