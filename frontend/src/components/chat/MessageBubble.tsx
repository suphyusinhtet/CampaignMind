import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { AnalysisPanel } from './AnalysisPanel'
import type { Message } from '@/types'

interface MessageBubbleProps {
  message: Message
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-xl rounded-2xl rounded-tr-sm bg-blue-600 px-4 py-3 text-white">
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
        <div className="rounded-2xl rounded-tl-sm border border-gray-200 bg-white px-5 py-4">
          <div className="prose prose-sm prose-gray max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>
        </div>

        {/* Sub-analyses panel for initial brief analysis */}
        {message.message_type === 'analysis' && message.metadata && (
          <AnalysisPanel metadata={message.metadata} />
        )}
      </div>
    </div>
  )
}
