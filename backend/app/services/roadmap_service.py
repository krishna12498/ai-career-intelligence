from backend.app.models.knowledge import KnowledgeSearchRequest
from backend.app.models.match import MatchReport, MatchStatus
from backend.app.models.roadmap import (
    RoadmapItem,
    RoadmapRequest,
    RoadmapResource,
    RoadmapResult,
)
from backend.app.services.knowledge_service import search_knowledge


GROUNDING_POLICY = (
    "Roadmap resources are limited to independently retrieved curated knowledge-base documents. "
    "Candidate context does not change roadmap facts, ordering, or resources."
)


def _unique_priority_skills(report: MatchReport, max_items: int) -> list[str]:
    skills: list[str] = []
    seen: set[str] = set()
    for skill in report.recommended_priority:
        normalized = skill.strip().casefold()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        skills.append(skill.strip())
        if len(skills) >= max_items:
            break
    return skills


def _match_metadata(report: MatchReport, skill: str) -> tuple[str, MatchStatus | None]:
    normalized = skill.casefold()
    match = next(
        (item for item in report.matches if item.job_skill.strip().casefold() == normalized),
        None,
    )
    if match is None:
        return "required", None
    return match.match_type, match.status


def _horizon(order: int, total: int) -> str:
    first_cutoff = (total + 2) // 3
    second_cutoff = first_cutoff + (total - first_cutoff + 1) // 2
    if order <= first_cutoff:
        return "30 days"
    if order <= second_cutoff:
        return "60 days"
    return "90 days"


def _reason(priority: str, status: MatchStatus | None) -> str:
    if status == MatchStatus.MISSING:
        return f"{priority.capitalize()} skill is missing from the candidate profile."
    if status == MatchStatus.PARTIAL:
        return f"{priority.capitalize()} skill has partial supporting evidence."
    return f"{priority.capitalize()} skill is prioritized for continued development."


def build_roadmap(request: RoadmapRequest) -> RoadmapResult:
    skills = _unique_priority_skills(request.match_report, request.max_items)
    items: list[RoadmapItem] = []

    for order, skill in enumerate(skills, start=1):
        priority, status = _match_metadata(request.match_report, skill)
        knowledge = search_knowledge(
            KnowledgeSearchRequest(query=skill, top_k=1)
        )
        result = knowledge.results[0] if knowledge.results else None
        resource = (
            RoadmapResource(
                skill=result.skill,
                title=result.title,
                summary=result.summary,
                resource_type=result.resource_type,
                level=result.level,
                url=result.url,
                source=result.source,
            )
            if result
            else None
        )
        items.append(
            RoadmapItem(
                order=order,
                horizon=_horizon(order, len(skills)),
                skill=skill,
                priority=priority,
                status=status,
                reason=_reason(priority, status),
                resource=resource,
                grounding_note=(
                    "Resource metadata comes from the curated knowledge base."
                    if resource
                    else "No matching curated resource was found for this gap."
                ),
            )
        )

    return RoadmapResult(
        items=items,
        source="match_report",
        grounding_policy=GROUNDING_POLICY,
    )