from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.match import MatchReport, MatchStatus, SkillMatchResult
from backend.app.services.readiness_service import calculate_readiness


client = TestClient(app)


def make_report(required_statuses, *, experience=70, project=60):
    matches = [
        SkillMatchResult(
            job_skill=f"Skill {index}",
            candidate_skill="Candidate skill" if status != MatchStatus.MISSING else None,
            similarity=1.0 if status == MatchStatus.STRONG else 0.6 if status == MatchStatus.PARTIAL else 0.0,
            match_type="required",
            status=status,
            score_percent=100 if status == MatchStatus.STRONG else 60 if status == MatchStatus.PARTIAL else 0,
        )
        for index, status in enumerate(required_statuses)
    ]
    return MatchReport(
        overall_match=50,
        skills_match=50,
        project_relevance=project,
        experience_relevance=experience,
        education_match=0,
        semantic_similarity=50,
        matches=matches,
    )


def test_readiness_calculates_weighted_components_and_blockers():
    report = make_report([MatchStatus.STRONG, MatchStatus.PARTIAL, MatchStatus.MISSING])

    result = calculate_readiness(report)

    assert result.required_skill_coverage == 53.33
    assert result.experience_evidence == 70
    assert result.project_evidence == 60
    assert result.readiness_score == 58.5
    assert [blocker.skill for blocker in result.blockers] == ["Skill 1", "Skill 2"]
    assert "Required-skill gaps" in result.reasons[0]


def test_stronger_required_alignment_improves_readiness():
    weak = calculate_readiness(make_report([MatchStatus.MISSING, MatchStatus.PARTIAL]))
    strong = calculate_readiness(make_report([MatchStatus.STRONG, MatchStatus.STRONG]))

    assert strong.readiness_score > weak.readiness_score


def test_readiness_is_bounded_and_handles_no_required_skills():
    result = calculate_readiness(make_report([], experience=150, project=-10))

    assert result.readiness_score == 25.0
    assert result.required_skill_coverage == 0
    assert result.experience_evidence == 100
    assert result.project_evidence == 0
    assert result.blockers == []
    assert "provisional" in result.reasons[0]


def test_readiness_endpoint_accepts_explicit_match_report_request():
    response = client.post(
        "/api/readiness",
        json={"match_report": make_report([MatchStatus.STRONG]).model_dump(mode="json")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["readiness_score"] == 86.5
    assert data["scope_note"].startswith("This score reflects")