'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ChatInput } from '@/components/chat/ChatInput'
import { conversationsApi } from '@/lib/api/conversations'
import { Zap } from 'lucide-react'

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
    <div className="flex flex-1 flex-col items-center justify-center p-8">
      {/* Hero */}
      <div className="mb-8 max-w-xl text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600">
          <Zap size={24} className="text-white" />
        </div>
        <h2 className="text-2xl font-semibold text-gray-900">
          Enhance your campaign brief
        </h2>
        <p className="mt-2 text-sm text-gray-500 leading-relaxed">
          Paste your marketing brief below. Pathfinder AI will analyze it with
          trend intelligence, competitor case studies, and market landscape
          research.
        </p>
      </div>

      {/* Input */}
      <div className="w-full max-w-2xl">
        <ChatInput
          onSend={handleSend}
          disabled={starting}
          placeholder={
            starting
              ? 'Creating conversation...'
              : 'Paste your campaign brief here...\n\nExample: Campaign Objective: Launch awareness campaign for eco-friendly sneakers...'
          }
          minRows={6}
        />
        <p className="mt-2 text-center text-xs text-gray-400">
          Press Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  )
}
