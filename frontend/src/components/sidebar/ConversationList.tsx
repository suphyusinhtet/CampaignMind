'use client'
import { useConversations } from '@/hooks/useConversations'
import { ConversationItem } from './ConversationItem'
import { Spinner } from '@/components/ui/Spinner'

export function ConversationList() {
  const { conversations, loading, deleteConversation } = useConversations()

  if (loading) {
    return (
      <div className="flex justify-center py-4">
        <Spinner size="sm" />
      </div>
    )
  }

  if (conversations.length === 0) {
    return (
      <p className="px-2 py-2 text-xs text-zinc-500">
        No conversations yet. Start a new chat!
      </p>
    )
  }

  return (
    <div className="space-y-1">
      {conversations.map((convo) => (
        <ConversationItem
          key={convo.id}
          conversation={convo}
          onDelete={deleteConversation}
        />
      ))}
    </div>
  )
}
