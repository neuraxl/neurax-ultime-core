"""UNX2 tenant identity gateway.

Tenant API keys are returned once, stored only as SHA-256 hashes, and mapped to
an organization and role. This module establishes tenant identity and audit
primitives; registry data-plane routes are not declared tenant-isolated until
their queries are explicitly scoped in the next integration step.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .main import engine, settings

router = APIRouter(prefix="/api/v1/security", tags=["security-tenant-gateway"])


class SecurityBase(DeclarativeBase):
    pass


class Organization(SecurityBase):
    __tablename__ = "unx2_organizations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ApiCredential(SecurityBase):
    __tablename__ = "unx2_api_credentials"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("unx2_organizations.id"), index=True, nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    secret_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="member", nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Membership(SecurityBase):
    __tablename__ = "unx2_memberships"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("unx2_organizations.id"), index=True, nullable=False)
    principal_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="member", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class AuditEvent(SecurityBase):
    __tablename__ = "unx2_audit_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organization_id: Mapped[str | None] = mapped_column(ForeignKey("unx2_organizations.id"), index=True, nullable=True)
    actor_id: Mapped[str] = mapped_column(String(36), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    outcome: Mapped[str] = mapped_column(String(20), default="success", nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


SessionFactory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_security_db():
    async with SessionFactory() as session:
        yield session


def _admin_check(token: str | None) -> None:
    expected = getattr(settings, "os_registry_admin_token", None)
    if not expected or expected == "CHANGE_ME_TO_A_LONG_RANDOM_SECRET":
        raise HTTPException(status_code=503, detail="Administrative provisioning is disabled until OS_REGISTRY_ADMIN_TOKEN is configured.")
    if not token or not secrets.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="Invalid administrative credential.")


async def require_platform_admin(x_unx2_registry_token: str | None = Header(default=None)) -> None:
    _admin_check(x_unx2_registry_token)


class TenantPrincipal(BaseModel):
    organization_id: str
    credential_id: str
    role: str
    scopes: list[str] = Field(default_factory=list)


async def require_tenant(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_security_db),
) -> TenantPrincipal:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="A tenant API key is required.")
    raw = authorization.removeprefix("Bearer ").strip()
    try:
        prefix, secret = raw.split(".", 1)
    except ValueError:
        raise HTTPException(status_code=401, detail="Malformed tenant API key.")
    result = await db.execute(
        select(ApiCredential, Organization)
        .join(Organization, Organization.id == ApiCredential.organization_id)
        .where(ApiCredential.key_prefix == prefix)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid tenant API key.")
    credential, organization = row
    candidate = hashlib.sha256(secret.encode("utf-8")).hexdigest()
    if not secrets.compare_digest(candidate, credential.secret_hash):
        raise HTTPException(status_code=401, detail="Invalid tenant API key.")
    now = datetime.now(timezone.utc)
    expiry = credential.expires_at
    if credential.revoked or organization.status != "active" or (expiry is not None and expiry <= now):
        raise HTTPException(status_code=401, detail="Tenant API key is inactive or expired.")
    scopes = ["tenant:read"]
    if credential.role in {"admin", "owner"}:
        scopes += ["tenant:write", "tenant:admin"]
    return TenantPrincipal(
        organization_id=organization.id,
        credential_id=credential.id,
        role=credential.role,
        scopes=scopes,
    )


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    slug: str = Field(min_length=2, max_length=80, pattern="^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ApiKeyCreate(BaseModel):
    label: str = Field(min_length=2, max_length=120)
    role: str = Field(default="member", pattern="^(owner|admin|member|viewer)$")
    expires_in_days: int | None = Field(default=90, ge=1, le=3650)


async def _audit(
    db: AsyncSession, organization_id: str | None, actor_id: str,
    action: str, resource_type: str, resource_id: str | None, detail: str | None = None,
) -> None:
    db.add(AuditEvent(
        id=str(uuid4()), organization_id=organization_id, actor_id=actor_id,
        action=action, resource_type=resource_type, resource_id=resource_id,
        outcome="success", detail=detail,
    ))


@router.post("/organizations", dependencies=[Depends(require_platform_admin)])
async def create_organization(
    payload: OrganizationCreate,
    db: AsyncSession = Depends(get_security_db),
) -> dict[str, Any]:
    existing = await db.scalar(select(Organization).where(Organization.slug == payload.slug))
    if existing:
        raise HTTPException(status_code=409, detail="Organization slug already exists.")
    organization = Organization(id=str(uuid4()), name=payload.name, slug=payload.slug)
    db.add(organization)
    await _audit(db, organization.id, "platform-admin", "organization.created", "organization", organization.id)
    await db.commit()
    return {"organization_id": organization.id, "name": organization.name, "slug": organization.slug, "status": organization.status}


@router.post("/organizations/{organization_id}/keys", dependencies=[Depends(require_platform_admin)])
async def create_api_key(
    organization_id: str,
    payload: ApiKeyCreate,
    db: AsyncSession = Depends(get_security_db),
) -> dict[str, Any]:
    organization = await db.get(Organization, organization_id)
    if not organization or organization.status != "active":
        raise HTTPException(status_code=404, detail="Active organization not found.")
    prefix = "unx2_" + secrets.token_hex(8)
    secret = secrets.token_urlsafe(32)
    credential = ApiCredential(
        id=str(uuid4()), organization_id=organization.id, label=payload.label,
        key_prefix=prefix, secret_hash=hashlib.sha256(secret.encode("utf-8")).hexdigest(),
        role=payload.role,
        expires_at=(datetime.now(timezone.utc) + timedelta(days=payload.expires_in_days)) if payload.expires_in_days else None,
    )
    db.add(credential)
    await _audit(db, organization.id, "platform-admin", "api_key.created", "api_credential", credential.id, f"role={payload.role}; label={payload.label}")
    await db.commit()
    return {
        "credential_id": credential.id,
        "organization_id": organization.id,
        "label": credential.label,
        "role": credential.role,
        "expires_at": credential.expires_at.isoformat() if credential.expires_at else None,
        "api_key": f"{prefix}.{secret}",
        "warning": "Copy this key now. Its secret is stored only as a hash and cannot be retrieved later.",
    }


@router.get("/me")
async def tenant_identity(
    principal: TenantPrincipal = Depends(require_tenant),
    db: AsyncSession = Depends(get_security_db),
) -> dict[str, Any]:
    organization = await db.get(Organization, principal.organization_id)
    await _audit(db, principal.organization_id, principal.credential_id, "tenant.identity.read", "organization", principal.organization_id)
    await db.commit()
    return {
        "organization": {"id": organization.id, "name": organization.name, "slug": organization.slug},
        "credential_id": principal.credential_id,
        "role": principal.role,
        "scopes": principal.scopes,
    }


@router.get("/audit-events")
async def tenant_audit_events(
    limit: int = 100,
    principal: TenantPrincipal = Depends(require_tenant),
    db: AsyncSession = Depends(get_security_db),
) -> dict[str, Any]:
    if principal.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Organization administrator role required.")
    bounded_limit = max(1, min(limit, 500))
    result = await db.execute(
        select(AuditEvent)
        .where(AuditEvent.organization_id == principal.organization_id)
        .order_by(AuditEvent.created_at.desc())
        .limit(bounded_limit)
    )
    events = result.scalars().all()
    return {"count": len(events), "items": [{
        "id": event.id, "actor_id": event.actor_id, "action": event.action,
        "resource_type": event.resource_type, "resource_id": event.resource_id,
        "outcome": event.outcome, "detail": event.detail,
        "created_at": event.created_at.isoformat(),
    } for event in events]}
