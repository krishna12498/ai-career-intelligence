"""Semantic skill detection using sentence embeddings."""

from __future__ import annotations

import re
from functools import lru_cache

from backend.app.services.skill_extractor import normalize_skill_token

# Concept phrases for semantic matching when exact keywords are absent
SKILL_CONCEPTS: dict[str, str] = {
    "rag": "retrieval augmented generation RAG document embeddings vector search knowledge base question answering",
    "machine learning": "machine learning predictive models supervised unsupervised training datasets",
    "deep learning": "deep learning neural networks CNN RNN transformers training models",
    "nlp": "natural language processing text analysis tokenization named entity recognition",
    "computer vision": "computer vision image recognition object detection CNN visual processing",
    "llm": "large language model LLM GPT transformer generative text models",
    "generative ai": "generative AI genai content generation diffusion models text generation",
    "embeddings": "text embeddings vector representations semantic encoding word2vec",
    "vector search": "vector search similarity search nearest neighbor embedding retrieval",
    "vector database": "vector database embedding store FAISS Pinecone semantic index",
    "agents": "AI agents autonomous agents multi-agent orchestration agentic workflows",
    "prompt engineering": "prompt engineering few-shot prompting chain of thought LLM prompts",
    "fine-tuning": "fine-tuning model training transfer learning LoRA adapter tuning",
    "langchain": "LangChain LLM application framework chains tools retrieval pipelines",
    "langgraph": "LangGraph agent workflow graph state machine multi-agent orchestration",
    "faiss": "FAISS vector index similarity search approximate nearest neighbors",
    "pytorch": "PyTorch deep learning framework tensor autograd neural network training",
    "tensorflow": "TensorFlow deep learning Keras model training neural networks",
    "scikit-learn": "scikit-learn machine learning classification regression clustering sklearn",
    "fastapi": "FastAPI Python web API REST endpoints async backend services",
    "docker": "Docker containerization container images deployment packaging",
    "kubernetes": "Kubernetes container orchestration k8s pods clusters deployment scaling",
    "aws": "Amazon Web Services AWS cloud EC2 S3 Lambda cloud infrastructure",
    "azure": "Microsoft Azure cloud services cloud computing infrastructure",
    "gcp": "Google Cloud Platform GCP cloud infrastructure compute storage",
    "postgresql": "PostgreSQL relational database SQL queries ACID transactions",
    "mongodb": "MongoDB NoSQL document database JSON storage",
    "react": "React JavaScript frontend UI components single page application",
    "python": "Python programming language scripting backend data science development",
    "sql": "SQL database queries relational data structured query language",
    "opencv": "OpenCV computer vision image processing video analysis",
    "mediapipe": "MediaPipe face detection pose estimation real-time vision pipelines",
    "mlflow": "MLflow machine learning experiment tracking model registry MLOps",
    "reinforcement learning": "reinforcement learning reward policy agent environment Q-learning",
    "transformers": "transformers attention mechanism BERT GPT HuggingFace transformer models",
}

SEMANTIC_THRESHOLD = 0.35
SKILL_THRESHOLDS: dict[str, float] = {
    "mlflow": 0.45,
    "pytorch": 0.45,
}


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts if len(p.strip()) > 20]


@lru_cache(maxsize=1)
def _get_embedding_model():
    from ml.embeddings import get_embedding_model

    return get_embedding_model()


def extract_skills_semantic(
    text: str,
    exclude: set[str] | None = None,
    threshold: float = SEMANTIC_THRESHOLD,
) -> list[tuple[str, float]]:
    """
    Detect skills via semantic similarity between JD sentences and skill concepts.

    Returns list of (canonical_skill, similarity_score).
    """
    exclude = exclude or set()
    sentences = _split_sentences(text)
    if not sentences:
        return []

    try:
        model = _get_embedding_model()
    except Exception:
        return []

    sentence_embeddings = model.encode(sentences, normalize_embeddings=True)

    results: list[tuple[str, float]] = []
    for skill, concept in SKILL_CONCEPTS.items():
        canonical = normalize_skill_token(skill)
        if canonical in exclude:
            continue

        concept_emb = model.encode([concept], normalize_embeddings=True)[0]
        # Cosine similarity (embeddings are normalized)
        similarities = sentence_embeddings @ concept_emb
        max_sim = float(similarities.max())

        if max_sim >= max(threshold, SKILL_THRESHOLDS.get(canonical, 0.0)):
            results.append((canonical, max_sim))

    return results


def get_semantic_skill_names(text: str, exclude: set[str] | None = None) -> list[str]:
    return [skill for skill, _ in extract_skills_semantic(text, exclude=exclude)]
