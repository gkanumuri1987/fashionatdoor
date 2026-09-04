-- 009_signup_approval.sql
-- Owner-gated signups: every NEW account starts 'pending' and cannot generate
-- or save a kundli until the owner (kanumuri.choudary@gmail.com) approves it.
-- Existing users are grandfathered (approved). Run after 008. Idempotent.

-- 1) Approval status on the flags row.
alter table public.user_flags
  add column if not exists approval_status text not null default 'pending'
  check (approval_status in ('pending', 'approved', 'rejected'));

-- 2) Grandfather EVERY existing account (approve all current users). New signups
--    created after this migration default to 'pending' via the column default.
insert into public.user_flags (user_id, approval_status)
  select id, 'approved' from auth.users
  on conflict (user_id) do update set approval_status = 'approved';

-- 3) my_account() — now also returns approval_status, and self-heals the owner
--    to approved + Lifetime Plus. (Signature changes → drop + recreate.)
drop function if exists public.my_account();
create function public.my_account()
returns table (plan text, is_premium boolean, credits int, referral_code text,
               approval_status text)
language plpgsql security definer set search_path = public, pg_temp as $$
declare
  _email text;
begin
  insert into public.user_flags (user_id, referral_code)
  values (auth.uid(), substr(md5(auth.uid()::text || 'jyotish-salt'), 1, 8))
  on conflict (user_id) do update
    set referral_code = coalesce(public.user_flags.referral_code,
                                 substr(md5(auth.uid()::text || 'jyotish-salt'), 1, 8));

  select lower(email) into _email from auth.users where id = auth.uid();
  if _email = 'kanumuri.choudary@gmail.com' then
    update public.user_flags
       set is_premium = true, plan = 'lifetime_plus', plan_expires_at = null,
           approval_status = 'approved',
           plan_started_at = coalesce(plan_started_at, now())
     where user_id = auth.uid();
  end if;

  return query
    select uf.plan, uf.is_premium, uf.credits, uf.referral_code, uf.approval_status
    from public.user_flags uf where uf.user_id = auth.uid();
end $$;

-- 4) Owner-only: list accounts awaiting approval (email + when they joined).
create or replace function public.pending_signups()
returns table (user_id uuid, email text, created_at timestamptz)
language plpgsql security definer set search_path = public, pg_temp as $$
begin
  if (select lower(email) from auth.users where id = auth.uid())
     <> 'kanumuri.choudary@gmail.com' then
    return;  -- non-owner gets nothing
  end if;
  return query
    select u.id, u.email::text, u.created_at
    from auth.users u
    left join public.user_flags uf on uf.user_id = u.id
    where coalesce(uf.approval_status, 'pending') = 'pending'
    order by u.created_at desc;
end $$;

-- 5) Owner-only: approve / reject / reset an account.
create or replace function public.set_approval(target uuid, new_status text)
returns boolean language plpgsql security definer set search_path = public, pg_temp as $$
begin
  if (select lower(email) from auth.users where id = auth.uid())
     <> 'kanumuri.choudary@gmail.com' then
    return false;
  end if;
  if new_status not in ('approved', 'rejected', 'pending') then
    return false;
  end if;
  insert into public.user_flags (user_id, approval_status)
    values (target, new_status)
    on conflict (user_id) do update set approval_status = excluded.approval_status;
  return true;
end $$;

-- 6) Server-side backstop: block SAVING a jaathakam until approved (keeps the
--    existing free-tier limit too). SET search_path preserved (migration 007).
create or replace function public.enforce_profile_limit()
returns trigger language plpgsql security definer set search_path = public, pg_temp as $$
declare
  n int;
  premium boolean;
  status text;
begin
  select coalesce(uf.approval_status, 'pending'), coalesce(uf.is_premium, false)
    into status, premium
    from public.user_flags uf where uf.user_id = new.user_id;

  if coalesce(status, 'pending') <> 'approved' then
    raise exception 'NOT_APPROVED'
      using hint = 'Your account is awaiting administrator approval.';
  end if;

  select count(*) into n from public.birth_profiles where user_id = new.user_id;
  if n >= 1 and not coalesce(premium, false) then
    raise exception 'FREE_LIMIT_REACHED'
      using hint = 'Free accounts can save one jaathakam; subscribe for more.';
  end if;
  return new;
end $$;

-- 7) Owner-only: full registration list (for the in-app Admin tab) — every user
--    with their status + plan + join date, newest first.
create or replace function public.all_signups()
returns table (user_id uuid, email text, created_at timestamptz,
               approval_status text, plan text, is_premium boolean)
language plpgsql security definer set search_path = public, pg_temp as $$
begin
  if (select lower(email) from auth.users where id = auth.uid())
     <> 'kanumuri.choudary@gmail.com' then
    return;
  end if;
  return query
    select u.id, u.email::text, u.created_at,
           coalesce(uf.approval_status, 'pending'),
           coalesce(uf.plan, 'free'), coalesce(uf.is_premium, false)
    from auth.users u
    left join public.user_flags uf on uf.user_id = u.id
    order by u.created_at desc;
end $$;
