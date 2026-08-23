"""Rule-based structured extraction from resume plain text."""

import re
from typing import Optional

from backend.app.data.skills_db import SKILL_ALIASES, SKILL_LOOKUP
from backend.app.models.resume import (
    Certification,
    ContactInfo,
    Education,
    Experience,
    Project,
    Skill,
    StructuredResume,
)

# Section headers commonly found in resumes
SECTION_PATTERNS = {
    "experience": re.compile(
        r"^(?:work\s+)?experience|employment|professional\s+experience|work\s+history",
        re.I,
    ),
    "education": re.compile(r"^education|academic|qualifications", re.I),
    "skills": re.compile(r"^skills|technical\s+skills|core\s+competencies|technologies", re.I),
    "projects": re.compile(r"^projects|personal\s+projects|portfolio", re.I),
    "certifications": re.compile(r"^certifications?|licenses?", re.I),
    "summary": re.compile(r"^(?:professional\s+)?summary|about\s+me|profile|objective", re.I),
}

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}(?:[-.\s]?\d{2,4})?"
)
LINKEDIN_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-]+/?", re.I)
GITHUB_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[\w\-]+/?", re.I)
URL_PATTERN = re.compile(r"https?://[\w\-./?=&%#]+", re.I)

DATE_RANGE_PATTERN = re.compile(
    r"(?P<start>(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{4}|\d{4})"
    r"\s*[-–—to]+\s*"
    r"(?P<end>(?:present|current|now|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{4}|\d{4}))",
    re.I,
)


def _split_sections(text: str) -> dict[str, str]:
    lines = text.split("\n")
    sections: dict[str, list[str]] = {"header": []}
    current = "header"

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        matched_section = None
        for name, pattern in SECTION_PATTERNS.items():
            if pattern.match(stripped) and len(stripped) < 60:
                matched_section = name
                break

        if matched_section:
            current = matched_section
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(stripped)

    return {k: "\n".join(v) if isinstance(v, list) else v for k, v in sections.items()}


def _extract_contact(text: str) -> ContactInfo:
    header_lines = text.split("\n")[:8]
    header = "\n".join(header_lines)

    email_match = EMAIL_PATTERN.search(header)
    phone_match = PHONE_PATTERN.search(header)
    linkedin_match = LINKEDIN_PATTERN.search(text)
    github_match = GITHUB_PATTERN.search(text)

    name = None
    for line in header_lines[:3]:
        line = line.strip()
        if not line:
            continue
        if EMAIL_PATTERN.search(line) or PHONE_PATTERN.search(line):
            continue
        if LINKEDIN_PATTERN.search(line) or GITHUB_PATTERN.search(line):
            continue
        if len(line) < 60 and not line.lower().startswith("http"):
            name = line
            break

    location = None
    for line in header_lines:
        if EMAIL_PATTERN.search(line) or PHONE_PATTERN.search(line):
            continue
        loc_match = re.search(
            r"\b(india|usa|uk|canada|remote|hyderabad|bangalore|mumbai|delhi|chennai|pune)\b",
            line,
            re.I,
        )
        if loc_match:
            location = loc_match.group(0)
            break

    website = None
    for url in URL_PATTERN.findall(header):
        if "linkedin" not in url.lower() and "github" not in url.lower():
            website = url
            break

    return ContactInfo(
        name=name,
        email=email_match.group(0) if email_match else None,
        phone=phone_match.group(0) if phone_match else None,
        location=location,
        linkedin=linkedin_match.group(0) if linkedin_match else None,
        github=github_match.group(0) if github_match else None,
        website=website,
    )


def _normalize_skill_token(token: str) -> str:
    t = token.lower().strip()
    return SKILL_ALIASES.get(t, t)


def _find_skills_in_text(text: str) -> list[Skill]:
    text_lower = text.lower()
    found: dict[str, Skill] = {}

    # Multi-word skills first (longer matches)
    all_skills = sorted(SKILL_LOOKUP.keys(), key=len, reverse=True)
    for skill_name in all_skills:
        pattern = r"\b" + re.escape(skill_name) + r"\b"
        if re.search(pattern, text_lower):
            canonical = _normalize_skill_token(skill_name)
            if canonical not in found:
                found[canonical] = Skill(
                    name=canonical,
                    category=SKILL_LOOKUP.get(skill_name, SKILL_LOOKUP.get(canonical)),
                )

    return list(found.values())


def _parse_skills_section(section_text: str) -> list[Skill]:
    skills = _find_skills_in_text(section_text)

    # Also split comma/bullet lists for explicit skill lines
    for line in section_text.split("\n"):
        if "," in line or "|" in line:
            parts = re.split(r"[,|•·]", line)
            for part in parts:
                part = part.strip()
                if 2 <= len(part) <= 40:
                    normalized = _normalize_skill_token(part)
                    if normalized in SKILL_LOOKUP or part.lower() in SKILL_LOOKUP:
                        key = normalized
                        if key not in {s.name for s in skills}:
                            skills.append(
                                Skill(name=key, category=SKILL_LOOKUP.get(key, SKILL_LOOKUP.get(part.lower())))
                            )

    return skills


