import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

/**
 * OAuth callback handler.
 * Supabase redirects here after Google / GitHub login with a `code` query param.
 * We exchange it for a session cookie and redirect the user to the app.
 */
export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url)
  const code = searchParams.get('code')
  const next = searchParams.get('next') ?? '/'

  if (code) {
    const supabase = await createClient()
    const { error } = await supabase.auth.exchangeCodeForSession(code)
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`)
    }
  }

  // Redirect to login with an error if exchange failed
  return NextResponse.redirect(`${origin}/login?error=auth_callback_failed`)
}
