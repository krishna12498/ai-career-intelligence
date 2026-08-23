import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from tests.fixtures.sample_job import SAMPLE_JOB_DESCRIPTION, SAMPLE_JOB_SEMANTIC

client = TestClient(app)


def test_analyze_job_keyword():
    response = client.post(
        "/api/job/analyze",
        json={"description": SAMPLE_JOB_DESCRIPTION, "use_semantic": False},
    )
    assert response.status_code == 200
    data = response.json()

    assert "Junior AI Engineer" in data["job_title"]
    assert data["experience_level"] == "Junior"

    required = set(data["required_skills"])
    assert "Python" in required
    assert "Machine Learning" in required
    assert "SQL" in required
    assert "FastAPI" in required
    assert "Docker" in required
    assert "AWS" in required

    preferred = set(data["preferred_skills"])
    assert "LangChain" in preferred
    assert "RAG" in preferred
    assert "LangGraph" in preferred

    assert "Machine Learning" in data["ai_ml_skills"]
    assert "Python" in data["technologies"]


def test_analyze_job_too_short():
    response = client.post("/api/job/analyze", json={"description": "short"})
    assert response.status_code == 422


def test_analyze_job_semantic_rag():
    """Semantic detection should find RAG from 'retrieval augmented generation' phrasing."""
    response = client.post(
        "/api/job/analyze",
        json={"description": SAMPLE_JOB_SEMANTIC, "use_semantic": True},
    )
    assert response.status_code == 200
    data = response.json()

    all_skills = (
        data["required_skills"]
        + data["preferred_skills"]
        + data["ai_ml_skills"]
        + data["technologies"]
    )
    assert any(s.upper() == "RAG" for s in all_skills)
    assert data["experience_level"] == "Senior"
