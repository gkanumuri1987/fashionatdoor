-- 006: grant the owner Lifetime Plus. Run after 005.
-- kanumuri.choudary@gmail.com gets every feature free, forever.
insert into public.user_flags (user_id, is_premium, plan, plan_started_at)
select id, true, 'lifetime_plus', now()
from auth.users where lower(email) = 'kanumuri.choudary@gmail.com'
on conflict (user_id) do update
  set is_premium = true, plan = 'lifetime_plus',
      plan_started_at = coalesce(public.user_flags.plan_started_at, now()),
      plan_expires_at = null;
