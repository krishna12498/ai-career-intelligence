from backend.app.services.job_analyzer import (
    analyze_job_description,
    detect_experience_level,
    extract_job_title,
)
from backend.app.services.skill_extractor import extract_skills_keyword
from tests.fixtures.sample_job import SAMPLE_JOB_DESCRIPTION, SAMPLE_JOB_SEMANTIC


def test_extract_job_title():
    title = extract_job_title(SAMPLE_JOB_DESCRIPTION)
    assert "Junior AI Engineer" in title


def test_detect_experience_level():
    assert detect_experience_level("Junior developer with 0-2 years") == "Junior"
    assert detect_experience_level("Senior engineer 5+ years") == "Senior"
    assert detect_experience_level("Random job post") == "Not specified"


def test_keyword_skill_extraction():
    skills = extract_skills_keyword(SAMPLE_JOB_DESCRIPTION)
    assert "python" in skills
    assert "fastapi" in skills
    assert "langchain" in skills


def test_analyze_job_description_keyword_only():
    result = analyze_job_description(SAMPLE_JOB_DESCRIPTION, use_semantic=False)
    assert len(result.required_skills) >= 6
    assert len(result.preferred_skills) >= 3
    assert result.extraction_metadata["method"] == "keyword_plus_semantic_v1"


def test_semantic_skill_detection():
    result = analyze_job_description(SAMPLE_JOB_SEMANTIC, use_semantic=True)
    all_display = set(
        result.required_skills
        + result.preferred_skills
        + result.ai_ml_skills
        + result.technologies
    )
    assert any(s.upper() == "RAG" for s in all_display)
