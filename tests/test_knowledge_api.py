from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.knowledge_service import get_knowledge_store


client = TestClient(app)


def test_knowledge_search_returns_relevant_results():
    get_knowledge_store.cache_clear()
    response = client.post(
        "/api/knowledge/search",
        json={"query": "Docker container deployment", "top_k": 3},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["results"]
    assert data["results"][0]["skill"] == "Docker"
    assert data["results"][0]["url"].startswith("https://")


def test_knowledge_search_prioritizes_missing_skills():
    response = client.post(
        "/api/knowledge/search",
        json={
            "missing_skills": ["Docker"],
            "preferred_skills": ["RAG"],
            "top_k": 2,
        },
    )

    assert response.status_code == 200
    results = response.json()["results"]
    assert results[0]["skill"] == "Docker"
    assert results[0]["priority"] == "missing"


def test_knowledge_search_empty_query_returns_empty_result():
    response = client.post("/api/knowledge/search", json={})

    assert response.status_code == 200
    assert response.json() == {"results": []}


def test_knowledge_search_unknown_query_returns_empty_result():
    response = client.post(
        "/api/knowledge/search",
        json={"query": "quantum computing", "top_k": 5},
    )

    assert response.status_code == 200
    assert response.json() == {"results": []}