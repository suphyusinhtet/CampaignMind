'use client'

import type { AgentEvent, AgentListItem } from '@/types'
import { clsx } from 'clsx'

interface AgentsTeamPanelProps {
  agents: AgentListItem[]
  events: AgentEvent[]
}

function getLatestStatusByAgent(events: AgentEvent[]) {
  const statusByAgent = new Map<string, string>()
  for (const event of events) {
    statusByAgent.set(event.agent_name, event.status)
  }
  return statusByAgent
}

function toLabel(status: string | undefined) {
  if (!status) return 'idle'
  if (status === 'started') return 'running'
  if (status === 'completed') return 'done'
  if (status === 'failed') return 'failed'
  return status
}

export function AgentsTeamPanel({ agents, events }: AgentsTeamPanelProps) {
  const statusByAgent = getLatestStatusByAgent(events)

  return (
    <aside className="h-full overflow-hidden rounded-2xl border border-[#21384f] bg-[#0e1e2f] text-zinc-100">
      <div className="border-b border-[#1f3954] px-4 py-4">
        <h2 className="text-sm font-semibold tracking-wide text-zinc-100">AGENTS TEAM</h2>
      </div>
      <div className="space-y-3 overflow-y-auto p-3">
        {agents.map((agent) => {
          const rawStatus = statusByAgent.get(agent.id)
          const status = toLabel(rawStatus)
          const isRunning = status === 'running'

          return (
            <article
              key={agent.id}
              className={clsx(
                'rounded-xl border px-3 py-3 transition-colors',
                isRunning
                  ? 'border-emerald-400 bg-emerald-500/10'
                  : status === 'done'
                    ? 'border-[#355677] bg-[#11263a]'
                    : status === 'failed'
                      ? 'border-red-500/70 bg-red-500/10'
                      : 'border-[#2b4764] bg-[#0f2539]',
              )}
            >
              <div className="mb-1 flex items-center justify-between gap-2">
                <p className="text-sm font-semibold text-zinc-100">{agent.name}</p>
                <span
                  className={clsx(
                    'rounded-full px-2 py-0.5 text-[10px] uppercase tracking-wide',
                    isRunning
                      ? 'bg-emerald-500/20 text-emerald-300'
                      : status === 'done'
                        ? 'bg-sky-500/20 text-sky-300'
                        : status === 'failed'
                          ? 'bg-red-500/20 text-red-300'
                          : 'bg-zinc-500/20 text-zinc-300',
                  )}
                >
                  {status}
                </span>
              </div>
              <p className="text-xs leading-relaxed text-zinc-300">{agent.description}</p>
            </article>
          )
        })}
        {agents.length === 0 && (
          <p className="px-1 py-2 text-xs text-zinc-400">No agent catalog available.</p>
        )}
      </div>
    </aside>
  )
}
