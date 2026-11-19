import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
import httpx
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.main import app
from app import open_source_registry as registry
from app import security


@pytest.mark.asyncio
async def test_registry_resources_are_isolated_between_organizations():
    # Security and registry models now share one declarative metadata collection.
    metadata = security.SecurityBase.metadata

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def override_db():
        async with sessions() as session:
            yield session

    app.dependency_overrides[security.get_security_db] = override_db
    app.dependency_overrides[registry.get_db] = override_db

    org_a = "org-a"
    org_b = "org-b"
    token_a = "unx2_testorgA.secret-A"
    token_b = "unx2_testorgB.secret-B"

    async with sessions() as db:
        db.add_all([
            security.Organization(id=org_a, name="Org A", slug="org-a"),
            security.Organization(id=org_b, name="Org B", slug="org-b"),
            security.ApiCredential(
                id="cred-a", organization_id=org_a, label="A key",
                key_prefix="unx2_testorgA", secret_hash=hashlib.sha256(b"secret-A").hexdigest(),
                role="admin",
            ),
            security.ApiCredential(
                id="cred-a-member", organization_id=org_a, label="A member",
                key_prefix="unx2_testmemberA", secret_hash=hashlib.sha256(b"member-A").hexdigest(),
                role="member",
            ),
            security.ApiCredential(
                id="cred-b", organization_id=org_b, label="B key",
                key_prefix="unx2_testorgB", secret_hash=hashlib.sha256(b"secret-B").hexdigest(),
                role="admin",
            ),
            registry.Project(
                id="github:owner/repo", repo_url="https://github.com/owner/repo",
                full_name="owner/repo", stars=10, forks=0, open_issues=0,
                maturity_score=50, maturity_details={}, dependencies=[],
                features=[], topics=[], status="discovered",
            ),
        ])
        await db.flush()
        db.add(registry.Connector(
            id=registry._connector_id(org_a, "github:owner/repo", "api"),
            organization_id=org_a, project_id="github:owner/repo", name="A connector",
            kind="api", capabilities=["read"], permissions={"default": "deny"}, enabled=True,
        ))
        await db.flush()
        connector_id = registry._connector_id(org_a, "github:owner/repo", "api")
        grant_id = registry._grant_id(org_a, "agent-a", connector_id, "read")
        db.add(registry.AgentGrant(id=grant_id, organization_id=org_a, agent_id="agent-a", connector_id=connector_id, tool_name="read", allowed=True, max_cost_usd=5.0))
        db.add(registry.IntegrationPlan(id="plan-a", organization_id=org_a, connector_id=connector_id, compose_yaml="services: {}", snapshot={}, status="planned"))
        await db.commit()

    connector_a = registry._connector_id(org_a, "github:owner/repo", "api")
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response_a = await client.get("/api/v1/open-source/registry", headers={"Authorization": f"Bearer {token_a}"})
            response_b = await client.get("/api/v1/open-source/registry", headers={"Authorization": f"Bearer {token_b}"})
            assert response_a.status_code == 200
            assert [x["id"] for x in response_a.json()["items"]] == [connector_a]
            assert response_b.status_code == 200
            assert response_b.json()["items"] == []

            # The owning tenant sees its allow-listed tool; the other tenant sees none.
            tools_a = await client.get("/api/v1/open-source/agents/agent-a/tools", headers={"Authorization": f"Bearer {token_a}"})
            tools_b = await client.get("/api/v1/open-source/agents/agent-a/tools", headers={"Authorization": f"Bearer {token_b}"})
            assert [item["tool"] for item in tools_a.json()["tools"]] == ["read"]
            assert tools_b.json()["tools"] == []

            # Knowing another tenant's resource ID does not grant access.
            denied = await client.post(
                f"/api/v1/open-source/registry/{connector_a}/enable",
                headers={"Authorization": f"Bearer {token_b}"},
                json={"enabled": False},
            )
            assert denied.status_code == 404

            denied_grant = await client.post(
                f"/api/v1/open-source/registry/{connector_a}/permissions",
                headers={"Authorization": f"Bearer {token_b}"},
                json={"agent_id": "agent-b", "tool_names": ["read"], "allowed": True, "max_cost_usd": 10},
            )
            assert denied_grant.status_code == 404

            denied_plan = await client.post(
                "/api/v1/open-source/integrations/plan",
                headers={"Authorization": f"Bearer {token_b}"},
                json={"connector_id": connector_a, "image": "example/app:1.0", "service_name": "example"},
            )
            assert denied_plan.status_code == 404

            denied_plan_read = await client.post(
                "/api/v1/open-source/integrations/plan-a/test",
                headers={"Authorization": f"Bearer {token_b}"},
            )
            assert denied_plan_read.status_code == 404

            denied_usage = await client.post(
                "/api/v1/open-source/usage",
                headers={"Authorization": f"Bearer {token_b}"},
                json={"agent_id": "agent-a", "connector_id": connector_a, "tool_name": "read", "cost_usd": 1, "success": True},
            )
            assert denied_usage.status_code == 403

            member_write = await client.post(
                f"/api/v1/open-source/registry/{connector_a}/enable",
                headers={"Authorization": "Bearer unx2_testmemberA.member-A"},
                json={"enabled": False},
            )
            assert member_write.status_code == 403
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()
