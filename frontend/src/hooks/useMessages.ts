'use client'
import { useState, useCallback } from 'react'
import { conversationsApi } from '@/lib/api/conversations'
import type { Conversation, Message } from '@/types'

export function useMessages(conversationId: string) {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadMessages = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const convo: Conversation = await conversationsApi.get(conversationId)
      setMessages(convo.messages ?? [])
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load messages')
    } finally {
      setLoading(false)
    }
  }, [conversationId])

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || sending) return
      setSending(true)
      setError(null)

      // Optimistic user message
      const optimisticId = `optimistic-${Date.now()}`
      const isFirst = messages.length === 0
      const optimisticUserMsg: Message = {
        id: optimisticId,
        conversation_id: conversationId,
        role: 'user',
        content,
        message_type: isFirst ? 'brief' : 'followup',
        created_at: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, optimisticUserMsg])

      try {
        const assistantMsg = await conversationsApi.sendMessage(conversationId, {
          content,
        })
        // Replace optimistic with confirmed user msg + append assistant response
        setMessages((prev) => [
          ...prev.filter((m) => m.id !== optimisticId),
          {
            ...optimisticUserMsg,
            id: `user-confirmed-${Date.now()}`,
          },
          assistantMsg,
        ])
      } catch (e: unknown) {
        // Roll back optimistic message on error
        setMessages((prev) => prev.filter((m) => m.id !== optimisticId))
        setError(e instanceof Error ? e.message : 'Failed to send message')
      } finally {
        setSending(false)
      }
    },
    [conversationId, messages.length, sending],
  )

  return { messages, loading, sending, error, loadMessages, sendMessage }
}
