import { createBrowserClient } from '@supabase/ssr'
import type { SupabaseClient } from '@supabase/supabase-js'
import { getSupabaseEnv } from './config'

let browserClient: SupabaseClient | null = null

export function createClient() {
  if (browserClient) return browserClient

  const { url, anonKey } = getSupabaseEnv()
  browserClient = createBrowserClient(url, anonKey)
  return browserClient
}
