# UNX2 AI UNIVERSE — Sprint 001 Repository Audit

**Product:** UNX2 AI UNIVERSE — Powered by LÉVIATHAN  
**Audit date:** 2026-11-24  
**Audited repository:** `neuraxl/neurax-ultime-core`  
**Audited baseline:** `main` at `3f303e618e3df649c96017747eb34e297ea55986`  
**Purpose:** establish a safe consolidation path; this document does not certify production readiness.

## 1. Executive assessment

The repository is a useful prototype/integration workspace, not yet a production-grade monorepo. The default branch contains a legacy static JavaScript interface, a small Node/Aedes MQTT broker, and an additive FastAPI service backed by PostgreSQL and Redis. Several more advanced capabilities exist in unmerged feature branches.

**Recommendation:** preserve the existing MQTT and FastAPI work, establish a clean application structure around the current repository, and consolidate selected branch work through reviewed pull requests. Do not merge the divergent UNX2 v0.2.1 branch wholesale.

## 2. Main branch inventory

Observed on `main`:

- Root `package.json` declares a Node.js Aedes/MQTT broker and only a `start` script.
- `server/broker.js` starts an Aedes TCP broker on port 1883.
- `api/` contains a FastAPI app, Python requirements, and a Dockerfile.
- `docker-compose.yml` defines MQTT, API, PostgreSQL 16, and Redis 7.
- PostgreSQL and Redis are not published to the host in the current Compose file.
- `index.html`, `neurax_frontend.html`, and assorted JS/CSS files are legacy frontend assets.
- `docs/emotion-factory-unx2-integration.md` already defines a multi-tenant commercial module boundary and human-approval requirements.
- `.github/workflows/node.js.yml` is the only workflow observed on main.

Repository metadata reports default branch `main`, public visibility, and a last push of 2026-11-20. The repository tree contains unusual one-byte placeholder files and root-level files whose names resemble directories (for example `agents`, `backend`, `frontend`, `public`, `<script>`). These should be reviewed before cleanup; do not delete them without confirming their history and purpose.

## 3. Verified blockers and risks on main

### P0 — CI workflow is inconsistent with the root package

The Node workflow runs `npm ci` and `npm test`, but the inspected root tree has no package lockfile and the root `package.json` defines no `test` script. This is likely to fail CI. Confirm with an actual Actions run before changing workflow behavior.

### P0 — MQTT broker has no visible authentication or transport security

`server/broker.js` creates Aedes without an authentication/authorization hook and listens on TCP port 1883. It logs published message payloads. Do not expose this broker publicly until authentication, topic ACLs, TLS termination, payload redaction, rate limits, and operational controls are implemented and tested.

### P0 — Development credentials have unsafe fallback values

The Compose configuration contains a development fallback password (`unx2_dev_only`) in the database connection and PostgreSQL environment. The README explicitly calls the Compose setup local-development-only. Production deployment must fail closed when secrets are missing; it must never silently use a default password.

### P1 — Legacy deployment helper is unsafe

Root `manager.js` contains a placeholder token-bearing Git remote and executes `git push origin main --force`. It must not be used as a deployment mechanism. Remove the placeholder credential pattern and prohibit force-push automation in the production workflow after preserving any required historical context.

### P1 — Legacy frontend has stale API assumptions

The inspected `neurax_frontend.html` hardcodes `http://127.0.0.1:8000` and calls legacy `/api/status` and `/api/neurons` routes not present in the inspected FastAPI `main.py`. It should be treated as a historical interface until routes are verified or the UI is migrated.

### P1 — No production auth or tenant boundary on main API

The main-branch FastAPI service currently exposes liveness, readiness, and a module registry endpoint. No authentication, organization membership, tenant-scoped data model, or migration framework is present in the inspected main-branch API.

### P1 — No automated backend test suite observed on main

No Python test suite or migration directory is present in the main-branch tree. Production hardening requires unit, integration, tenant-isolation, API-contract, and end-to-end tests.

## 4. Existing branch assets to consolidate selectively

Branches compared against `main` on 2026-11-24:

| Branch | Relation to main | Observed assets | Recommendation |
|---|---:|---|---|
| `feat/emotion-factory-crm-multitenant` | 15 commits ahead, 0 behind | JWT/password auth, tenant/user models, CRM contacts/leads/activities, basic tests/UI | Candidate for review and extraction after security and migration review |
| `feat/unx2-open-source-registry` | 55 commits ahead, 0 behind | API key security, tenant-aware registry/connectors, permission grants, Alembic migrations, tenant isolation tests | Strong candidate for review; inspect every route and migration before merge |
| `feat/leviathan-skill-runtime` | 4 commits ahead, 0 behind | Skill registry/runtime endpoint and documentation | Candidate for later integration behind policy and sandbox controls |
| `unx2/v0.2.1-production-activation` | 53 ahead, 11 behind; diverged | Separate `unx2/` app, Supabase/Vercel functions, Stripe endpoints, WebSocket runtime, RLS and E2E artifacts | Do not merge wholesale; selectively port contracts and proven tests into the chosen Docker backend architecture |

The CRM, registry, and skill branches share the same main ancestor according to the branch comparison. They still need conflict and dependency checks when combined. The v0.2.1 branch has diverged and uses a different deployment/data approach; treat it as a reference implementation, not the integration base.

## 5. Immediate architecture decisions

1. Keep the selected hybrid topology: Vercel frontend, independently deployed Docker backend.
2. Make FastAPI the primary business API and agent orchestration control plane for the first production architecture.
3. Retain the MQTT broker as an optional isolated service; do not make it a prerequisite for chat or ordinary API operations.
4. Use PostgreSQL as the source of truth; introduce Alembic migrations before adding new persistent business entities.
5. Use PostgreSQL/pgvector for the initial knowledge and retrieval layer; defer Neo4j until graph workloads justify it.
6. Use Redis for cache, quotas, short-lived coordination, and queue support where appropriate.
7. Place provider integrations behind a provider-neutral AI adapter interface; store all provider secrets server-side.
8. Enforce tenant isolation at both application query boundaries and database policy/RLS boundaries where supported.
9. Keep all external side effects behind policy checks, audit records, and explicit human approvals where required.
10. Add marketplace, creator payouts, and production billing only after identity, metering, ledger, and tenant isolation are verified.

## 6. Sprint 001 acceptance checklist

- [x] Confirm target repository and default branch.
- [x] Inspect repository tree and baseline files.
- [x] Inspect current Docker Compose, API, MQTT, package, and CI configuration.
- [x] Discover and compare existing feature branches.
- [x] Record blockers and consolidation recommendations.
- [ ] Run CI and local Docker tests in a controlled environment.
- [ ] Review all candidate branch diffs and dependency changes.
- [ ] Create a reviewed integration PR for the first production foundation.
- [ ] Validate tenant isolation, secrets handling, and backup/restore.

## 7. Scope boundary

This audit is based on GitHub metadata, repository trees, and selected text files. It does not include a local build, running containers, dynamic security testing, live provider calls, production database inspection, or deployment verification. Any claim of operational readiness requires those tests.
