-- 005: login activity tracking. Run after 004. Idempotent.

alter table public.user_flags add column if not exists last_login_at timestamptz;
alter table public.user_flags add column if not exists login_count int not null default 0;

-- Per-login audit trail (last 90 days is plenty; prune later if desired).
create table if not exists public.login_activity (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  at timestamptz not null default now(),
  user_agent text
);
alter table public.login_activity enable row level security;
drop policy if exists "own login activity" on public.login_activity;
create policy "own login activity" on public.login_activity
  for select using (auth.uid() = user_id);

create index if not exists login_activity_user_idx
  on public.login_activity (user_id, at desc);

-- RPC the client calls once per sign-in: stamps last_login + count + a row.
create or replace function public.touch_login(ua text default null)
returns void language plpgsql security definer as $$
begin
  if auth.uid() is null then return; end if;
  insert into public.user_flags (user_id, last_login_at, login_count)
    values (auth.uid(), now(), 1)
    on conflict (user_id) do update
      set last_login_at = now(),
          login_count = public.user_flags.login_count + 1;
  insert into public.login_activity (user_id, user_agent) values (auth.uid(), ua);
end $$;
