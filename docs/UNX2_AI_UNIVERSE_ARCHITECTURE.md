# UNX2 AI UNIVERSE — Target Architecture

**Brand:** UNX2 AI UNIVERSE — Powered by LÉVIATHAN  
**Topology:** Vercel frontend + independent Docker backend  
**Audience:** public users with professional workspaces  
**Architecture status:** target design; implementation is incremental

## 1. Product boundaries

### UNX2 Experience Platform
Owns the public product experience: registration, workspaces, universal chat, model selection, comparison, creator studio, marketplace, usage dashboard, and professional administration.

### LÉVIATHAN Core
Owns trusted execution and coordination: provider-neutral model routing, agent runtime, policy evaluation, memory access, tool permissions, event orchestration, usage metering, and telemetry.

### AI UNIVERSE Marketplace
Owns discovery and commerce for third-party assistants and applications: listings, versions, reviews, purchases, subscriptions, seller reporting, moderation, refunds, and revenue settlement.

These are product domains, not necessarily separate microservices in the first release. Start with a modular FastAPI backend and extract independently scaling workloads only when needed.

## 2. Deployment topology

- **Frontend:** Next.js + TypeScript on Vercel.
- **Backend:** FastAPI in Docker on an independently managed container platform.
- **Database:** managed PostgreSQL; pgvector extension for embeddings.
- **Cache/coordination:** Redis.
- **Object storage:** S3-compatible storage for uploads and generated artifacts.
- **Realtime:** SSE for model output; WebSocket service for telemetry and interactive events when justified.
- **Observability:** OpenTelemetry-compatible traces, structured logs, metrics, and error reporting.
- **Secrets:** backend secret manager/environment injection; never expose provider keys to browser bundles.
- **CI/CD:** GitHub Actions for lint, type checks, tests, migration checks, image build, and deployment gates.

Vercel is not the system of record for business data or provider secrets. Browser requests call the backend through a configured HTTPS API origin. Use a BFF only when it provides a clear security or session-management benefit.

## 3. Logical components

### Identity and tenancy
- Users, organizations, memberships, invitations, roles, sessions, API credentials.
- Roles: platform_admin, organization_owner, admin, creator, member, billing_manager, reviewer.
- Every tenant-owned entity has an organization_id/tenant_id.
- Apply tenant filters in every repository/service query and database RLS where supported.
- Test cross-tenant read, write, update, delete, search, file, memory, and agent-tool access.

### AI Gateway and Router
- Provider adapter interface: capabilities, model catalogue, generate, stream, structured output, embeddings, health, pricing metadata.
- Provider/model catalogue is refreshed and versioned; never assume a model identifier remains available.
- Routing inputs: task class, quality tier, latency target, budget, modality, context window, provider health, user/tenant policy.
- Fallback must be explicit, observable, and respect data residency and privacy constraints.
- Per-request cost estimate and actual usage are recorded with provider/model/version.

### Universal Chat
- Streaming conversation API with durable conversation/message records.
- Single-model and parallel comparison modes.
- Model handoff that preserves selected conversation context.
- Attachments with malware/type/size checks and tenant-scoped object storage.
- Export/delete controls and retention settings.

### Meta-Arbiter
- Parallel model calls are independent agent runs.
- Consolidation produces a structured synthesis with claims, supporting evidence, disagreement, uncertainty, and citations/provenance where available.
- No model vote is treated as proof of truth.
- High-impact claims require external evidence or human review.

### Agent Registry and Runtime
- Versioned agent definitions, owner tenant, prompt/config version, allowed tools, model policy, memory policy, cost ceiling, timeout, and execution status.
- Runtime uses typed tools and bounded execution loops.
- Sandboxed code execution is a separate capability and is disabled by default.
- Each run has a trace ID, idempotency key where appropriate, budget, cancellation path, and audit events.

### Memory Fabric
- Separate conversation history, user-approved preferences, organization knowledge, and retrieval indexes.
- Explicit consent, retention, export, deletion, and access rules.
- Retrieval is tenant-scoped and filtered by ACL before content reaches a model.
- Never mix personal and organizational memory implicitly.

### Creator Studio and App Builder
- No-code assistant builder first; visual app composition later.
- Draft → test → review → publish lifecycle.
- Immutable versions and rollback.
- Permission manifest for every tool, integration, data scope, and outbound action.
- Generated code is not executed on the API host; use isolated sandboxes and resource limits.

### Marketplace and Commerce
- Listings, versioned artifacts, moderation state, price plans, entitlements, purchases, subscriptions, refunds, and seller balances.
- A double-entry or immutable ledger records credits, debits, refunds, fees, and creator liabilities.
- Payment provider webhooks are signature-verified and idempotent.
- Do not store raw card data.
- Creator payouts require identity/tax/compliance review and provider support before launch.

### Governance and observability
- Policy engine: deny by default for external side effects and sensitive tools.
- Human approval queue for messages, purchases, refunds, publication, external integrations, and destructive actions.
- Append-only audit events for permission changes, tool calls, approvals, billing, and data export/deletion.
- Per-tenant rate limits, concurrency limits, model budgets, and abuse detection.

