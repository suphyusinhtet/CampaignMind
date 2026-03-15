export type MessageRole = 'user' | 'assistant'
export type MessageType = 'brief' | 'interactive_brief' | 'analysis' | 'followup'

export interface AnalysisMetadata {
  brief_analysis?: string
  trend_analysis?: string
  case_analysis?: string
  landscape_analysis?: string
  final_insights?: string
  insight_analysis?: string
  creator_concepts?: string
  selected_creator_option?: string
  required_metadata?: Record<string, string>
  missing_required_metadata?: string[]
  processing_time_seconds?: number
  workflow_mode?: 'interactive' | 'autonomous'
  current_step?: string
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

export interface UpdateConversationPayload {
  title: string
}

export interface AgentListItem {
  id: string
  name: string
  description: string
  display_order: number
  enabled: boolean
}

export interface ConversationState {
  conversation_id: string
  mode: 'interactive' | 'autonomous'
  current_step: string
  pipeline_status: string
  pending_prompt?: string | null
  updated_at: string
}

export interface ConversationStateUpdatePayload {
  mode?: 'interactive' | 'autonomous'
  current_step?: string
  pipeline_status?: string
  pending_prompt?: string | null
}

export interface AgentEvent {
  id?: string | null
  conversation_id: string
  agent_name: string
  status: string
  content?: string | null
  metadata?: Record<string, unknown> | null
  created_at: string
}
