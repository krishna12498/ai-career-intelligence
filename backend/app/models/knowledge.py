from pydantic import BaseModel, Field


class KnowledgeSearchRequest(BaseModel):
    query: str = ""
    missing_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=20)


class KnowledgeResult(BaseModel):
    skill: str
    title: str
    summary: str
    resource_type: str
    level: str
    url: str
    source: str
    similarity: float
    priority: str


class KnowledgeSearchResponse(BaseModel):
    results: list[KnowledgeResult] = Field(default_factory=list)
