"""Job description analyzer — keyword + semantic skill extraction."""

import re

from backend.app.models.job import JobDescriptionResponse
from backend.app.services.skill_extractor import (
    extract_skills_keyword,
    get_ai_ml_skill_set,
    to_display_name,
)
from ml.semantic_skills import extract_skills_semantic

TITLE_KEYWORDS = [
    "engineer",
    "developer",
    "analyst",
    "scientist",
    "architect",
    "specialist",
    "manager",
    "consultant",
    "intern",
]

PREFERRED_KEYWORDS = [
    "preferred",
    "nice to have",
    "good to have",
    "bonus",
    "plus",
    "optional",
]

REQUIRED_KEYWORDS = [
    "required",
    "must have",
    "requirements",
    "qualifications",
    "essential",
]

EXPERIENCE_PATTERNS: list[tuple[str, str]] = [
    (r"\b(junior|entry[- ]?level|graduate|fresher|intern)\b", "Junior"),
    (r"\b(0\s*[-–]\s*2|1\s*[-–]\s*2|0\s*to\s*2|1\s*to\s*2)\s*years?", "Junior"),
    (r"\b(senior|sr\.?)\b", "Senior"),
    (r"\b(lead|principal|staff|director)\b", "Lead"),
    (r"\b(mid[- ]?level|intermediate)\b", "Mid"),
    (r"\b(3\s*[-–]\s*5|4\s*[-–]\s*6|3\s*to\s*5)\s*years?", "Mid"),
    (r"\b(5\s*\+|6\s*\+|7\s*\+|8\s*\+|10\s*\+)\s*years?", "Senior"),
    (r"\b(5\s*[-–]\s*8|6\s*[-–]\s*10)\s*years?", "Senior"),
]

AI_ML_SKILLS = get_ai_ml_skill_set()


def extract_job_title(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line in lines[:12]:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in TITLE_KEYWORDS):
            if len(line) <= 100:
                return line
            return line[:100]

    return "Not specified"


def detect_experience_level(text: str) -> str:
    text_lower = text.lower()
    for pattern, level in EXPERIENCE_PATTERNS:
        if re.search(pattern, text_lower, re.I):
            return level
    return "Not specified"


def _split_required_preferred_sections(text: str) -> tuple[str, str]:
    """Split JD into required and preferred blocks when explicit sections exist."""
    text_lower = text.lower()

    required_start = -1
    for kw in REQUIRED_KEYWORDS:
        idx = text_lower.find(kw)
        if idx != -1:
            required_start = idx
            break

    preferred_start = -1
    for kw in PREFERRED_KEYWORDS:
        idx = text_lower.find(kw)
        if idx != -1:
            preferred_start = idx
            break

    required_block = ""
    preferred_block = ""

    if required_start != -1 and preferred_start != -1:
        if required_start < preferred_start:
            required_block = text[required_start:preferred_start]
            preferred_block = text[preferred_start:]
        else:
            preferred_block = text[preferred_start:required_start]
            required_block = text[required_start:]
    elif required_start != -1:
        required_block = text[required_start:]
    elif preferred_start != -1:
        preferred_block = text[preferred_start:]

    return required_block, preferred_block


def _merge_skills(
    keyword_skills: list[str],
    semantic_skills: list[tuple[str, float]],
) -> tuple[list[str], dict]:
    """Merge keyword and semantic results; semantic only adds skills not already found."""
    found = set(keyword_skills)
    semantic_matches: dict[str, float] = {}

    for skill, score in semantic_skills:
        if skill not in found:
            found.add(skill)
            semantic_matches[skill] = round(score, 3)

    return sorted(found), semantic_matches


def _classify_required_preferred(
    text: str,
    skills: list[str],
) -> tuple[list[str], list[str]]:
    required_block, preferred_block = _split_required_preferred_sections(text)

    preferred_skills: list[str] = []
    required_skills: list[str] = []

    for skill in skills:
        display = to_display_name(skill)
        skill_lower = skill.lower()

        in_preferred = preferred_block and skill_lower in preferred_block.lower()
        in_required = required_block and skill_lower in required_block.lower()

        if in_preferred and not in_required:
            preferred_skills.append(display)
        elif in_required and not in_preferred:
            required_skills.append(display)
        elif in_preferred:
            preferred_skills.append(display)
        else:
            required_skills.append(display)

    return sorted(required_skills), sorted(preferred_skills)


def analyze_job_description(
    text: str,
    use_semantic: bool = True,
) -> JobDescriptionResponse:
    """
    Analyze a job description into structured requirements.

    Pipeline:
        1. Text preprocessing (implicit via section extraction)
        2. Keyword skill extraction
        3. Semantic skill detection (sentence embeddings)
        4. Required vs preferred classification
        5. Experience level + job title detection
    """
    normalized = text.strip()
    keyword_skills = extract_skills_keyword(normalized)

    semantic_results: list[tuple[str, float]] = []
    if use_semantic:
        semantic_results = extract_skills_semantic(
            normalized,
            exclude=set(keyword_skills),
        )

    all_skills, semantic_matches = _merge_skills(keyword_skills, semantic_results)
    required_skills, preferred_skills = _classify_required_preferred(normalized, all_skills)

    ai_ml_skills = sorted(
        {to_display_name(s) for s in all_skills if s.lower() in AI_ML_SKILLS}
    )
    technologies = sorted(
        {to_display_name(s) for s in all_skills if s.lower() not in AI_ML_SKILLS}
    )

    return JobDescriptionResponse(
        job_title=extract_job_title(normalized),
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        technologies=technologies,
        ai_ml_skills=ai_ml_skills,
        experience_level=detect_experience_level(normalized),
        extraction_metadata={
            "method": "keyword_plus_semantic_v1",
            "keyword_skill_count": len(keyword_skills),
            "semantic_skill_count": len(semantic_matches),
            "semantic_matches": semantic_matches,
            "total_skills": len(all_skills),
        },
    )
