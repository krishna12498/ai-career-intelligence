from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.match import MatchReport
from backend.app.models.multi_match import MultiMatchJobResult
from backend.app.services import multi_match_service
from backend.app.services.multi_match_service import _rank_results
from tests.fixtures.sample_resume import SAMPLE_RESUME_TEXT


client = TestClient(app)

JOB_ONE = {
    "job_id": "job-one",
    "label": "Backend role",
    "description": "Backend engineer required Python, FastAPI, SQL, and Docker skills.",
}
JOB_TWO = {
    "job_id": "job-two",
    "label": "AI role",
    "description": "AI engineer required Python, machine learning, SQL, and RAG skills.",
}


def test_multi_match_returns_independent_reports_with_provenance():
    response = client.post(
        "/api/match/multi",
        json={"resume_text": SAMPLE_RESUME_TEXT, "jobs": [JOB_ONE, JOB_TWO], "use_semantic": False},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["analysis_id"]) == 36
    assert [result["job_id"] for result in data["results"]] == ["job-one", "job-two"]
    assert all(result["status"] == "completed" for result in data["results"])
    assert all(result["match_report"] for result in data["results"])
    assert data["summary"] == {"requested": 2, "completed": 2, "failed": 0}
    assert data["ranked_job_ids"] == sorted(
        [result["job_id"] for result in data["results"]],
        key=lambda job_id: next(
            result["match_report"]["overall_match"]
            for result in data["results"]
            if result["job_id"] == job_id
        ),
        reverse=True,
    )
    assert data["results"][0]["rank"] is not None
    assert data["results"][0]["ranking_score"] == data["results"][0]["match_report"]["overall_match"]


def test_duplicate_job_ids_fail_before_resume_analysis(monkeypatch):
    called = False

    def fail_if_called(text):
        nonlocal called
        called = True
        raise AssertionError("resume parsing should not run")

    monkeypatch.setattr(multi_match_service, "parse_resume_text", fail_if_called)
    response = client.post(
        "/api/match/multi",
        json={"resume_text": SAMPLE_RESUME_TEXT, "jobs": [JOB_ONE, {**JOB_TWO, "job_id": JOB_ONE["job_id"]}]},
    )

    assert response.status_code == 422
    assert "job_id values must be unique" in response.text
    assert called is False


