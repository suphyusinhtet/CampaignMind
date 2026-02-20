'use client'

import { useState } from 'react'
import { Copy, RefreshCw } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { AnalysisPanel } from './AnalysisPanel'
import type { Message } from '@/types'

interface MessageBubbleProps {
  message: Message
  onRegenerate?: (assistantMessageId: string) => void
}

export function MessageBubble({ message, onRegenerate }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1200)
    } catch {
      setCopied(false)
    }
  }

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-xl rounded-3xl rounded-tr-md bg-zinc-900 px-4 py-3 text-white">
          <p className="text-sm whitespace-pre-wrap leading-relaxed">
            {message.content}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex justify-start">
      <div className="w-full max-w-3xl space-y-2">
        {/* Main markdown response */}
        <div className="rounded-3xl rounded-tl-md border border-zinc-200 bg-white px-5 py-4">
          <div className="prose prose-zinc prose-sm max-w-none leading-7 prose-headings:mb-3 prose-headings:mt-5 prose-p:my-3 prose-pre:rounded-xl prose-pre:border prose-pre:border-zinc-200 prose-code:rounded prose-code:bg-zinc-100 prose-code:px-1 prose-code:py-0.5 prose-code:text-[0.92em] prose-ul:my-3 prose-ol:my-3">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>
        </div>

        <div className="flex items-center gap-2 pl-1">
          <button
            onClick={handleCopy}
            className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs text-zinc-500 transition-colors hover:bg-zinc-100 hover:text-zinc-700"
          >
            <Copy size={13} />
            {copied ? 'Copied' : 'Copy'}
          </button>
          {onRegenerate && (
            <button
              onClick={() => onRegenerate(message.id)}
              className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs text-zinc-500 transition-colors hover:bg-zinc-100 hover:text-zinc-700"
            >
              <RefreshCw size={13} />
              Regenerate
            </button>
          )}
        </div>

        {/* Sub-analyses panel for initial brief analysis */}
        {message.message_type === 'analysis' && message.metadata && (
          <AnalysisPanel metadata={message.metadata} />
        )}
      </div>
    </div>
  )
}
