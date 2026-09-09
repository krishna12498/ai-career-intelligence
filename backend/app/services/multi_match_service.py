"""Independent multi-job orchestration over the existing single-job matcher."""

from uuid import uuid4

from backend.app.models.multi_match import (
    MultiMatchJobResult,
    MultiMatchRequest,
    MultiMatchResponse,
    MultiMatchSummary,
    RankingMetadata,
)
from backend.app.services.job_analyzer import analyze_job_description
from backend.app.services.match_service import generate_match_report
from backend.app.services.readiness_service import calculate_readiness
from backend.app.services.resume_service import parse_resume_text


SAFE_ANALYSIS_ERROR = "Job analysis could not be completed."


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
    response = MultiMatchResponse(
        analysis_id=uuid4(),
        results=results,
        summary=MultiMatchSummary(
            requested=len(results),
            completed=completed,
            failed=failed,
        ),
    )
    response.ranked_job_ids = _rank_results(response.results)
    return response