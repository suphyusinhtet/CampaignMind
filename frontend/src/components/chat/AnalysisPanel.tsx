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
  { key: 'brief_analysis' as const, label: 'Brief Analysis', emoji: '📋' },
  { key: 'trend_analysis' as const, label: 'Trend Analysis', emoji: '📈' },
  { key: 'case_analysis' as const, label: 'Case Intelligence', emoji: '🔍' },
  { key: 'landscape_analysis' as const, label: 'Market Landscape', emoji: '🗺️' },
] as const

export function AnalysisPanel({ metadata }: AnalysisPanelProps) {
  const [openSection, setOpenSection] = useState<string | null>(null)

  const availableSections = SECTIONS.filter(({ key }) => !!metadata[key])

  if (availableSections.length === 0) return null

  return (
    <div className="space-y-1 mt-2">
      {metadata.processing_time_seconds !== undefined && (
        <p className="text-xs text-gray-400 px-1">
          Multi-agent pipeline completed in{' '}
          {metadata.processing_time_seconds.toFixed(1)}s
        </p>
      )}
      {availableSections.map(({ key, label, emoji }) => {
        const content = metadata[key]!
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
                  {content}
                </ReactMarkdown>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
