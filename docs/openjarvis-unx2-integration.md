# OpenJarvis × UNX2 integration plan

**Decision:** Option A — one shared engine, isolated logical assistant instances.  
**Target repository:** `neuraxl/neurax-ultime-core`  
**Upstream:** `open-jarvis/OpenJarvis`  
**Upstream pin:** `86f75ef7faeeb2b022a6621716d88c57ba105db0`  
**License:** Apache-2.0

## 1. Boundary and ownership

UNX2 remains the control plane and owns:
- user identity, tenant membership, RBAC and policy;
- instance creation, lifecycle, quotas and billing;
- provider credentials and secret rotation;
- tenant-scoped memory provisioning;
- audit logs, telemetry and event bus;
- the independent META-ARBITER.

OpenJarvis is an execution engine behind an adapter. It must not own UNX2 identity, tenant policy, billing, or cross-instance routing. The adapter is replaceable so Mistral, DeepSeek, or another runtime can be added without changing the instance API.

## 2. Target request flow

```text
Authenticated user
  -> UNX2 API / Tenant Context
  -> Instance Registry (tenant_id + instance_id)
  -> Policy / quota checks
  -> Provider-neutral Runtime Adapter
  -> OpenJarvis SDK
  -> configured model engine
  -> response + usage + trace
  -> UNX2 audit / telemetry
```

META-ARBITER remains outside OpenJarvis. It receives candidate outputs and telemetry through a provider-neutral contract, applies UNX2 policies, and returns a decision. It is not implemented by this first adapter.

## 3. Isolation invariants

1. Every instance belongs to one tenant.
2. Tenant identity is taken from authenticated server context, never accepted as authoritative from a JSON body.
3. Instance lookup always filters by both tenant_id and instance_id.
4. Each instance has a server-generated config path and memory namespace.
5. No request may change process-wide environment variables to select a tenant.
6. Provider credentials are server-side only and excluded from prompts/logs.
7. Tools and external actions are disabled until permission, sandbox, and approval gates exist.
8. A runtime failure must not fall back to another tenant's config or memory.

The current adapter validates the tenant/instance pair and confines config files to a managed root. This is a code-level guard, not a substitute for authenticated API dependencies, database row-level security, filesystem permissions, or adversarial integration tests.

## 4. Delivery phases

### Phase 0 — repository and upstream audit
- Inspect existing FastAPI, PostgreSQL, Redis, MQTT, Compose and deployment contracts.
- Pin upstream OpenJarvis to an immutable commit.
- Record Apache-2.0 attribution and dependency provenance.
- Do not copy the entire upstream repository into the UNX2 codebase.

### Phase 1 — adapter foundation (this change)
- Add a narrow SDK adapter and typed instance/request/response contracts.
- Require an explicit per-instance config file under a managed root.
- Add tests for path traversal, missing config, cross-tenant requests and empty prompts.
- Keep the adapter optional; existing UNX2 services remain operational without it.

### Phase 2 — durable instance registry
- Add PostgreSQL migration for assistant_instances.
- Add tenant_id, instance_id, config reference, runtime key, model policy, status, timestamps and version.
- Enforce unique (tenant_id, instance_id), indexes, and PostgreSQL RLS.
- Store memory outside public/static paths, with restrictive file permissions or a tenant-aware database backend.

### Phase 3 — authenticated API and runtime lifecycle
- Integrate with the real UNX2 authentication and RBAC mechanism.
- Add create/list/get/update/archive endpoints scoped to authenticated tenant.
- Use lifespan-managed runtime pools; do not instantiate/close a model on every production request.
- Add concurrency limits, timeout/cancellation, retries, quotas and graceful shutdown.

### Phase 4 — memory and multi-provider tests
- Verify OpenJarvis config keys and actual memory DB location for the pinned commit.
- Prove two tenants cannot retrieve one another's memory through API, DB, file path, cache or telemetry.
- Test Ollama/local engine and each enabled cloud provider separately.
- Add cost, latency, token and energy telemetry where available.

### Phase 5 — META-ARBITER
- Implement provider-neutral candidate, score, policy and decision contracts in a separate package.
- Add deterministic policy tests and failure behavior.
- Keep arbitration independent from OpenJarvis SDK types and vendor-specific SDKs.

## 5. Test and release gates

Required before production:
- unit tests for all adapter and registry paths;
- migration tests and PostgreSQL RLS tests;
- two-tenant isolation and path traversal tests;
- provider contract tests with mocked HTTP boundaries;
- load/concurrency tests and cancellation tests;
- secret scanning and dependency vulnerability scan;
- CI green on supported Python 3.12 runtime;
- manual review of OpenJarvis upstream changes before updating the pin.

## 6. Rollback

The integration is additive. Disable the OpenJarvis adapter feature flag and continue using the existing UNX2 API, MQTT broker, PostgreSQL and Redis services. Do not remove existing tables or services as part of rollback.

## 7. Explicitly not claimed

This phase does not claim production-ready tenant authentication, persistent clone provisioning, isolated production memory, active provider credentials, end-to-end multi-IA arbitration, or a completed runtime deployment. Those require the subsequent phases and verified tests.
