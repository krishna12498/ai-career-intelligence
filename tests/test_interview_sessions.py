from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services import interview_session_service
from backend.app.services.interview_session_store import InterviewSessionStore
from tests.fixtures.sample_resume import SAMPLE_RESUME_TEXT


client = TestClient(app)

JOB_DESCRIPTION = """
Junior AI Engineer

Required: Python, FastAPI, Kubernetes, SQL
Preferred: AWS, RAG

The role involves building practical machine learning products.
"""


def setup_session_store(monkeypatch, tmp_path: Path):
    store = InterviewSessionStore(tmp_path / "sessions.sqlite3")
    monkeypatch.setattr(interview_session_service, "get_session_store", lambda: store)
    return store


def create_session():
    response = client.post(
        "/api/interview/sessions",
        json={
            "resume_text": SAMPLE_RESUME_TEXT,
            "job_description": JOB_DESCRIPTION,
            "questions_per_category": 1,
        },
    )
    assert response.status_code == 200
    return response.json()


def test_session_creation_persists_opaque_questions(monkeypatch, tmp_path):
    store = setup_session_store(monkeypatch, tmp_path)
    created = create_session()

    assert len(created["session_id"]) == 32
    assert created["status"] == "created"
    assert created["questions"]
    assert store.get_session(created["session_id"]) is not None
    assert store.get_questions(created["session_id"])[0].evidence == created["questions"][0]["evidence"]


def test_answer_submission_uses_server_question_and_rejects_duplicates(monkeypatch, tmp_path):
    setup_session_store(monkeypatch, tmp_path)
    created = create_session()
    session_id = created["session_id"]
    question_id = created["questions"][0]["id"]

    first = client.post(
        f"/api/interview/sessions/{session_id}/answers",
        json={"question_id": question_id, "answer": "I used Python to build an API with a measurable result."},
    )
    duplicate = client.post(
        f"/api/interview/sessions/{session_id}/answers",
        json={"question_id": question_id, "answer": "A replacement answer."},
    )

    assert first.status_code == 200
    assert first.json()["evaluation"]["question_id"] == question_id
    assert duplicate.status_code == 409


def test_sessions_are_isolated_and_unknown_resources_are_404(monkeypatch, tmp_path):
    setup_session_store(monkeypatch, tmp_path)
    first = create_session()
    second = create_session()
    second_question = second["questions"][0]["id"]

    second_answer = client.post(
        f"/api/interview/sessions/{second['session_id']}/answers",
        json={"question_id": second_question, "answer": "Answer with enough detail and an outcome."},
    )
    first_state = client.get(f"/api/interview/sessions/{first['session_id']}")
    unknown = client.get("/api/interview/sessions/not-a-real-session")

    assert first["session_id"] != second["session_id"]
    assert second_answer.status_code == 200
    assert first_state.status_code == 200
    assert first_state.json()["answers"] == []
    assert unknown.status_code == 404


def test_completion_summary_is_transparent_and_idempotent(monkeypatch, tmp_path):
    setup_session_store(monkeypatch, tmp_path)
    created = create_session()
    session_id = created["session_id"]
    for question in created["questions"]:
        response = client.post(
            f"/api/interview/sessions/{session_id}/answers",
            json={
                "question_id": question["id"],
                "answer": "I used the grounded topic in a project, took an action, and achieved an outcome.",
            },
        )
        assert response.status_code == 200

    first = client.post(f"/api/interview/sessions/{session_id}/complete")
    second = client.post(f"/api/interview/sessions/{session_id}/complete")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    summary = first.json()["summary"]
    assert summary["completion_status"] == "complete"
    assert summary["overall_structure_coverage"] >= 0
    assert isinstance(summary["category_structure_coverage"], dict)
    assert "hiring" not in first.json()["grounding_policy"].lower()