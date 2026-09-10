from backend.app.models.match import MatchReport, SkillMatchResult
from backend.app.models.multi_match import (
    CrossJobGap,
    CrossJobGapAnalysis,
    CrossJobGapOccurrence,
    MultiMatchJobResult,
    MultiMatchRequest,
    MultiJobInput,
    RankingMetadata,
)
from backend.app.services.application_strategy_service import generate_application_strategy
from backend.app.services.multi_match_service import analyze_multiple_jobs
from backend.app.services.target_recommendation_service import recommend_target


def create_mock_report(score=85.0, missing_skill=None):
    matches = [
        SkillMatchResult(
            job_skill="Python",
            candidate_skill="Python",
            similarity=1.0,
            match_type="required",
            status="Strong Match",
            score_percent=100,
        )
    ]
    if missing_skill:
        matches.append(
            SkillMatchResult(
                job_skill=missing_skill,
                candidate_skill=None,
                similarity=0.0,
                match_type="required",
                status="Missing",
                score_percent=0,
            )
        )
    return MatchReport(
        overall_match=score,
        skills_match=score,
        project_relevance=80.0,
        experience_relevance=80.0,
        education_match=100.0,
        semantic_similarity=80.0,
        matches=matches,
    )


def create_mock_job_result(job_id, score=85.0, rank=1, missing_skill=None, status="completed"):
    if status != "completed":
        return MultiMatchJobResult(job_id=job_id, label=f"Label {job_id}", status="failed", errors=["Failed"])
    report = create_mock_report(score, missing_skill)
    metadata = RankingMetadata(
        overall_match=score,
        skills_match=score,
        readiness_score=score,
        required_skill_coverage=score / 100.0,
        required_skill_count=1 if not missing_skill else 2,
        preferred_skill_count=0,
        provisional=False,
        input_position=rank - 1,
    )
    return MultiMatchJobResult(
        job_id=job_id,
        label=f"Label {job_id}",
        status="completed",
        match_report=report,
        rank=rank,
        ranking_score=score,
        ranking_metadata=metadata,
    )


def test_strategy_apply_now_for_high_match():
    results = [create_mock_job_result("job-1", score=85.0, rank=1)]
    rec = recommend_target(results, ["job-1"])
    strategy = generate_application_strategy(results, gap_analysis=None, target_recommendation=rec)

    assert strategy.status == "strategy_generated"
    assert strategy.primary_target_job_id == "job-1"
    assert strategy.timeline_status == "apply_now"
    assert "high_match_immediate_apply" in strategy.reason_codes
    assert len(strategy.pillars) > 0


def test_strategy_polish_and_apply_for_medium_match():
    results = [create_mock_job_result("job-1", score=65.0, rank=1, missing_skill="Docker")]
    rec = recommend_target(results, ["job-1"])
    strategy = generate_application_strategy(results, gap_analysis=None, target_recommendation=rec)

    assert strategy.status == "strategy_generated"
    assert strategy.timeline_status == "polish_and_apply"
    assert "strong_coverage_minor_polish" in strategy.reason_codes


def test_strategy_skill_up_first_for_low_match():
    results = [create_mock_job_result("job-1", score=45.0, rank=1, missing_skill="Kubernetes")]
    rec = recommend_target(results, ["job-1"])
    strategy = generate_application_strategy(results, gap_analysis=None, target_recommendation=rec)

    assert strategy.status == "strategy_generated"
    assert strategy.timeline_status == "skill_up_first"
    assert "critical_required_skills_missing" in strategy.reason_codes


def test_cross_job_quick_wins_identified():
    results = [create_mock_job_result("job-1", score=70.0, rank=1)]
    rec = recommend_target(results, ["job-1"])
    gap_analysis = CrossJobGapAnalysis(
        gaps=[
            CrossJobGap(
                skill="Docker",
                normalized_skill="docker",
                match_type="required",
                job_count=2,
                missing_count=2,
                partial_count=0,
                strong_count=0,
                missing_job_ids=["job-1", "job-2"],
                occurrences=[],
            )
        ]
    )
    strategy = generate_application_strategy(results, gap_analysis=gap_analysis, target_recommendation=rec)

    assert "cross_job_leveraged_skill_focus" in strategy.reason_codes
    quick_win_pillar = next((p for p in strategy.pillars if p.category == "quick_win_skills"), None)
    assert quick_win_pillar is not None
    assert any("Docker" in item for item in quick_win_pillar.items)


def test_all_failed_jobs_returns_fallback_strategy():
    results = [create_mock_job_result("job-1", status="failed")]
    rec = recommend_target(results, [])
    strategy = generate_application_strategy(results, gap_analysis=None, target_recommendation=rec)

    assert strategy.status == "no_completed_jobs"
    assert strategy.timeline_status == "no_target_resume_overhaul"
    assert "no_completed_jobs_resume_overhaul" in strategy.reason_codes


def test_multi_match_integration_populates_application_strategy():
    req = MultiMatchRequest(
        resume_text="Senior Python Engineer with SQL, Docker, FastAPI, and AWS experience.",
        jobs=[
            MultiJobInput(
                job_id="job-python",
                label="Python Developer",
                description="We need a Python Developer skilled in Python, SQL, Docker, and AWS.",
            )
        ],
    )
    resp = analyze_multiple_jobs(req)
    assert resp.application_strategy is not None
    assert resp.application_strategy.status == "strategy_generated"
    assert resp.application_strategy.primary_target_job_id == "job-python"

