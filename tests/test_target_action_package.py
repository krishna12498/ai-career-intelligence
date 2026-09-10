from backend.app.models.match import MatchReport, SkillMatchResult
from backend.app.models.multi_match import (
    CrossJobGap,
    CrossJobGapAnalysis,
    MultiMatchJobResult,
    MultiMatchRequest,
    MultiJobInput,
    RankingMetadata,
)
from backend.app.services.application_strategy_service import generate_application_strategy
from backend.app.services.multi_match_service import analyze_multiple_jobs
from backend.app.services.target_action_package_service import generate_target_action_package
from backend.app.services.target_recommendation_service import recommend_target


def create_mock_report(score=85.0, missing_required_skill=None, partial_skill=None):
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
    if partial_skill:
        matches.append(
            SkillMatchResult(
                job_skill=partial_skill,
                candidate_skill="PostgreSQL",
                similarity=0.7,
                match_type="required",
                status="Partial Match",
                score_percent=70,
            )
        )
    if missing_required_skill:
        matches.append(
            SkillMatchResult(
                job_skill=missing_required_skill,
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


def create_mock_job_result(job_id, score=85.0, rank=1, missing_required_skill=None, partial_skill=None, status="completed"):
    if status != "completed":
        return MultiMatchJobResult(job_id=job_id, label=f"Label {job_id}", status="failed", errors=["Failed"])
    report = create_mock_report(score, missing_required_skill, partial_skill)
    metadata = RankingMetadata(
        overall_match=score,
        skills_match=score,
        readiness_score=score,
        required_skill_coverage=score / 100.0,
        required_skill_count=1,
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


def test_action_package_immediate_application_focus():
    results = [create_mock_job_result("job-1", score=85.0, rank=1)]
    rec = recommend_target(results, ["job-1"])
    strat = generate_application_strategy(results, None, rec)
    pkg = generate_target_action_package(results, None, rec, strat)

    assert pkg.status == "action_package_generated"
    assert pkg.target_job_id == "job-1"
    assert "action_plan_immediate_application" in pkg.reason_codes
    assert len(pkg.action_plan) > 0
    assert len(pkg.interview_blueprint) > 0


def test_action_package_missing_skill_triggers_claim_protection():
    results = [create_mock_job_result("job-1", score=65.0, rank=1, missing_required_skill="Docker")]
    rec = recommend_target(results, ["job-1"])
    strat = generate_application_strategy(results, None, rec)
    pkg = generate_target_action_package(results, None, rec, strat)

    assert "resume_claim_protection_applied" in pkg.reason_codes
    missing_guidance = next((g for g in pkg.resume_tailoring if g.target_skill == "Docker"), None)
    assert missing_guidance is not None
    assert missing_guidance.current_gap_status == "missing"
    assert missing_guidance.risk_warning is not None
    assert "Do not claim this skill" in missing_guidance.risk_warning


def test_action_package_zero_gaps_focuses_on_evidence_and_interview_prep():
    results = [create_mock_job_result("job-1", score=100.0, rank=1)]
    rec = recommend_target(results, ["job-1"])
    strat = generate_application_strategy(results, None, rec)
    pkg = generate_target_action_package(results, None, rec, strat)

    assert "resume_claim_protection_applied" not in pkg.reason_codes
    assert any(q.question_type in {"technical_deep_dive", "project_experience"} for q in pkg.interview_blueprint)
    assert not any("architecture topic" in q.question for q in pkg.interview_blueprint)


def test_action_package_cross_job_quick_wins_integrated():
    results = [create_mock_job_result("job-1", score=70.0, rank=1)]
    rec = recommend_target(results, ["job-1"])
    strat = generate_application_strategy(results, None, rec)
    gap_analysis = CrossJobGapAnalysis(
        gaps=[
            CrossJobGap(
                skill="AWS",
                normalized_skill="aws",
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
    pkg = generate_target_action_package(results, gap_analysis, rec, strat)

    assert "cross_job_quick_wins_integrated" in pkg.reason_codes
    quick_win_step = next((s for s in pkg.action_plan if s.skill == "AWS"), None)
    assert quick_win_step is not None


def test_action_package_all_failed_jobs_fallback():
    results = [create_mock_job_result("job-1", status="failed")]
    rec = recommend_target(results, [])
    strat = generate_application_strategy(results, None, rec)
    pkg = generate_target_action_package(results, None, rec, strat)

    assert pkg.status == "no_completed_jobs"
    assert "no_completed_jobs_action_package" in pkg.reason_codes
    assert len(pkg.action_plan) == 0


def test_multi_match_integration_populates_target_action_package():
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
    assert resp.target_action_package is not None
    assert resp.target_action_package.status == "action_package_generated"
    assert resp.target_action_package.target_job_id == "job-python"
