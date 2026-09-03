-- 004: share-credits, referrals, Lifetime Plus plan. Run after 003. Idempotent.

-- ── Credits on the account ──────────────────────────────────────────────────
alter table public.user_flags add column if not exists credits int not null default 0;
alter table public.user_flags add column if not exists referral_code text unique;

-- Everyone gets a row + a referral code on first touch (function below creates
-- lazily). Referral log: who invited whom, credited once.
create table if not exists public.referrals (
  id uuid primary key default gen_random_uuid(),
  referrer_user_id uuid not null references auth.users(id) on delete cascade,
  referred_user_id uuid not null unique references auth.users(id) on delete cascade,
  created_at timestamptz not null default now()
);
alter table public.referrals enable row level security;
drop policy if exists "own referrals select" on public.referrals;
create policy "own referrals select" on public.referrals
  for select using (auth.uid() = referrer_user_id or auth.uid() = referred_user_id);
-- inserts only via the security-definer RPC below.

-- ── New plan tier: Lifetime Plus ────────────────────────────────────────────
alter table public.subscription_requests drop constraint if exists subscription_requests_plan_check;
alter table public.subscription_requests add constraint subscription_requests_plan_check
  check (plan in ('monthly_basic','monthly_plus','lifetime','lifetime_plus'));

-- ── RPC: ensure my flags row + referral code; returns my account state ──────
create or replace function public.my_account()
returns table (plan text, is_premium boolean, credits int, referral_code text)
language plpgsql security definer as $$
begin
  insert into public.user_flags (user_id, referral_code)
  values (auth.uid(), substr(md5(auth.uid()::text || 'jyotish-salt'), 1, 8))
  on conflict (user_id) do update
    set referral_code = coalesce(public.user_flags.referral_code,
                                 substr(md5(auth.uid()::text || 'jyotish-salt'), 1, 8));
  return query
    select uf.plan, uf.is_premium, uf.credits, uf.referral_code
    from public.user_flags uf where uf.user_id = auth.uid();
end $$;

-- ── RPC: claim a referral (called once by the REFERRED user after sign-in).
--    Credits the REFERRER with 1 credit; the new user gets 1 welcome credit. ──
create or replace function public.claim_referral(code text)
returns boolean language plpgsql security definer as $$
declare
  ref_user uuid;
begin
  if auth.uid() is null then return false; end if;
  select user_id into ref_user from public.user_flags
    where referral_code = code and user_id <> auth.uid();
  if ref_user is null then return false; end if;
  if exists (select 1 from public.referrals where referred_user_id = auth.uid()) then
    return false;  -- already claimed once
  end if;
  insert into public.referrals (referrer_user_id, referred_user_id)
    values (ref_user, auth.uid());
  update public.user_flags set credits = credits + 1 where user_id = ref_user;
  insert into public.user_flags (user_id, credits) values (auth.uid(), 1)
    on conflict (user_id) do update set credits = public.user_flags.credits + 1;
  return true;
end $$;

-- ── RPC: spend one credit (pays for one AI assistant question on free plans) ─
create or replace function public.spend_credit()
returns boolean language plpgsql security definer as $$
declare ok boolean := false;
begin
  update public.user_flags set credits = credits - 1
    where user_id = auth.uid() and credits > 0
    returning true into ok;
  return coalesce(ok, false);
end $$;
