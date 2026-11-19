"""UNX2 Open Source Registry — additive API module.

Discovery is read-only against public GitHub metadata. Integration endpoints generate
and validate plans; they never start containers or execute repository code.
"""
from __future__ import annotations

import base64
import hashlib
import re
import secrets
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from .database import Base, engine
from .config import settings
from .security import TenantPrincipal, require_tenant

router = APIRouter(prefix="/api/v1/open-source", tags=["open-source-registry"])


class RegistryBase(Base):
    pass


class Project(RegistryBase):
    __tablename__ = "unx2_os_projects"
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    repo_url: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    license_spdx: Mapped[str | None] = mapped_column(String(100), nullable=True)
    default_branch: Mapped[str | None] = mapped_column(String(200), nullable=True)
    latest_release: Mapped[str | None] = mapped_column(String(100), nullable=True)
    stars: Mapped[int] = mapped_column(Integer, default=0)
    forks: Mapped[int] = mapped_column(Integer, default=0)
    open_issues: Mapped[int] = mapped_column(Integer, default=0)
    pushed_at: Mapped[str | None] = mapped_column(String(80), nullable=True)
    maturity_score: Mapped[int] = mapped_column(Integer, default=0)
    maturity_details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    dependencies: Mapped[list[Any]] = mapped_column(JSON, default=list)
    features: Mapped[list[Any]] = mapped_column(JSON, default=list)
    topics: Mapped[list[Any]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(30), default="discovered")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Connector(RegistryBase):
    __tablename__ = "unx2_os_connectors"
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("unx2_organizations.id"), index=True, nullable=False)
    project_id: Mapped[str] = mapped_column(ForeignKey("unx2_os_projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(30), default="api")
    version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    endpoint: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    capabilities: Mapped[list[Any]] = mapped_column(JSON, default=list)
    permissions: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class AgentGrant(RegistryBase):
    __tablename__ = "unx2_os_agent_grants"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("unx2_organizations.id"), index=True, nullable=False)
    agent_id: Mapped[str] = mapped_column(String(200), index=True)
    connector_id: Mapped[str] = mapped_column(String(255), ForeignKey("unx2_os_connectors.id"), index=True)
    tool_name: Mapped[str] = mapped_column(String(200))
    allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    max_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class IntegrationPlan(RegistryBase):
    __tablename__ = "unx2_os_integration_plans"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("unx2_organizations.id"), index=True, nullable=False)
    connector_id: Mapped[str] = mapped_column(ForeignKey("unx2_os_connectors.id"), index=True)
    compose_yaml: Mapped[str] = mapped_column(Text)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="planned")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class UsageEvent(RegistryBase):
    __tablename__ = "unx2_os_usage_events"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("unx2_organizations.id"), index=True, nullable=False)
    agent_id: Mapped[str] = mapped_column(String(200), index=True)
    connector_id: Mapped[str] = mapped_column(ForeignKey("unx2_os_connectors.id"), index=True)
    tool_name: Mapped[str] = mapped_column(String(200))
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


async def get_db():
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        yield session


async def require_admin(x_unx2_registry_token: str | None = Header(default=None)) -> None:
    expected = getattr(settings, "os_registry_admin_token", None)
    if not expected or expected == "CHANGE_ME_TO_A_LONG_RANDOM_SECRET":
        raise HTTPException(status_code=503, detail="Registry write operations disabled: configure OS_REGISTRY_ADMIN_TOKEN.")
    if not x_unx2_registry_token or not secrets.compare_digest(x_unx2_registry_token, expected):
        raise HTTPException(status_code=401, detail="Invalid registry administrator token.")


class DiscoverRequest(BaseModel):
    repository_url: str = Field(min_length=20, max_length=500)


class RegisterRequest(BaseModel):
    project_id: str
    name: str = Field(min_length=2, max_length=200)
    kind: str = Field(default="api", pattern="^(api|mcp|webhook|service|library)$")
    version: str | None = None
    endpoint: str | None = None
    capabilities: list[str] = Field(default_factory=list)


class GrantRequest(BaseModel):
    agent_id: str = Field(min_length=2, max_length=200)
    tool_names: list[str] = Field(min_length=1, max_length=50)
    allowed: bool = True
    max_cost_usd: float = Field(default=0.0, ge=0.0, le=100000.0)


