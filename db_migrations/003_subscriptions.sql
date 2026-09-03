-- 003: subscription plans + per-user tracking. Run after 002. Idempotent.

-- Extend the premium flag into a real plan record.
alter table public.user_flags add column if not exists plan text not null default 'free';
alter table public.user_flags add column if not exists plan_started_at timestamptz;
alter table public.user_flags add column if not exists plan_expires_at timestamptz;  -- null = lifetime/free

-- What a user CHOSE (pending until payment completes; billing webhook or the
-- admin flips it to 'active' via service_role and mirrors into user_flags).
create table if not exists public.subscription_requests (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  plan text not null check (plan in ('monthly_basic','monthly_plus','lifetime')),
  price_usd numeric(6,2) not null,
  period text not null check (period in ('monthly','lifetime')),
  status text not null default 'pending' check (status in ('pending','active','cancelled')),
  created_at timestamptz not null default now()
);
alter table public.subscription_requests enable row level security;

drop policy if exists "own subreq select" on public.subscription_requests;
create policy "own subreq select" on public.subscription_requests
  for select using (auth.uid() = user_id);
drop policy if exists "own subreq insert" on public.subscription_requests;
create policy "own subreq insert" on public.subscription_requests
  for insert with check (auth.uid() = user_id);

create index if not exists subreq_user_idx
  on public.subscription_requests (user_id, created_at desc);

-- Free-limit trigger update: premium = active plan OR legacy is_premium.
create or replace function public.enforce_profile_limit()
returns trigger language plpgsql security definer as $$
declare
  n int;
  premium boolean;
begin
  select count(*) into n from public.birth_profiles where user_id = new.user_id;
  select coalesce(uf.is_premium, false)
         or (uf.plan is not null and uf.plan <> 'free'
             and (uf.plan_expires_at is null or uf.plan_expires_at > now()))
    into premium
    from public.user_flags uf where uf.user_id = new.user_id;
  if n >= 1 and not coalesce(premium, false) then
    raise exception 'FREE_LIMIT_REACHED'
      using hint = 'Free accounts can save one jaathakam; subscribe for more.';
  end if;
  return new;
end $$;
