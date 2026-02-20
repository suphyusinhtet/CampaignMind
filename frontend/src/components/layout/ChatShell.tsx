'use client'

import { useEffect, useState } from 'react'
import { usePathname } from 'next/navigation'
import { Menu, X, Zap } from 'lucide-react'
import { Sidebar } from '@/components/sidebar/Sidebar'

interface ChatShellProps {
  children: React.ReactNode
  userEmail: string | null
  authEnabled: boolean
}

export function ChatShell({ children, userEmail, authEnabled }: ChatShellProps) {
  const pathname = usePathname()
  const [drawerOpen, setDrawerOpen] = useState(false)

  useEffect(() => {
    setDrawerOpen(false)
  }, [pathname])

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar userEmail={userEmail} authEnabled={authEnabled} className="hidden md:flex" />

      <div className="fixed inset-x-0 top-0 z-40 border-b border-zinc-200 bg-[#f7f7f8]/95 backdrop-blur md:hidden">
        <div className="flex h-14 items-center justify-between px-3">
          <button
            onClick={() => setDrawerOpen(true)}
            className="rounded-lg p-2 text-zinc-700 hover:bg-zinc-200/70"
            aria-label="Open sidebar"
          >
            <Menu size={18} />
          </button>
          <div className="flex items-center gap-2 text-sm font-medium text-zinc-900">
            <Zap size={14} className="text-emerald-500" />
            CampaignMind
          </div>
          <div className="w-9" />
        </div>
      </div>

      {drawerOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <button
            aria-label="Close sidebar backdrop"
            className="absolute inset-0 bg-black/40"
            onClick={() => setDrawerOpen(false)}
          />
          <div className="absolute inset-y-0 left-0 z-10 flex w-72 flex-col">
            <div className="flex h-14 items-center justify-end border-b border-[#2f2f2f] bg-[#171717] px-3">
              <button
                onClick={() => setDrawerOpen(false)}
                className="rounded-lg p-2 text-zinc-300 hover:bg-zinc-800"
                aria-label="Close sidebar"
              >
                <X size={18} />
              </button>
            </div>
            <Sidebar userEmail={userEmail} authEnabled={authEnabled} className="w-72 border-r-0" />
          </div>
        </div>
      )}

      <main className="flex min-w-0 flex-1 flex-col overflow-hidden bg-[#f7f7f8] pt-14 md:pt-0">
        {children}
      </main>
    </div>
  )
}
