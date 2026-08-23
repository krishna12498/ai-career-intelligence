from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.match import SkillMatchRequest
from backend.app.services.match_service import match_skills_only
from backend.app.services.matching_engine import classify_match, MatchingEngine
from tests.fixtures.sample_job import SAMPLE_JOB_DESCRIPTION
from tests.fixtures.sample_resume import SAMPLE_RESUME_TEXT

client = TestClient(app)

CANDIDATE_SKILLS = [
    "Python",
    "SQL",
    "Machine Learning",
    "React",
    "Firebase",
]

REQUIRED_SKILLS = [
    "Python",
    "SQL",
    "Machine Learning",
    "Docker",
]

PREFERRED_SKILLS = [
    "AWS",
    "RAG",
]


def test_classify_match_thresholds():
    assert classify_match(0.95).value == "Strong Match"
    assert classify_match(0.73).value == "Partial Match"
    assert classify_match(0.21).value == "Missing"


def test_match_skills_endpoint():
    response = client.post(
        "/api/match/skills",
        json={
            "candidate_skills": CANDIDATE_SKILLS,
            "required_skills": REQUIRED_SKILLS,
            "preferred_skills": PREFERRED_SKILLS,
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert 0 < data["overall_match"] < 100
    assert len(data["matches"]) == 6

    matches = {m["job_skill"]: m for m in data["matches"]}
    assert matches["Python"]["candidate_skill"] == "Python"
    assert matches["Python"]["status"] == "Strong Match"
    assert matches["Docker"]["status"] == "Missing"
    assert matches["Docker"]["candidate_skill"] is None
    assert matches["AWS"]["status"] == "Missing"


def test_match_skills_service():
    result = match_skills_only(
        SkillMatchRequest(
            candidate_skills=CANDIDATE_SKILLS,
            required_skills=REQUIRED_SKILLS,
            preferred_skills=PREFERRED_SKILLS,
        )
    )
    docker_match = next(m for m in result.matches if m.job_skill == "Docker")
    assert docker_match.candidate_skill is None
    assert docker_match.status.value == "Missing"


def test_match_from_text_endpoint():
    response = client.post(
        "/api/match/from-text",
        json={
            "resume_text": SAMPLE_RESUME_TEXT,
            "job_description": SAMPLE_JOB_DESCRIPTION,
            "use_semantic": False,
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert data["overall_match"] > 0
    assert data["skills_match"] > 0
    assert "Python" in data["strong_skills"] or "python" in str(data["strong_skills"]).lower()
    assert isinstance(data["missing_skills"], list)
    assert isinstance(data["recommended_priority"], list)


def test_matching_engine_text_similarity():
    engine = MatchingEngine()
    sim = engine.text_similarity("Python developer", "Python programming engineer")
    assert sim > 0.7


def test_matching_engine_maps_related_rag_phrases():
    result = match_skills_only(
        SkillMatchRequest(
            candidate_skills=["vector search and embeddings"],
            required_skills=["RAG"],
        )
    )

    assert result.matches[0].similarity >= 0.55
    assert result.matches[0].status.value == "Partial Match"


def test_matching_engine_maps_postgresql_to_sql():
    result = match_skills_only(
        SkillMatchRequest(
            candidate_skills=["PostgreSQL"],
            required_skills=["SQL"],
        )
    )

    match = result.matches[0]
    assert match.candidate_skill == "PostgreSQL"
    assert match.status.value == "Strong Match"
