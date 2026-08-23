from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from backend.app.models.resume import ResumeParseResponse, StructuredResume
from backend.app.services.resume_service import parse_resume_pdf, parse_resume_text

router = APIRouter(prefix="/resume", tags=["resume"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


class TextResumeRequest(BaseModel):
    text: str


@router.post("/parse", response_model=ResumeParseResponse)
async def parse_resume(file: UploadFile = File(...)) -> ResumeParseResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 10 MB)")

    result = parse_resume_pdf(content)
    if not result.success:
        raise HTTPException(status_code=422, detail=result.error or "Failed to parse resume")

    return result


@router.post("/parse-text", response_model=StructuredResume)
async def parse_resume_from_text(body: TextResumeRequest) -> StructuredResume:
    if not body.text or len(body.text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Resume text too short (min 50 characters)")
    return parse_resume_text(body.text)
