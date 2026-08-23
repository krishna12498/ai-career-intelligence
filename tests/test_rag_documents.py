import json

import pytest

from rag.documents import KnowledgeDocument, load_documents


def test_load_seeded_knowledge_documents():
    documents = load_documents()

    assert len(documents) == 20
    assert len({document.skill.casefold() for document in documents}) == 20
    assert all(document.url.startswith("https://") for document in documents)


def test_load_documents_rejects_duplicate_skills(tmp_path):
    record = {
        "skill": "Python",
        "title": "Python",
        "summary": "Summary",
        "resource_type": "guide",
        "level": "beginner",
        "url": "https://example.com",
        "source": "test",
    }
    path = tmp_path / "skills.json"
    path.write_text(json.dumps([record, record]), encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate"):
        load_documents(path)


def test_document_text_contains_searchable_context():
    document = KnowledgeDocument(
        skill="Docker",
        title="Container fundamentals",
        summary="Learn images and deployment.",
        resource_type="guide",
        level="beginner",
        url="https://example.com",
        source="test",
    )

    assert document.text == "Docker. Container fundamentals. Learn images and deployment."
