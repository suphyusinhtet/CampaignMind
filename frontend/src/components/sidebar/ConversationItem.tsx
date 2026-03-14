'use client'
import { useEffect, useRef, useState } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { Check, Pencil, Trash2, X } from 'lucide-react'
import { clsx } from 'clsx'
import { formatDistanceToNow } from 'date-fns'
import type { Conversation } from '@/types'

interface ConversationItemProps {
  conversation: Conversation
  onDelete: (id: string) => void
  onRename: (id: string, title: string) => Promise<unknown>
}

const MAX_CONVERSATION_TITLE_CHARS = 60
const MAX_CONVERSATION_TITLE_WORDS = 10

function normalizeTitleInput(title: string) {
  let normalized = title.trim().replace(/\s+/g, ' ')
  if (!normalized) return ''

  const words = normalized.split(' ')
  if (words.length > MAX_CONVERSATION_TITLE_WORDS) {
    normalized = words.slice(0, MAX_CONVERSATION_TITLE_WORDS).join(' ')
  }
  if (normalized.length > MAX_CONVERSATION_TITLE_CHARS) {
    normalized = normalized.slice(0, MAX_CONVERSATION_TITLE_CHARS).trimEnd()
  }
  return normalized
}

export function ConversationItem({
  conversation,
  onDelete,
  onRename,
}: ConversationItemProps) {
  const pathname = usePathname()
  const router = useRouter()
  const isActive = pathname === `/conversations/${conversation.id}`
  const [isEditing, setIsEditing] = useState(false)
  const [draftTitle, setDraftTitle] = useState(conversation.title)
  const [isSaving, setIsSaving] = useState(false)
  const inputRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    if (!isEditing) setDraftTitle(conversation.title)
  }, [conversation.title, isEditing])

  useEffect(() => {
    if (!isEditing) return
    inputRef.current?.focus()
    inputRef.current?.select()
  }, [isEditing])

  const handleDelete = async (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (isEditing || isSaving) return
    if (confirm('Delete this conversation?')) {
      try {
        await onDelete(conversation.id)
        if (isActive) router.push('/')
      } catch (error) {
        console.error('Failed to delete conversation:', error)
      }
    }
  }

  const handleOpen = () => {
    if (isEditing) return
    router.push(`/conversations/${conversation.id}`)
  }

  const handleStartRename = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (isSaving) return
    setIsEditing(true)
  }

  const handleCancelRename = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (isSaving) return
    setDraftTitle(conversation.title)
    setIsEditing(false)
  }

  const submitRename = async () => {
    if (isSaving) return
    const nextTitle = normalizeTitleInput(draftTitle)

    if (!nextTitle) {
      setDraftTitle(conversation.title)
      setIsEditing(false)
      return
    }

    if (nextTitle === conversation.title) {
      setDraftTitle(nextTitle)
      setIsEditing(false)
      return
    }

    try {
      setIsSaving(true)
      await onRename(conversation.id, nextTitle)
      setDraftTitle(nextTitle)
      setIsEditing(false)
    } catch (error) {
      console.error('Failed to rename conversation:', error)
      setDraftTitle(conversation.title)
      setIsEditing(false)
    } finally {
      setIsSaving(false)
    }
  }

  const handleSaveRename = async (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    await submitRename()
  }

  const handleInputBlur = async () => {
    await submitRename()
  }

  return (
    <div
      onClick={handleOpen}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter') handleOpen()
      }}
      className={clsx(
        'group flex items-start justify-between rounded-xl px-2.5 py-2 text-sm transition-colors',
        isActive
          ? 'bg-zinc-700 text-white'
          : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200 cursor-pointer',
      )}
    >
      <div className="flex-1 min-w-0">
        {isEditing ? (
          <input
            ref={inputRef}
            value={draftTitle}
            maxLength={120}
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
            }}
            onChange={(e) => setDraftTitle(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault()
                void submitRename()
              } else if (e.key === 'Escape') {
                e.preventDefault()
                setDraftTitle(conversation.title)
                setIsEditing(false)
              }
            }}
            onBlur={() => void handleInputBlur()}
            className="w-full rounded bg-zinc-900 px-1.5 py-0.5 text-sm font-medium leading-tight text-zinc-100 outline-none ring-1 ring-zinc-700 focus:ring-zinc-500"
            aria-label="Conversation title"
          />
        ) : (
          <p className="truncate font-medium leading-tight">{conversation.title}</p>
        )}
        <p className="mt-0.5 text-xs text-zinc-500">
          {formatDistanceToNow(new Date(conversation.updated_at), {
            addSuffix: true,
          })}
        </p>
      </div>

      <div className="ml-2 mt-0.5 flex shrink-0 items-center gap-1">
        {isEditing ? (
          <>
            <button
              data-conversation-action="true"
              onMouseDown={(e) => e.preventDefault()}
              onClick={handleSaveRename}
              disabled={isSaving}
              className="text-zinc-500 transition-colors hover:text-emerald-400 disabled:opacity-50"
              title="Save title"
            >
              <Check size={13} />
            </button>
            <button
              data-conversation-action="true"
              onMouseDown={(e) => e.preventDefault()}
              onClick={handleCancelRename}
              disabled={isSaving}
              className="text-zinc-500 transition-colors hover:text-zinc-200 disabled:opacity-50"
              title="Cancel rename"
            >
              <X size={13} />
            </button>
          </>
        ) : (
          <>
            <button
              onClick={handleStartRename}
              className="text-zinc-600 opacity-0 transition-opacity hover:text-zinc-200 group-hover:opacity-100"
              title="Rename conversation"
            >
              <Pencil size={13} />
            </button>
            <button
              onClick={handleDelete}
              className="text-zinc-600 opacity-0 transition-opacity hover:text-red-400 group-hover:opacity-100"
              title="Delete conversation"
            >
              <Trash2 size={13} />
            </button>
          </>
        )}
      </div>
    </div>
  )
}
