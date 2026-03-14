'use client'
import { useRouter } from 'next/navigation'
import { Plus } from 'lucide-react'
import { useConversations } from '@/hooks/useConversations'
import { useState } from 'react'

export function NewChatButton() {
  const { createConversation } = useConversations()
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleNewChat = async () => {
    setError(null)
    setLoading(true)
    try {
      const convo = await createConversation()
      router.push(`/conversations/${convo.id}`)
    } catch {
      setError('Could not create conversation. Check backend connection.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-1">
      <button
        onClick={handleNewChat}
        disabled={loading}
        className="flex w-full items-center gap-2 rounded-xl border border-zinc-700 bg-zinc-800/70 px-3 py-2.5 text-sm font-medium text-zinc-100 transition-colors hover:bg-zinc-700 disabled:opacity-50"
      >
        <Plus size={16} />
        New chat
      </button>
      {error && <p className="px-1 text-[11px] text-red-400">{error}</p>}
    </div>
  )
}
