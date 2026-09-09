from fastapi import APIRouter, HTTPException

from backend.app.models.interview_session import (
    InterviewAnswerRequest,
    InterviewAnswerResponse,
    InterviewSessionCompleteResponse,
    InterviewSessionCreateRequest,
    InterviewSessionCreateResponse,
    InterviewSessionResponse,
)
from backend.app.services.interview_session_service import (
    complete_session,
    create_session,
    get_session,
    submit_answer,
)


router = APIRouter(prefix="/interview/sessions", tags=["interview sessions"])


@router.post("", response_model=InterviewSessionCreateResponse)
async def create_interview_session(request: InterviewSessionCreateRequest) -> InterviewSessionCreateResponse:
    return create_session(request)


@router.post("/{session_id}/answers", response_model=InterviewAnswerResponse)
async def submit_interview_answer(session_id: str, request: InterviewAnswerRequest) -> InterviewAnswerResponse:
    try:
        return submit_answer(session_id, request.question_id, request.answer)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except FileExistsError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get("/{session_id}", response_model=InterviewSessionResponse)
async def get_interview_session(session_id: str) -> InterviewSessionResponse:
    try:
        return get_session(session_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/{session_id}/complete", response_model=InterviewSessionCompleteResponse)
async def complete_interview_session(session_id: str) -> InterviewSessionCompleteResponse:
    try:
        return complete_session(session_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error