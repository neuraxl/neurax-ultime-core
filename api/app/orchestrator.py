import asyncio
import time
import uuid

from .ai_schemas import ArbitrationResult, CompareRequest, CompareResponse, ProviderResult
from .providers import (
    ModelReply,
    ProviderConfigurationError,
    ProviderRequestError,
    generate,
)
from .settings import settings

PROVIDERS = ("openai", "claude", "gemini")


async def _call(provider: str, prompt: str, max_tokens: int):
    started = time.perf_counter()
    try:
        reply = await generate(provider, prompt, max_tokens)
        return ProviderResult(
            provider=reply.provider,
            model=reply.model,
            status="ok",
            response=reply.text,
            latency_ms=reply.latency_ms,
            input_tokens=reply.input_tokens,
            output_tokens=reply.output_tokens,
        )
    except (ProviderConfigurationError, ProviderRequestError) as exc:
        return ProviderResult(
            provider=provider,
            model=_model_name(provider),
            status="error",
            latency_ms=int((time.perf_counter() - started) * 1000),
            error=str(exc),
        )


def _model_name(provider: str) -> str:
    return {
        "openai": settings.openai_model,
        "claude": settings.anthropic_model,
        "gemini": settings.gemini_model,
    }[provider]


async def compare(request: CompareRequest) -> CompareResponse:
    trace_id = str(uuid.uuid4())
    results = await asyncio.gather(
        *(_call(provider, request.prompt, request.max_output_tokens) for provider in PROVIDERS)
    )
    successful = [result for result in results if result.status == "ok" and result.response]
    arbitration = None

    if len(successful) >= 2:
        arbiter = settings.arbiter_provider.lower()
        if arbiter not in PROVIDERS:
            arbiter = "openai"
        evidence = "\n\n".join(
            f"--- {item.provider.upper()} / {item.model} ---\n{item.response}"
            for item in successful
        )
        synthesis_prompt = (
            "You are the UNX2 Meta-Arbiter. Compare the following independent model answers. "
            "Produce a concise synthesis with: points of agreement, material disagreements, "
            "claims that need verification, and a balanced conclusion. Do not treat consensus "
            "as proof. Do not invent sources. Explicitly state uncertainty.\n\n"
            f"USER QUESTION:\n{request.prompt}\n\nMODEL ANSWERS:\n{evidence}"
        )
        started = time.perf_counter()
        try:
            reply: ModelReply = await generate(
                arbiter, synthesis_prompt, request.max_output_tokens
            )
            arbitration = ArbitrationResult(
                provider=reply.provider,
                model=reply.model,
                status="ok",
                synthesis=reply.text,
                latency_ms=reply.latency_ms,
            )
        except (ProviderConfigurationError, ProviderRequestError) as exc:
            arbitration = ArbitrationResult(
                provider=arbiter,
                model=_model_name(arbiter),
                status="error",
                latency_ms=int((time.perf_counter() - started) * 1000),
                error=str(exc),
            )

    status = "complete" if len(successful) == 3 and arbitration and arbitration.status == "ok" else (
        "partial" if successful else "failed"
    )
    return CompareResponse(
        trace_id=trace_id,
        status=status,
        successful_providers=len(successful),
        results=results,
        arbitration=arbitration,
    )
