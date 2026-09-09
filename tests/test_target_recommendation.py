from backend.app.models.match import MatchReport, SkillMatchResult
from backend.app.models.multi_match import MultiMatchJobResult, RankingMetadata
from backend.app.services.target_recommendation_service import recommend_target


def report(score, *, required_coverage=90, provisional=False, preferred_gap=False):
    matches = [
        SkillMatchResult(
            job_skill="Python",
            candidate_skill="Python",
            similarity=1,
            match_type="required",
            status="Strong Match",
            score_percent=100,
        )
    ]
    if preferred_gap:
        matches.append(
            SkillMatchResult(
                job_skill="AWS",
                candidate_skill=None,
                similarity=0,
                match_type="preferred",
                status="Missing",
                score_percent=0,
            )
        )
    return MatchReport(
        overall_match=score,
        skills_match=score,
        project_relevance=50,
        experience_relevance=50,
        education_match=0,
        semantic_similarity=50,
        matches=[] if provisional else matches,
    )


def result(job_id, score, *, rank, coverage=90, provisional=False, preferred_gap=False, status="completed"):
    match_report = report(score, required_coverage=coverage, provisional=provisional, preferred_gap=preferred_gap) if status == "completed" else None
    metadata = RankingMetadata(
        overall_match=score,
        skills_match=score,
        readiness_score=70,
        required_skill_coverage=coverage,
        required_skill_count=0 if provisional else 1,
        preferred_skill_count=1 if preferred_gap else 0,
        provisional=provisional,
        input_position=rank - 1,
    ) if status == "completed" else None
    return MultiMatchJobResult(
        job_id=job_id,
        label=f"Label {job_id}",
        status=status,
        match_report=match_report,
        rank=rank if status == "completed" else None,
        ranking_score=score if status == "completed" else None,
        ranking_metadata=metadata,
    )


def test_recommends_top_ranked_job_and_reason_codes():
    results = [result("job-one", 80, rank=2), result("job-two", 90, rank=1, preferred_gap=True), result("failed", 0, rank=0, status="failed")]

    recommendation = recommend_target(results, ["job-two", "job-one"])

    assert recommendation.selected_job_id == "job-two"
    assert recommendation.selected_score == 90
    assert recommendation.reason_codes == [
        "highest_overall_match",
        "failed_jobs_excluded",
        "required_skill_coverage_strong",
        "preferred_skill_gaps_present",
    ]


def test_tied_top_scores_report_input_order_resolution():
    results = [result("first", 90, rank=1), result("second", 90, rank=2)]

    recommendation = recommend_target(results, ["first", "second"])

    assert recommendation.selected_job_id == "first"
    assert recommendation.tied_job_ids == ["first", "second"]
    assert "tie_resolved_by_input_order" in recommendation.reason_codes


def test_no_required_skills_are_provisional_but_selectable():
    recommendation = recommend_target([result("provisional", 85, rank=1, provisional=True)], ["provisional"])

    assert recommendation.status == "recommended"
    assert recommendation.provisional is True
    assert recommendation.reason_codes == ["highest_overall_match", "no_required_skills_provisional"]


def test_all_failed_jobs_return_no_completed_jobs():
    recommendation = recommend_target([result("failed", 0, rank=0, status="failed")], [])

    assert recommendation.status == "no_completed_jobs"
    assert recommendation.selected_job_id is None
    assert recommendation.reason_codes == ["no_completed_jobs"]
    assert recommendation.failed_count == 1