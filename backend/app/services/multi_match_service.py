"""Independent multi-job orchestration over the existing single-job matcher."""

from uuid import uuid4

from backend.app.models.multi_match import (
    CrossJobGap,
    CrossJobGapAnalysis,
    CrossJobGapOccurrence,
    MultiMatchJobResult,
    MultiMatchRequest,
    MultiMatchResponse,
    MultiMatchSummary,
    RankingMetadata,
)
from backend.app.services.application_strategy_service import generate_application_strategy
from backend.app.services.job_analyzer import analyze_job_description
from backend.app.services.match_service import generate_match_report
from backend.app.services.readiness_service import calculate_readiness
from backend.app.services.resume_service import parse_resume_text
from backend.app.services.target_action_package_service import generate_target_action_package
from backend.app.services.target_recommendation_service import recommend_target

SAFE_ANALYSIS_ERROR = "Job analysis could not be completed."


def _normalize_skill(skill: str) -> str:
    return " ".join(skill.strip().casefold().split())


def _gap_priority(match_type: str, status: str) -> int:
    priority = {
        ("required", "Missing"): 0,
        ("required", "Partial Match"): 1,
        ("preferred", "Missing"): 2,
        ("preferred", "Partial Match"): 3,
    }
    return priority.get((match_type, status), 4)


def _aggregate_gaps(results: list[MultiMatchJobResult]) -> CrossJobGapAnalysis:
    aggregates: dict[tuple[str, str], dict] = {}
    completed_job_ids: list[str] = []

    for input_position, result in enumerate(results):
        if result.status != "completed" or result.match_report is None:
            continue
        completed_job_ids.append(result.job_id)
        seen_in_job: set[tuple[str, str, str]] = set()
        for match in result.match_report.matches:
            normalized_skill = _normalize_skill(match.job_skill)
            if not normalized_skill or match.match_type not in {"required", "preferred"}:
                continue
            occurrence_key = (normalized_skill, match.match_type, match.status.value)
            if occurrence_key in seen_in_job:
                continue
            seen_in_job.add(occurrence_key)
            key = (normalized_skill, match.match_type)
            aggregate = aggregates.setdefault(
                key,
                {
                    "skill": match.job_skill.strip(),
                    "normalized_skill": normalized_skill,
                    "match_type": match.match_type,
                    "first_position": input_position,
                    "occurrences": [],
                    "job_ids": set(),
                    "missing_job_ids": [],
                    "partial_job_ids": [],
                    "strong_job_ids": [],
                },
            )
            aggregate["job_ids"].add(result.job_id)
            status = match.status.value
            job_ids_key = {
                "Missing": "missing_job_ids",
                "Partial Match": "partial_job_ids",
                "Strong Match": "strong_job_ids",
            }[status]
            if result.job_id not in aggregate[job_ids_key]:
                aggregate[job_ids_key].append(result.job_id)
            aggregate["occurrences"].append(
                CrossJobGapOccurrence(
                    job_id=result.job_id,
                    label=result.label,
                    input_position=input_position,
                    rank=result.rank,
                    status=match.status,
                    candidate_skill=match.candidate_skill,
                    similarity=match.similarity,
                    score_percent=match.score_percent,
                )
            )

    gaps: list[CrossJobGap] = []
    for aggregate in aggregates.values():
        occurrences = aggregate["occurrences"]
        gaps.append(
            CrossJobGap(
                skill=aggregate["skill"],
                normalized_skill=aggregate["normalized_skill"],
                match_type=aggregate["match_type"],
                job_count=len(aggregate["job_ids"]),
                missing_count=len(aggregate["missing_job_ids"]),
                partial_count=len(aggregate["partial_job_ids"]),
                strong_count=len(aggregate["strong_job_ids"]),
                missing_job_ids=aggregate["missing_job_ids"],
                partial_job_ids=aggregate["partial_job_ids"],
                strong_job_ids=aggregate["strong_job_ids"],
                occurrences=occurrences,
            )
        )
    gaps.sort(
        key=lambda gap: (
            min(_gap_priority(gap.match_type, occurrence.status.value) for occurrence in gap.occurrences),
            gap.occurrences[0].input_position,
            gap.normalized_skill,
        )
    )
    return CrossJobGapAnalysis(
        completed_job_ids=completed_job_ids,
        gaps=gaps,
        required_gap_count=sum(gap.match_type == "required" for gap in gaps),
        preferred_gap_count=sum(gap.match_type == "preferred" for gap in gaps),
        missing_occurrence_count=sum(gap.missing_count for gap in gaps),
        partial_occurrence_count=sum(gap.partial_count for gap in gaps),
    )


