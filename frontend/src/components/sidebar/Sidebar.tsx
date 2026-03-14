'use client'
import { LogOut, Zap } from 'lucide-react'
import { clsx } from 'clsx'
import { usePathname, useRouter } from 'next/navigation'
import { useState } from 'react'
import { NewChatButton } from './NewChatButton'
import { ConversationList } from './ConversationList'
import { useAuth } from '@/hooks/useAuth'

interface SidebarProps {
  userEmail: string | null
  authEnabled?: boolean
  className?: string
}

export function Sidebar({
  userEmail,
  authEnabled = true,
  className,
}: SidebarProps) {
  const router = useRouter()
  const pathname = usePathname()
  const { signOut } = useAuth()
  const [signingOut, setSigningOut] = useState(false)

  const handleSignOut = async () => {
    if (signingOut) return
    setSigningOut(true)
    try {
      await signOut()
      router.replace('/login')
      router.refresh()
    } finally {
      setSigningOut(false)
    }
  }

  const handleSignIn = () => {
    const nextPath = pathname && pathname.trim().length > 0 ? pathname : '/'
    router.push(`/login?next=${encodeURIComponent(nextPath)}`)
  }

  return (
    <aside
      className={clsx(
        'flex h-full w-72 shrink-0 flex-col border-r border-[#2f2f2f] bg-[#171717] text-white',
        className,
      )}
    >
      {/* Header */}
      <div className="flex items-center gap-2 border-b border-[#2f2f2f] px-4 py-3">
        <Zap size={16} className="text-emerald-400" />
        <span className="text-sm font-semibold tracking-tight text-zinc-100">
          CampaignMind
        </span>
      </div>

      {/* New Chat */}
      <div className="px-3 pt-3">
        <NewChatButton />
      </div>

      {/* Conversation list */}
      <div className="flex-1 overflow-y-auto px-3 py-3">
        <p className="mb-2 px-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-zinc-500">
          Recent
        </p>
        <ConversationList />
      </div>

      {/* User footer */}
      <div className="flex items-center gap-3 border-t border-[#2f2f2f] px-3 py-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-zinc-700 text-xs font-semibold text-white">
          {userEmail?.[0].toUpperCase() ?? 'G'}
        </div>
        <div className="flex-1 min-w-0">
          <p className="truncate text-xs text-zinc-300">{userEmail ?? 'Guest mode'}</p>
        </div>
        {authEnabled ? (
          <button
            onClick={handleSignOut}
            disabled={signingOut}
            className="shrink-0 text-zinc-500 transition-colors hover:text-white"
            title={signingOut ? 'Signing out...' : 'Sign out'}
          >
            <LogOut size={15} />
          </button>
        ) : (
          <button
            onClick={handleSignIn}
            className="shrink-0 rounded-md border border-zinc-600 px-2 py-1 text-xs font-medium text-zinc-200 transition-colors hover:border-zinc-500 hover:bg-zinc-800 hover:text-white"
            title="Sign in"
          >
            Sign in
          </button>
        )}
      </div>
    </aside>
  )
}
