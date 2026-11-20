# LÉVIATHAN Skill Runtime — UNX2 API

## Endpoints

- `GET /api/v1/skills`: returns the 14 registered skills and runtime capability flags.
- `POST /api/v1/skills/route`: routes a mission to a skill and publishes sanitized metadata to Redis channel `unx2:events:skills` when Redis is available.
- `GET /health/live` and `GET /health/ready`: existing health checks.

Example request:

```json
{
  "request": "Vérifier la sécurité de la passerelle API",
  "selected_skill": null
}
```

The route endpoint is a planning operation only. It does not call an LLM, execute an agent, access tenant data, or invoke external tools. Its HORUS preflight intentionally reports authorization and tenant isolation as `NOT_TESTED`.

## Browser integration

Serve the Windows XV HTML from a local web origin, for example:

```bash
python -m http.server 5500
```

Then use the API base URL `http://localhost:8000`. CORS defaults allow localhost ports 5500 and 8000. For another origin, set `CORS_ORIGINS` to an explicit comma-separated allowlist.

Do not open the HTML with `file://` for API mode; browsers typically send an opaque origin that is not in the CORS allowlist.

## Production gate

Before enabling execution, implement authenticated actor identity, server-derived tenant context, RBAC/ABAC, database-backed audit, idempotency, approval gates, secret storage, rate limits, and cross-tenant security tests. Do not trust a tenant ID supplied by the browser.
