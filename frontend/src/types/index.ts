export type MessageRole = 'user' | 'assistant'
export type MessageType = 'brief' | 'analysis' | 'followup'

export interface AnalysisMetadata {
  brief_analysis?: string
  trend_analysis?: string
  case_analysis?: string
  landscape_analysis?: string
  processing_time_seconds?: number
}

export interface Message {
  id: string
  conversation_id: string
  role: MessageRole
  content: string
  message_type: MessageType
  metadata?: AnalysisMetadata | null
  created_at: string
}

export interface Conversation {
  id: string
  user_id: string
  title: string
  created_at: string
  updated_at: string
  messages?: Message[]
}

export interface SendMessagePayload {
  content: string
}

export interface CreateConversationPayload {
  title?: string
}
