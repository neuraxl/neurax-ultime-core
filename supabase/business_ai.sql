create table if not exists public.business_diagnostics (
id uuid primary key default gen_random_uuid(),company text not null,sector text not null,city text,website text,email text not null,problem text not null,customers text,diagnostic jsonb not null,created_at timestamptz not null default now());
create table if not exists public.business_events (
id uuid primary key default gen_random_uuid(),event text not null,source text,received_at timestamptz not null default now(),payload jsonb);
alter table public.business_diagnostics enable row level security;
alter table public.business_events enable row level security;
-- Les écritures applicatives utilisent la clé service côté serveur uniquement.