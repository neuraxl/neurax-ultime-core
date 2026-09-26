create table if not exists public.profiles (
 id uuid primary key references auth.users(id) on delete cascade,
 full_name text, role text not null default 'client' check (role in ('client','manager','admin')), created_at timestamptz not null default now()
);
create table if not exists public.business_diagnostics (
 id uuid primary key default gen_random_uuid(), user_id uuid references auth.users(id) on delete set null,
 company text not null, sector text not null, city text, website text, email text not null, problem text not null, customers text, diagnostic jsonb not null, created_at timestamptz not null default now()
);
create table if not exists public.leads (
 id uuid primary key default gen_random_uuid(), user_id uuid references auth.users(id) on delete set null,
 company text not null, email text not null, sector text, status text not null default 'new' check (status in ('new','qualified','proposal','won','lost')), source text not null default 'business-ai', created_at timestamptz not null default now()
);
create table if not exists public.payments (
 id uuid primary key default gen_random_uuid(), stripe_event_id text unique not null, stripe_session_id text unique, email text, amount_cents integer, currency text, status text, payload jsonb, created_at timestamptz not null default now()
);
create table if not exists public.business_events (
 id uuid primary key default gen_random_uuid(), event text not null, source text, received_at timestamptz not null default now(), payload jsonb
);
alter table public.profiles enable row level security;
alter table public.business_diagnostics enable row level security;
alter table public.leads enable row level security;
alter table public.payments enable row level security;
alter table public.business_events enable row level security;

create or replace function public.is_business_admin() returns boolean language sql stable security definer set search_path=public as $$
 select exists(select 1 from public.profiles where id=auth.uid() and role in ('admin','manager'));
$$;

revoke all on table public.profiles, public.business_diagnostics, public.leads, public.payments, public.business_events from anon;
grant select,insert,update on public.profiles to authenticated;
grant select,insert on public.business_diagnostics to authenticated;
grant select,insert,update on public.leads to authenticated;
grant select on public.payments to authenticated;
grant select on public.business_events to authenticated;

create policy "profile own" on public.profiles for select to authenticated using (id=auth.uid());
create policy "diagnostics own read" on public.business_diagnostics for select to authenticated using (user_id=auth.uid() or public.is_business_admin());
create policy "diagnostics own insert" on public.business_diagnostics for insert to authenticated with check (user_id=auth.uid());
create policy "leads admin read" on public.leads for select to authenticated using (user_id=auth.uid() or public.is_business_admin());
create policy "leads own insert" on public.leads for insert to authenticated with check (user_id=auth.uid());
create policy "leads admin update" on public.leads for update to authenticated using (public.is_business_admin()) with check (public.is_business_admin());
create policy "payments admin read" on public.payments for select to authenticated using (public.is_business_admin());
create policy "events admin read" on public.business_events for select to authenticated using (public.is_business_admin());

create or replace function public.handle_new_business_user() returns trigger language plpgsql security definer set search_path=public as $$
begin insert into public.profiles(id,full_name) values(new.id,coalesce(new.raw_user_meta_data->>'full_name','')) on conflict(id) do nothing; return new; end; $$;
drop trigger if exists on_auth_user_created_business on auth.users;
create trigger on_auth_user_created_business after insert on auth.users for each row execute procedure public.handle_new_business_user();
