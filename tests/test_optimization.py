from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.optimization import OptimizationRequest
from backend.app.services.optimization_service import build_optimization_suggestions


client = TestClient(app)


RESUME = """Alex Morgan
Summary
Python backend engineer.

Skills
Python, FastAPI, SQL

Experience
Backend Engineer | Northstar Labs | 2022 - Present
Worked with APIs
"""

JOB = """Backend Engineer
Required: Python, FastAPI, AWS, REST APIs.
"""


def test_optimization_preserves_master_and_marks_unsupported_claims():
    request = OptimizationRequest(master_resume_text=RESUME, job_description=JOB)

    result = build_optimization_suggestions(request)

    assert request.master_resume_text == RESUME
    assert not any(
        suggestion.status == "supported"
        and "REST" in suggestion.proposed_text
        for suggestion in result.suggestions
    )
    aws_gap = next(s for s in result.suggestions if "AWS" in s.proposed_text)
    assert aws_gap.status == "learning_gap"
    rest_suggestion = next(
        s for s in result.suggestions if "rest apis" in s.proposed_text.casefold()
    )
    assert rest_suggestion.status == "learning_gap"
    assert "designed and implemented" not in str(result.suggestions)


def test_supported_replacement_retains_explicit_source_evidence():
    result = build_optimization_suggestions(
        OptimizationRequest(
            master_resume_text=RESUME.replace("Worked with APIs", "Worked with APIs!"),
            job_description=JOB,
        )
    )

    replacement = next(
        suggestion for suggestion in result.suggestions if suggestion.operation == "replace"
    )
    assert replacement.status == "supported"
    assert replacement.evidence[0].source_text == replacement.original_text
    assert replacement.proposed_text.rstrip(".") == replacement.original_text.rstrip("!?")


def test_optimization_is_deterministic_and_api_is_suggestion_only():
    request = {
        "master_resume_text": RESUME,
        "job_description": JOB,
        "base_version_id": "master",
    }

    first = client.post("/api/resume/optimization/suggestions", json=request)
    second = client.post("/api/resume/optimization/suggestions", json=request)

    assert first.status_code == 200
    assert first.json() == second.json()
    assert first.json()["base_version_id"] == "master"
    assert first.json()["grounding_policy"]
    assert all("original_text" in suggestion for suggestion in first.json()["suggestions"])