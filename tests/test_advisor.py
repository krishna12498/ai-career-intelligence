import httpx

from backend.app.models.advisor import AdvisorRequest
from backend.app.services import advisor_service
from rag.generator import GeneratorTimeoutError, build_advice_prompt, generate_advice


def test_advice_prompt_contains_skill_and_grounding():
    prompt = build_advice_prompt("Docker", "Docker fundamentals", "Python developer")

    assert "Docker" in prompt
    assert "Docker fundamentals" in prompt
    assert "Python developer" in prompt
    assert "Do not make technical claims about" in prompt


def test_generate_advice_returns_ollama_response(monkeypatch):
    def fake_post(*args, **kwargs):
        request = httpx.Request("POST", "http://localhost:11434/api/generate")
        return httpx.Response(
            200,
            json={"response": "Learn Docker by building an image."},
            request=request,
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    assert generate_advice("Docker", "Docker fundamentals", "") == "Learn Docker by building an image."


def test_generate_advice_translates_timeout(monkeypatch):
    def fake_post(*args, **kwargs):
        raise httpx.ReadTimeout("slow Ollama")

    monkeypatch.setattr(httpx, "post", fake_post)

    try:
        generate_advice("Docker", "Docker fundamentals", "")
    except GeneratorTimeoutError:
        pass
    else:
        raise AssertionError("Expected GeneratorTimeoutError")


def test_explain_skill_uses_retrieved_resource(monkeypatch):
    captured = {}

    def fake_search(request):
        captured["query"] = request.query
        return type("KnowledgeResponse", (), {"results": []})()

    def fake_generate(skill, resource_context, candidate_context):
        captured["context"] = resource_context
        return "A focused learning plan."

    monkeypatch.setattr(advisor_service, "search_knowledge", fake_search)
    monkeypatch.setattr(advisor_service, "generate_advice", fake_generate)

    result = advisor_service.explain_skill(
        AdvisorRequest(skill="Docker", candidate_context="Python developer")
    )

    assert result.explanation == "A focused learning plan."
    assert captured["query"] == "Docker"
    assert captured["context"] == "No matching curated resource was found."