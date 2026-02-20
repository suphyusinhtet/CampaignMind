'use client'
import { useState, type KeyboardEvent } from 'react'
import TextareaAutosize from 'react-textarea-autosize'
import { Send } from 'lucide-react'
import { clsx } from 'clsx'

interface ChatInputProps {
  onSend: (content: string) => void
  disabled?: boolean
  placeholder?: string
  minRows?: number
}

export function ChatInput({
  onSend,
  disabled,
  placeholder,
  minRows = 1,
}: ChatInputProps) {
  const [value, setValue] = useState('')

  const submit = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  const canSend = value.trim().length > 0 && !disabled

  return (
    <div
      className={clsx(
        'flex items-end gap-3 rounded-3xl border border-zinc-300 bg-white px-4 py-3 shadow-[0_2px_10px_rgba(0,0,0,0.04)] transition-shadow',
        'focus-within:border-zinc-400 focus-within:shadow-[0_4px_20px_rgba(0,0,0,0.08)]',
        disabled && 'opacity-60',
      )}
    >
      <TextareaAutosize
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder={placeholder ?? 'Message CampaignMind...'}
        minRows={minRows}
        maxRows={12}
        className="flex-1 resize-none bg-transparent text-sm leading-relaxed text-zinc-900 outline-none placeholder:text-zinc-400"
      />
      <button
        onClick={submit}
        disabled={!canSend}
        className={clsx(
          'shrink-0 rounded-full p-2 transition-colors',
          canSend
            ? 'bg-zinc-900 text-white hover:bg-zinc-700'
            : 'cursor-not-allowed bg-zinc-100 text-zinc-300',
        )}
      >
        <Send size={16} />
      </button>
    </div>
  )
}
