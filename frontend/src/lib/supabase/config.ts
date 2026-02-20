const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL?.trim() ?? ''
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY?.trim() ?? ''
const guestModeRaw = process.env.NEXT_PUBLIC_GUEST_MODE?.trim().toLowerCase()

export const isSupabaseConfigured =
  supabaseUrl.length > 0 && supabaseAnonKey.length > 0
export const isGuestModeEnabled = guestModeRaw !== 'false'

export function getSupabaseEnv() {
  if (!isSupabaseConfigured) {
    throw new Error(
      'Supabase is not configured. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in frontend/.env.',
    )
  }

  return {
    url: supabaseUrl,
    anonKey: supabaseAnonKey,
  }
}