class ConnectorToggleRequest(BaseModel):
    enabled: bool


class PlanRequest(BaseModel):
    connector_id: str
    image: str = Field(min_length=3, max_length=300, pattern="^[A-Za-z0-9./:_-]+$")
    service_name: str = Field(min_length=2, max_length=60, pattern="^[a-z][a-z0-9_-]*$")
    host_port: int | None = Field(default=None, ge=1024, le=65535)
    container_port: int | None = Field(default=None, ge=1, le=65535)


class OrchestrationRequest(BaseModel):
    agent_id: str
    task: str = Field(min_length=3, max_length=2000)
    estimated_cost_usd: float = Field(default=0.0, ge=0.0)


class UsageRequest(BaseModel):
    agent_id: str
    connector_id: str
    tool_name: str
    cost_usd: float = Field(ge=0.0)
    success: bool = False


def _grant_id(organization_id: str, agent_id: str, connector_id: str, tool_name: str) -> str:
    raw = f"{organization_id}|{agent_id}|{connector_id}|{tool_name}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _github_repo(url: str) -> tuple[str, str, str]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        raise HTTPException(status_code=422, detail="Only public https://github.com/{owner}/{repo} repositories are supported.")
    parts = [p for p in parsed.path.strip("/").split("/") if p]
    if len(parts) < 2 or not re.fullmatch(r"[A-Za-z0-9_.-]+", parts[0]) or not re.fullmatch(r"[A-Za-z0-9_.-]+", parts[1]):
        raise HTTPException(status_code=422, detail="Invalid GitHub repository URL.")
    owner, repo = parts[0], parts[1].removesuffix(".git")
    return owner, repo, f"https://github.com/{owner}/{repo}"


