from fastapi.testclient import TestClient

from backend.app.main import app
from tests.fixtures.sample_job import SAMPLE_JOB_DESCRIPTION
from tests.fixtures.sample_resume import SAMPLE_RESUME_TEXT


client = TestClient(app)


def test_improvement_endpoint_returns_grounded_skill_actions():
    job = """
    Backend Engineer
    Required: Python, FastAPI, Kubernetes
    Preferred: Terraform
    """
    response = client.post(
        "/api/improvement",
        json={
            "resume_text": SAMPLE_RESUME_TEXT,
            "job_description": job,
            "use_semantic": False,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["grounding_policy"]
    assert isinstance(data["suggestions"], list)

    missing_actions = [
        suggestion["action"]
        for suggestion in data["suggestions"]
        if suggestion["category"] == "skill"
    ]
    assert missing_actions
    assert all("If you have hands-on experience" in action for action in missing_actions)


def test_improvement_does_not_invent_candidate_facts():
    resume = """
    Alex Morgan

    SKILLS
    Python, FastAPI, SQL

    EXPERIENCE
    Backend Engineer
    Built REST APIs using Python and FastAPI
    """
    job = """
    Backend Engineer
    Required: Python, FastAPI, AWS, Docker
    """

    response = client.post(
        "/api/improvement",
        json={"resume_text": resume, "job_description": job, "use_semantic": False},
    )

    assert response.status_code == 200
    data = response.json()
    rendered = str(data["suggestions"])
    assert "40%" not in rendered
    assert "AWS" in rendered
    assert "Docker" in rendered
    assert "never add it without verification" in rendered


def test_improvement_can_polish_existing_evidence_without_adding_facts():
    response = client.post(
        "/api/improvement",
        json={
            "resume_text": SAMPLE_RESUME_TEXT,
            "job_description": SAMPLE_JOB_DESCRIPTION,
            "use_semantic": False,
        },
    )

    data = response.json()
    rewrites = [suggestion for suggestion in data["suggestions"] if suggestion["category"] == "rewrite"]
    assert rewrites
    assert rewrites[0]["evidence"][0] in rewrites[0]["action"]
