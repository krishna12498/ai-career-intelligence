"""ML matching engine — semantic skill matching and weighted scoring."""

from __future__ import annotations

from functools import lru_cache
import re
from typing import Optional

from sklearn.metrics.pairwise import cosine_similarity

from backend.app.models.match import MatchStatus, SkillMatchResult
from ml.embeddings import encode_texts, get_embedding_model
from ml.semantic_skills import SKILL_CONCEPTS

# Minimum similarity to accept a candidate skill as a real match
MIN_MATCH_THRESHOLD = 0.55

STRONG_THRESHOLD = 0.80
PARTIAL_THRESHOLD = MIN_MATCH_THRESHOLD

REQUIRED_WEIGHT = 1.0
PREFERRED_WEIGHT = 0.5

SKILL_EQUIVALENTS: dict[str, set[str]] = {
    "sql": {"postgresql", "mysql", "sqlite", "mariadb"},
}


def classify_match(score: float) -> MatchStatus:
    if score >= STRONG_THRESHOLD:
        return MatchStatus.STRONG
    if score >= PARTIAL_THRESHOLD:
        return MatchStatus.PARTIAL
    return MatchStatus.MISSING


def score_to_percent(score: float) -> int:
    return round(max(0.0, min(1.0, score)) * 100)


class MatchingEngine:
    """Semantic skill matcher using sentence embeddings and cosine similarity."""

    def __init__(self):
        self._model = get_embedding_model()

    @staticmethod
    def _expand_skill_text(text: str) -> str:
        """Add curated concepts so abbreviations and related phrases compare semantically."""
        expansions = [
            concept
            for skill, concept in SKILL_CONCEPTS.items()
            if re.search(r"\b" + re.escape(skill) + r"\b", text, re.IGNORECASE)
        ]
        return " ".join([text, *expansions]) if expansions else text

    @staticmethod
    def _is_equivalent_skill(job_skill: str, candidate_skill: str) -> bool:
        job_key = job_skill.casefold().strip()
        candidate_key = candidate_skill.casefold().strip()
        return candidate_key in SKILL_EQUIVALENTS.get(job_key, set())

    def calculate_similarity(self, resume_text: str, job_skill: str) -> float:
        embeddings = encode_texts([resume_text, job_skill])
        return float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])

    def match_skills(
        self,
        candidate_skills: list[str],
        job_skills: list[str],
        match_type: str = "required",
    ) -> list[SkillMatchResult]:
        if not job_skills:
            return []

        if not candidate_skills:
            return [
                SkillMatchResult(
                    job_skill=skill,
                    candidate_skill=None,
                    similarity=0.0,
                    match_type=match_type,
                    status=MatchStatus.MISSING,
                    score_percent=0,
                )
                for skill in job_skills
            ]

        candidate_embeddings = encode_texts([self._expand_skill_text(skill) for skill in candidate_skills])
        job_embeddings = encode_texts([self._expand_skill_text(skill) for skill in job_skills])

        similarity_matrix = cosine_similarity(job_embeddings, candidate_embeddings)

        results: list[SkillMatchResult] = []
        for i, job_skill in enumerate(job_skills):
            equivalent_indices = [
                index
                for index, candidate_skill in enumerate(candidate_skills)
                if self._is_equivalent_skill(job_skill, candidate_skill)
            ]
            if equivalent_indices:
                best_index = equivalent_indices[0]
                best_score = 1.0
            else:
                best_index = int(similarity_matrix[i].argmax())
                best_score = float(similarity_matrix[i][best_index])
            best_candidate = candidate_skills[best_index]

            if best_score < MIN_MATCH_THRESHOLD:
                best_candidate = None
                best_score = 0.0

            status = classify_match(best_score)
            results.append(
                SkillMatchResult(
                    job_skill=job_skill,
                    candidate_skill=best_candidate,
                    similarity=round(best_score, 3),
                    match_type=match_type,
                    status=status,
                    score_percent=score_to_percent(best_score),
                )
            )

        return results

    def calculate_weighted_score(self, matches: list[SkillMatchResult]) -> float:
        if not matches:
            return 0.0

        total_score = 0.0
        total_weight = 0.0

        for match in matches:
            weight = REQUIRED_WEIGHT if match.match_type == "required" else PREFERRED_WEIGHT
            total_score += match.similarity * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return round((total_score / total_weight) * 100, 2)

    def text_similarity(self, text_a: str, text_b: str) -> float:
        if not text_a.strip() or not text_b.strip():
            return 0.0
        embeddings = encode_texts([text_a, text_b])
        return float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])

    def max_text_similarity(self, source_text: str, target_texts: list[str]) -> float:
        if not target_texts or not source_text.strip():
            return 0.0
        source_emb = encode_texts([source_text])[0]
        target_embs = encode_texts(target_texts)
        similarities = target_embs @ source_emb
        return float(similarities.max())


@lru_cache(maxsize=1)
def get_matching_engine() -> MatchingEngine:
    return MatchingEngine()
