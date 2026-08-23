from fastapi import APIRouter

from backend.app.models.knowledge import KnowledgeSearchRequest, KnowledgeSearchResponse
from backend.app.services.knowledge_service import search_knowledge

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge_endpoint(request: KnowledgeSearchRequest) -> KnowledgeSearchResponse:
    return search_knowledge(request)
