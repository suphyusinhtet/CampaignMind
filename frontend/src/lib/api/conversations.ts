'use client'

import type {
  Conversation,
  CreateConversationPayload,
  Message,
  SendMessagePayload,
} from '@/types'
import { createClient } from '@/lib/supabase/client'
import { isGuestModeEnabled, isSupabaseConfigured } from '@/lib/supabase/config'

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
const GUEST_STORAGE_KEY = 'campaignmind.guest.conversations.v1'
const GUEST_USER_ID = 'guest-user'

async function getAccessToken(): Promise<string | null> {
  if (!isSupabaseConfigured) return null

  const supabase = createClient()
  const {
    data: { session },
  } = await supabase.auth.getSession()

  return session?.access_token ?? null
}

function guestNow() {
  return new Date().toISOString()
}

function guestId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function readGuestConversations(): Conversation[] {
  if (typeof window === 'undefined') return []
  const raw = window.localStorage.getItem(GUEST_STORAGE_KEY)
  if (!raw) return []

  try {
    const parsed = JSON.parse(raw) as Conversation[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function writeGuestConversations(conversations: Conversation[]) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(GUEST_STORAGE_KEY, JSON.stringify(conversations))
}

function createGuestAssistantMessage(content: string, conversationId: string): Message {
  return {
    id: guestId('msg'),
    conversation_id: conversationId,
    role: 'assistant',
    content,
    message_type: 'analysis',
    created_at: guestNow(),
    metadata: null,
  }
}

async function runGuestEnhancement(content: string): Promise<string> {
  try {
    const response = await fetch(`${API_BASE}/api/v1/enhance-brief`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ brief: content }),
    })
    if (!response.ok) throw new Error('enhancement request failed')
    const data = (await response.json()) as { final_insights?: string }
    if (data.final_insights?.trim()) return data.final_insights
  } catch {
    // fall through to local fallback response
  }

  return [
    'Guest mode is active, so this response is running in local fallback mode.',
    'Connect the backend API at NEXT_PUBLIC_API_URL for full AI analysis.',
    '',
    `You wrote: ${content}`,
  ].join('\n')
}

async function guestList() {
  return readGuestConversations().sort((a, b) =>
    b.updated_at.localeCompare(a.updated_at),
  )
}

async function guestCreate(payload: CreateConversationPayload = {}) {
  const now = guestNow()
  const conversation: Conversation = {
    id: guestId('convo'),
    user_id: GUEST_USER_ID,
    title: payload.title?.trim() || 'New Conversation',
    created_at: now,
    updated_at: now,
    messages: [],
  }
  const conversations = readGuestConversations()
  conversations.unshift(conversation)
  writeGuestConversations(conversations)
  return conversation
}

async function guestGet(conversationId: string) {
  const conversation = readGuestConversations().find((c) => c.id === conversationId)
  if (!conversation) throw new Error('Conversation not found')
  return conversation
}

async function guestDelete(conversationId: string) {
  const updated = readGuestConversations().filter((c) => c.id !== conversationId)
  writeGuestConversations(updated)
}

async function guestSendMessage(
  conversationId: string,
  payload: SendMessagePayload,
): Promise<Message> {
  const conversations = readGuestConversations()
  const conversation = conversations.find((c) => c.id === conversationId)
  if (!conversation) throw new Error('Conversation not found')

  const now = guestNow()
  const userMessage: Message = {
    id: guestId('msg'),
    conversation_id: conversationId,
    role: 'user',
    content: payload.content,
    message_type: (conversation.messages?.length ?? 0) === 0 ? 'brief' : 'followup',
    created_at: now,
    metadata: null,
  }

  const assistantText = await runGuestEnhancement(payload.content)
  const assistantMessage = createGuestAssistantMessage(assistantText, conversationId)
  assistantMessage.message_type = userMessage.message_type === 'brief' ? 'analysis' : 'followup'

  const existing = conversation.messages ?? []
  conversation.messages = [...existing, userMessage, assistantMessage]
  if (
    conversation.title === 'New Conversation' &&
    userMessage.content.trim().length > 0
  ) {
    const cleaned = userMessage.content.trim().replace(/\s+/g, ' ')
    conversation.title = cleaned.length > 60 ? `${cleaned.slice(0, 57)}...` : cleaned
  }
  conversation.updated_at = now
  writeGuestConversations(conversations)
  return assistantMessage
}

async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await getAccessToken()
  const headers = new Headers(init.headers)
  headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
  })

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`
    try {
      const data = await response.json()
      if (typeof data?.detail === 'string') message = data.detail
    } catch {
      // Keep default message when response body is not JSON.
    }
    throw new Error(message)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export const conversationsApi = {
  async list() {
    const token = await getAccessToken()
    if (!token && isGuestModeEnabled) return guestList()
    return apiRequest<Conversation[]>('/api/v1/conversations')
  },

  async create(payload: CreateConversationPayload = {}) {
    const token = await getAccessToken()
    if (!token && isGuestModeEnabled) return guestCreate(payload)
    return apiRequest<Conversation>('/api/v1/conversations', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  async get(conversationId: string) {
    const token = await getAccessToken()
    if (!token && isGuestModeEnabled) return guestGet(conversationId)
    return apiRequest<Conversation>(`/api/v1/conversations/${conversationId}`)
  },

  async sendMessage(conversationId: string, payload: SendMessagePayload) {
    const token = await getAccessToken()
    if (!token && isGuestModeEnabled) return guestSendMessage(conversationId, payload)
    return apiRequest<Message>(`/api/v1/conversations/${conversationId}/messages`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  async delete(conversationId: string) {
    const token = await getAccessToken()
    if (!token && isGuestModeEnabled) return guestDelete(conversationId)
    return apiRequest<void>(`/api/v1/conversations/${conversationId}`, {
      method: 'DELETE',
    })
  },
}
