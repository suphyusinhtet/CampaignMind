'use client'
import type { User } from '@supabase/supabase-js'
import { LogOut, Zap } from 'lucide-react'
import { NewChatButton } from './NewChatButton'
import { ConversationList } from './ConversationList'
import { useAuth } from '@/hooks/useAuth'

interface SidebarProps {
  user: User
}

export function Sidebar({ user }: SidebarProps) {
  const { signOut } = useAuth()

  return (
    <aside className="flex h-full w-64 shrink-0 flex-col bg-gray-900 text-white">
      {/* Header */}
      <div className="flex items-center gap-2 border-b border-gray-700 px-4 py-3">
        <Zap size={16} className="text-blue-400" />
        <span className="text-sm font-semibold tracking-tight">
          CampaignMind
        </span>
      </div>

      {/* New Chat */}
      <div className="px-2 pt-2">
        <NewChatButton />
      </div>

      {/* Conversation list */}
      <div className="flex-1 overflow-y-auto px-2 py-2">
        <p className="mb-1 px-3 text-[10px] font-semibold uppercase tracking-wider text-gray-500">
          Recent
        </p>
        <ConversationList />
      </div>

      {/* User footer */}
      <div className="flex items-center gap-3 border-t border-gray-700 px-3 py-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-500 text-xs font-semibold text-white">
          {user.email?.[0].toUpperCase() ?? '?'}
        </div>
        <div className="flex-1 min-w-0">
          <p className="truncate text-xs text-gray-300">{user.email}</p>
        </div>
        <button
          onClick={signOut}
          className="shrink-0 text-gray-500 hover:text-white transition-colors"
          title="Sign out"
        >
          <LogOut size={15} />
        </button>
      </div>
    </aside>
  )
}
