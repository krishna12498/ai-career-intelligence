"""Independent multi-job orchestration over the existing single-job matcher."""

from uuid import uuid4

from backend.app.models.multi_match import (
    MultiMatchJobResult,
    MultiMatchRequest,
    MultiMatchResponse,
    MultiMatchSummary,
)
from backend.app.services.job_analyzer import analyze_job_description
from backend.app.services.match_service import generate_match_report
from backend.app.services.resume_service import parse_resume_text


SAFE_ANALYSIS_ERROR = "Job analysis could not be completed."


def analyze_multiple_jobs(request: MultiMatchRequest) -> MultiMatchResponse:
    results: list[MultiMatchJobResult] = []

    try:
        resume = parse_resume_text(request.resume_text)
    except Exception:
        return MultiMatchResponse(
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
    return MultiMatchResponse(
        analysis_id=uuid4(),
        results=results,
        summary=MultiMatchSummary(
            requested=len(results),
            completed=completed,
            failed=failed,
        ),
    )