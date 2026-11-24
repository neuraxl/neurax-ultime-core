import time
from dataclasses import dataclass

import httpx

from .settings import settings


class ProviderConfigurationError(Exception):
    pass


class ProviderRequestError(Exception):
    pass


@dataclass
class ModelReply:
    provider: str
    model: str
    text: str
    latency_ms: int
    input_tokens: int | None = None
    output_tokens: int | None = None


def _provider_config(provider: str) -> tuple[str, str]:
    configs = {
        "openai": (settings.openai_api_key, settings.openai_model),
        "claude": (settings.anthropic_api_key, settings.anthropic_model),
        "gemini": (settings.gemini_api_key, settings.gemini_model),
    }
    if provider not in configs:
        raise ProviderConfigurationError("Unknown provider.")
    key, model = configs[provider]
    if not key:
        raise ProviderConfigurationError(f"{provider} API key is not configured.")
    return key, model


async def generate(provider: str, prompt: str, max_tokens: int) -> ModelReply:
    key, model = _provider_config(provider)
    started = time.perf_counter()
    timeout = httpx.Timeout(settings.provider_timeout_seconds)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            if provider == "openai":
                response = await client.post(
                    "https://api.openai.com/v1/responses",
                    headers={"Authorization": f"Bearer {key}"},
                    json={
                        "model": model,
                        "input": prompt,
                        "max_output_tokens": max_tokens,
                        "store": False,
                    },
                )
                response.raise_for_status()
                data = response.json()
                if data.get("status") != "completed":
                    raise ProviderRequestError(
                        f"openai response ended with status {data.get('status', 'unknown')}."
                    )
                content = "\n".join(
                    part.get("text", "")
                    for item in data.get("output", [])
                    if item.get("type") == "message"
                    for part in item.get("content", [])
                    if part.get("type") == "output_text"
                )
                usage = data.get("usage", {})
                input_tokens, output_tokens = usage.get("input_tokens"), usage.get("output_tokens")
            elif provider == "claude":
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": model,
                        "max_tokens": max_tokens,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                response.raise_for_status()
                data = response.json()
                content = "\n".join(
                    block.get("text", "") for block in data.get("content", [])
                    if block.get("type") == "text"
                )
                usage = data.get("usage", {})
                input_tokens, output_tokens = usage.get("input_tokens"), usage.get("output_tokens")
            else:
                response = await client.post(
                    "https://generativelanguage.googleapis.com/v1beta/interactions",
                    headers={"x-goog-api-key": key},
                    json={
                        "model": model,
                        "input": prompt,
                        "store": False,
                        "generation_config": {"max_output_tokens": max_tokens, "thinking_level": "low"},
                    },
                )
                response.raise_for_status()
                data = response.json()
                if data.get("status") != "completed":
                    raise ProviderRequestError(f"gemini interaction ended with status {data.get('status', 'unknown')}.")
                content = "\n".join(
                    part.get("text", "")
                    for step in data.get("steps", [])
                    if step.get("type") == "model_output"
                    for part in step.get("content", [])
                    if part.get("type") == "text"
                )
                usage = data.get("usage", {})
                input_tokens = usage.get("total_input_tokens")
                output_tokens = usage.get("total_output_tokens")
        if not content:
            raise ProviderRequestError(f"{provider} returned an empty response.")
        return ModelReply(
            provider=provider,
            model=model,
            text=content,
            latency_ms=int((time.perf_counter() - started) * 1000),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
        # Do not expose upstream response bodies, prompts, or credentials to clients.
        raise ProviderRequestError(f"{provider} request failed ({type(exc).__name__}).") from exc
