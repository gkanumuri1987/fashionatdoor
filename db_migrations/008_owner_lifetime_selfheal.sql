-- 008_owner_lifetime_selfheal.sql
-- Makes the owner's Lifetime Plus entitlement SELF-HEALING at the server.
--
-- Migration 006 granted it once, but only for accounts that existed when it ran
-- (an owner who signed up later stayed on 'free'). This redefines my_account()
-- so that every time the owner loads their account, their flags are ensured to
-- be Lifetime Plus — no dependency on running a one-time grant at the right
-- moment. Idempotent; safe to re-run. (The frontend also recognises the owner
-- immediately; this keeps the DB — the source of truth for server-side gating —
-- correct too.)

create or replace function public.my_account()
returns table (plan text, is_premium boolean, credits int, referral_code text)
language plpgsql security definer set search_path = public, pg_temp as $$
declare
  _email text;
begin
  -- ensure a flags row + referral code exist
  insert into public.user_flags (user_id, referral_code)
  values (auth.uid(), substr(md5(auth.uid()::text || 'jyotish-salt'), 1, 8))
  on conflict (user_id) do update
    set referral_code = coalesce(public.user_flags.referral_code,
                                 substr(md5(auth.uid()::text || 'jyotish-salt'), 1, 8));

  -- self-heal the owner to Lifetime Plus
  select lower(email) into _email from auth.users where id = auth.uid();
  if _email = 'kanumuri.choudary@gmail.com' then
    update public.user_flags
       set is_premium = true, plan = 'lifetime_plus',
           plan_started_at = coalesce(plan_started_at, now()),
           plan_expires_at = null
     where user_id = auth.uid();
  end if;

  return query
    select uf.plan, uf.is_premium, uf.credits, uf.referral_code
    from public.user_flags uf where uf.user_id = auth.uid();
end $$;
