-- Guest mode support for backend conversation routes
-- Apply this once in Supabase SQL editor before using backend guest mode.

begin;

alter table public.conversations
  add column if not exists guest_id text null;

-- Allow guest conversations without auth.users foreign key user_id.
alter table public.conversations
  alter column user_id drop not null;

-- Ensure at least one owner identity exists.
do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'conversations_owner_identity_check'
      and conrelid = 'public.conversations'::regclass
  ) then
    alter table public.conversations
      add constraint conversations_owner_identity_check
      check (user_id is not null or guest_id is not null);
  end if;
end $$;

create index if not exists idx_conversations_guest_updated_at
  on public.conversations(guest_id, updated_at desc)
  where guest_id is not null;

commit;

