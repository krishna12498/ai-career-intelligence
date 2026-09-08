import re

from fastapi.testclient import TestClient

from backend.app.main import app
from tests.fixtures.sample_resume import SAMPLE_RESUME_TEXT


client = TestClient(app)


JOB_DESCRIPTION = """
Junior AI Engineer

Required: Python, FastAPI, Kubernetes, SQL
Preferred: AWS, RAG

The role involves building practical machine learning products.
"""


def test_interview_questions_cover_all_grounded_categories():
    response = client.post(
        "/api/interview/questions",
        json={
            "resume_text": SAMPLE_RESUME_TEXT,
            "job_description": JOB_DESCRIPTION,
            "use_semantic": False,
            "questions_per_category": 2,
        },
    )

    assert response.status_code == 200
    data = response.json()
    categories = {question["category"] for question in data["questions"]}
    assert categories == {"technical", "resume-specific", "behavioral", "gap"}
    assert data["grounding_policy"]
    assert any("Kubernetes" in question["question"] for question in data["questions"])


def test_interview_question_evidence_is_supported_by_input():
    response = client.post(
        "/api/interview/questions",
        json={
            "resume_text": SAMPLE_RESUME_TEXT,
            "job_description": JOB_DESCRIPTION,
            "use_semantic": False,
        },
    )

    source = re.sub(r"\s+", " ", f"{SAMPLE_RESUME_TEXT}\n{JOB_DESCRIPTION}").lower()
    for question in response.json()["questions"]:
        assert all(re.sub(r"\s+", " ", evidence.lower()).strip() in source for evidence in question["evidence"])


def test_interview_evaluation_is_structured_and_transparent():
    question = {
        "id": "technical-1",
        "category": "technical",
        "question": "How would you use Python to contribute in this role?",
        "evidence": ["Python"],
        "grounding_note": "Evidence lists the source terms used to form this question.",
    }
    response = client.post(
        "/api/interview/evaluate",
        json={
            "question": question,
            "answer": "I used Python to build an API, tested the integration, and improved the result for the project.",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["question_id"] == "technical-1"
    assert data["score"] >= 70
    assert data["strengths"]
    assert "not whether" in data["feedback"]
    assert "submitted answer" in data["grounding_note"]
