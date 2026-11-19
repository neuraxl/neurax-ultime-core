from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import current_user
from .db import get_db
from .models import Activity, Contact, Lead, User

router = APIRouter(prefix="/api/v1/crm", tags=["EMOTION FACTORY CRM"])
Db = Annotated[AsyncSession, Depends(get_db)]
Actor = Annotated[User, Depends(current_user)]


class ContactIn(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(default="", max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    company: str | None = Field(default=None, max_length=160)
    notes: str | None = None


class LeadIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    contact_id: str | None = None
    source: str | None = Field(default=None, max_length=80)
    status: str = "new"
    value_cents: int = Field(default=0, ge=0)
    notes: str | None = None


class ActivityIn(BaseModel):
    kind: str = Field(min_length=1, max_length=40)
    body: str = Field(min_length=1)
    lead_id: str | None = None
    contact_id: str | None = None
    due_at: datetime | None = None


def contact_out(c: Contact):
    return {"id": c.id, "first_name": c.first_name, "last_name": c.last_name,
            "email": c.email, "phone": c.phone, "company": c.company,
            "notes": c.notes, "created_at": c.created_at}


def lead_out(l: Lead):
    return {"id": l.id, "title": l.title, "contact_id": l.contact_id,
            "source": l.source, "status": l.status, "value_cents": l.value_cents,
            "notes": l.notes, "created_at": l.created_at}


@router.get("/dashboard")
async def dashboard(db: Db, user: Actor):
    tid = user.tenant_id
    contacts = await db.scalar(select(func.count()).select_from(Contact).where(Contact.tenant_id == tid))
    leads = await db.scalar(select(func.count()).select_from(Lead).where(Lead.tenant_id == tid))
    open_leads = await db.scalar(select(func.count()).select_from(Lead).where(
        Lead.tenant_id == tid, Lead.status.notin_(["won", "lost"])))
    pipeline = await db.scalar(select(func.coalesce(func.sum(Lead.value_cents), 0)).where(
        Lead.tenant_id == tid, Lead.status.notin_(["won", "lost"])))
    return {"contacts": contacts or 0, "leads": leads or 0,
            "open_leads": open_leads or 0, "pipeline_value_cents": pipeline or 0}


@router.get("/contacts")
async def list_contacts(db: Db, user: Actor, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    rows = await db.scalars(select(Contact).where(Contact.tenant_id == user.tenant_id)
                            .order_by(Contact.created_at.desc()).limit(limit).offset(offset))
    return [contact_out(c) for c in rows]


@router.post("/contacts", status_code=201)
async def create_contact(data: ContactIn, db: Db, user: Actor):
    c = Contact(tenant_id=user.tenant_id, **data.model_dump())
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return contact_out(c)


@router.get("/contacts/{contact_id}")
async def get_contact(contact_id: str, db: Db, user: Actor):
    c = await db.scalar(select(Contact).where(Contact.id == contact_id, Contact.tenant_id == user.tenant_id))
    if c is None:
        raise HTTPException(404, "Contact not found")
    return contact_out(c)


@router.patch("/contacts/{contact_id}")
async def update_contact(contact_id: str, data: ContactIn, db: Db, user: Actor):
    c = await db.scalar(select(Contact).where(Contact.id == contact_id, Contact.tenant_id == user.tenant_id))
    if c is None:
        raise HTTPException(404, "Contact not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(c, key, value)
    await db.commit()
    await db.refresh(c)
    return contact_out(c)


@router.delete("/contacts/{contact_id}", status_code=204)
async def delete_contact(contact_id: str, db: Db, user: Actor):
    c = await db.scalar(select(Contact).where(Contact.id == contact_id, Contact.tenant_id == user.tenant_id))
    if c is None:
        raise HTTPException(404, "Contact not found")
    await db.delete(c)
    await db.commit()


@router.get("/leads")
async def list_leads(db: Db, user: Actor, status: str | None = None,
                     limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    stmt = select(Lead).where(Lead.tenant_id == user.tenant_id)
    if status:
        stmt = stmt.where(Lead.status == status)
    rows = await db.scalars(stmt.order_by(Lead.created_at.desc()).limit(limit).offset(offset))
    return [lead_out(l) for l in rows]


@router.post("/leads", status_code=201)
async def create_lead(data: LeadIn, db: Db, user: Actor):
    if data.contact_id:
        contact = await db.scalar(select(Contact).where(
            Contact.id == data.contact_id, Contact.tenant_id == user.tenant_id))
        if contact is None:
            raise HTTPException(404, "Contact not found in this workspace")
    if data.status not in {"new", "qualified", "proposal", "won", "lost"}:
        raise HTTPException(422, "Invalid lead status")
    lead = Lead(tenant_id=user.tenant_id, **data.model_dump())
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return lead_out(lead)


@router.patch("/leads/{lead_id}")
async def update_lead(lead_id: str, data: LeadIn, db: Db, user: Actor):
    lead = await db.scalar(select(Lead).where(Lead.id == lead_id, Lead.tenant_id == user.tenant_id))
    if lead is None:
        raise HTTPException(404, "Lead not found")
    payload = data.model_dump(exclude_unset=True)
    if payload.get("status", lead.status) not in {"new", "qualified", "proposal", "won", "lost"}:
        raise HTTPException(422, "Invalid lead status")
    if payload.get("contact_id"):
        contact = await db.scalar(select(Contact).where(
            Contact.id == payload["contact_id"], Contact.tenant_id == user.tenant_id))
        if contact is None:
            raise HTTPException(404, "Contact not found in this workspace")
    for key, value in payload.items():
        setattr(lead, key, value)
    await db.commit()
    await db.refresh(lead)
    return lead_out(lead)


@router.post("/activities", status_code=201)
async def create_activity(data: ActivityIn, db: Db, user: Actor):
    if not data.lead_id and not data.contact_id:
        raise HTTPException(422, "An activity must be linked to a lead or contact")
    if data.lead_id and await db.scalar(select(Lead.id).where(
        Lead.id == data.lead_id, Lead.tenant_id == user.tenant_id)) is None:
        raise HTTPException(404, "Lead not found in this workspace")
    if data.contact_id and await db.scalar(select(Contact.id).where(
        Contact.id == data.contact_id, Contact.tenant_id == user.tenant_id)) is None:
        raise HTTPException(404, "Contact not found in this workspace")
    activity = Activity(tenant_id=user.tenant_id, **data.model_dump())
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    return {"id": activity.id, "kind": activity.kind, "body": activity.body,
            "lead_id": activity.lead_id, "contact_id": activity.contact_id,
            "due_at": activity.due_at, "completed": activity.completed,
            "created_at": activity.created_at}


@router.get("/activities")
async def list_activities(db: Db, user: Actor, limit: int = Query(50, ge=1, le=200)):
    rows = await db.scalars(select(Activity).where(Activity.tenant_id == user.tenant_id)
                            .order_by(Activity.created_at.desc()).limit(limit))
    return [{"id": a.id, "kind": a.kind, "body": a.body, "lead_id": a.lead_id,
             "contact_id": a.contact_id, "due_at": a.due_at, "completed": a.completed,
             "created_at": a.created_at} for a in rows]
