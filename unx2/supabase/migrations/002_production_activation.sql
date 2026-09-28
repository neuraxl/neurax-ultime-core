-- UNX2 v0.2.1 — Production Activation
create table if not exists public.diagnostics (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  company_name text not null,
  operations text not null,
  result jsonb not null default '{}',
  created_at timestamptz not null default now()
);
create table if not exists public.subscriptions (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null unique references public.organizations(id) on delete cascade,
  stripe_customer_id text,
  stripe_subscription_id text unique,
  stripe_price_id text,
  status text not null default 'inactive',
  current_period_end timestamptz,
  cancel_at_period_end boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
alter table public.billing_events enable row level security;
alter table public.diagnostics enable row level security;
alter table public.subscriptions enable row level security;
alter table public.organizations enable row level security;
alter table public.profiles enable row level security;

drop policy if exists "users own profile" on public.profiles;
create policy "users own profile" on public.profiles
  for select to authenticated using ((select auth.uid()) = id);
drop policy if exists "members read organization" on public.organizations;
create policy "members read organization" on public.organizations
  for select to authenticated using (public.is_org_member(id));
drop policy if exists "org members diagnostics" on public.diagnostics;
create policy "org members diagnostics" on public.diagnostics
  for all to authenticated
  using (public.is_org_member(organization_id))
  with check (public.is_org_member(organization_id) and user_id = (select auth.uid()));
drop policy if exists "org members subscriptions" on public.subscriptions;
create policy "org members subscriptions" on public.subscriptions
  for select to authenticated using (public.is_org_member(organization_id));
drop policy if exists "org members billing events" on public.billing_events;
create policy "org members billing events" on public.billing_events
  for select to authenticated using (public.is_org_member(organization_id));

revoke insert, update, delete on public.billing_events from anon, authenticated;
revoke insert, update, delete on public.subscriptions from anon, authenticated;
grant select on public.organizations, public.profiles, public.agents, public.workflows,
  public.leads, public.workflow_runs, public.telemetry_events, public.diagnostics,
  public.subscriptions, public.billing_events to authenticated;
grant insert, update, delete on public.agents, public.workflows, public.leads,
  public.workflow_runs, public.telemetry_events, public.diagnostics to authenticated;

create index if not exists idx_profiles_org on public.profiles(organization_id);
create index if not exists idx_diagnostics_org_created on public.diagnostics(organization_id, created_at desc);
create index if not exists idx_billing_events_org_created on public.billing_events(organization_id, created_at desc);
create unique index if not exists idx_billing_events_provider_external
  on public.billing_events(provider, external_id) where external_id is not null;

create or replace function public.my_organization_id()
returns uuid language sql stable security definer set search_path=public
as $fn$ select organization_id from public.profiles where id = auth.uid() $fn$;
