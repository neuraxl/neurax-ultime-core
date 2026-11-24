# UNX2 CORE v0.3 — Three Intelligence Foundation

## Purpose

Build one secure server-side gateway that can call three real model providers (OpenAI, Anthropic Claude, Google Gemini), return their independent answers, and request a comparative arbitration pass from one configured provider.

This is a first integration slice, not a production-ready multi-tenant platform.

## Implemented in this branch

- Provider adapters using current official HTTPS API endpoints: OpenAI Responses API, Anthropic Messages API, and Google Gemini Interactions API.
- Default model IDs are configuration values and can be replaced per environment: GPT `gpt-6.1-terra`, Claude `claude-sonnet-5-5`, Gemini `gemini-3.8-flash`.
- Server-side API keys only; no provider key is accepted from request bodies.
- Bearer authentication for the compare endpoint using a high-entropy shared service key.
- Constant-time credential comparison and fail-closed behavior when the service key is absent or shorter than 32 characters.
- Concurrent calls to OpenAI, Claude, and Gemini with independent success/error results.
- Per-provider model name, latency, and token usage where supplied by the provider.
- Meta-Arbiter pass, only when at least two providers return successfully. The pass uses one of the same three providers; it is not a fourth intelligence.
- A trace UUID per comparison.
- Provider timeout and output-token bounds.
- Client responses do not expose upstream response bodies, prompts, or credentials.
- Compose binds API and MQTT host ports to loopback and requires database/API secrets.
- Dedicated Python compile/test workflow.

## API

`POST /api/v1/ai/compare`

Headers:

`Authorization: Bearer <UNX2_API_KEY>`
`Content-Type: application/json`

Body:

```json
{
  "prompt": "Compare three approaches to secure AI orchestration.",
  "max_output_tokens": 1200
}
```

The response contains:
- `trace_id`
- `status` (`complete`, `partial`, or `failed`)
- three provider result objects
- an arbitration result when at least two provider calls succeed
- an explicit warning that model consensus is not proof of truth

## Local setup

1. Copy root `.env.example` to `.env`.
2. Generate a unique `UNX2_API_KEY` with at least 32 random characters and a unique `POSTGRES_PASSWORD`.
3. Add the three provider keys to `.env`. Keep the values out of Git and frontend environment variables.
4. Run `docker compose up --build`.
5. The API is bound to `127.0.0.1:8000`.
6. Call `POST http://127.0.0.1:8000/api/v1/ai/compare` with the bearer key.

Do not commit `.env`. Do not expose the API publicly until user/org authentication, tenant isolation, durable audit records, rate/concurrency limits, TLS termination, and security review are implemented.

## Current limitations and release gates

- Shared service-key authentication is a controlled integration gate, not end-user identity.
- No tenant/user model or per-tenant provider credentials yet.
- No durable database persistence for prompts, outputs, usage, or audit events.
- No streaming endpoint yet.
- No automatic retries or provider fallback; partial failures are visible rather than silently hidden.
- No independent fact-checking source. The Meta-Arbiter compares model outputs but cannot establish truth.
- Provider API calls require real credentials and network access; a green unit test does not prove live provider connectivity.
- Existing MQTT broker is not part of the AI request path and remains a separate legacy service requiring its own authentication/ACL/TLS work before any external exposure.

## Acceptance test for real provider connectivity

After secrets are configured in a controlled environment:
1. Call the endpoint with an invalid bearer token and confirm HTTP 401.
2. Call with no configured service key and confirm HTTP 503.
3. Configure all three provider keys and make one low-risk test request.
4. Confirm all three provider results have status `ok`, with provider/model identifiers and latency.
5. Confirm the arbitration pass succeeds and identifies agreement, disagreement, and uncertainty.
6. Remove one provider key and confirm the other results remain visible and the response is marked `partial`.
7. Confirm no provider secret or full upstream error body appears in API logs or client responses.

A live end-to-end validation must be recorded separately from CI results.
