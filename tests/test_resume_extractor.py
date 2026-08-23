import pytest

from backend.app.services.pdf_parser import PDFParserError, extract_text_from_pdf, normalize_text
from backend.app.services.resume_extractor import extract_structured_resume
from tests.fixtures.sample_resume import SAMPLE_RESUME_TEXT


def test_normalize_text():
    assert normalize_text("  hello   world  \n\n  test  ") == "hello world\ntest"


def test_extract_structured_resume():
    text = normalize_text(SAMPLE_RESUME_TEXT)
    resume = extract_structured_resume(text)

    assert resume.contact.email == "john.doe@email.com"
    assert resume.contact.name == "John Doe"
    assert len(resume.skills) >= 8
    assert len(resume.experience) >= 1
    assert resume.experience[0].title == "AI Engineer"
    assert len(resume.education) >= 1
    assert len(resume.projects) >= 1
    assert resume.extraction_metadata["method"] == "rule_based_v1"


def test_extract_pipe_delimited_project():
    resume = extract_structured_resume(
        normalize_text(
            "Alex Morgan\n\nProjects\n"
            "Career match assistant | Built a resume and job matching tool with Python and embeddings."
        )
    )

    assert len(resume.projects) == 1
    assert resume.projects[0].name == "Career match assistant"
    assert "resume and job matching tool" in (resume.projects[0].description or "")


def test_pdf_parser_empty():
    with pytest.raises(PDFParserError):
        extract_text_from_pdf(b"")


def test_pdf_parser_invalid():
    with pytest.raises(PDFParserError):
        extract_text_from_pdf(b"not a pdf")
