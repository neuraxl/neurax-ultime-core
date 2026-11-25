# OpenJarvis integration for UNX2

Status: integration foundation (not production-enabled).

## Upstream provenance

- Project: https://github.com/open-jarvis/OpenJarvis
- Pinned upstream commit: `86f75ef7faeeb2b022a6621716d88c57ba105db0`
- License: Apache License 2.0
- This integration initially uses the upstream Python SDK as a dependency. It does not vendor or copy upstream source files into UNX2.
- Keep the upstream LICENSE and NOTICE obligations intact if source files are vendored in a later phase. Record every modified upstream file and retain its copyright notices.

## Design

UNX2 owns identity, tenant authorization, instance lifecycle, policy, provider credentials, telemetry, and billing. OpenJarvis is a replaceable inference/agent runtime behind the UNX2 adapter.

One shared application process may host many logical assistant instances. Each instance must receive:
- an authenticated tenant ID from UNX2 (never from an untrusted request body);
- its own generated OpenJarvis config file;
- a tenant-scoped memory database/path;
- an explicit model/engine policy;
- independent usage and audit metadata.

Do not change process-wide `OPENJARVIS_HOME` per request: environment variables are process-global and unsafe for concurrent tenants. Use explicit per-instance config paths and test the memory backend path before enabling a runtime.

## Current scope

The adapter requires a pre-provisioned config path and refuses to construct an SDK client without one. It exposes a narrow ask/close contract. It does not yet provision PostgreSQL tenants, authenticate users, execute tools, expose public API routes, or claim a production-safe memory isolation boundary.

## Installation

From the repository root:

```bash
python -m pip install -r api/requirements.txt
python -m pip install -r api/requirements-openjarvis.txt
```

The upstream package supports Python 3.11–3.13. UNX2's API container currently uses Python 3.12.

## Next gates before production

1. Implement authenticated tenant context and RBAC.
2. Provision per-instance config and persistent memory namespace using server-generated paths.
3. Confirm upstream config fields for every supported memory backend.
4. Add PostgreSQL instance registry + migrations and tenant-level RLS.
5. Add provider-secret vault, rate limits, quotas, and audit events.
6. Run two-tenant adversarial isolation tests and provider contract tests.
7. Pin and scan the complete transitive dependency lockfile.
