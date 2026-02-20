# db/supabase_client.py
from supabase import create_client, Client
from functools import lru_cache
from config.settings import settings


@lru_cache(maxsize=1)
def get_supabase_admin() -> Client:
    """
    Service-role Supabase client — bypasses Row Level Security.

    Use this for all server-side DB writes (inserting assistant messages,
    updating conversation titles, etc.).

    NEVER expose this client's credentials to the frontend or include
    the service role key in any API response.
    """
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


@lru_cache(maxsize=1)
def get_supabase_anon() -> Client:
    """
    Anon-key Supabase client — respects Row Level Security.

    Available for reads that should be scoped by RLS policies,
    when passing the user's JWT via the client's auth header.
    """
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
