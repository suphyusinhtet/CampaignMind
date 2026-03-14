'use client'
import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { ChevronDown, ChevronRight } from 'lucide-react'
import type { AnalysisMetadata } from '@/types'

interface AnalysisPanelProps {
  metadata: AnalysisMetadata
}

const SECTIONS = [
  {
    key: 'brief_analysis',
    label: 'Brief Analysis',
    emoji: '📋',
    getContent: (metadata: AnalysisMetadata) => metadata.brief_analysis,
  },
  {
    key: 'trend_analysis',
    label: 'Trend Analysis',
    emoji: '📈',
    getContent: (metadata: AnalysisMetadata) => metadata.trend_analysis,
  },
  {
    key: 'case_analysis',
    label: 'Case Intelligence',
    emoji: '🔍',
    getContent: (metadata: AnalysisMetadata) => metadata.case_analysis,
  },
  {
    key: 'landscape_analysis',
    label: 'Market Landscape',
    emoji: '🗺️',
    getContent: (metadata: AnalysisMetadata) => metadata.landscape_analysis,
  },
  {
    key: 'final_insights',
    label: 'Insight Generator',
    emoji: '💡',
    getContent: (metadata: AnalysisMetadata) =>
      metadata.final_insights || metadata.insight_analysis,
  },
  {
    key: 'creator_concepts',
    label: 'Creator Agent',
    emoji: '🎨',
    getContent: (metadata: AnalysisMetadata) => metadata.creator_concepts,
  },
] as const

export function AnalysisPanel({ metadata }: AnalysisPanelProps) {
  const [openSection, setOpenSection] = useState<string | null>(null)

  const availableSections = SECTIONS.map((section) => ({
    ...section,
    content: section.getContent(metadata),
  })).filter((section) => !!section.content)

  if (availableSections.length === 0) return null

  return (
    <div className="space-y-1 mt-2">
      {metadata.processing_time_seconds !== undefined && (
        <p className="text-xs text-gray-400 px-1">
          Multi-agent pipeline completed in{' '}
          {metadata.processing_time_seconds.toFixed(1)}s
        </p>
      )}
      {availableSections.map(({ key, label, emoji, content }) => {
        const isOpen = openSection === key

        return (
          <div
            key={key}
            className="overflow-hidden rounded-lg border border-gray-200"
          >
            <button
              onClick={() => setOpenSection(isOpen ? null : key)}
              className="flex w-full items-center justify-between px-4 py-2.5 text-sm text-gray-600 hover:bg-gray-50 transition-colors"
            >
              <span className="flex items-center gap-2 font-medium">
                <span>{emoji}</span>
                {label}
              </span>
              {isOpen ? (
                <ChevronDown size={14} />
              ) : (
                <ChevronRight size={14} />
              )}
            </button>
            {isOpen && (
              <div className="border-t border-gray-100 px-4 py-3 prose prose-sm prose-gray max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {content ?? ''}
                </ReactMarkdown>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
