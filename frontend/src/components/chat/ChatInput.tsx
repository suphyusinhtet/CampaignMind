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
        'flex items-end gap-2 rounded-xl border border-gray-200 bg-white px-4 py-3 transition-shadow',
        'focus-within:border-blue-400 focus-within:ring-2 focus-within:ring-blue-100',
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
        className="flex-1 resize-none bg-transparent text-sm text-gray-900 placeholder:text-gray-400 outline-none leading-relaxed"
      />
      <button
        onClick={submit}
        disabled={!canSend}
        className={clsx(
          'shrink-0 rounded-lg p-1.5 transition-colors',
          canSend
            ? 'bg-blue-600 text-white hover:bg-blue-700'
            : 'bg-gray-100 text-gray-300 cursor-not-allowed',
        )}
      >
        <Send size={16} />
      </button>
    </div>
  )
}
