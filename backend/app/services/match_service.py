"""Full match report — connects Phase 1 resume + Phase 2 job analysis."""

import re

from backend.app.models.job import JobDescriptionResponse
from backend.app.models.match import MatchReport, MatchStatus, SkillMatchRequest, SkillMatchResponse
from backend.app.models.resume import StructuredResume
from backend.app.services.job_analyzer import analyze_job_description
from backend.app.services.matching_engine import get_matching_engine
from backend.app.services.resume_service import parse_resume_text
from backend.app.services.skill_extractor import to_display_name


def _collect_candidate_skills(resume: StructuredResume) -> list[str]:
    """Gather skills from resume profile including experience and projects."""
    skills: set[str] = set()

    for skill in resume.skills:
        skills.add(to_display_name(skill.name))

    for exp in resume.experience:
        for tech in exp.technologies:
            skills.add(to_display_name(tech))

    for project in resume.projects:
        for tech in project.technologies:
            skills.add(to_display_name(tech))

    return sorted(skills)


def _build_job_context(job: JobDescriptionResponse, job_description: str | None) -> str:
    parts = [job.job_title, job.experience_level]
    parts.extend(job.required_skills)
    parts.extend(job.preferred_skills)
    if job_description:
        parts.append(job_description)
    return " ".join(parts)


def _build_resume_context(resume: StructuredResume) -> str:
    parts: list[str] = []
    if resume.summary:
        parts.append(resume.summary)
    if resume.raw_text:
        parts.append(resume.raw_text)
    for exp in resume.experience:
        parts.append(f"{exp.title} {exp.description or ''}")
    for proj in resume.projects:
        parts.append(f"{proj.name} {proj.description or ''}")
    return " ".join(parts)


def _calculate_project_relevance(
    resume: StructuredResume,
    job_context: str,
    engine,
) -> float:
    if not resume.projects:
        return 0.0

    project_texts = [
        f"{p.name}. {p.description or ''}. Technologies: {', '.join(p.technologies)}"
        for p in resume.projects
    ]
    score = engine.max_text_similarity(job_context, project_texts)
    return round(score * 100, 2)


def _calculate_experience_relevance(
    resume: StructuredResume,
    job: JobDescriptionResponse,
    engine,
) -> float:
    if not resume.experience:
        return 0.0

    job_context = f"{job.job_title} {job.experience_level}"
    exp_texts = [
        f"{e.title} at {e.company}. {e.description or ''}. Tech: {', '.join(e.technologies)}"
        for e in resume.experience
    ]
    score = engine.max_text_similarity(job_context, exp_texts)
    return round(score * 100, 2)


def _calculate_education_match(
    resume: StructuredResume,
    job_context: str,
    engine,
) -> float:
    if not resume.education:
        return 0.0

    edu_texts = [
        f"{e.institution} {e.degree or ''} {e.field or ''}"
        for e in resume.education
    ]

    # If JD doesn't mention education requirements, assume strong match when degree exists
    if not re.search(r"\b(bachelor|master|degree|b\.?tech|m\.?tech|phd|graduate)\b", job_context, re.I):
        return 95.0

    score = engine.max_text_similarity(job_context, edu_texts)
    return round(score * 100, 2)


def _build_skill_lists(matches: list) -> tuple[list[str], list[str], list[str]]:
    strong, partial, missing = [], [], []
    for m in matches:
        if m.status == MatchStatus.STRONG:
            strong.append(m.job_skill)
        elif m.status == MatchStatus.PARTIAL:
            partial.append(m.job_skill)
        else:
            missing.append(m.job_skill)
    return strong, partial, missing


def _recommended_priority(matches: list) -> list[str]:
    """Order missing skills: required first, then preferred."""
    required_missing = [
        m.job_skill for m in matches
        if m.status == MatchStatus.MISSING and m.match_type == "required"
    ]
    preferred_missing = [
        m.job_skill for m in matches
        if m.status == MatchStatus.MISSING and m.match_type == "preferred"
    ]
    partial_required = [
        m.job_skill for m in matches
        if m.status == MatchStatus.PARTIAL and m.match_type == "required"
    ]
    partial_preferred = [
        m.job_skill for m in matches
        if m.status == MatchStatus.PARTIAL and m.match_type == "preferred"
    ]
    return required_missing + partial_required + preferred_missing + partial_preferred


def match_skills_only(request: SkillMatchRequest) -> SkillMatchResponse:
    engine = get_matching_engine()

    required_matches = engine.match_skills(
        request.candidate_skills,
        request.required_skills,
        match_type="required",
    )
    preferred_matches = engine.match_skills(
        request.candidate_skills,
        request.preferred_skills,
        match_type="preferred",
    )

    all_matches = required_matches + preferred_matches
    overall = engine.calculate_weighted_score(all_matches)

    return SkillMatchResponse(overall_match=overall, matches=all_matches)


def generate_match_report(
    resume: StructuredResume,
    job: JobDescriptionResponse,
    job_description: str | None = None,
) -> MatchReport:
    engine = get_matching_engine()
    candidate_skills = _collect_candidate_skills(resume)
    job_context = _build_job_context(job, job_description)
    resume_context = _build_resume_context(resume)

    required_matches = engine.match_skills(
        candidate_skills,
        job.required_skills,
        match_type="required",
    )
    preferred_matches = engine.match_skills(
        candidate_skills,
        job.preferred_skills,
        match_type="preferred",
    )
    all_matches = required_matches + preferred_matches

    skills_match = engine.calculate_weighted_score(all_matches)
    project_relevance = _calculate_project_relevance(resume, job_context, engine)
    experience_relevance = _calculate_experience_relevance(resume, job, engine)
    education_match = _calculate_education_match(resume, job_context, engine)
    semantic_sim = round(engine.text_similarity(resume_context, job_context) * 100, 2)

    # Weighted overall: skills-heavy with supporting signals
    overall_match = round(
        skills_match * 0.45
        + project_relevance * 0.20
        + experience_relevance * 0.20
        + education_match * 0.10
        + semantic_sim * 0.05,
        2,
    )

    strong, partial, missing = _build_skill_lists(all_matches)
    priority = _recommended_priority(all_matches)

    return MatchReport(
        overall_match=overall_match,
        skills_match=skills_match,
        project_relevance=project_relevance,
        experience_relevance=experience_relevance,
        education_match=education_match,
        semantic_similarity=semantic_sim,
        matches=all_matches,
        strong_skills=strong,
        partial_skills=partial,
        missing_skills=missing,
        recommended_priority=priority,
    )


def match_from_text(
    resume_text: str,
    job_description: str,
    use_semantic: bool = True,
) -> MatchReport:
    resume = parse_resume_text(resume_text)
    job = analyze_job_description(job_description, use_semantic=use_semantic)
    return generate_match_report(resume, job, job_description=job_description)
