import hashlib

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.main import app
from app import open_source_registry as registry
from app import security


@pytest.mark.asyncio
async def test_registry_resources_are_isolated_between_organizations():
    # Combine both declarative metadata collections so cross-module FKs resolve.
    metadata = MetaData()
    for table in security.SecurityBase.metadata.sorted_tables:
        table.to_metadata(metadata)
    for table in registry.RegistryBase.metadata.sorted_tables:
        table.to_metadata(metadata)

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
            id=f"connector:{org_a}:github:owner/repo:api",
            organization_id=org_a, project_id="github:owner/repo", name="A connector",
            kind="api", capabilities=["read"], permissions={"default": "deny"}, enabled=True,
        ))
        await db.commit()

    connector_a = f"connector:{org_a}:github:owner/repo:api"
    try:
        with TestClient(app) as client:
            response_a = client.get("/api/v1/open-source/registry", headers={"Authorization": f"Bearer {token_a}"})
            response_b = client.get("/api/v1/open-source/registry", headers={"Authorization": f"Bearer {token_b}"})
            assert response_a.status_code == 200
            assert [x["id"] for x in response_a.json()["items"]] == [connector_a]
            assert response_b.status_code == 200
            assert response_b.json()["items"] == []

            # Knowing another tenant's resource ID does not grant access.
            denied = client.post(
                f"/api/v1/open-source/registry/{connector_a}/enable",
                headers={"Authorization": f"Bearer {token_b}"},
                json={"enabled": False},
            )
            assert denied.status_code == 404

            tools_b = client.get(
                "/api/v1/open-source/agents/agent-a/tools",
                headers={"Authorization": f"Bearer {token_b}"},
            )
            assert tools_b.status_code == 200
            assert tools_b.json()["tools"] == []
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()
