-- 007_harden_definer_search_path.sql
-- Security hardening: pin search_path on every SECURITY DEFINER function.
--
-- A definer function runs with the owner's privileges. Without an explicit
-- search_path, a caller who can create objects in a schema earlier on their
-- search_path could shadow a referenced table/function and have the definer
-- run their version (the standard Supabase linter "Function Search Path
-- Mutable" warning / a privilege-escalation vector). Pinning to
-- `public, pg_temp` closes it. Idempotent — safe to re-run.

alter function public.enforce_profile_limit()            set search_path = public, pg_temp;
alter function public.my_account()                        set search_path = public, pg_temp;
alter function public.claim_referral(text)                set search_path = public, pg_temp;
alter function public.spend_credit()                      set search_path = public, pg_temp;
alter function public.touch_login(text)                   set search_path = public, pg_temp;
