"""Extract text from PDF resumes using PyMuPDF."""

import fitz  # PyMuPDF


class PDFParserError(Exception):
    pass


def extract_text_from_pdf(file_bytes: bytes) -> tuple[str, int]:
    """
    Extract plain text from a PDF file.

    Returns:
        (full_text, page_count)
    """
    if not file_bytes:
        raise PDFParserError("Empty file provided")

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise PDFParserError(f"Failed to open PDF: {e}") from e

    page_count = len(doc)
    if page_count == 0:
        doc.close()
        raise PDFParserError("PDF has no pages")

    parts: list[str] = []
    for page in doc:
        text = page.get_text("text")
        if text:
            parts.append(text)

    doc.close()
    full_text = "\n".join(parts).strip()

    if not full_text:
        raise PDFParserError("No text could be extracted from PDF (may be image-only)")

    return full_text, page_count


def normalize_text(text: str) -> str:
    """Normalize whitespace and common PDF artifacts."""
    lines = []
    for line in text.splitlines():
        cleaned = " ".join(line.split())
        if cleaned:
            lines.append(cleaned)
    return "\n".join(lines)
