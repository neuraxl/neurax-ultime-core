# EMOTION FACTORY — Commercial Management Center on UNX2

## Product objective

Evolve the existing tenant-scoped CRM MVP into a commercial operating system for EMOTION FACTORY. The current CRM remains the starting point; the existing Aedes MQTT broker remains untouched.

## End-to-end business lifecycle

1. Lead capture and qualification.
2. Contact and customer account creation (a contact is a person; a customer is the commercial account).
3. AI-assisted discovery and creative brief.
4. Proposal generation and internal approval.
5. Quote creation, versioning, expiry, and customer acceptance.
6. Contract drafting, review, signature status, and renewal tracking.
7. Creative project delivery with client review, approval, or revision request.
8. Invoice issuance, payment tracking, Stripe reconciliation, and revenue reporting.
9. Renewal, upsell, referral, and post-delivery follow-up.

## Functional domains

### 1. Customers and contracts
- Customer accounts linked to one or more contacts.
- Billing identity, billing address, tax identifiers where applicable, preferred currency, payment terms, and internal account owner.
- Contracts with reference number, scope, deliverables, dates, amount, currency, status, renewal date, document reference, and approval history.
- Contract states: draft, pending_internal_approval, pending_customer_signature, active, completed, cancelled, expired.
- Do not represent an electronic signature as legally executed unless a qualified signature provider has confirmed it.

### 2. Quotes, proposals, and invoicing
- Reusable catalogue of services and packages (Emotion Ads, Emotion Identity, Emotion Experience).
- Quotes with immutable numbered revisions, line items, quantities, unit prices, discounts, tax lines, currency, validity date, and acceptance status.
- Proposals with editable narrative sections, objectives, strategy, creative direction, deliverables, schedule, investment, assumptions, and exclusions.
- Invoices generated from accepted quotes or contract milestones; sequential numbering must be configurable per legal entity and jurisdiction.
- Credit notes, partial payments, overdue tracking, and reconciliation.
- Store monetary values as integer minor units (for CAD, cents); never use floating point for accounting calculations.
- Tax calculations must be configurable and reviewed for the actual business jurisdiction; do not hardcode a universal tax rate.

### 3. AI sales and creative agents
- Sales agent: lead research from supplied/authorized data, qualification suggestions, next-best-action, call/email draft, follow-up reminders.
- Strategy agent: discovery synthesis, positioning, campaign concept, audience hypotheses, measurable objectives.
- Creative agent: creative brief, concepts, copy variants, storyboard, production checklist.
- Proposal agent: builds a proposal draft from approved customer data, service catalogue, quote, and brief.
- Finance assistant: explains pipeline and receivables, flags anomalies, drafts reminders; it cannot change books or initiate money movement.
- Agent execution is provider-agnostic through the UNX2 AI Router. No model provider is assumed connected.
- Every agent run records tenant, actor, agent/version, input references, output, status, and approval requirement. Minimize personal data sent to providers.

### 4. Stripe and revenue
- **Decision for launch: one Stripe account owned by EMOTION FACTORY.** EMOTION FACTORY sells its own services and collects its own invoices; this is the simplest operating and reconciliation model.
- Do not use Stripe Connect at launch. Introduce Connect only if UNX2 later enables independent tenant businesses to sell to their own customers and receive payouts through the platform.
- Keep the payment layer provider-abstracted so Connect can be added later without redesigning invoices, customers, or payment records.
- Use hosted Checkout / Billing Portal where suitable; verify webhook signatures; process events idempotently; never store card numbers or CVC.
- Keep internal invoices and payments as the accounting source of record; Stripe events are payment evidence and reconciliation inputs.
- Separate quote value, invoiced revenue, collected cash, refunds, taxes, and recurring revenue.
- Stripe is not connected by this change. API keys, webhook secret, account account, and test/live mode must be configured explicitly before enabling payments.

### 5. Client portal and creative approvals
- Separate customer identity from staff identity; customer access is invitation-based and scoped to that customer's records only.
- Portal: proposals, quotes, contracts, invoices, payment status, project milestones, creative previews, comments, and revision requests.
- Approval request records the exact asset/version, reviewer, decision, timestamp, and comment.
- States: pending, approved, changes_requested, rejected, withdrawn.
- Approval is version-specific; a changed asset requires a new approval request.
- No public file URLs for confidential creative assets; use expiring signed links and access checks.

## Cross-cutting architecture

- Continue FastAPI + PostgreSQL + Redis + existing MQTT.
- Add domain services and routers rather than putting all logic in the existing CRM router.
- Every tenant-owned table includes tenant_id, with tenant-scoped foreign-key validation.
- Add Alembic migrations before expanding production data; the existing create_all bootstrap is development-only.
- Implement PostgreSQL row-level security and automated cross-tenant isolation tests before production.
- Add granular RBAC: owner, admin, sales, creative, finance, customer.
- Add immutable audit events for approvals, quote/contract changes, invoice issuance, payments, refunds, and access-sensitive actions.
- Store files in private object storage, with metadata in PostgreSQL.
- Use an outbox/webhook event pattern for reliable external integrations; background jobs in Redis are not a substitute for idempotency.
- All external actions require explicit authorization and auditable approval: sending proposals/contracts, publishing campaigns, charging/refunding, and sending client communications.

## Recommended implementation sequence

### Phase 0 — Security and domain foundation (first)
- Alembic migrations and migration-based startup.
- PostgreSQL RLS and tenant-isolation tests.
- RBAC and audit log.
- Customer/contact domain separation and currency/tax settings.

### Phase 1 — Commercial records
- Customers, contracts, service catalogue.
- Quotes with line items and version history.
- Proposal drafts and approval workflow.
- Invoices, payment records, receivables, and revenue dashboard (manual payment recording initially).

### Phase 2 — Client portal
- Customer invitation and authentication.
- Customer-scoped quote/proposal/contract/invoice views.
- Versioned creative approval and revision loop.

### Phase 3 — AI workbench
- Agent registry and run history.
- Sales, strategy, creative, proposal, and finance assistants via the existing UNX2 AI Router.
- Human review queue; no autonomous external send or financial action.

### Phase 4 — Stripe and automation
- Choose Stripe account model (single account or Connect).
- Stripe test mode, signed webhooks, idempotency, reconciliation, refunds approval.
- Revenue reports and recurring billing only after finance/legal review.

## Definition of done for production

- Migration from a clean database and from the current MVP database succeeds.
- Automated tests prove cross-tenant reads/writes and customer-portal isolation are denied.
- RBAC and audit coverage for sensitive actions.
- Backups and restore test, TLS, secrets manager, monitoring, rate limits, retention/export/deletion workflows.
- Stripe webhook signature and replay tests in test mode.
- No live payments or customer data until security, tax, privacy, contract, and operational reviews are complete.

## Explicit non-claims

This plan does not mean Stripe, an e-signature provider, email, file storage, AI model providers, or a production deployment are connected. Those integrations must be configured and tested separately.
