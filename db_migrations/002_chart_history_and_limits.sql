-- 002: account-level chart history + free-tier saved-jaathakam limit.
-- Run in the Supabase SQL editor (after 001). Idempotent.

-- ── Every chart computed while signed in, stored to the account ─────────────
create table if not exists public.chart_history (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  person_name text not null default '',
  birth_date date not null,
  birth_time time not null,
  time_accuracy text not null default 'exact',
  place_name text not null default '',
  lat double precision not null,
  lng double precision not null,
  ayanamsa text not null default 'lahiri',
  lagna_sign text,
  moon_sign text,
  moon_nakshatra text,
  created_at timestamptz not null default now()
);

alter table public.chart_history enable row level security;

drop policy if exists "own history select" on public.chart_history;
create policy "own history select" on public.chart_history
  for select using (auth.uid() = user_id);
drop policy if exists "own history insert" on public.chart_history;
create policy "own history insert" on public.chart_history
  for insert with check (auth.uid() = user_id);
drop policy if exists "own history delete" on public.chart_history;
create policy "own history delete" on public.chart_history
  for delete using (auth.uid() = user_id);

create index if not exists chart_history_user_idx
  on public.chart_history (user_id, created_at desc);

-- ── Subscription flag (set via dashboard / future billing webhook) ──────────
create table if not exists public.user_flags (
  user_id uuid primary key references auth.users(id) on delete cascade,
  is_premium boolean not null default false,
  updated_at timestamptz not null default now()
);
alter table public.user_flags enable row level security;
drop policy if exists "own flags select" on public.user_flags;
create policy "own flags select" on public.user_flags
  for select using (auth.uid() = user_id);
-- no insert/update policy: only service_role (billing) writes this table.

-- ── Free-tier limit: max 1 SAVED jaathakam unless premium ──────────────────
create or replace function public.enforce_profile_limit()
returns trigger language plpgsql security definer as $$
declare
  n int;
  premium boolean;
begin
  select count(*) into n from public.birth_profiles where user_id = new.user_id;
  select coalesce(uf.is_premium, false) into premium
    from public.user_flags uf where uf.user_id = new.user_id;
  if n >= 1 and not coalesce(premium, false) then
    raise exception 'FREE_LIMIT_REACHED'
      using hint = 'Free accounts can save one jaathakam; subscribe for more.';
  end if;
  return new;
end $$;

drop trigger if exists birth_profiles_limit on public.birth_profiles;
create trigger birth_profiles_limit
  before insert on public.birth_profiles
  for each row execute function public.enforce_profile_limit();
