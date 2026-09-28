-- UNX2 Business OS v0.1 relational foundation
create extension if not exists pgcrypto;

create table if not exists organizations (
 id uuid primary key default gen_random_uuid(),
 name text not null,
 created_at timestamptz not null default now()
);
create table if not exists users (
 id uuid primary key,
 organization_id uuid references organizations(id) on delete cascade,
 email text not null,
 role text not null default 'member',
 created_at timestamptz not null default now()
);
create table if not exists agents (
 id uuid primary key default gen_random_uuid(),
 organization_id uuid references organizations(id) on delete cascade,
 name text not null,
 purpose text,
 status text not null default 'ready',
 created_at timestamptz not null default now()
);
create table if not exists workflows (
 id uuid primary key default gen_random_uuid(),
 organization_id uuid references organizations(id) on delete cascade,
 name text not null,
 definition jsonb not null default '{}'::jsonb,
 status text not null default 'draft',
 created_at timestamptz not null default now()
);
create table if not exists leads (
 id uuid primary key default gen_random_uuid(),
 organization_id uuid references organizations(id) on delete cascade,
 company_name text not null,
 score integer,
 status text not null default 'new',
 metadata jsonb not null default '{}'::jsonb,
 created_at timestamptz not null default now()
);
create table if not exists workflow_runs (
 id uuid primary key default gen_random_uuid(),
 organization_id uuid references organizations(id) on delete cascade,
 workflow_id uuid references workflows(id) on delete set null,
 status text not null,
 started_at timestamptz not null default now(),
 finished_at timestamptz,
 duration_ms integer,
 result jsonb not null default '{}'::jsonb
);
create table if not exists telemetry_events (
 id uuid primary key default gen_random_uuid(),
 organization_id uuid references organizations(id) on delete cascade,
 run_id uuid references workflow_runs(id) on delete cascade,
 event_type text not null,
 agent_name text,
 latency_ms integer,
 status text,
 payload jsonb not null default '{}'::jsonb,
 created_at timestamptz not null default now()
);
create table if not exists billing_events (
 id uuid primary key default gen_random_uuid(),
 organization_id uuid references organizations(id) on delete cascade,
 provider text not null,
 external_id text,
 event_type text not null,
 payload jsonb not null default '{}'::jsonb,
 created_at timestamptz not null default now()
);
create index if not exists telemetry_org_time on telemetry_events(organization_id,created_at desc);
create index if not exists leads_org_status on leads(organization_id,status);
create index if not exists workflow_runs_org_time on workflow_runs(organization_id,started_at desc);
