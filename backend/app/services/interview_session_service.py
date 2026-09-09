"""Multi-question mock interview session orchestration."""

from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

from backend.app.config import settings
from backend.app.models.interview import InterviewEvaluationRequest, InterviewQuestion
from backend.app.models.interview_session import (
    InterviewAnswerResponse,
    InterviewSessionCompleteResponse,
    InterviewSessionCreateRequest,
    InterviewSessionCreateResponse,
    InterviewSessionResponse,
    InterviewSessionSummary,
)
from backend.app.services.interview_service import (
    GROUNDING_POLICY,
    evaluate_interview_answer,
    generate_interview_questions,
)
from backend.app.services.interview_session_store import InterviewSessionStore


@lru_cache(maxsize=1)
def get_session_store(database_path: Path | None = None) -> InterviewSessionStore:
    return InterviewSessionStore(database_path or settings.data_dir / "interview_sessions.sqlite3")


def _progress(answered: int, total: int) -> float:
    return round(answered / total * 100, 2) if total else 0.0


def _summary(status: str, questions: list[InterviewQuestion], answers: list[dict]) -> InterviewSessionSummary:
    scores = [answer["evaluation"].score for answer in answers]
    category_scores: dict[str, list[int]] = {}
    question_categories = {question.id: question.category for question in questions}
    for answer in answers:
        category = question_categories.get(answer["question_id"], "unknown")
        category_scores.setdefault(category, []).append(answer["evaluation"].score)
    category_summary = {
        category: round(sum(scores) / len(scores), 2)
        for category, scores in category_scores.items()
    }
    themes: list[str] = []
    for answer in answers:
        for improvement in answer["evaluation"].improvements:
            if improvement not in themes:
                themes.append(improvement)
    completion_status = "complete" if status == "completed" else "in_progress"
    return InterviewSessionSummary(
        overall_structure_coverage=round(sum(scores) / len(scores), 2) if scores else 0.0,
        category_structure_coverage=category_summary,
        recurring_feedback_themes=themes,
        answered=len(answers),
        total_questions=len(questions),
        completion_status=completion_status,
    )


def _session_response(session_id: str, include_summary: bool = True) -> InterviewSessionResponse:
    store = get_session_store()
    session = store.get_session(session_id)
    if session is None:
        raise KeyError("Interview session not found")
    questions = store.get_questions(session_id)
    answers = store.get_answers(session_id)
    summary = _summary(session["status"], questions, answers) if include_summary else None
    return InterviewSessionResponse(
        session_id=session_id,
        status=session["status"],
        questions=questions,
        answers=answers,
        created_at=datetime.fromisoformat(session["created_at"]),
        grounding_policy=session["grounding_policy"],
        progress_percent=_progress(len(answers), len(questions)),
        summary=summary,
    )


def create_session(request: InterviewSessionCreateRequest) -> InterviewSessionCreateResponse:
    result = generate_interview_questions(
        request.resume_text,
        request.job_description,
        questions_per_category=request.questions_per_category,
        use_semantic=False,
    )
    session_id = uuid4().hex
    created_at = get_session_store().create_session(session_id, result.questions, result.grounding_policy)
    return InterviewSessionCreateResponse(
        session_id=session_id,
        status="created",
        questions=result.questions,
        created_at=created_at,
        grounding_policy=result.grounding_policy,
    )


def submit_answer(session_id: str, question_id: str, answer: str) -> InterviewAnswerResponse:
    store = get_session_store()
    session = store.get_session(session_id)
    if session is None:
        raise KeyError("Interview session not found")
    question = store.get_question(session_id, question_id)
    if question is None:
        raise LookupError("Interview question not found")
    evaluation = evaluate_interview_answer(
        InterviewEvaluationRequest(question=question, answer=answer)
    )
    submitted_at = store.add_answer(session_id, question_id, answer, evaluation)
    if submitted_at is None:
        raise FileExistsError("This question has already been answered")
    answered = len(store.get_answers(session_id))
    total = len(store.get_questions(session_id))
    return InterviewAnswerResponse(
        question_id=question_id,
        evaluation=evaluation,
        submitted_at=submitted_at,
        answered=answered,
        total_questions=total,
        progress_percent=_progress(answered, total),
    )


def get_session(session_id: str) -> InterviewSessionResponse:
    return _session_response(session_id)


def complete_session(session_id: str) -> InterviewSessionCompleteResponse:
    store = get_session_store()
    session = store.get_session(session_id)
    if session is None:
        raise KeyError("Interview session not found")
    questions = store.get_questions(session_id)
    answers = store.get_answers(session_id)
    summary = _summary("completed", questions, answers)
    if session["status"] != "completed":
        store.complete(session_id, summary.model_dump())
    response = _session_response(session_id)
    response_data = response.model_dump()
    response_data["summary"] = summary
    return InterviewSessionCompleteResponse(**response_data)