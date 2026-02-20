'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ChatInput } from '@/components/chat/ChatInput'
import { conversationsApi } from '@/lib/api/conversations'
import { Sparkles } from 'lucide-react'

export default function NewChatPage() {
  const router = useRouter()
  const [starting, setStarting] = useState(false)

  const handleSend = async (content: string) => {
    setStarting(true)
    try {
      const convo = await conversationsApi.create()
      // Navigate to conversation page with initial message in URL
      router.push(
        `/conversations/${convo.id}?initialMessage=${encodeURIComponent(content)}`,
      )
    } catch (e) {
      console.error('Failed to create conversation:', e)
      setStarting(false)
    }
  }

  return (
    <div className="flex flex-1 flex-col items-center justify-center px-4 py-10 md:px-8">
      {/* Hero */}
      <div className="mb-8 max-w-2xl text-center">
        <div className="mx-auto mb-4 flex h-11 w-11 items-center justify-center rounded-2xl bg-zinc-900">
          <Sparkles size={20} className="text-white" />
        </div>
        <h2 className="text-3xl font-semibold tracking-tight text-zinc-900 md:text-4xl">
          How can I help with your campaign?
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-zinc-500 md:text-base">
          Paste your marketing brief below. Pathfinder AI will analyze it with
          trend intelligence, competitor case studies, and market landscape
          research.
        </p>
      </div>

      {/* Input */}
      <div className="w-full max-w-3xl rounded-3xl border border-zinc-200 bg-white p-4 shadow-[0_16px_50px_rgba(0,0,0,0.06)] md:p-6">
        <ChatInput
          onSend={handleSend}
          disabled={starting}
          placeholder={
            starting
              ? 'Creating conversation...'
              : 'Paste your campaign brief here...\n\nExample: Campaign Objective: Launch awareness campaign for eco-friendly sneakers...'
          }
          minRows={5}
        />
        <p className="mt-3 text-center text-xs text-zinc-400">
          Press Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  )
}
