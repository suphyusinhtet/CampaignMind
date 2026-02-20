import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import { ChatShell } from '@/components/layout/ChatShell'
import { isGuestModeEnabled, isSupabaseConfigured } from '@/lib/supabase/config'

export default async function ChatLayout({
  children,
}: {
  children: React.ReactNode
}) {
  if (!isSupabaseConfigured) {
    return (
      <ChatShell userEmail={null} authEnabled={false}>
        {children}
      </ChatShell>
    )
  }

  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user && !isGuestModeEnabled) redirect('/login')

  return (
    <ChatShell userEmail={user?.email ?? null} authEnabled={!!user}>
      {children}
    </ChatShell>
  )
}
