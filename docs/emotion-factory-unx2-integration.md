# EMOTION FACTORY × UNX2 — Integration Blueprint

**Status:** Architecture decision / implementation blueprint  
**Parent platform:** UNX2 (NeuraX Ultime Core)  
**Commercial product:** EMOTION FACTORY  
**Owner / decision authority:** Founder and creative director

## 1. Product boundary

EMOTION FACTORY is an independently branded commercial workspace running on UNX2 infrastructure. It is not a separate identity, billing, memory, or agent platform.

- UNX2 owns shared infrastructure: authentication, tenant isolation, roles, AI routing, agent orchestration, memory, event bus, observability, integrations, and policy enforcement.
- EMOTION FACTORY owns its brand experience, service catalog, customer-facing workflows, campaign assets, proposals, projects, and commercial reporting.
- The architecture must allow future commercial brands to reuse UNX2 without sharing customer data.

## 2. Logical architecture

```
UNX2 CORE
  Identity & Tenant Registry
  RBAC / Policy & Approval Gateway
  AI Router (provider-agnostic)
  Agent Orchestrator
  Memory Fabric (tenant-scoped)
  Event Bus + WebSocket Telemetry
  Integration Registry + Secrets Vault
  Audit Log + Usage / Billing Metering
          |
          +-- EMOTION FACTORY tenant / workspace
                Sales & Lead Qualification
                Creative Brief & Proposal
                Campaign Studio
                Music / Video Production Queue
                Project Delivery & Client Portal
                CRM & Follow-up
                Quotes / Invoices / Payment Status
                Analytics & Brand Reporting
```

## 3. Tenant and data isolation

- Give EMOTION FACTORY its own organization/tenant identifier and brand configuration.
- Every business record must carry tenant_id and be protected by database-level row security where supported.
- Keep contacts, briefs, files, campaign data, invoices, agent memory, embeddings, and telemetry tenant-scoped.
- Shared templates and public service definitions may be global; customer-specific content must never be global.
- Enforce role-based access: Founder/Owner, Creative Operator, Sales Operator, Production Operator, Finance Operator, Client.
- Never place provider API keys in browser code, prompts, logs, or client-visible configuration. Use server-side secret storage.

## 4. Core workflow

1. Lead arrives through a website form, referral, or manually entered contact.
2. UNX2 validates consent and records the lead in the EMOTION FACTORY CRM.
3. Sales agent enriches only from permitted sources, scores fit, and drafts a personalized first response.
4. Brief agent structures goals, audience, deliverables, schedule, and budget.
5. Proposal agent drafts scope, pricing, assumptions, and terms.
6. Founder reviews and approves proposal and any external communication.
7. Client accepts; the system creates a project and prepares an invoice/payment link.
8. Production agents draft copy, visual directions, scripts, music briefs, and video plans.
9. Founder approves creative deliverables and publication.
10. Delivery, client feedback, follow-up, and performance reporting are tracked.

## 5. Human approval policy

The system may automate internal preparation, classification, drafting, reminders, and status updates. Explicit approval is required before:
- sending external sales or marketing messages;
- issuing or accepting contracts and binding commitments;
- charging a payment method, refunding, or incurring paid expenses;
- launching paid advertising;
- publishing content under a client's name;
- delivering final creative work as approved.

Record who approved what, when, and which version was approved. Provide pause, revoke, and emergency-stop controls.

## 6. Initial service modules

- Emotion Ads: advertising concepts, copy, campaign packages.
- Emotion Identity: brand narrative, visual direction, sonic identity.
- Emotion Experience: interactive campaigns and digital experiences.
- Music and Video: briefs, scripts, production coordination, review queues.
- Client Operations: CRM, project tracking, delivery, follow-up.
- Finance Operations: estimates, invoices, payment reconciliation, revenue reporting.

Start with human-reviewed drafts and workflow automation. Do not claim AI can autonomously produce professional final video/music unless the relevant generation and editing providers are connected and tested.

## 7. Canonical data entities

Organization/Tenant, User, Role, Client, Contact, ConsentRecord, Lead, Opportunity, Service, PriceBook, Brief, Proposal, Approval, Project, Task, Asset, AssetVersion, Campaign, Invoice, Payment, IntegrationConnection, AgentRun, Event, AuditEntry.

All tenant-owned entities include tenant_id, created_at, updated_at, and appropriate ownership/access metadata. Financial records should retain immutable status history.

## 8. Event-driven automation

Suggested events:
- lead.created
- lead.qualified
- brief.ready
- proposal.drafted
- approval.requested
- approval.granted / approval.rejected
- proposal.accepted
- invoice.issued
- payment.confirmed
- project.started
- asset.review_requested
- asset.approved
- delivery.completed
- followup.due

Use idempotency keys for payment and webhook handlers. Retry transient failures safely; route permanent failures to a visible exception queue. Every workflow needs an owner, status, timestamp, and audit trail.

## 9. Integrations (connect only after explicit authorization)

CRM: HubSpot, Zoho, or UNX2 native CRM.  
Payments: Stripe.  
Email/calendar: provider connector selected by founder.  
Automation: UNX2 Event Bus first; Make/n8n as optional external orchestrators.  
AI: provider-agnostic UNX2 AI Router (OpenAI, Gemini, Claude where configured).  
Creative tools: image, audio, video generation/editing providers selected and tested individually.

Store credentials server-side and show connection health without exposing secrets. A disconnected integration must degrade gracefully.

## 10. Quebec / Canada compliance baseline

Design for Quebec Law 25 privacy principles and Canadian anti-spam requirements (CASL): collect only necessary personal information, document purposes and consent, provide access/correction/deletion workflows, maintain retention rules, protect exports, and include unsubscribe handling for commercial electronic messages. Obtain qualified legal review before production launch.

## 11. Delivery phases

**Phase 0 — Foundation:** confirm repository structure and existing UNX2 contracts; define tenant, roles, policy, and event schemas.  
**Phase 1 — Commercial MVP:** EMOTION FACTORY workspace, service catalog, lead intake, CRM pipeline, brief/proposal drafts, approval queue, project board.  
**Phase 2 — Revenue operations:** quotes, invoices, Stripe test-mode integration, payment webhooks, audit trail.  
**Phase 3 — Creative operations:** asset library/versioning, copy and creative brief agents, music/video production queue, client review portal.  
**Phase 4 — Controlled automation:** consent-aware follow-ups, scheduled workflows, analytics, failure queue, operational monitoring.  
**Phase 5 — Multi-brand expansion:** reusable brand/tenant provisioning and isolated workspaces for future UNX2 businesses.

## 12. Definition of done for MVP

- EMOTION FACTORY is visually independent but authenticates through UNX2.
- Tenant isolation tests prove one workspace cannot read another's data.
- Every external action is gated by policy and recorded in the audit log.
- Leads can move through qualification, brief, proposal, approval, project, and delivery.
- AI outputs are drafts with provenance and editable versions.
- Stripe remains in test mode until explicitly approved for production.
- No integration is represented as connected until credentials, health checks, and end-to-end tests pass.
