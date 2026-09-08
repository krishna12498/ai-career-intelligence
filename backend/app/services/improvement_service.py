"""Grounded resume improvement suggestions based on extracted resume evidence."""

from backend.app.models.improvement import ImprovementResponse, ImprovementSuggestion
from backend.app.services.match_service import match_from_text
from backend.app.services.resume_service import parse_resume_text

GROUNDING_POLICY = (
    "Suggestions may clarify or organize facts found in the resume. "
    "They must not add technologies, metrics, responsibilities, or experience "
    "unless the candidate verifies those facts."
)


def _section_suggestions(resume) -> list[ImprovementSuggestion]:
    suggestions: list[ImprovementSuggestion] = []

    if not resume.summary:
        suggestions.append(
            ImprovementSuggestion(
                category="section",
                priority="medium",
                title="Add a targeted summary",
                action=(
                    "Write a two- or three-sentence summary using only your existing roles, "
                    "skills, and projects, then connect it to this target role."
                ),
                evidence=[],
                grounding_note="Do not add a title, technology, or achievement not present in the resume.",
            )
        )

    if not resume.projects:
        suggestions.append(
            ImprovementSuggestion(
                category="section",
                priority="low",
                title="Show relevant project evidence",
                action=(
                    "Add a project only if you completed it. Describe the problem, your contribution, "
                    "and technologies that are already supported by your experience."
                ),
                evidence=[],
                grounding_note="Do not create a project to cover a missing skill.",
            )
        )

    descriptions = [experience.description for experience in resume.experience if experience.description]
    if descriptions:
        original = descriptions[0].strip()
        normalized = original.rstrip(".!?") + "."
        if normalized != original:
            suggestions.append(
                ImprovementSuggestion(
                    category="rewrite",
                    priority="low",
                    title="Polish an existing experience bullet",
                    action=f"Use this fact-preserving version: {normalized}",
                    evidence=[original],
                    grounding_note="Only punctuation was normalized; verify the wording before publishing.",
                )
            )

    return suggestions


def build_improvement_report(
    resume_text: str,
    job_description: str,
    use_semantic: bool = True,
) -> ImprovementResponse:
    resume = parse_resume_text(resume_text)
    match = match_from_text(resume_text, job_description, use_semantic=use_semantic)
    suggestions = _section_suggestions(resume)

    required_missing: list[str] = []
    preferred_missing: list[str] = []
    for skill_match in match.matches:
        if skill_match.status.value != "Missing":
            continue
        if skill_match.match_type == "required":
            required_missing.append(skill_match.job_skill)
            priority = "high"
        else:
            preferred_missing.append(skill_match.job_skill)
            priority = "low"

        suggestions.append(
            ImprovementSuggestion(
                category="skill",
                priority=priority,
                title=f"Address {skill_match.job_skill}",
                action=(
                    f"If you have hands-on experience with {skill_match.job_skill}, add it to the "
                    "most relevant skills or experience section. Otherwise, treat it as a learning gap."
                ),
                evidence=[],
                grounding_note="The skill is missing from the extracted resume; never add it without verification.",
            )
        )

    for skill_match in match.matches:
        if skill_match.status.value != "Partial Match" or not skill_match.candidate_skill:
            continue
        suggestions.append(
            ImprovementSuggestion(
                category="evidence",
                priority="medium" if skill_match.match_type == "required" else "low",
                title=f"Clarify {skill_match.job_skill} evidence",
                action=(
                    f"Make the connection between {skill_match.candidate_skill} and {skill_match.job_skill} "
                    "explicit in the relevant bullet, only where that relationship is accurate."
                ),
                evidence=[skill_match.candidate_skill],
                grounding_note="The recommendation is based on the extracted candidate skill shown as evidence.",
            )
        )

    return ImprovementResponse(
        missing_required_skills=required_missing,
        missing_preferred_skills=preferred_missing,
        suggestions=suggestions,
        grounding_policy=GROUNDING_POLICY,
    )