def _parse_experience_section(section_text: str) -> list[Experience]:
    experiences: list[Experience] = []
    lines = [l.strip() for l in section_text.split("\n") if l.strip()]

    date_indices = [i for i, line in enumerate(lines) if DATE_RANGE_PATTERN.search(line)]
    if not date_indices:
        return experiences

    for pos, date_idx in enumerate(date_indices):
        title_idx = date_idx - 2 if date_idx >= 2 else max(0, date_idx - 1)
        company_idx = date_idx - 1 if date_idx >= 1 else date_idx

        title = lines[title_idx]
        company = lines[company_idx] if company_idx != title_idx else "Unknown"

        date_match = DATE_RANGE_PATTERN.search(lines[date_idx])
        start_date = date_match.group("start") if date_match else None
        end_date = date_match.group("end") if date_match else None
        is_current = bool(end_date and re.search(r"present|current|now", end_date, re.I))

        next_date_idx = date_indices[pos + 1] if pos + 1 < len(date_indices) else len(lines)
        description_lines = lines[date_idx + 1:next_date_idx]
        description = " ".join(description_lines) if description_lines else None

        block_text = "\n".join(lines[title_idx:next_date_idx])
        technologies = [s.name for s in _find_skills_in_text(block_text)]

        experiences.append(
            Experience(
                company=company,
                title=title,
                start_date=start_date,
                end_date=end_date,
                is_current=is_current,
                description=description,
                technologies=technologies,
            )
        )

    return experiences


def _parse_education_section(section_text: str) -> list[Education]:
    educations: list[Education] = []
    blocks = re.split(r"\n(?=[A-Z])", section_text)

    for block in blocks:
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if not lines:
            continue

        institution = lines[0]
        degree = None
        field = None

        degree_pattern = re.compile(
            r"(b\.?s\.?|b\.?a\.?|m\.?s\.?|m\.?a\.?|ph\.?d\.?|bachelor|master|doctorate|b\.?tech|m\.?tech|diploma)",
            re.I,
        )
        for line in lines[1:]:
            if degree_pattern.search(line):
                degree = line
                break

        date_match = DATE_RANGE_PATTERN.search(block)
        start_date = date_match.group("start") if date_match else None
        end_date = date_match.group("end") if date_match else None

        gpa_match = re.search(r"gpa\s*[:.]?\s*([\d.]+)", block, re.I)
        gpa = gpa_match.group(1) if gpa_match else None

        educations.append(
            Education(
                institution=institution,
                degree=degree,
                field=field,
                start_date=start_date,
                end_date=end_date,
                gpa=gpa,
            )
        )

    return educations


def _parse_projects_section(section_text: str) -> list[Project]:
    projects: list[Project] = []
    blocks = re.split(r"\n(?=[•\-*]|\w)", section_text)

    for block in blocks:
        lines = [l.strip().lstrip("•-* ") for l in block.split("\n") if l.strip()]
        if not lines:
            continue

        name = lines[0]
        if "|" in name:
            name, inline_description = [part.strip() for part in name.split("|", 1)]
            lines = [name, inline_description, *lines[1:]]
        if len(name) > 80:
            continue

        description = " ".join(lines[1:]) if len(lines) > 1 else None
        url_match = URL_PATTERN.search(block)
        technologies = [s.name for s in _find_skills_in_text(block)]

        projects.append(
            Project(
                name=name,
                description=description,
                technologies=technologies,
                url=url_match.group(0) if url_match else None,
            )
        )

    return projects


def _parse_certifications_section(section_text: str) -> list[Certification]:
    certifications: list[Certification] = []
    for line in section_text.split("\n"):
        line = line.strip().lstrip("•-* ")
        if not line or len(line) < 5:
            continue
        date_match = re.search(r"\b(20\d{2}|19\d{2})\b", line)
        certifications.append(
            Certification(
                name=line,
                date=date_match.group(0) if date_match else None,
            )
        )
    return certifications


def extract_structured_resume(text: str) -> StructuredResume:
    """
    Parse plain resume text into a structured profile using heuristics.
    Phase 2 will add LLM-assisted extraction for higher accuracy.
    """
    sections = _split_sections(text)
    contact = _extract_contact(text)

    skills = _parse_skills_section(sections.get("skills", ""))
    # Also mine skills from full document
    global_skills = _find_skills_in_text(text)
    skill_names = {s.name for s in skills}
    for s in global_skills:
        if s.name not in skill_names:
            skills.append(s)

    experience = _parse_experience_section(sections.get("experience", ""))
    education = _parse_education_section(sections.get("education", ""))
    projects = _parse_projects_section(sections.get("projects", ""))
    certifications = _parse_certifications_section(sections.get("certifications", ""))

    summary = sections.get("summary", "").strip() or None
    if summary and len(summary) > 500:
        summary = summary[:500] + "..."

    return StructuredResume(
        contact=contact,
        summary=summary,
        skills=skills,
        experience=experience,
        education=education,
        projects=projects,
        certifications=certifications,
        raw_text=text,
        extraction_metadata={
            "method": "rule_based_v1",
            "sections_detected": list(sections.keys()),
            "skill_count": len(skills),
        },
    )
