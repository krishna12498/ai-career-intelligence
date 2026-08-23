from __future__ import annotations

from functools import lru_cache

from backend.app.config import settings
from backend.app.models.knowledge import KnowledgeResult, KnowledgeSearchRequest, KnowledgeSearchResponse
from rag.vector_store import KnowledgeVectorStore


@lru_cache(maxsize=1)
def get_knowledge_store() -> KnowledgeVectorStore:
    store = KnowledgeVectorStore(
        settings.models_dir / "knowledge_base.faiss",
        settings.models_dir / "knowledge_base.json",
    )
    if store.index_path.exists() and store.metadata_path.exists():
        store.load()
    else:
        store.build()
    return store


def search_knowledge(request: KnowledgeSearchRequest) -> KnowledgeSearchResponse:
    if not request.query.strip() and not request.missing_skills and not request.preferred_skills:
        return KnowledgeSearchResponse()

    store = get_knowledge_store()
    queries: list[tuple[str, str]] = []
    queries.extend((skill, "missing") for skill in request.missing_skills if skill.strip())
    queries.extend((skill, "preferred") for skill in request.preferred_skills if skill.strip())
    if request.query.strip():
        queries.append((request.query.strip(), "query"))

    results: list[KnowledgeResult] = []
    seen: set[str] = set()
    for query, priority in queries:
        for document, similarity in store.search(query, top_k=request.top_k):
            if document.skill.casefold() in seen:
                continue
            seen.add(document.skill.casefold())
            results.append(
                KnowledgeResult(
                    skill=document.skill,
                    title=document.title,
                    summary=document.summary,
                    resource_type=document.resource_type,
                    level=document.level,
                    url=document.url,
                    source=document.source,
                    similarity=round(similarity, 3),
                    priority=priority,
                )
            )
            if len(results) >= request.top_k:
                return KnowledgeSearchResponse(results=results)

    return KnowledgeSearchResponse(results=results)
