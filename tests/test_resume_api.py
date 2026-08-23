import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from tests.fixtures.sample_resume import SAMPLE_RESUME_TEXT


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_parse_resume_text():
    response = client.post("/api/resume/parse-text", json={"text": SAMPLE_RESUME_TEXT})
    assert response.status_code == 200
    data = response.json()

    assert data["contact"]["email"] == "john.doe@email.com"
    assert data["contact"]["name"] == "John Doe"
    assert len(data["skills"]) >= 5

    skill_names = {s["name"] for s in data["skills"]}
    assert "python" in skill_names
    assert "fastapi" in skill_names or "langchain" in skill_names

    assert len(data["experience"]) >= 1
    assert len(data["education"]) >= 1
    assert len(data["projects"]) >= 1


def test_parse_resume_text_too_short():
    response = client.post("/api/resume/parse-text", json={"text": "short"})
    assert response.status_code == 400


def test_parse_pdf_invalid_file():
    response = client.post(
        "/api/resume/parse",
        files={"file": ("resume.txt", b"not a pdf", "text/plain")},
    )
    assert response.status_code == 400
