-- Runtime tables for 3-panel chat UI:
-- 1) left panel agent list (API-backed)
-- 2) center panel user chat (conversations/messages)
-- 3) right panel live agent events and history

create extension if not exists pgcrypto;

-- Base chat tables (required by routers/conversations.py)
create table if not exists public.conversations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid null references auth.users(id) on delete cascade,
  guest_id text null,
  title text not null default 'New Conversation',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint conversations_owner_identity_check check (user_id is not null or guest_id is not null)
);

create table if not exists public.messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references public.conversations(id) on delete cascade,
  role text not null check (role in ('user', 'assistant', 'system')),
  content text not null,
  message_type text not null default 'followup',
  metadata jsonb null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_conversations_user_updated_at
  on public.conversations(user_id, updated_at desc);

create index if not exists idx_conversations_guest_updated_at
  on public.conversations(guest_id, updated_at desc)
  where guest_id is not null;

create index if not exists idx_messages_conversation_created_at
  on public.messages(conversation_id, created_at);

create table if not exists public.conversation_states (
  conversation_id uuid primary key references public.conversations(id) on delete cascade,
  mode text not null default 'autonomous' check (mode in ('interactive', 'autonomous')),
  current_step text not null default 'idle',
  pipeline_status text not null default 'idle',
  pending_prompt text null,
  required_metadata jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);

create table if not exists public.agent_events (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references public.conversations(id) on delete cascade,
  agent_name text not null,
  status text not null,
  content text null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_agent_events_conversation_created_at
  on public.agent_events(conversation_id, created_at);

alter table public.conversation_states enable row level security;
alter table public.agent_events enable row level security;
alter table public.conversations enable row level security;
alter table public.messages enable row level security;

-- Ensure required_metadata exists for projects created before this column.
alter table public.conversation_states
  add column if not exists required_metadata jsonb not null default '{}'::jsonb;

-- Example RLS policies (adjust if your project already has policy conventions):
do $$
begin
  if not exists (
    select 1
    from pg_policies
    where schemaname = 'public'
      and tablename = 'conversations'
      and policyname = 'conversations_owner_select'
  ) then
    create policy conversations_owner_select
      on public.conversations
      for select
      using (user_id = auth.uid());
  end if;
end $$;

do $$
begin
  if not exists (
    select 1
    from pg_policies
    where schemaname = 'public'
      and tablename = 'conversations'
      and policyname = 'conversations_owner_insert'
  ) then
    create policy conversations_owner_insert
      on public.conversations
      for insert
      with check (user_id = auth.uid());
  end if;
end $$;

do $$
begin
  if not exists (
    select 1
    from pg_policies
    where schemaname = 'public'
      and tablename = 'conversations'
      and policyname = 'conversations_owner_update'
  ) then
    create policy conversations_owner_update
      on public.conversations
      for update
      using (user_id = auth.uid())
      with check (user_id = auth.uid());
  end if;
end $$;

do $$
begin
  if not exists (
    select 1
    from pg_policies
    where schemaname = 'public'
      and tablename = 'conversations'
      and policyname = 'conversations_owner_delete'
  ) then
    create policy conversations_owner_delete
      on public.conversations
      for delete
      using (user_id = auth.uid());
  end if;
end $$;

do $$
begin
  if not exists (
    select 1
    from pg_policies
    where schemaname = 'public'
      and tablename = 'messages'
      and policyname = 'messages_owner_select'
  ) then
    create policy messages_owner_select
      on public.messages
      for select
      using (
        exists (
          select 1
          from public.conversations c
          where c.id = conversation_id
            and c.user_id = auth.uid()
        )
      );
  end if;
end $$;

do $$
begin
  if not exists (
    select 1
    from pg_policies
    where schemaname = 'public'
      and tablename = 'messages'
      and policyname = 'messages_owner_insert'
  ) then
    create policy messages_owner_insert
      on public.messages
      for insert
      with check (
        exists (
          select 1
          from public.conversations c
          where c.id = conversation_id
            and c.user_id = auth.uid()
        )
      );
  end if;
end $$;

do $$
begin
  if not exists (
    select 1
    from pg_policies
    where schemaname = 'public'
      and tablename = 'conversation_states'
      and policyname = 'conversation_states_owner_read'
  ) then
    create policy conversation_states_owner_read
      on public.conversation_states
      for select
      using (
        exists (
          select 1
          from public.conversations c
          where c.id = conversation_id
            and c.user_id = auth.uid()
        )
      );
  end if;
end $$;

do $$
begin
  if not exists (
    select 1
    from pg_policies
    where schemaname = 'public'
      and tablename = 'agent_events'
      and policyname = 'agent_events_owner_read'
  ) then
    create policy agent_events_owner_read
      on public.agent_events
      for select
      using (
        exists (
          select 1
          from public.conversations c
          where c.id = conversation_id
            and c.user_id = auth.uid()
        )
      );
  end if;
end $$;
