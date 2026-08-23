from pydantic import BaseModel, Field


class AdvisorRequest(BaseModel):
    skill: str = Field(..., min_length=1, max_length=100)
    candidate_context: str = Field(default="", max_length=4000)


class AdvisorResource(BaseModel):
    skill: str
    title: str
    summary: str
    resource_type: str
    level: str
    url: str
    source: str


class AdvisorResponse(BaseModel):
    skill: str
    explanation: str
    resource: AdvisorResource | None = None