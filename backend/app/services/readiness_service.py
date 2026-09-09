from backend.app.models.match import MatchReport, MatchStatus
from backend.app.models.readiness import ReadinessBlocker, ReadinessResult


READINESS_SCOPE_NOTE = (
    "This score reflects resume evidence and is not a hiring-probability estimate."
)


def _required_skill_coverage(report: MatchReport) -> float:
    required_matches = [match for match in report.matches if match.match_type == "required"]
    if not required_matches:
        return 0.0

    status_scores = {
        MatchStatus.STRONG: 100.0,
        MatchStatus.PARTIAL: 60.0,
        MatchStatus.MISSING: 0.0,
    }
    total = sum(status_scores[match.status] for match in required_matches)
    return round(total / len(required_matches), 2)


def _build_blockers(report: MatchReport) -> list[ReadinessBlocker]:
    blockers = []
    for match in report.matches:
        if match.match_type != "required" or match.status == MatchStatus.STRONG:
            continue
        if match.status == MatchStatus.MISSING:
            reason = "Required skill is not supported by the candidate profile."
        else:
            reason = "Required skill has only partial supporting evidence."
        blockers.append(
            ReadinessBlocker(skill=match.job_skill, status=match.status, reason=reason)
        )
    return blockers


def calculate_readiness(report: MatchReport) -> ReadinessResult:
    required_skill_coverage = _required_skill_coverage(report)
    experience_evidence = round(max(0.0, min(100.0, report.experience_relevance)), 2)
    project_evidence = round(max(0.0, min(100.0, report.project_relevance)), 2)
    readiness_score = round(
        required_skill_coverage * 0.60
        + experience_evidence * 0.25
        + project_evidence * 0.15,
        2,
    )

    blockers = _build_blockers(report)
    reasons = []
    if not any(match.match_type == "required" for match in report.matches):
        reasons.append("No required skills were identified, so readiness is provisional.")
    elif required_skill_coverage >= 80:
        reasons.append("Most required skills have strong or partial matches.")
    else:
        reasons.append("Required-skill gaps materially reduce readiness for this role.")
    if experience_evidence > 0:
        reasons.append("Relevant experience evidence is present.")
    else:
        reasons.append("No relevant experience evidence was identified.")
    if project_evidence > 0:
        reasons.append("Relevant project evidence is present.")
    else:
        reasons.append("No relevant project evidence was identified.")

    return ReadinessResult(
        readiness_score=readiness_score,
        required_skill_coverage=required_skill_coverage,
        experience_evidence=experience_evidence,
        project_evidence=project_evidence,
        blockers=blockers,
        reasons=reasons,
        scope_note=READINESS_SCOPE_NOTE,
    )