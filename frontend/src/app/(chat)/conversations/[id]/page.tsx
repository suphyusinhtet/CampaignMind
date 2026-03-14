'use client'
import { useCallback, useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { useRouter } from 'next/navigation'
import { useMessages } from '@/hooks/useMessages'
import { MessageList } from '@/components/chat/MessageList'
import { ChatInput } from '@/components/chat/ChatInput'
import { ThinkingIndicator } from '@/components/chat/ThinkingIndicator'
import { AgentsTeamPanel } from '@/components/chat/AgentsTeamPanel'
import { AgentsChatPanel } from '@/components/chat/AgentsChatPanel'
import { conversationsApi } from '@/lib/api/conversations'
import { House, Plus } from 'lucide-react'
import type { AgentEvent, AgentListItem, ConversationState } from '@/types'

interface PageProps {
  params: { id: string }
}

export default function ConversationPage({ params }: PageProps) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const initialMessage = searchParams.get('initialMessage')
  const { messages, loading, sending, error, loadMessages, sendMessage } =
    useMessages(params.id)
  const [agents, setAgents] = useState<AgentListItem[]>([])
  const [agentEvents, setAgentEvents] = useState<AgentEvent[]>([])
  const [conversationState, setConversationState] = useState<ConversationState | null>(null)
  const [runtimeError, setRuntimeError] = useState<string | null>(null)
  const [creatingConversation, setCreatingConversation] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const initialSentRef = useRef(false)
  const eventsCursorRef = useRef<string | undefined>(undefined)

  useEffect(() => {
    loadMessages()
  }, [loadMessages])

  const mergeEvents = useCallback((incoming: AgentEvent[]) => {
    if (incoming.length === 0) return
    setAgentEvents((prev) => {
      const map = new Map<string, AgentEvent>()
      for (const item of prev) {
        const key = item.id ?? `${item.agent_name}-${item.created_at}-${item.status}`
        map.set(key, item)
      }
      for (const item of incoming) {
        const key = item.id ?? `${item.agent_name}-${item.created_at}-${item.status}`
        map.set(key, item)
      }
      return Array.from(map.values()).sort((a, b) =>
        a.created_at.localeCompare(b.created_at),
      )
    })
  }, [])

  const loadRuntime = useCallback(async () => {
    setRuntimeError(null)
    try {
      const [nextAgents, nextState, events] = await Promise.all([
        conversationsApi.listAgents(),
        conversationsApi.getState(params.id),
        conversationsApi.listAgentEvents(params.id, { limit: 200 }),
      ])
      setAgents(nextAgents)
      setConversationState(nextState)
      setAgentEvents(events)
      if (events.length > 0) {
        eventsCursorRef.current = events[events.length - 1].created_at
      }
    } catch (e: unknown) {
      setRuntimeError(e instanceof Error ? e.message : 'Failed to load runtime panels')
    }
  }, [params.id])

  useEffect(() => {
    loadRuntime()
  }, [loadRuntime])

  useEffect(() => {
    let stopped = false
    const poll = async () => {
      if (stopped) return
      try {
        const [nextState, newEvents] = await Promise.all([
          conversationsApi.getState(params.id),
          conversationsApi.listAgentEvents(params.id, {
            limit: 120,
            after: eventsCursorRef.current,
          }),
        ])
        if (stopped) return
        setConversationState(nextState)
        if (newEvents.length > 0) {
          eventsCursorRef.current = newEvents[newEvents.length - 1].created_at
          mergeEvents(newEvents)
        }
      } catch {
        // Keep polling even if one cycle fails.
      }
      window.setTimeout(poll, 1500)
    }

    const timer = window.setTimeout(poll, 1500)
    return () => {
      stopped = true
      window.clearTimeout(timer)
    }
  }, [params.id, mergeEvents])

  useEffect(() => {
    if (initialMessage && !initialSentRef.current && !loading) {
      initialSentRef.current = true
      sendMessage(initialMessage)
      window.history.replaceState({}, '', `/conversations/${params.id}`)
    }
  }, [initialMessage, loading, sendMessage, params.id])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, sending])

  const handleRegenerate = (assistantMessageId: string) => {
    const assistantIndex = messages.findIndex((m) => m.id === assistantMessageId)
    if (assistantIndex <= 0) return

    for (let i = assistantIndex - 1; i >= 0; i -= 1) {
      if (messages[i].role === 'user') {
        sendMessage(messages[i].content)
        return
      }
    }
  }

  const shouldHidePendingPrompt = useCallback((prompt: string | null | undefined) => {
    if (!prompt) return true
    const normalized = prompt.toLowerCase()
    return normalized.includes('choose mode') && normalized.includes('interactive') && normalized.includes('autonomous')
  }, [])

  const handleNewChat = useCallback(async () => {
    if (creatingConversation) return
    setCreatingConversation(true)
    setRuntimeError(null)
    try {
      const convo = await conversationsApi.create()
      router.push(`/conversations/${convo.id}`)
    } catch (e: unknown) {
      setRuntimeError(e instanceof Error ? e.message : 'Failed to create conversation')
    } finally {
      setCreatingConversation(false)
    }
  }, [creatingConversation, router])

  return (
    <div className="flex flex-1 overflow-hidden p-4 md:p-5">
      <div className="grid h-full w-full grid-cols-1 gap-4 md:grid-cols-[260px_minmax(0,1fr)_330px]">
        <AgentsTeamPanel agents={agents} events={agentEvents} />

        <section className="flex min-h-0 flex-col overflow-hidden rounded-2xl border border-zinc-200 bg-[#f4f5f6]">
          <div className="border-b border-zinc-200 px-4 py-4">
            <div className="flex items-center justify-between gap-3">
              <h1 className="text-base font-semibold text-zinc-800">USER CHAT</h1>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => router.push('/')}
                  className="inline-flex items-center gap-1 rounded-lg border border-zinc-300 bg-white px-2.5 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50"
                >
                  <House size={13} />
                  Back to Home
                </button>
                <button
                  onClick={handleNewChat}
                  disabled={creatingConversation}
                  className="inline-flex items-center gap-1 rounded-lg border border-zinc-800 bg-zinc-900 px-2.5 py-1.5 text-xs font-medium text-white hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <Plus size={13} />
                  {creatingConversation ? 'Creating...' : 'New Chat'}
                </button>
              </div>
            </div>
            {conversationState?.pending_prompt && !shouldHidePendingPrompt(conversationState.pending_prompt) && (
              <p className="mt-2 rounded-md border border-zinc-300 bg-white px-3 py-2 text-xs text-zinc-600">
                {conversationState.pending_prompt}
              </p>
            )}
          </div>
          <div className="flex-1 overflow-y-auto">
            {messages.length === 0 && !loading && !sending && (
              <div className="flex h-full items-center justify-center">
                <p className="text-sm text-zinc-500">Send your first message to get started.</p>
              </div>
            )}
            <MessageList
              messages={messages}
              loading={loading}
              onRegenerate={handleRegenerate}
            />
            {sending && <ThinkingIndicator />}
            {error && (
              <div className="mx-auto max-w-3xl px-4 py-2">
                <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-600">
                  {error}
                </p>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
          <div className="border-t border-zinc-200/80 bg-[#f4f5f6] px-4 py-4">
            <ChatInput
              onSend={sendMessage}
              disabled={sending || loading}
              placeholder={
                sending
                  ? 'Agents are working...'
                  : conversationState?.mode === 'interactive' &&
                      conversationState?.current_step === 'awaiting_user_creator_option'
                    ? 'Reply with 1, 2, or 3 to choose Creator output.'
                    : conversationState?.mode === 'interactive' &&
                        conversationState?.current_step?.startsWith('awaiting_user_continue')
                      ? "Type 'continue' to run next step..."
                    : 'Write your message to continue...'
              }
            />
          </div>
        </section>

        <AgentsChatPanel events={agentEvents} state={conversationState} />
      </div>
      {runtimeError && (
        <div className="pointer-events-none absolute bottom-4 right-4 max-w-sm rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700 shadow">
          {runtimeError}
        </div>
      )}
    </div>
  )
}
