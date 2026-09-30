-- backend/schema.sql
-- Run this in Supabase's SQL Editor (left sidebar -> SQL Editor -> New query)
-- BEFORE running the backend with real database.py -- these two tables
-- match exactly what database.py and models.py expect.

create table if not exists resources (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    resource_type text not null,
    location text not null,
    capacity integer not null,
    available boolean not null default true,
    created_at timestamptz not null default now()
);

create table if not exists emergency_requests (
    id uuid primary key default gen_random_uuid(),
    location text not null,
    request_type text not null,
    people_affected integer not null,
    severity text not null check (severity in ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    description text,
    status text not null default 'PENDING' check (status in ('PENDING', 'ASSIGNED', 'RESOLVED')),
    assigned_resource_id uuid references resources(id),
    created_at timestamptz not null default now()
);

-- Row Level Security: since we're using the publishable (anon) key from
-- the frontend/backend rather than a secret key, RLS policies control
-- what that key is actually allowed to do. For this class project, we
-- allow full read/write -- NOT what you'd want for a real production
-- system with sensitive data, but fine for a demo.
alter table resources enable row level security;
alter table emergency_requests enable row level security;

create policy "Allow all access for demo purposes" on resources
    for all using (true) with check (true);

create policy "Allow all access for demo purposes" on emergency_requests
    for all using (true) with check (true);
