'use client'
import { usePathname, useRouter } from 'next/navigation'
import { Trash2 } from 'lucide-react'
import { clsx } from 'clsx'
import { formatDistanceToNow } from 'date-fns'
import type { Conversation } from '@/types'

interface ConversationItemProps {
  conversation: Conversation
  onDelete: (id: string) => void
}

export function ConversationItem({
  conversation,
  onDelete,
}: ConversationItemProps) {
  const pathname = usePathname()
  const router = useRouter()
  const isActive = pathname === `/conversations/${conversation.id}`

  const handleDelete = async (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (confirm('Delete this conversation?')) {
      onDelete(conversation.id)
      if (isActive) router.push('/')
    }
  }

  return (
    <a
      href={`/conversations/${conversation.id}`}
      className={clsx(
        'group flex items-start justify-between rounded-xl px-2.5 py-2 text-sm transition-colors',
        isActive
          ? 'bg-zinc-700 text-white'
          : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200',
      )}
    >
      <div className="flex-1 min-w-0">
        <p className="truncate font-medium leading-tight">{conversation.title}</p>
        <p className="mt-0.5 text-xs text-zinc-500">
          {formatDistanceToNow(new Date(conversation.updated_at), {
            addSuffix: true,
          })}
        </p>
      </div>
      <button
        onClick={handleDelete}
        className="ml-2 mt-0.5 shrink-0 text-zinc-600 opacity-0 transition-opacity hover:text-red-400 group-hover:opacity-100"
        title="Delete conversation"
      >
        <Trash2 size={13} />
      </button>
    </a>
  )
}