def test_one_job_failure_does_not_remove_successful_jobs(monkeypatch):
    real_analyzer = multi_match_service.analyze_job_description

    def fail_one(description, use_semantic):
        if "AI engineer" in description:
            raise RuntimeError("private implementation detail")
        return real_analyzer(description, use_semantic=use_semantic)

    monkeypatch.setattr(multi_match_service, "analyze_job_description", fail_one)
    response = client.post(
        "/api/match/multi",
        json={"resume_text": SAMPLE_RESUME_TEXT, "jobs": [JOB_ONE, JOB_TWO], "use_semantic": False},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["results"][0]["status"] == "completed"
    assert data["results"][1]["status"] == "failed"
    assert data["results"][1]["errors"] == [multi_match_service.SAFE_ANALYSIS_ERROR]
    assert "private implementation detail" not in response.text
    assert data["summary"] == {"requested": 2, "completed": 1, "failed": 1}


def test_resume_is_parsed_once_and_semantic_setting_reaches_each_job(monkeypatch):
    parse_calls = 0
    semantic_values = []
    real_parse = multi_match_service.parse_resume_text
    real_analyzer = multi_match_service.analyze_job_description

    def count_parse(text):
        nonlocal parse_calls
        parse_calls += 1
        return real_parse(text)

    def capture_semantic(description, use_semantic):
        semantic_values.append(use_semantic)
        return real_analyzer(description, use_semantic=use_semantic)

    monkeypatch.setattr(multi_match_service, "parse_resume_text", count_parse)
    monkeypatch.setattr(multi_match_service, "analyze_job_description", capture_semantic)
    response = client.post(
        "/api/match/multi",
        json={"resume_text": SAMPLE_RESUME_TEXT, "jobs": [JOB_ONE, JOB_TWO], "use_semantic": False},
    )

    assert response.status_code == 200
    assert parse_calls == 1
    assert semantic_values == [False, False]


def test_multi_match_validates_job_count_and_description_length():
    too_many_jobs = [{**JOB_ONE, "job_id": f"job-{index}"} for index in range(11)]
    response = client.post(
        "/api/match/multi",
        json={"resume_text": SAMPLE_RESUME_TEXT, "jobs": too_many_jobs},
    )
    short_job = client.post(
        "/api/match/multi",
        json={"resume_text": SAMPLE_RESUME_TEXT, "jobs": [{"job_id": "short", "description": "Too short"}]},
    )

    assert response.status_code == 422
    assert short_job.status_code == 422


def make_result(job_id, score, *, required=True, status="completed"):
    report = MatchReport(
        overall_match=score,
        skills_match=score,
        project_relevance=50,
        experience_relevance=40,
        education_match=0,
        semantic_similarity=30,
        matches=(
            [
                {
                    "job_skill": "Python",
                    "candidate_skill": "Python",
                    "similarity": 1,
                    "match_type": "required",
                    "status": "Strong Match",
                    "score_percent": 100,
                }
            ]
            if required
            else []
        ),
    ) if status == "completed" else None
    return MultiMatchJobResult(job_id=job_id, status=status, match_report=report)


def test_ranking_orders_scores_and_preserves_input_order_on_ties():
    results = [make_result("first", 80), make_result("second", 95), make_result("third", 95)]

    ranked_ids = _rank_results(results)

    assert ranked_ids == ["second", "third", "first"]
    assert [result.rank for result in results] == [3, 1, 2]
    assert [result.ranking_score for result in results] == [80, 95, 95]


def test_ranking_excludes_failures_and_keeps_contiguous_ranks():
    results = [make_result("first", 90), make_result("failed", 0, status="failed"), make_result("third", 75)]

    ranked_ids = _rank_results(results)

    assert ranked_ids == ["first", "third"]
    assert [result.rank for result in results] == [1, None, 2]
    assert results[1].ranking_score is None
    assert results[1].ranking_metadata is None


def test_ranking_marks_no_required_skill_jobs_provisional_without_changing_order():
    results = [make_result("no-required", 90, required=False), make_result("lower", 80)]

    ranked_ids = _rank_results(results)

    assert ranked_ids == ["no-required", "lower"]
    assert results[0].ranking_metadata.required_skill_count == 0
    assert results[0].ranking_metadata.required_skill_coverage == 0
    assert results[0].ranking_metadata.provisional is True
    assert results[0].ranking_score == 90


def test_all_failed_jobs_have_no_ranked_ids():
    results = [make_result("failed-one", 0, status="failed"), make_result("failed-two", 0, status="failed")]

    assert _rank_results(results) == []
    assert all(result.rank is None for result in results)


def test_mixed_api_response_exposes_original_order_and_ranked_ids(monkeypatch):
    real_analyzer = multi_match_service.analyze_job_description

    def fail_ai(description, use_semantic):
        if "AI engineer" in description:
            raise RuntimeError("private implementation detail")
        return real_analyzer(description, use_semantic=use_semantic)

    monkeypatch.setattr(multi_match_service, "analyze_job_description", fail_ai)
    response = client.post(
        "/api/match/multi",
        json={"resume_text": SAMPLE_RESUME_TEXT, "jobs": [JOB_ONE, JOB_TWO, {**JOB_ONE, "job_id": "job-three"}], "use_semantic": False},
    )

    assert response.status_code == 200
    data = response.json()
    assert [result["job_id"] for result in data["results"]] == ["job-one", "job-two", "job-three"]
    assert data["ranked_job_ids"] == ["job-one", "job-three"]
    assert [result["rank"] for result in data["results"]] == [1, None, 2]