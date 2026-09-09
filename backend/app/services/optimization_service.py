"""Deterministic, suggestion-only resume optimization."""

from backend.app.models.match import MatchStatus
from backend.app.models.optimization import (
    OptimizationEvidence,
    OptimizationRequest,
    OptimizationResponse,
    OptimizationSuggestion,
)
from backend.app.services.job_analyzer import analyze_job_description
from backend.app.services.match_service import generate_match_report
from backend.app.services.resume_service import parse_resume_text


GROUNDING_POLICY = (
    "Suggestions are reviewable proposals only. The master resume is never modified, "
    "and unsupported metrics, technologies, responsibilities, employers, titles, dates, "
    "or achievements are never presented as supported facts."
)


def _punctuation_suggestions(resume) -> list[OptimizationSuggestion]:
    suggestions: list[OptimizationSuggestion] = []
    seen: set[str] = set()
    for experience in resume.experience:
        original = (experience.description or "").strip()
        proposed = original.rstrip(".!?") + "." if original else ""
        if not original or proposed == original or original.casefold() in seen:
            continue
        seen.add(original.casefold())
        suggestions.append(
            OptimizationSuggestion(
                id=f"rewrite-{len(suggestions) + 1}",
                section="experience",
                operation="replace",
                original_text=original,
                proposed_text=proposed,
                evidence=[
                    OptimizationEvidence(
                        source_type="resume",
                        source_text=original,
                        source_section="experience",
                        support="explicit",
                    )
                ],
                status="supported",
                grounding_note="Only terminal punctuation was normalized; review before publishing.",
            )
        )
    return suggestions


def _match_suggestions(match) -> list[OptimizationSuggestion]:
    suggestions: list[OptimizationSuggestion] = []
    seen: set[tuple[str, str]] = set()
    for skill_match in match.matches:
        key = (skill_match.job_skill.casefold(), skill_match.status.value)
        if key in seen or skill_match.status == MatchStatus.STRONG:
            continue
        seen.add(key)

        if skill_match.status == MatchStatus.MISSING:
            suggestions.append(
                OptimizationSuggestion(
                    id=f"gap-{len(suggestions) + 1}",
                    section="skills",
                    operation="add",
                    proposed_text=(
                        f"Do not add {skill_match.job_skill} unless you can verify relevant hands-on experience."
                    ),
                    evidence=[
                        OptimizationEvidence(
                            source_type="job_match",
                            source_text=skill_match.job_skill,
                            source_section="required" if skill_match.match_type == "required" else "preferred",
                            support="missing",
                        )
                    ],
                    status="learning_gap",
                    risk_flags=["missing_resume_evidence"],
                    grounding_note="This is a learning-gap reminder, not a resume claim.",
                )
            )
            continue

        if not skill_match.candidate_skill:
            continue
        suggestions.append(
            OptimizationSuggestion(
                id=f"verify-{len(suggestions) + 1}",
                section="experience",
                operation="replace",
                proposed_text=(
                    f"Verify whether existing resume evidence supports the connection between "
                    f"{skill_match.candidate_skill} and {skill_match.job_skill}; do not add a stronger claim automatically."
                ),
                evidence=[
                    OptimizationEvidence(
                        source_type="resume",
                        source_text=skill_match.candidate_skill,
                        source_section="extracted skill",
                        support="inferred",
                    ),
                    OptimizationEvidence(
                        source_type="job_match",
                        source_text=skill_match.job_skill,
                        source_section=skill_match.match_type,
                        support="inferred",
                    ),
                ],
                status="verify_before_use",
                risk_flags=["semantic_or_partial_match"],
                grounding_note="The match is partial or inferred; verify the relationship before changing wording.",
            )
        )
    return suggestions


def build_optimization_suggestions(request: OptimizationRequest) -> OptimizationResponse:
    resume = parse_resume_text(request.master_resume_text)
    job = analyze_job_description(request.job_description, use_semantic=request.use_semantic)
    match = generate_match_report(
        resume,
        job,
        job_description=request.job_description,
    )

    suggestions = _punctuation_suggestions(resume) + _match_suggestions(match)
    return OptimizationResponse(
        base_version_id=request.base_version_id,
        target_role=job.job_title,
        grounding_policy=GROUNDING_POLICY,
        suggestions=suggestions,
    )