## 4. Canonical domain model

Core entities:

- User, Organization, Membership, Role, Session, ApiCredential
- Provider, Model, ProviderCredentialReference, ModelCapability, ModelPriceSnapshot
- Conversation, Message, Attachment, UsageRecord
- Agent, AgentVersion, ToolDefinition, ToolGrant, AgentRun, AgentRunEvent
- MemoryCollection, MemoryEntry, KnowledgeSource, EmbeddingRecord
- App, AppVersion, AppPermission, AppDeployment
- MarketplaceListing, ListingVersion, Review, Entitlement
- Purchase, Subscription, CreditAccount, LedgerEntry, Refund, CreatorBalance, Payout
- ApprovalRequest, PolicyDecision, AuditEvent, WebhookEvent
- TelemetryMetric, TraceReference, Incident

Every tenant-owned record includes tenant_id, created_at, updated_at, and appropriate actor/owner metadata. Use UUID primary keys unless a domain-specific identifier is required.

## 5. Initial API contract

Prefix all application endpoints with `/api/v1`.

- `GET /health/live`, `GET /health/ready`
- `GET /models`, `GET /providers/status`
- `POST /chat`, `POST /chat/compare`, `POST /chat/synthesize`
- `GET/POST /conversations`, `GET /conversations/{id}`
- `GET/POST /agents`, `POST /agents/{id}/runs`
- `GET/POST /creator/agents`, `POST /creator/agents/{id}/publish`
- `GET /marketplace/listings`, `GET /marketplace/listings/{slug}`
- `POST /billing/checkout`, `POST /billing/webhooks/{provider}`
- `GET /usage`, `GET /telemetry`
- `POST /approvals/{id}/decision`

Use OpenAPI-generated contracts, pagination, request IDs, typed errors, rate limits, idempotency keys for write operations, and consistent audit metadata.

## 6. Data and event architecture

PostgreSQL is authoritative. Redis is disposable cache/coordination and must not be the only copy of business events. Use an outbox pattern for reliable event publication from database transactions. Event envelopes include event_id, event_type, schema_version, tenant_id, actor_id, occurred_at, correlation_id, and payload reference.

Initial events:
- identity.user_registered
- tenant.created
- chat.message_created
- ai.run_started / ai.run_completed / ai.run_failed
- agent.published / agent.run_completed
- approval.requested / approval.granted / approval.rejected
- marketplace.purchase_created / marketplace.refund_created
- billing.webhook_received / billing.reconciled
- usage.recorded

## 7. Security requirements

- MFA for privileged users; secure password/session policy.
- Tenant isolation in API, database, object storage, vector search, cache keys, telemetry, and agent tools.
- Encryption in transit and at rest; managed secrets.
- Strict CORS, CSRF protection where cookie sessions are used, secure headers, and rate limits.
- SSRF protections for URL-fetch tools; egress allowlists for agent integrations.
- Prompt-injection defenses and tool-output distrust.
- File validation, malware scanning, size limits, and private object storage.
- Signed webhooks, replay protection, and idempotency.
- Backups with tested restoration and defined RPO/RTO.
- Privacy workflows for consent, access, correction, export, deletion, and retention.
- Security review against Quebec Law 25, Canadian privacy obligations, CASL, and applicable AI marketplace/platform obligations before public launch.

## 8. Initial service boundaries

Keep these as modules inside one backend deployment initially:

1. identity_tenancy
2. provider_gateway
3. chat
4. agent_runtime
5. memory
6. creator_studio
7. marketplace
8. billing_ledger
9. policy_approvals
10. telemetry_audit

Separate runtime workers, websocket/telemetry, and sandbox execution when isolation or scaling requires it.

## 9. Non-functional targets

- Initial API availability objective: 99.5% during beta.
- API overhead target: p95 under 500 ms excluding upstream model generation and large file operations.
- Every AI run has a trace ID and usage/cost record.
- All provider calls have timeouts, bounded retries, cancellation, and budget ceilings.
- Database migrations are reversible where practical and tested on a production-like copy.
- Backups and restore tests are mandatory before public paid launch.
- Accessibility, responsive layout, localization (French/English), and clear usage disclosure are release requirements.

## 10. Architecture decision records

### ADR-001 — Hybrid hosting
Accepted: Vercel for the Next.js frontend; Docker backend deployed independently. This keeps provider secrets, long-running orchestration, and stateful workloads outside browser code and frontend deployment constraints.

### ADR-002 — Modular monolith first
Accepted: one FastAPI control-plane API with explicit domain modules, plus separate runtime/worker processes where needed. Avoid premature microservices.

### ADR-003 — PostgreSQL first
Accepted: PostgreSQL + pgvector as the first source of truth and vector retrieval layer. Redis for cache/coordination. Neo4j deferred until graph query needs are demonstrated.

### ADR-004 — Provider-neutral model layer
Accepted: adapter contract rather than provider-specific logic spread throughout application modules. Model IDs and prices are refreshed from provider catalogues and configuration.

### ADR-005 — Fail-closed security
Accepted: missing secrets, invalid tenant context, unapproved tools, unknown payment events, and missing policy decisions must deny the operation.
