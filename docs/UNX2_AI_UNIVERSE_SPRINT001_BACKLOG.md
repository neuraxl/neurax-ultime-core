# UNX2 AI UNIVERSE — Sprint 001 Implementation Backlog

## Sprint goal

Establish a verified, secure foundation for evolving `neurax-ultime-core` into UNX2 AI UNIVERSE — Powered by LÉVIATHAN. Sprint 001 is repository audit, architecture alignment, and foundation preparation. It does not claim a production release.

## Workstreams

### S001-A — Repository safety and CI
- [ ] Replace the root CI workflow with separate Node, Python, Docker Compose, migration, and security checks.
- [ ] Add/commit the correct Node lockfile and a real test command, or remove invalid npm steps until a real package test suite exists.
- [ ] Add Python lint/type/test tooling and a minimal API test suite.
- [ ] Validate Compose configuration and build all images in CI.
- [ ] Remove force-push deployment helper from active deployment paths; document it as deprecated.
- [ ] Audit placeholder files and root-level legacy assets before any deletion.

### S001-B — Branch consolidation review
- [ ] Review CRM branch dependencies, migrations, authentication/session handling, and authorization.
- [ ] Review registry branch security, API credentials, permissions, migrations, and tenant isolation tests.
- [ ] Review skill runtime branch for untrusted skill loading, tool boundaries, and resource controls.
- [ ] Compare the divergent v0.2.1 branch with target architecture; port only verified contracts/tests.
- [ ] Prepare small pull requests in dependency order; no bulk merge.

### S001-C — Backend foundation
- [ ] Establish Python package structure and settings validation.
- [ ] Add Alembic migration baseline.
- [ ] Implement health/readiness and request correlation IDs.
- [ ] Add structured logs with sensitive-value and payload redaction.
- [ ] Add PostgreSQL connection lifecycle, Redis health, and graceful shutdown.
- [ ] Define tenant-aware repository conventions and authorization dependencies.
- [ ] Add outbox/event envelope contract.

### S001-D — Provider gateway foundation
- [ ] Define provider/model adapter interfaces.
- [ ] Add server-side provider credential references.
- [ ] Add model capability and model-price metadata schemas.
- [ ] Implement provider health and catalogue refresh interfaces.
- [ ] Add mock provider only for automated tests; label it clearly as mock.
- [ ] Add one real provider integration behind server-side secrets and an opt-in test.

### S001-E — Frontend foundation
- [ ] Establish Next.js + TypeScript app under an explicit root directory.
- [ ] Create UNX2 design tokens and responsive shell.
- [ ] Configure API origin per environment.
- [ ] Add sign-in/workspace shell and error/loading states.
- [ ] Do not port legacy static pages as production components without review.

## Definition of done

- CI checks are internally consistent and pass on a clean checkout.
- Docker Compose validates and services build in CI.
- API liveness/readiness behavior is covered by tests.
- Tenant access conventions are documented and tested before user data is stored.
- No production path uses default credentials or browser-visible provider secrets.
- Branch integration is represented by reviewed PRs with migration and test evidence.
- Architecture and audit docs are committed to the repository.
- No deployment is described as production-ready without an end-to-end test and security review.

## Release gates

**Gate A — Safe baseline:** CI, configuration, secrets, logging, health checks.  
**Gate B — Tenant-safe foundation:** identity, organizations, roles, migrations, isolation tests.  
**Gate C — Real multi-IA:** at least two real provider adapters, usage metering, streaming, failover tests.  
**Gate D — Agent platform:** versioned agents, bounded tools, approval policy, traceability.  
**Gate E — Commercial platform:** entitlement, immutable ledger, payment webhooks, marketplace moderation and payout readiness.

Do not open public paid access before Gates A–E and the applicable privacy/security reviews are complete.
