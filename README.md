# NeuraX Ultime Core (UNX2)

Core services for the NeuraX / UNX2 ecosystem.

## Services

- **MQTT broker:** existing Aedes broker, retained as an independent service on port 1883.
- **UNX2 API:** additive FastAPI service on port 8000.
- **PostgreSQL 16:** persistent relational data service.
- **Redis 7:** cache and coordination service.

The new API and data services are added alongside MQTT. The existing Node.js broker entry point remains `server/broker.js`.

## Local development

1. Copy `.env.example` to `.env`.
2. Replace `POSTGRES_PASSWORD` with a strong local secret.
3. Start the stack with Docker Compose: `docker compose up --build`.
4. Check API liveness at `http://localhost:8000/health/live`.
5. Check dependencies at `http://localhost:8000/health/ready`.
6. Open API documentation at `http://localhost:8000/docs`.

Default ports: MQTT 1883, API 8000. PostgreSQL and Redis are internal to the Compose network and are not published to the host.

## EMOTION FACTORY

EMOTION FACTORY is planned as an independently branded commercial module running on UNX2 shared infrastructure. Its initial API module registry entry is present; CRM, customer data, billing, and external actions are intentionally not enabled yet.

Before enabling commercial workflows, implement and test:
- authentication and role-based authorization;
- tenant isolation and database migrations;
- audit logging and consent records;
- secret management for third-party integrations;
- approval gates for outbound messages, contracts, charges, ad spend, and publication.

## Security notice

This Compose configuration is for local development only. Do not deploy with example credentials or expose the API publicly until production secrets, authentication, TLS, network policy, backups, migrations, and monitoring are configured. No external AI, email, CRM, payment, or creative provider is claimed to be connected.
