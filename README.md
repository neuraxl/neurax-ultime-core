# NeuraX Ultime Core (UNX2)

Shared platform for NeuraX / UNX2 and independently branded business workspaces.

## Services

- **MQTT:** existing Aedes broker retained on port 1883.
- **FastAPI:** UNX2 API on port 8000.
- **PostgreSQL 16:** persistent CRM data.
- **Redis 7:** cache / coordination service and readiness check.

## EMOTION FACTORY CRM — MVP

The API currently provides:
- workspace registration (creates a dedicated tenant and first owner);
- email/password login with signed JWT access tokens;
- authenticated user profile;
- tenant-scoped contacts (list, create, read, update, delete);
- tenant-scoped leads (list, create, update) with new / qualified / proposal / won / lost stages;
- tenant-scoped activities linked to a contact or lead;
- workspace dashboard counts and open pipeline total.

All CRM queries derive tenant_id from the verified JWT and filter records by that tenant. A contact or lead belonging to another workspace is not returned by ID and cannot be attached to a record in the current workspace.

### Start locally

1. Copy `.env.example` to `.env`.
2. Set unique strong values for `POSTGRES_PASSWORD` and `JWT_SECRET` (at least 32 random bytes).
3. Run `docker compose up --build`.
4. Open `http://localhost:8000/docs`.
5. Register a workspace with `POST /api/v1/auth/register`, then use the returned bearer token for `/api/v1/crm/*`.

Health checks:
- `GET /health/live`
- `GET /health/ready`

MQTT remains available separately on port 1883.

## CRM interface

The responsive French-language workspace is served at `/` and includes sign-in / workspace registration, KPI dashboard, prospect pipeline, contacts directory, lead editing, and activity tracking. It calls the authenticated UNX2 API directly; the access token is held in browser session storage and cleared on logout.

## API routes

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/crm/dashboard`
- `GET|POST /api/v1/crm/contacts`
- `GET|PATCH|DELETE /api/v1/crm/contacts/{contact_id}`
- `GET|POST /api/v1/crm/leads`
- `PATCH /api/v1/crm/leads/{lead_id}`
- `GET|POST /api/v1/crm/activities`

## Important maturity and security limits

This is a functional development MVP, not a production-ready CRM. Schema bootstrap currently uses SQLAlchemy `create_all`; versioned Alembic migrations must replace this before production. Tenant isolation is enforced in the application query layer; PostgreSQL row-level security policies and automated cross-tenant penetration tests are still required. The initial registration endpoint creates an owner account; team invitations, granular RBAC, password reset, email verification, login throttling, audit log, consent / CASL workflows, data export/deletion, backups, and production secret management remain to be implemented. Do not expose this API publicly or store real customer data until those controls are complete.

No email, payment, AI provider, marketing automation, or external CRM integration is claimed to be connected. External messages, contracts, charges, paid campaigns, and publications remain outside this MVP and require explicit human approval when added.
