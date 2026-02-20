'use client'
import { useState, useEffect, useCallback } from 'react'
import { conversationsApi } from '@/lib/api/conversations'
import type { Conversation } from '@/types'

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    try {
      const data = await conversationsApi.list()
      setConversations(data)
    } catch (e) {
      console.error('Failed to load conversations:', e)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const createConversation = useCallback(
    async (title?: string): Promise<Conversation> => {
      const convo = await conversationsApi.create({ title })
      setConversations((prev) => [convo, ...prev])
      return convo
    },
    [],
  )

  const deleteConversation = useCallback(async (id: string) => {
    await conversationsApi.delete(id)
    setConversations((prev) => prev.filter((c) => c.id !== id))
  }, [])

  const updateTitle = useCallback((id: string, title: string) => {
    setConversations((prev) =>
      prev.map((c) => (c.id === id ? { ...c, title } : c)),
    )
  }, [])

  return {
    conversations,
    loading,
    refresh,
    createConversation,
    deleteConversation,
    updateTitle,
  }
}
