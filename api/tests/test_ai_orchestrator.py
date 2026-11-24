import pytest

from app.ai_schemas import CompareRequest
from app.providers import ModelReply
from app import orchestrator


@pytest.mark.asyncio
async def test_compare_calls_three_providers_and_arbitrates(monkeypatch):
    calls = []

    async def fake_generate(provider, prompt, max_tokens):
        calls.append(provider)
        return ModelReply(
            provider=provider,
            model=f"{provider}-test-model",
            text=f"Answer from {provider}",
            latency_ms=12,
            input_tokens=10,
            output_tokens=20,
        )

    monkeypatch.setattr(orchestrator, "generate", fake_generate)
    result = await orchestrator.compare(CompareRequest(prompt="A test question"))

    assert result.status == "complete"
    assert result.successful_providers == 3
    assert {item.provider for item in result.results} == {"openai", "claude", "gemini"}
    assert result.arbitration is not None
    assert result.arbitration.status == "ok"
    assert len(calls) == 4
    assert calls[:3] == ["openai", "claude", "gemini"]


@pytest.mark.asyncio
async def test_compare_keeps_partial_provider_failures(monkeypatch):
    async def fake_generate(provider, prompt, max_tokens):
        if provider == "claude":
            raise orchestrator.ProviderRequestError("claude unavailable")
        return ModelReply(provider, f"{provider}-model", f"Answer from {provider}", 5)

    monkeypatch.setattr(orchestrator, "generate", fake_generate)
    result = await orchestrator.compare(CompareRequest(prompt="A test question"))

    assert result.status == "partial"
    assert result.successful_providers == 2
    assert next(item for item in result.results if item.provider == "claude").status == "error"
    assert result.arbitration is not None
    assert result.arbitration.status == "ok"
