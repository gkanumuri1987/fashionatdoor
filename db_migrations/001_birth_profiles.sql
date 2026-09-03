-- 001: saved birth profiles, per-user via RLS.
-- Run in the Supabase SQL editor (Dashboard → SQL → New query → paste → Run).
-- Idempotent: safe to re-run.

create table if not exists public.birth_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null default '',
  relation text not null default 'self',        -- self | family | friend | client
  birth_date date not null,
  birth_time time not null,
  time_accuracy text not null default 'exact' check (time_accuracy in ('exact','approximate','unknown')),
  place_name text not null default '',
  lat double precision not null,
  lng double precision not null,
  tz text,
  ayanamsa text not null default 'lahiri',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.birth_profiles enable row level security;

drop policy if exists "own profiles select" on public.birth_profiles;
create policy "own profiles select" on public.birth_profiles
  for select using (auth.uid() = user_id);

drop policy if exists "own profiles insert" on public.birth_profiles;
create policy "own profiles insert" on public.birth_profiles
  for insert with check (auth.uid() = user_id);

drop policy if exists "own profiles update" on public.birth_profiles;
create policy "own profiles update" on public.birth_profiles
  for update using (auth.uid() = user_id);

drop policy if exists "own profiles delete" on public.birth_profiles;
create policy "own profiles delete" on public.birth_profiles
  for delete using (auth.uid() = user_id);

create index if not exists birth_profiles_user_idx
  on public.birth_profiles (user_id, created_at desc);
