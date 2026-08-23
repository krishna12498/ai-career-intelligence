"""Persistent FAISS storage for career knowledge documents."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import faiss
import numpy as np

from ml.embeddings import encode_texts
from rag.documents import KnowledgeDocument, load_documents

MIN_RETRIEVAL_SCORE = 0.35


class KnowledgeVectorStore:
    def __init__(self, index_path: Path, metadata_path: Path):
        self.index_path = index_path
        self.metadata_path = metadata_path
        self._index: faiss.Index | None = None
        self._documents: list[KnowledgeDocument] = []

    @property
    def documents(self) -> list[KnowledgeDocument]:
        return list(self._documents)

    def build(self, documents: list[KnowledgeDocument] | None = None) -> None:
        self._documents = documents or load_documents()
        if not self._documents:
            raise ValueError("Cannot build an empty knowledge-base index")

        embeddings = np.asarray(encode_texts([document.text for document in self._documents]), dtype="float32")
        self._index = faiss.IndexFlatIP(embeddings.shape[1])
        self._index.add(embeddings)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(self.index_path))
        self.metadata_path.write_text(
            json.dumps([asdict(document) for document in self._documents], indent=2),
            encoding="utf-8",
        )

    def load(self) -> None:
        if not self.index_path.exists() or not self.metadata_path.exists():
            raise FileNotFoundError("Knowledge-base index has not been built")
        self._index = faiss.read_index(str(self.index_path))
        records = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        self._documents = [KnowledgeDocument(**record) for record in records]
        if self._index.ntotal != len(self._documents):
            raise ValueError("Knowledge-base index and metadata are out of sync")

    def search(self, query: str, top_k: int = 5) -> list[tuple[KnowledgeDocument, float]]:
        if self._index is None:
            raise RuntimeError("Knowledge-base index is not loaded")
        if not query.strip() or top_k <= 0:
            return []

        query_embedding = np.asarray(encode_texts([query]), dtype="float32")
        scores, indices = self._index.search(query_embedding, min(top_k, self._index.ntotal))
        return [
            (self._documents[index], float(score))
            for score, index in zip(scores[0], indices[0])
            if index >= 0 and score >= MIN_RETRIEVAL_SCORE
        ]
