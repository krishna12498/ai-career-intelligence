"""Structured career knowledge-base document loading."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from backend.app.config import settings


@dataclass(frozen=True)
class KnowledgeDocument:
    skill: str
    title: str
    summary: str
    resource_type: str
    level: str
    url: str
    source: str

    @property
    def text(self) -> str:
        return f"{self.skill}. {self.title}. {self.summary}"


def default_knowledge_base_path() -> Path:
    return settings.data_dir / "knowledge_base" / "skills.json"


def load_documents(path: Path | None = None) -> list[KnowledgeDocument]:
    """Load and validate one structured document per skill."""
    source_path = path or default_knowledge_base_path()
    with source_path.open(encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list):
        raise ValueError("Knowledge base must contain a JSON list")

    required_fields = {"skill", "title", "summary", "resource_type", "level", "url", "source"}
    documents: list[KnowledgeDocument] = []
    seen_skills: set[str] = set()
    for record in records:
        if not isinstance(record, dict) or not required_fields.issubset(record):
            raise ValueError("Each knowledge document must contain all required fields")
        skill = str(record["skill"]).strip()
        if not skill or skill.casefold() in seen_skills:
            raise ValueError(f"Duplicate or empty knowledge-base skill: {skill!r}")
        seen_skills.add(skill.casefold())
        documents.append(KnowledgeDocument(**{field: str(record[field]).strip() for field in required_fields}))

    return documents
