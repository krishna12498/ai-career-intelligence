"""SQLite persistence for mock interview sessions."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from backend.app.models.interview import InterviewEvaluation, InterviewQuestion


class InterviewSessionStore:
    def __init__(self, database_path: Path):
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS interview_sessions (
                    session_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    grounding_policy TEXT NOT NULL,
                    summary_json TEXT
                );
                CREATE TABLE IF NOT EXISTS interview_questions (
                    session_id TEXT NOT NULL,
                    question_id TEXT NOT NULL,
                    question_json TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    PRIMARY KEY (session_id, question_id),
                    FOREIGN KEY (session_id) REFERENCES interview_sessions(session_id)
                );
                CREATE TABLE IF NOT EXISTS interview_answers (
                    session_id TEXT NOT NULL,
                    question_id TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    evaluation_json TEXT NOT NULL,
                    submitted_at TEXT NOT NULL,
                    PRIMARY KEY (session_id, question_id),
                    FOREIGN KEY (session_id, question_id)
                        REFERENCES interview_questions(session_id, question_id)
                );
                """
            )

    def create_session(
        self,
        session_id: str,
        questions: list[InterviewQuestion],
        grounding_policy: str,
    ) -> datetime:
        created_at = datetime.now(timezone.utc)
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO interview_sessions(session_id, status, created_at, grounding_policy) VALUES (?, ?, ?, ?)",
                (session_id, "created", created_at.isoformat(), grounding_policy),
            )
            connection.executemany(
                "INSERT INTO interview_questions(session_id, question_id, question_json, position) VALUES (?, ?, ?, ?)",
                [
                    (session_id, question.id, question.model_dump_json(), position)
                    for position, question in enumerate(questions)
                ],
            )
        return created_at

    def get_session(self, session_id: str) -> sqlite3.Row | None:
        with self._connect() as connection:
            return connection.execute(
                "SELECT * FROM interview_sessions WHERE session_id = ?", (session_id,)
            ).fetchone()

    def get_questions(self, session_id: str) -> list[InterviewQuestion]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT question_json FROM interview_questions WHERE session_id = ? ORDER BY position",
                (session_id,),
            ).fetchall()
        return [InterviewQuestion.model_validate_json(row["question_json"]) for row in rows]

    def get_question(self, session_id: str, question_id: str) -> InterviewQuestion | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT question_json FROM interview_questions WHERE session_id = ? AND question_id = ?",
                (session_id, question_id),
            ).fetchone()
        return InterviewQuestion.model_validate_json(row["question_json"]) if row else None

    def get_answers(self, session_id: str) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT question_id, answer, evaluation_json, submitted_at FROM interview_answers "
                "WHERE session_id = ? ORDER BY submitted_at",
                (session_id,),
            ).fetchall()
        return [
            {
                "question_id": row["question_id"],
                "answer": row["answer"],
                "evaluation": InterviewEvaluation.model_validate_json(row["evaluation_json"]),
                "submitted_at": datetime.fromisoformat(row["submitted_at"]),
            }
            for row in rows
        ]

    def add_answer(
        self,
        session_id: str,
        question_id: str,
        answer: str,
        evaluation: InterviewEvaluation,
    ) -> datetime | None:
        submitted_at = datetime.now(timezone.utc)
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT OR IGNORE INTO interview_answers "
                "(session_id, question_id, answer, evaluation_json, submitted_at) VALUES (?, ?, ?, ?, ?)",
                (session_id, question_id, answer, evaluation.model_dump_json(), submitted_at.isoformat()),
            )
            if cursor.rowcount == 0:
                return None
            connection.execute(
                "UPDATE interview_sessions SET status = 'in_progress' WHERE session_id = ? AND status = 'created'",
                (session_id,),
            )
        return submitted_at

    def complete(self, session_id: str, summary: dict) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE interview_sessions SET status = 'completed', summary_json = ? WHERE session_id = ?",
                (json.dumps(summary), session_id),
            )