def _rank_results(results: list[MultiMatchJobResult]) -> list[str]:
    completed = [
        (position, result)
        for position, result in enumerate(results)
        if result.status == "completed" and result.match_report is not None
    ]
    completed.sort(key=lambda item: (-item[1].match_report.overall_match, item[0]))

    ranked_job_ids: list[str] = []
    for rank, (position, result) in enumerate(completed, start=1):
        report = result.match_report
        readiness = calculate_readiness(report)
        required_matches = [match for match in report.matches if match.match_type == "required"]
        preferred_matches = [match for match in report.matches if match.match_type == "preferred"]
        result.rank = rank
        result.ranking_score = report.overall_match
        result.ranking_metadata = RankingMetadata(
            overall_match=report.overall_match,
            skills_match=report.skills_match,
            readiness_score=readiness.readiness_score,
            required_skill_coverage=readiness.required_skill_coverage,
            required_skill_count=len(required_matches),
            preferred_skill_count=len(preferred_matches),
            provisional=not required_matches,
            input_position=position,
        )
        ranked_job_ids.append(result.job_id)
    return ranked_job_ids


def analyze_multiple_jobs(request: MultiMatchRequest) -> MultiMatchResponse:
    results: list[MultiMatchJobResult] = []

    try:
        resume = parse_resume_text(request.resume_text)
    except Exception:
        rec = recommend_target([], [])
        gap_a = CrossJobGapAnalysis()
        response = MultiMatchResponse(
            analysis_id=uuid4(),
            results=[
                MultiMatchJobResult(
                    job_id=job_input.job_id,
                    label=job_input.label,
                    status="failed",
                    errors=[SAFE_ANALYSIS_ERROR],
                )
                for job_input in request.jobs
            ],
            summary=MultiMatchSummary(
                requested=len(request.jobs),
                completed=0,
                failed=len(request.jobs),
            ),
            gap_analysis=gap_a,
            target_recommendation=rec,
            application_strategy=generate_application_strategy([], gap_a, rec),
        )
        return response

    for job_input in request.jobs:
        try:
            job = analyze_job_description(job_input.description, use_semantic=request.use_semantic)
            report = generate_match_report(
                resume,
                job,
                job_description=job_input.description,
            )
            results.append(
                MultiMatchJobResult(
                    job_id=job_input.job_id,
                    label=job_input.label,
                    job=job,
                    match_report=report,
                    status="completed",
                )
            )
        except Exception:
            results.append(
                MultiMatchJobResult(
                    job_id=job_input.job_id,
                    label=job_input.label,
                    status="failed",
                    errors=[SAFE_ANALYSIS_ERROR],
                )
            )

    completed = sum(result.status == "completed" for result in results)
    failed = len(results) - completed
    rec = recommend_target([], [])
    gap_a = CrossJobGapAnalysis()
    app_strat = generate_application_strategy([], gap_a, rec)
    response = MultiMatchResponse(
        analysis_id=uuid4(),
        results=results,
        summary=MultiMatchSummary(
            requested=len(results),
            completed=completed,
            failed=failed,
        ),
        gap_analysis=gap_a,
        target_recommendation=rec,
        application_strategy=app_strat,
        target_action_package=generate_target_action_package([], gap_a, rec, app_strat),
    )
    response.ranked_job_ids = _rank_results(response.results)
    response.gap_analysis = _aggregate_gaps(response.results)
    response.target_recommendation = recommend_target(response.results, response.ranked_job_ids)
    response.application_strategy = generate_application_strategy(
        response.results, response.gap_analysis, response.target_recommendation
    )
    response.target_action_package = generate_target_action_package(
        response.results, response.gap_analysis, response.target_recommendation, response.application_strategy
    )
    return response