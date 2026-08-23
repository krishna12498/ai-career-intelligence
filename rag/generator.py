"""Ollama-backed generation for grounded career advice."""

from __future__ import annotations

import httpx

from backend.app.config import settings

OLLAMA_TIMEOUT_SECONDS = 120.0


class GeneratorError(RuntimeError):
    """Base error for failures talking to the local language model."""


class GeneratorUnavailableError(GeneratorError):
    """Ollama could not be reached or returned an invalid response."""


class GeneratorTimeoutError(GeneratorError):
    """Ollama did not finish within the configured timeout."""


def build_advice_prompt(skill: str, resource_context: str, candidate_context: str) -> str:
    candidate_section = candidate_context.strip() or "No candidate background was provided."
    return f"""You are a practical career advisor.

Explain how the candidate should learn and demonstrate the skill: {skill}

Use only the following curated resource context as factual grounding:
{resource_context}

Candidate background:
{candidate_section}

Write a concise response with:
1. What to learn first
2. A small hands-on project
3. How to show this skill on a resume or in an interview
Do not invent links, credentials, or experience. Do not make technical claims about
tools or frameworks that are not named in the curated resource context or candidate
background. If a detail is not supported, omit it. Keep the response under 300 words."""


def generate_advice(skill: str, resource_context: str, candidate_context: str) -> str:
    prompt = build_advice_prompt(skill, resource_context, candidate_context)
    try:
        response = httpx.post(
            f"{settings.ollama_base_url.rstrip('/')}/api/generate",
            json={
                "model": settings.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2},
            },
            timeout=OLLAMA_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        body = response.json()
        explanation = body.get("response", "").strip()
    except httpx.TimeoutException as error:
        raise GeneratorTimeoutError("Ollama generation timed out") from error
    except (httpx.HTTPError, ValueError, TypeError) as error:
        raise GeneratorUnavailableError("Ollama generation failed") from error

    if not explanation:
        raise GeneratorUnavailableError("Ollama returned an empty response")
    return explanation