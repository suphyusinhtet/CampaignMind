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

  const renameConversation = useCallback(
    async (id: string, title: string) => {
      const updated = await conversationsApi.rename(id, { title })
      setConversations((prev) => {
        const next = prev.map((c) => (c.id === id ? updated : c))
        return next.sort((a, b) => b.updated_at.localeCompare(a.updated_at))
      })
      return updated
    },
    [],
  )

  return {
    conversations,
    loading,
    refresh,
    createConversation,
    deleteConversation,
    renameConversation,
  }
}
