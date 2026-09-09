from backend.app.models.multi_match import (
    MultiMatchJobResult,
    TargetRecommendation,
)


SCOPE_NOTE = (
    "This recommendation compares resume evidence across the submitted jobs. "
    "It is not a hiring-probability estimate."
)


def recommend_target(
    results: list[MultiMatchJobResult],
    ranked_job_ids: list[str],
) -> TargetRecommendation:
    completed = [
        result
        for result in results
        if result.status == "completed" and result.match_report is not None
    ]
    failed_count = sum(result.status == "failed" for result in results)
    if not completed or not ranked_job_ids:
        return TargetRecommendation(
            status="no_completed_jobs",
            reason_codes=["no_completed_jobs"],
            completed_count=0,
            failed_count=failed_count,
            scope_note=SCOPE_NOTE,
        )

    selected_id = ranked_job_ids[0]
    selected = next(result for result in completed if result.job_id == selected_id)
    metadata = selected.ranking_metadata
    score = selected.match_report.overall_match
    top_ties = [
        result.job_id
        for result in completed
        if result.match_report.overall_match == score
    ]
    reason_codes = ["highest_overall_match"]
    if len(top_ties) > 1:
        reason_codes.append("tie_resolved_by_input_order")
    if failed_count:
        reason_codes.append("failed_jobs_excluded")
    if metadata and metadata.provisional:
        reason_codes.append("no_required_skills_provisional")
    elif metadata and metadata.required_skill_coverage >= 80:
        reason_codes.append("required_skill_coverage_strong")
    else:
        reason_codes.append("required_skill_gaps_present")

    if any(
        match.match_type == "preferred"
        and match.status.value in {"Missing", "Partial Match"}
        for match in selected.match_report.matches
    ):
        reason_codes.append("preferred_skill_gaps_present")

    return TargetRecommendation(
        status="recommended",
        selected_job_id=selected.job_id,
        selected_label=selected.label,
        selected_rank=selected.rank,
        selected_score=score,
        selected_readiness_score=metadata.readiness_score if metadata else None,
        selected_required_skill_coverage=metadata.required_skill_coverage if metadata else None,
        provisional=metadata.provisional if metadata else False,
        reason_codes=reason_codes,
        tied_job_ids=top_ties if len(top_ties) > 1 else [],
        completed_count=len(completed),
        failed_count=failed_count,
        scope_note=SCOPE_NOTE,
    )