async def _github_json(client: httpx.AsyncClient, path: str) -> Any:
    response = await client.get("https://api.github.com" + path, headers={"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
    if response.status_code == 404:
        return None
    if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
        raise HTTPException(status_code=429, detail="GitHub API rate limit reached. Configure an authenticated GitHub token in a future connector.")
    response.raise_for_status()
    return response.json()


def _maturity(meta: dict[str, Any], has_readme: bool, has_ci: bool, has_tests: bool, has_release: bool) -> tuple[int, dict[str, Any]]:
    license_ok = bool((meta.get("license") or {}).get("spdx_id") not in (None, "NOASSERTION"))
    recent = False
    try:
        pushed = datetime.fromisoformat(meta["pushed_at"].replace("Z", "+00:00"))
        recent = (datetime.now(timezone.utc) - pushed).days <= 365
    except Exception:
        pass
    checks = {
        "license_declared": (20 if license_ok else 0),
        "readme": (15 if has_readme else 0),
        "ci_workflows": (15 if has_ci else 0),
        "tests_detected": (15 if has_tests else 0),
        "release_published": (15 if has_release else 0),
        "maintained_within_12_months": (15 if recent else 0),
        "community_signal": (5 if meta.get("stargazers_count", 0) >= 100 else 0),
    }
    return sum(checks.values()), checks


@router.post("/discover", dependencies=[Depends(require_admin)])
async def discover(payload: DiscoverRequest, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    owner, repo, canonical = _github_repo(payload.repository_url)
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=False) as client:
        meta = await _github_json(client, f"/repos/{owner}/{repo}")
        if not meta:
            raise HTTPException(status_code=404, detail="GitHub repository not found or not public.")
        if meta.get("private"):
            raise HTTPException(status_code=422, detail="Private repositories are not scanned by this public discovery endpoint.")
        contents = await _github_json(client, f"/repos/{owner}/{repo}/contents")
        release = await _github_json(client, f"/repos/{owner}/{repo}/releases/latest")
        topics = await _github_json(client, f"/repos/{owner}/{repo}/topics") or {}
        files = {x.get("name", "").lower(): x for x in (contents or []) if isinstance(x, dict)}
        readme = await _github_json(client, f"/repos/{owner}/{repo}/readme")
        has_readme = bool(readme)
        has_ci = ".github" in files
        has_tests = any(n in files for n in ("tests", "test", "__tests__", "spec"))
        manifest_names = ("package.json", "pyproject.toml", "requirements.txt", "go.mod", "Cargo.toml", "composer.json")
        dependencies: list[str] = []
        for filename in manifest_names:
            entry = files.get(filename.lower())
            if not entry or not entry.get("download_url"):
                continue
            manifest = await _github_json(client, f"/repos/{owner}/{repo}/contents/{filename}")
            encoded = (manifest or {}).get("content")
            if not encoded:
                continue
            try:
                text = base64.b64decode(encoded).decode("utf-8", "replace")[:200000]
            except Exception:
                continue
            if filename == "package.json":
                import json
                try:
                    data = json.loads(text)
                    dependencies.extend(sorted((data.get("dependencies") or {}).keys()))
                    dependencies.extend(sorted((data.get("devDependencies") or {}).keys()))
                except Exception:
                    pass
            else:
                dependencies.extend(re.findall(r"(?m)^([A-Za-z0-9_.-]+)(?:\s*[=<>~!].*)?$", text)[:100])
        score, details = _maturity(meta, has_readme, has_ci, has_tests, bool(release))
        license_info = meta.get("license") or {}
        project_id = f"github:{owner.lower()}/{repo.lower()}"
        record = await db.get(Project, project_id)
        values = dict(
            id=project_id, repo_url=canonical, full_name=meta["full_name"],
            description=meta.get("description"), license_spdx=license_info.get("spdx_id"),
            default_branch=meta.get("default_branch"), latest_release=(release or {}).get("tag_name"),
            stars=meta.get("stargazers_count", 0), forks=meta.get("forks_count", 0),
            open_issues=meta.get("open_issues_count", 0), pushed_at=meta.get("pushed_at"),
            maturity_score=score, maturity_details=details, dependencies=sorted(set(dependencies)),
            features=(topics.get("names") or []), topics=(topics.get("names") or []),
            status="discovered", updated_at=datetime.now(timezone.utc))
        if record:
            for key, value in values.items():
                setattr(record, key, value)
        else:
            record = Project(**values)
            db.add(record)
        await db.commit()
        return {"project_id": project_id, "repository": meta["full_name"], "license": license_info.get("spdx_id"), "latest_release": values["latest_release"], "dependencies": values["dependencies"], "features": values["features"], "maturity_score": score, "maturity_breakdown": details, "status": "discovered"}


@router.get("/catalog")
async def catalog(q: str | None = None, min_score: int = 0, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    result = await db.execute(select(Project).where(Project.maturity_score >= min_score).order_by(Project.maturity_score.desc()).limit(200))
    rows = result.scalars().all()
    if q:
        needle = q.lower()
        rows = [p for p in rows if needle in p.full_name.lower() or needle in (p.description or "").lower() or any(needle in str(x).lower() for x in (p.features or []) + (p.dependencies or []))]
    return {"count": len(rows), "items": [{"id":p.id,"repository":p.full_name,"url":p.repo_url,"description":p.description,"license":p.license_spdx,"version":p.latest_release,"stars":p.stars,"maturity_score":p.maturity_score,"features":p.features,"dependencies":p.dependencies,"status":p.status} for p in rows]}


@router.post("/registry")
async def register(payload: RegisterRequest, principal: TenantPrincipal = Depends(require_tenant), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    project = await db.get(Project, payload.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Discover the project before registering it.")
    if principal.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Organization administrator role required.")
    connector_id = f"connector:{principal.organization_id}:{payload.project_id}:{payload.kind}"
    existing = await db.get(Connector, connector_id)
    if existing:
        raise HTTPException(status_code=409, detail="A connector of this type is already registered for this project.")
    item = Connector(id=connector_id, organization_id=principal.organization_id, project_id=payload.project_id, name=payload.name, kind=payload.kind, version=payload.version or project.latest_release, endpoint=payload.endpoint, capabilities=payload.capabilities, permissions={"default": "deny"}, enabled=False)
    db.add(item)
    await db.commit()
    return {"connector_id": connector_id, "status": "registered", "enabled": False, "note": "Connectors are deny-by-default and require explicit agent grants."}


@router.get("/registry")
async def registry(principal: TenantPrincipal = Depends(require_tenant), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    rows = (await db.execute(select(Connector).where(Connector.organization_id == principal.organization_id).order_by(Connector.created_at.desc()).limit(200))).scalars().all()
    return {"count": len(rows), "items": [{"id":x.id,"project_id":x.project_id,"name":x.name,"kind":x.kind,"version":x.version,"endpoint":x.endpoint,"capabilities":x.capabilities,"enabled":x.enabled} for x in rows]}


@router.post("/registry/{connector_id}/permissions")
async def set_permissions(connector_id: str, payload: GrantRequest, principal: TenantPrincipal = Depends(require_tenant), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    if principal.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Organization administrator role required.")
    connector = await db.scalar(select(Connector).where(Connector.id == connector_id, Connector.organization_id == principal.organization_id))
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found.")
    changed = []
    for tool_name in payload.tool_names:
        grant_id = _grant_id(principal.organization_id, payload.agent_id, connector_id, tool_name)
        grant = await db.scalar(select(AgentGrant).where(AgentGrant.id == grant_id, AgentGrant.organization_id == principal.organization_id))
        if grant:
            grant.allowed, grant.max_cost_usd = payload.allowed, payload.max_cost_usd
        else:
            db.add(AgentGrant(id=grant_id, organization_id=principal.organization_id, agent_id=payload.agent_id, connector_id=connector_id, tool_name=tool_name, allowed=payload.allowed, max_cost_usd=payload.max_cost_usd))
        changed.append(tool_name)
    await db.commit()
    return {"agent_id": payload.agent_id, "connector_id": connector_id, "tools": changed, "allowed": payload.allowed, "max_cost_usd": payload.max_cost_usd}


@router.post("/registry/{connector_id}/enable")
async def toggle_connector(connector_id: str, payload: ConnectorToggleRequest, principal: TenantPrincipal = Depends(require_tenant), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    if principal.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Organization administrator role required.")
    connector = await db.scalar(select(Connector).where(Connector.id == connector_id, Connector.organization_id == principal.organization_id))
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found.")
    connector.enabled = payload.enabled
    await db.commit()
    return {"connector_id": connector_id, "enabled": connector.enabled, "default_permission": "deny"}


@router.get("/agents/{agent_id}/tools")
async def agent_tools(agent_id: str, principal: TenantPrincipal = Depends(require_tenant), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    result = await db.execute(select(AgentGrant, Connector).join(Connector, AgentGrant.connector_id == Connector.id).where(AgentGrant.agent_id == agent_id, AgentGrant.organization_id == principal.organization_id, Connector.organization_id == principal.organization_id, AgentGrant.allowed.is_(True), Connector.enabled.is_(True)))
    items = [{"connector_id":g.connector_id,"connector":c.name,"kind":c.kind,"tool":g.tool_name,"max_cost_usd":g.max_cost_usd} for g,c in result.all()]
    return {"agent_id": agent_id, "count": len(items), "tools": items, "policy": "allow-list; disabled connectors are never exposed"}


@router.post("/integrations/plan")
async def create_integration_plan(payload: PlanRequest, principal: TenantPrincipal = Depends(require_tenant), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    if principal.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Organization administrator role required.")
    connector = await db.scalar(select(Connector).where(Connector.id == payload.connector_id, Connector.organization_id == principal.organization_id))
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found.")
    if ":" not in payload.image or payload.image.endswith(":latest"):
        raise HTTPException(status_code=422, detail="Use an explicitly versioned container image; the floating latest tag is prohibited.")
    ports = ""
    if payload.host_port and payload.container_port:
        ports = f"\n    ports:\n      - \"{payload.host_port}:{payload.container_port}\""
    compose = f"services:\n  {payload.service_name}:\n    image: {payload.image}\n    restart: unless-stopped\n    read_only: true\n    security_opt:\n      - no-new-privileges:true\n    cap_drop:\n      - ALL\n    tmpfs:\n      - /tmp:rw,noexec,nosuid,size=64m{ports}\n"
    snapshot = {"connector_id": connector.id, "previous_enabled": connector.enabled, "compose_yaml": compose, "created_at": datetime.now(timezone.utc).isoformat()}
    plan_id = secrets.token_hex(16)
    db.add(IntegrationPlan(id=plan_id, organization_id=principal.organization_id, connector_id=connector.id, compose_yaml=compose, snapshot=snapshot, status="planned"))
    await db.commit()
    return {"plan_id": plan_id, "status": "planned", "compose_yaml": compose, "executed": False, "note": "Review and deploy manually. This API never starts containers or runs third-party code."}


@router.post("/integrations/{plan_id}/test")
async def test_integration_plan(plan_id: str, principal: TenantPrincipal = Depends(require_tenant), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    plan = await db.scalar(select(IntegrationPlan).where(IntegrationPlan.id == plan_id, IntegrationPlan.organization_id == principal.organization_id))
    if not plan:
        raise HTTPException(status_code=404, detail="Integration plan not found.")
    checks = {"connector_exists": await db.scalar(select(Connector.id).where(Connector.id == plan.connector_id, Connector.organization_id == principal.organization_id)) is not None, "read_only_filesystem": "read_only: true" in plan.compose_yaml, "no_new_privileges": "no-new-privileges:true" in plan.compose_yaml, "drop_all_capabilities": "      - ALL" in plan.compose_yaml, "deployment_executed": False}
    return {"plan_id": plan_id, "status": "validated" if all(v for k,v in checks.items() if k != "deployment_executed") else "needs_review", "checks": checks, "note": "Static validation only; live connectivity requires deployment in the target environment."}


@router.post("/integrations/{plan_id}/rollback")
async def rollback_plan(plan_id: str, principal: TenantPrincipal = Depends(require_tenant), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    if principal.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Organization administrator role required.")
    plan = await db.scalar(select(IntegrationPlan).where(IntegrationPlan.id == plan_id, IntegrationPlan.organization_id == principal.organization_id))
    if not plan:
        raise HTTPException(status_code=404, detail="Integration plan not found.")
    plan.status = "rolled_back"
    await db.commit()
    return {"plan_id": plan_id, "status": "rolled_back", "snapshot": plan.snapshot, "note": "The plan record is reverted. No running container was changed because deployment is deliberately manual."}


@router.post("/orchestration/plan")
async def orchestration_plan(payload: OrchestrationRequest, principal: TenantPrincipal = Depends(require_tenant), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    result = await db.execute(select(AgentGrant, Connector).join(Connector, AgentGrant.connector_id == Connector.id).where(AgentGrant.agent_id == payload.agent_id, AgentGrant.organization_id == principal.organization_id, Connector.organization_id == principal.organization_id, AgentGrant.allowed.is_(True), Connector.enabled.is_(True)))
    tools = [{"connector_id":g.connector_id,"tool":g.tool_name,"max_cost_usd":g.max_cost_usd} for g,c in result.all()]
    return {"agent_id": payload.agent_id, "task": payload.task, "authorized_tools": tools, "estimated_cost_usd": payload.estimated_cost_usd, "within_budget": all(payload.estimated_cost_usd <= t["max_cost_usd"] for t in tools) if tools else False, "execution": "not_started", "note": "Planning and authorization lookup only; no agent runtime is invoked by this endpoint."}


@router.post("/usage")
async def record_usage(payload: UsageRequest, principal: TenantPrincipal = Depends(require_tenant), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    grant_id = _grant_id(principal.organization_id, payload.agent_id, payload.connector_id, payload.tool_name)
    grant = await db.scalar(select(AgentGrant).where(AgentGrant.id == grant_id, AgentGrant.organization_id == principal.organization_id))
    if not grant or not grant.allowed:
        raise HTTPException(status_code=403, detail="No active grant for this agent/tool combination.")
    if payload.cost_usd > grant.max_cost_usd:
        raise HTTPException(status_code=402, detail="Reported usage exceeds the configured per-call cost ceiling.")
    connector = await db.scalar(select(Connector).where(Connector.id == payload.connector_id, Connector.organization_id == principal.organization_id))
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found.")
    event = UsageEvent(id=secrets.token_hex(16), organization_id=principal.organization_id, agent_id=payload.agent_id, connector_id=payload.connector_id, tool_name=payload.tool_name, cost_usd=payload.cost_usd, success=payload.success)
    db.add(event)
    await db.commit()
    return {"recorded": True, "cost_usd": payload.cost_usd, "success": payload.success}
