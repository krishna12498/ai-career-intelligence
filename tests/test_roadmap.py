from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.match import MatchReport, MatchStatus, SkillMatchResult
from backend.app.models.roadmap import RoadmapRequest
from backend.app.services import roadmap_service
from backend.app.services.roadmap_service import build_roadmap


client = TestClient(app)


def make_report(priority=None):
    matches = [
        SkillMatchResult(
            job_skill="Docker",
            candidate_skill=None,
            similarity=0,
            match_type="required",
            status=MatchStatus.MISSING,
            score_percent=0,
        ),
        SkillMatchResult(
            job_skill="AWS",
            candidate_skill="Cloud platform",
            similarity=0.6,
            match_type="preferred",
            status=MatchStatus.PARTIAL,
            score_percent=60,
        ),
        SkillMatchResult(
            job_skill="RAG",
            candidate_skill=None,
            similarity=0,
            match_type="preferred",
            status=MatchStatus.MISSING,
            score_percent=0,
        ),
    ]
    return MatchReport(
        overall_match=50,
        skills_match=50,
        project_relevance=50,
        experience_relevance=50,
        education_match=0,
        semantic_similarity=50,
        matches=matches,
        recommended_priority=priority or ["Docker", "docker", "AWS", "RAG"],
    )


def fake_search(request):
    result = type(
        "KnowledgeResult",
        (),
        {
            "skill": request.query,
            "title": f"{request.query} guide",
            "summary": f"Learn {request.query} fundamentals.",
            "resource_type": "guide",
            "level": "beginner",
            "url": f"https://example.com/{request.query.lower()}",
            "source": "Curated test resource",
        },
    )()
    return type("KnowledgeResponse", (), {"results": [result]})()


def test_roadmap_preserves_first_duplicate_and_assigns_horizons(monkeypatch):
    monkeypatch.setattr(roadmap_service, "search_knowledge", fake_search)

    result = build_roadmap(RoadmapRequest(match_report=make_report()))

    assert [item.skill for item in result.items] == ["Docker", "AWS", "RAG"]
    assert [item.horizon for item in result.items] == ["30 days", "60 days", "90 days"]
    assert result.items[0].priority == "required"
    assert result.items[0].status == MatchStatus.MISSING


def test_roadmap_keeps_missing_resources_and_does_not_use_candidate_context(monkeypatch):
    queries = []

    def search(request):
        queries.append(request.query)
        return type("KnowledgeResponse", (), {"results": []})()

    monkeypatch.setattr(roadmap_service, "search_knowledge", search)
    report = make_report(["Docker", "AWS"])

    first = build_roadmap(
        RoadmapRequest(match_report=report, candidate_context="Python developer")
    )
    second = build_roadmap(
        RoadmapRequest(match_report=report, candidate_context="Unrelated background")
    )

    assert queries == ["Docker", "AWS", "Docker", "AWS"]
    assert first == second
    assert all(item.resource is None for item in first.items)
    assert all("No matching curated resource" in item.grounding_note for item in first.items)


def test_roadmap_respects_max_items_and_api_contract(monkeypatch):
    monkeypatch.setattr(roadmap_service, "search_knowledge", fake_search)
    report = make_report(["Docker", "AWS", "RAG"])

    response = client.post(
        "/api/roadmap",
        json={
            "match_report": report.model_dump(mode="json"),
            "max_items": 2,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert [item["skill"] for item in data["items"]] == ["Docker", "AWS"]
    assert data["source"] == "match_report"
    assert "curated knowledge-base" in data["grounding_policy"]