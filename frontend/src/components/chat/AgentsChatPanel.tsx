'use client'

import type { AgentEvent, ConversationState } from '@/types'
import { formatDistanceToNowStrict } from 'date-fns'

interface AgentsChatPanelProps {
  events: AgentEvent[]
  state: ConversationState | null
}

function truncate(text: string | null | undefined, limit = 260) {
  if (!text) return ''
  const compact = text.replace(/\s+/g, ' ').trim()
  if (compact.length <= limit) return compact
  return `${compact.slice(0, limit)}...`
}

const NEXT_AGENT_HINT: Record<string, string> = {
  brief_analyzer: 'Output passed to Trend Agent.',
  trend_agent: 'Output passed to Case Intelligence Agent.',
  case_intelligence: 'Output passed to Market Landscape Agent.',
  market_landscape: 'Output passed to Insight Generator.',
  insight_generator: 'Output passed to Creator Agent.',
  creator_agent: 'Final campaign concepts prepared.',
}

function eventDisplayText(event: AgentEvent) {
  const status = (event.status || '').toLowerCase()
  if (status === 'completed') {
    return NEXT_AGENT_HINT[event.agent_name] || 'Step completed.'
  }
  if (status === 'failed') {
    return truncate(event.content, 220) || 'Step failed.'
  }
  return truncate(event.content, 280) || 'In progress...'
}

function shouldHidePendingPrompt(prompt: string | null | undefined) {
  if (!prompt) return true
  const normalized = prompt.toLowerCase()
  return normalized.includes('choose mode') && normalized.includes('interactive') && normalized.includes('autonomous')
}

export function AgentsChatPanel({
  events,
  state,
}: AgentsChatPanelProps) {
  return (
    <aside className="flex h-full flex-col overflow-hidden rounded-2xl border border-zinc-200 bg-[#e9ecef]">
      <div className="space-y-3 border-b border-zinc-200 px-4 py-4">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-sm font-semibold tracking-wide text-zinc-700">AGENTS CHAT</h2>
          <div className="text-[11px] uppercase tracking-wide text-zinc-500">
            {state?.pipeline_status ?? 'idle'}
          </div>
        </div>

        {state?.pending_prompt && !shouldHidePendingPrompt(state.pending_prompt) && (
          <p className="rounded-md border border-zinc-300 bg-white px-3 py-2 text-xs text-zinc-600">
            {state.pending_prompt}
          </p>
        )}
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto p-3">
        {events.map((event) => (
          <article key={`${event.id ?? event.created_at}-${event.agent_name}`} className="rounded-xl bg-white p-3 shadow-sm">
            <div className="mb-2 flex items-center justify-between gap-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-zinc-700">
                {event.agent_name.replaceAll('_', ' ')}
              </p>
              <div className="text-[11px] text-zinc-500">
                {formatDistanceToNowStrict(new Date(event.created_at), { addSuffix: true })}
              </div>
            </div>
            <p className="mb-1 text-[11px] font-medium uppercase tracking-wide text-zinc-500">
              {event.status}
            </p>
            <p className="text-xs leading-relaxed text-zinc-700">
              {eventDisplayText(event)}
            </p>
          </article>
        ))}

        {events.length === 0 && (
          <div className="rounded-xl border border-dashed border-zinc-300 bg-white/60 px-3 py-6 text-center text-xs text-zinc-500">
            Agent updates will appear here while the pipeline runs.
          </div>
        )}
      </div>
    </aside>
  )
}
