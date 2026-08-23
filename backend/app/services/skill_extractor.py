"""Shared keyword-based skill extraction from text."""

import re

from backend.app.data.skills_db import SKILL_ALIASES, SKILL_LOOKUP

# Display names for API output
DISPLAY_NAMES: dict[str, str] = {
    "aws": "AWS",
    "sql": "SQL",
    "rag": "RAG",
    "nlp": "NLP",
    "llm": "LLM",
    "api": "API",
    "ci/cd": "CI/CD",
    "k8s": "Kubernetes",
    "gcp": "GCP",
    "html": "HTML",
    "css": "CSS",
    "go": "Go",
    "r": "R",
    "c++": "C++",
    "c#": "C#",
    "node.js": "Node.js",
    "next.js": "Next.js",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "fastapi": "FastAPI",
    "langchain": "LangChain",
    "langgraph": "LangGraph",
    "opencv": "OpenCV",
    "mediapipe": "MediaPipe",
    "huggingface": "HuggingFace",
    "scikit-learn": "Scikit-learn",
    "postgresql": "PostgreSQL",
    "mongodb": "MongoDB",
    "dynamodb": "DynamoDB",
    "firestore": "Firestore",
    "faiss": "FAISS",
    "github": "GitHub",
    "gitlab": "GitLab",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "computer vision": "Computer Vision",
    "natural language processing": "Natural Language Processing",
    "generative ai": "Generative AI",
    "vector search": "Vector Search",
    "vector database": "Vector Database",
    "prompt engineering": "Prompt Engineering",
    "fine-tuning": "Fine-tuning",
    "reinforcement learning": "Reinforcement Learning",
    "sentence transformers": "Sentence Transformers",
    "retrieval augmented generation": "RAG",
    "large language model": "LLM",
}


def normalize_skill_token(token: str) -> str:
    t = token.lower().strip()
    return SKILL_ALIASES.get(t, t)


def to_display_name(skill: str) -> str:
    key = skill.lower()
    if key in DISPLAY_NAMES:
        return DISPLAY_NAMES[key]
    return " ".join(
        word.capitalize() if word.lower() not in DISPLAY_NAMES else DISPLAY_NAMES[word.lower()]
        for word in skill.split()
    )


def extract_skills_keyword(text: str) -> list[str]:
    """Return canonical lowercase skill names found via keyword matching."""
    text_lower = text.lower()
    found: dict[str, str] = {}

    all_skills = sorted(SKILL_LOOKUP.keys(), key=len, reverse=True)
    for skill_name in all_skills:
        pattern = r"\b" + re.escape(skill_name) + r"\b"
        if re.search(pattern, text_lower):
            canonical = normalize_skill_token(skill_name)
            if canonical not in found:
                found[canonical] = canonical

    return list(found.keys())


def get_ai_ml_skill_set() -> set[str]:
    return {s.lower() for s in SKILL_LOOKUP if SKILL_LOOKUP[s] == "ai_ml"}
