'use client'
import { useEffect, useRef } from 'react'
import { useSearchParams } from 'next/navigation'
import { useMessages } from '@/hooks/useMessages'
import { MessageList } from '@/components/chat/MessageList'
import { ChatInput } from '@/components/chat/ChatInput'
import { ThinkingIndicator } from '@/components/chat/ThinkingIndicator'

interface PageProps {
  params: { id: string }
}

export default function ConversationPage({ params }: PageProps) {
  const searchParams = useSearchParams()
  const initialMessage = searchParams.get('initialMessage')
  const { messages, loading, sending, error, loadMessages, sendMessage } =
    useMessages(params.id)
  const bottomRef = useRef<HTMLDivElement>(null)
  const initialSentRef = useRef(false)

  // Load existing messages on mount
  useEffect(() => {
    loadMessages()
  }, [loadMessages])

  // Send the initial message (from new chat redirect) exactly once
  useEffect(() => {
    if (initialMessage && !initialSentRef.current && !loading) {
      initialSentRef.current = true
      sendMessage(decodeURIComponent(initialMessage))
      // Remove query param from URL without triggering re-render
      window.history.replaceState({}, '', `/conversations/${params.id}`)
    }
  }, [initialMessage, loading, sendMessage, params.id])

  // Auto-scroll to bottom on new messages or while sending
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, sending])

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Message thread */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 && !loading && !sending && (
          <div className="flex h-full items-center justify-center">
            <p className="text-sm text-gray-400">
              Send your first message to get started.
            </p>
          </div>
        )}
        <MessageList messages={messages} loading={loading} />
        {sending && <ThinkingIndicator />}
        {error && (
          <div className="mx-auto max-w-3xl px-4 py-2">
            <p className="rounded-lg bg-red-50 px-4 py-2 text-sm text-red-600">
              {error}
            </p>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="border-t border-gray-200 bg-white px-4 py-3">
        <div className="mx-auto max-w-3xl">
          <ChatInput
            onSend={sendMessage}
            disabled={sending || loading}
            placeholder={
              sending
                ? 'Analyzing your brief...'
                : 'Ask a follow-up question...'
            }
          />
        </div>
      </div>
    </div>
  )
}
