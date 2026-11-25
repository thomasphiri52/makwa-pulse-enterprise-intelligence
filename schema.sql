create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  role text not null default 'analyst'
    check (role in ('platform_admin','operations_manager','engineer','analyst','viewer')),
  active boolean not null default true,
  created_at timestamptz not null default now()
);
create table if not exists public.services (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  environment text not null default 'development'
    check (environment in ('development','staging','production')),
  status text not null default 'unknown'
    check (status in ('unknown','healthy','degraded','outage')),
  owner_team text, description text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create table if not exists public.incidents (
  id uuid primary key default gen_random_uuid(),
  title text not null, description text,
  priority text not null default 'medium'
    check (priority in ('low','medium','high','critical')),
  status text not null default 'open'
    check (status in ('open','investigating','pending','resolved','closed')),
  service_id uuid references public.services(id) on delete set null,
  created_by uuid references auth.users(id) on delete set null,
  assigned_to uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create table if not exists public.audit_logs (
  id uuid primary key default gen_random_uuid(),
  actor_id uuid references auth.users(id) on delete set null,
  action text not null, entity_type text, entity_id uuid,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists incidents_status_created_idx on public.incidents(status, created_at desc);
create index if not exists audit_logs_created_idx on public.audit_logs(created_at desc);

alter table public.profiles enable row level security;
alter table public.services enable row level security;
alter table public.incidents enable row level security;
alter table public.audit_logs enable row level security;

create policy "profile_read_self" on public.profiles
for select to authenticated using (id = auth.uid());

create policy "active_read_services" on public.services
for select to authenticated using (exists(
 select 1 from public.profiles p where p.id=auth.uid() and p.active=true
));
create policy "active_read_incidents" on public.incidents
for select to authenticated using (exists(
 select 1 from public.profiles p where p.id=auth.uid() and p.active=true
));
create policy "admin_read_audit" on public.audit_logs
for select to authenticated using (exists(
 select 1 from public.profiles p where p.id=auth.uid() and p.active=true and p.role='platform_admin'
));

create policy "manager_insert_services" on public.services
for insert to authenticated with check (exists(
 select 1 from public.profiles p where p.id=auth.uid() and p.active=true and p.role in ('platform_admin','operations_manager')
));
create policy "manager_update_services" on public.services
for update to authenticated using (exists(
 select 1 from public.profiles p where p.id=auth.uid() and p.active=true and p.role in ('platform_admin','operations_manager')
)) with check (exists(
 select 1 from public.profiles p where p.id=auth.uid() and p.active=true and p.role in ('platform_admin','operations_manager')
));
create policy "active_insert_incidents" on public.incidents
for insert to authenticated with check (
 created_by=auth.uid() and exists(select 1 from public.profiles p where p.id=auth.uid() and p.active=true)
);
create policy "manager_update_incidents" on public.incidents
for update to authenticated using (exists(
 select 1 from public.profiles p where p.id=auth.uid() and p.active=true and p.role in ('platform_admin','operations_manager')
)) with check (exists(
 select 1 from public.profiles p where p.id=auth.uid() and p.active=true and p.role in ('platform_admin','operations_manager')
));
create policy "active_insert_audit" on public.audit_logs
for insert to authenticated with check (
 actor_id=auth.uid() and exists(select 1 from public.profiles p where p.id=auth.uid() and p.active=true)
);

-- Create the first profile after creating the auth user in Supabase:
-- insert into public.profiles(id,display_name,role,active)
-- values ('AUTH_USER_UUID','Development Admin','platform_admin',true);
