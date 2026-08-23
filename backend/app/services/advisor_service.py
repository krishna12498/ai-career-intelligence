from backend.app.models.advisor import AdvisorRequest, AdvisorResponse, AdvisorResource
from backend.app.models.knowledge import KnowledgeSearchRequest
from backend.app.services.knowledge_service import search_knowledge
from rag.generator import generate_advice


def explain_skill(request: AdvisorRequest) -> AdvisorResponse:
    skill = request.skill.strip()
    knowledge = search_knowledge(KnowledgeSearchRequest(query=skill, top_k=1))
    resource = knowledge.results[0] if knowledge.results else None
    resource_context = (
        f"{resource.title}: {resource.summary} ({resource.level}, {resource.url})"
        if resource
        else "No matching curated resource was found."
    )
    explanation = generate_advice(skill, resource_context, request.candidate_context)

    return AdvisorResponse(
        skill=skill,
        explanation=explanation,
        resource=(
            AdvisorResource(
                skill=resource.skill,
                title=resource.title,
                summary=resource.summary,
                resource_type=resource.resource_type,
                level=resource.level,
                url=resource.url,
                source=resource.source,
            )
            if resource
            else None
        ),
    )