create extension if not exists pgcrypto;

create table if not exists public.custom_companies (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    company_id text not null,
    company_name text not null,
    workspace_json jsonb not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (user_id, company_id)
);

alter table public.custom_companies enable row level security;

drop policy if exists "Users can select their own custom companies"
    on public.custom_companies;
create policy "Users can select their own custom companies"
    on public.custom_companies
    for select
    using (auth.uid() = user_id);

drop policy if exists "Users can insert their own custom companies"
    on public.custom_companies;
create policy "Users can insert their own custom companies"
    on public.custom_companies
    for insert
    with check (auth.uid() = user_id);

drop policy if exists "Users can update their own custom companies"
    on public.custom_companies;
create policy "Users can update their own custom companies"
    on public.custom_companies
    for update
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

drop policy if exists "Users can delete their own custom companies"
    on public.custom_companies;
create policy "Users can delete their own custom companies"
    on public.custom_companies
    for delete
    using (auth.uid() = user_id);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists set_custom_companies_updated_at
    on public.custom_companies;
create trigger set_custom_companies_updated_at
    before update on public.custom_companies
    for each row
    execute function public.set_updated_at();
