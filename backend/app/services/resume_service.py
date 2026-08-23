"""Resume parsing pipeline: PDF bytes → structured profile."""

from backend.app.models.resume import ResumeParseResponse, StructuredResume
from backend.app.services.pdf_parser import extract_text_from_pdf, normalize_text, PDFParserError
from backend.app.services.resume_extractor import extract_structured_resume


def parse_resume_pdf(file_bytes: bytes) -> ResumeParseResponse:
    try:
        raw_text, page_count = extract_text_from_pdf(file_bytes)
        normalized = normalize_text(raw_text)
        structured = extract_structured_resume(normalized)
        return ResumeParseResponse(
            success=True,
            resume=structured,
            page_count=page_count,
        )
    except PDFParserError as e:
        return ResumeParseResponse(success=False, error=str(e))
    except Exception as e:
        return ResumeParseResponse(success=False, error=f"Unexpected error: {e}")


def parse_resume_text(text: str) -> StructuredResume:
    normalized = normalize_text(text)
    return extract_structured_resume(normalized)
