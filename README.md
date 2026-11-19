# NeuraX Ultime Core (UNX2)

Core services for the NeuraX / UNX2 ecosystem.

## Services

- **MQTT broker:** existing Aedes broker, retained as an independent service on port 1883.
- **UNX2 API:** additive FastAPI service on port 8000.
- **PostgreSQL 16:** persistent relational data service.
- **Redis 7:** cache and coordination service.
- **Open Source Registry:** additive discovery, catalog, connector registry, permission grants, integration plans, and agent tool lookup.

The registry is added alongside existing services. The MQTT service definition, Node.js broker entry point (server/broker.js), port 1883, and existing topics are not changed.

## Local development

1. Copy .env.example to .env.
2. Set strong unique values for POSTGRES_PASSWORD and OS_REGISTRY_ADMIN_TOKEN.
3. Start the stack with Docker Compose: docker compose up --build.
4. Check API liveness at http://localhost:8000/health/live.
5. Check dependencies at http://localhost:8000/health/ready.
6. Open API documentation at http://localhost:8000/docs.

Default ports: MQTT 1883, API 8000. PostgreSQL and Redis are internal to the Compose network and are not published to the host.

## Open Source Registry API

All write endpoints require the X-UNX2-Registry-Token header. If OS_REGISTRY_ADMIN_TOKEN is not configured, write operations fail closed with HTTP 503.

- POST /api/v1/open-source/discover — inspect a public GitHub repository, license, release, root manifests, dependencies, topics, and maturity signals.
- GET /api/v1/open-source/catalog?q=...&min_score=... — search discovered projects by name, description, feature, or dependency.
- POST /api/v1/open-source/registry — register a discovered project as an API, MCP, webhook, service, or library connector.
- GET /api/v1/open-source/registry — list registered connectors.
- POST /api/v1/open-source/registry/{connector_id}/permissions — grant or revoke named tools for an agent with a per-call cost ceiling.
- POST /api/v1/open-source/registry/{connector_id}/enable — explicitly enable or disable a connector; tool grants remain deny-by-default.
- GET /api/v1/open-source/agents/{agent_id}/tools — list tools allowed for an agent on enabled connectors.
- POST /api/v1/open-source/integrations/plan — generate a hardened Docker Compose service proposal.
- POST /api/v1/open-source/integrations/{plan_id}/test — statically validate the integration proposal.
- POST /api/v1/open-source/integrations/{plan_id}/rollback — mark a proposal reverted and return its saved snapshot.
- POST /api/v1/open-source/orchestration/plan — resolve an agent's authorized tools and compare estimated cost with grants.
- POST /api/v1/open-source/usage — record a usage/cost event for an authorized tool.

Example admin header: X-UNX2-Registry-Token: your configured secret.

## Safety boundaries and current implementation status

- Discovery only scans public GitHub repositories. GitHub unauthenticated rate limits apply.
- Maturity score is a transparent heuristic, not a security or quality certification.
- Connectors are disabled by default; agent permissions are allow-list based.
- Compose plans are generated and statically checked only. The API does not execute Docker, install third-party code, or run repository scripts.
- Rollback currently reverts a plan record and exposes its snapshot; it does not alter running containers.
- Agent orchestration currently performs authorization lookup and planning only. A runtime adapter to the existing LEVIATHAN orchestrator must be connected before agents can execute tools.
- Usage recording checks the configured per-call ceiling; production billing ledger and aggregate budget enforcement remain future work.
- Registry tables are initialized additively with SQLAlchemy create_all. A versioned Alembic migration workflow should be introduced before production rollout.
- This initial registry is platform-wide, not tenant-scoped. Do not expose write operations publicly until tenant-aware authorization, audit logging, TLS, secret rotation, backups, and migrations are in place.

## EMOTION FACTORY

EMOTION FACTORY remains an independently branded commercial module running on UNX2 shared infrastructure. CRM, customer data, billing, and external commercial actions remain gated until tenant authentication, authorization, audit logging, and migrations are implemented.

## Security notice

This Compose configuration is for local development only. Do not deploy with example credentials or expose the API publicly until production secrets, authentication, TLS, network policy, backups, migrations, and monitoring are configured. No external AI, email, CRM, payment, or creative provider is claimed to be connected.
