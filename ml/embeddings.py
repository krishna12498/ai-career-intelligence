"""Shared sentence-transformer embedding utilities."""

from functools import lru_cache

from backend.app.config import settings


@lru_cache(maxsize=1)
def get_embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.embedding_model)


def encode_texts(texts: list[str], normalize: bool = True):
    model = get_embedding_model()
    return model.encode(texts, normalize_embeddings=normalize)


def cosine_similarity_vectors(a, b) -> float:
    """Cosine similarity between two normalized embedding vectors."""
    return float(a @ b)
