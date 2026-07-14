'use client'
import { useState, useEffect, useRef } from 'react'

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface Filters {
  topic: string
  healthcare_system: string
  age_group: string
  gender: string
  sentiment: string
}

const TOPICS = ['', 'waiting_times', 'cost', 'mental_health', 'gp_access', 'staff', 'quality', 'general']
const SYSTEMS = ['', 'NHS', 'GP', 'Mental_Health', 'A_and_E', 'Private', 'Social_Care']
const AGE_GROUPS = ['', 'under_40', '40_to_60', 'over_60']
const GENDERS = ['', 'male', 'female']
const SENTIMENTS = ['', 'positive', 'negative', 'neutral', 'mixed']

export default function RepresentativePage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [filters, setFilters] = useState<Filters>({
    topic: '', healthcare_system: '', age_group: '', gender: '', sentiment: ''
  })
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  function setFilter(key: keyof Filters, val: string) {
    setFilters(prev => ({ ...prev, [key]: val }))
  }

  function resetFilters() {
    setFilters({ topic: '', healthcare_system: '', age_group: '', gender: '', sentiment: '' })
  }

  const activeFilterCount = Object.values(filters).filter(Boolean).length

  async function send() {
    const msg = input.trim()
    if (!msg || loading) return
    const userMsg: Message = { role: 'user', content: msg }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)
    // close filter panel on mobile when sending
    setFiltersOpen(false)

    try {
      const activeFilters = Object.fromEntries(
        Object.entries(filters).filter(([, v]) => v !== '')
      )
      const r = await fetch(`${API}/api/representative/chat/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: msg,
          history: messages,
          filters: activeFilters,
        }),
      })
      const data = await r.json()
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Could not reach the server.' }])
    } finally {
      setLoading(false)
    }
  }

  const personaLabel = [
    filters.gender, filters.age_group, filters.topic, filters.healthcare_system
  ].filter(Boolean).join(' · ') || 'General public'

  const filterPanel = (
    <div className="flex flex-col gap-4 p-6">
      <div>
        <h2 className="text-base font-semibold text-[--color-text-primary] mb-1">Patient Representative</h2>
        <p className="text-xs text-[--color-text-muted]">
          Speaks on behalf of real public opinions collected from healthcare interviews.
        </p>
      </div>

      <div className="flex flex-col gap-4">
        {([
          ['Topic', 'topic', TOPICS],
          ['Healthcare system', 'healthcare_system', SYSTEMS],
          ['Age group', 'age_group', AGE_GROUPS],
          ['Gender', 'gender', GENDERS],
          ['Sentiment', 'sentiment', SENTIMENTS],
        ] as [string, keyof Filters, string[]][]).map(([label, key, opts]) => (
          <div key={key}>
            <label className="block text-xs text-[--color-text-muted] mb-1">{label}</label>
            <select
              value={filters[key]}
              onChange={e => setFilter(key, e.target.value)}
              className="w-full bg-[--color-bg-deep] text-[--color-text-primary] border border-[--color-border] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[--color-accent]"
            >
              {opts.map(o => (
                <option key={o} value={o}>{o === '' ? 'Any' : o.replace(/_/g, ' ')}</option>
              ))}
            </select>
          </div>
        ))}
      </div>

      <button
        onClick={resetFilters}
        className="text-xs text-[--color-text-muted] hover:text-[--color-text-primary] underline text-left"
      >
        Reset filters
      </button>

      <div className="pt-4 border-t border-[--color-border]">
        <p className="text-xs text-[--color-text-muted]">Active persona</p>
        <p className="text-sm text-[--color-accent] font-medium mt-1">{personaLabel}</p>
      </div>
    </div>
  )

  return (
    <main className="flex h-screen bg-[--color-bg-deep] overflow-hidden">

      {/* ── Filters sidebar — desktop only ──────────────────────────── */}
      <aside className="w-[280px] shrink-0 bg-[--color-bg-surface] border-r border-[--color-border] hidden md:flex flex-col overflow-y-auto">
        {filterPanel}
      </aside>

      {/* ── Chat panel ──────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-h-0 min-w-0">

        <header className="border-b border-[--color-border] px-4 md:px-6 py-3 md:py-4 shrink-0 flex items-center gap-3">
          {/* Mobile filter toggle */}
          <button
            onClick={() => setFiltersOpen(v => !v)}
            aria-label={filtersOpen ? 'Close filters' : 'Open filters'}
            className="md:hidden shrink-0 w-10 h-10 flex items-center justify-center rounded-lg border border-[--color-border] text-[--color-text-secondary] relative"
          >
            {/* hamburger / X icon */}
            {filtersOpen ? (
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="2" y1="2" x2="14" y2="14"/><line x1="14" y1="2" x2="2" y2="14"/>
              </svg>
            ) : (
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="2" y1="4" x2="14" y2="4"/><line x1="2" y1="8" x2="14" y2="8"/><line x1="2" y1="12" x2="14" y2="12"/>
              </svg>
            )}
            {activeFilterCount > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-[--color-accent] text-[--color-bg-deep] text-[10px] font-bold rounded-full flex items-center justify-center">
                {activeFilterCount}
              </span>
            )}
          </button>

          <div className="min-w-0">
            <h1 className="text-base md:text-lg font-semibold text-[--color-text-primary]">Patient Representative</h1>
            <p className="text-xs md:text-sm text-[--color-text-secondary] hidden sm:block">
              Ask about patient views on healthcare
            </p>
          </div>
        </header>

        {/* Mobile filter drawer — slides in below header */}
        {filtersOpen && (
          <div className="md:hidden bg-[--color-bg-surface] border-b border-[--color-border] overflow-y-auto max-h-[60vh]">
            {filterPanel}
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 md:px-6 py-4 flex flex-col gap-4">
          {messages.length === 0 && (
            <div className="flex items-center justify-center h-full text-[--color-text-muted] text-sm text-center">
              <p>
                Ask about patient experiences, opinions, or feelings on any healthcare topic.
                <br />
                <span className="text-xs mt-1 block">Use the filters to represent a specific demographic.</span>
              </p>
            </div>
          )}
          {messages.map((m, i) => (
            <div
              key={i}
              className={`max-w-[85%] md:max-w-[75%] px-4 py-3 rounded-xl text-sm leading-relaxed ${
                m.role === 'user'
                  ? 'self-end bg-[--color-accent] text-[--color-bg-deep]'
                  : 'self-start bg-[--color-bg-surface] text-[--color-text-primary] border border-[--color-border]'
              }`}
            >
              {m.content}
            </div>
          ))}
          {loading && (
            <div className="self-start bg-[--color-bg-surface] border border-[--color-border] px-4 py-3 rounded-xl text-sm text-[--color-text-muted]">
              Thinking…
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="border-t border-[--color-border] p-3 md:p-4 shrink-0 bg-[--color-bg-surface]">
          <div className="flex gap-2 md:gap-3 items-end">
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
              placeholder="Ask a question…"
              rows={2}
              disabled={loading}
              className="flex-1 min-w-0 bg-[--color-bg-deep] text-[--color-text-primary] border border-[--color-border] rounded-lg px-3 md:px-4 py-2 md:py-3 resize-none placeholder:text-[--color-text-muted] focus:outline-none focus:border-[--color-accent] text-sm md:text-base"
            />
            <button
              onClick={send}
              disabled={loading || !input.trim()}
              className="shrink-0 px-3 md:px-4 py-2 md:py-3 bg-[--color-accent] text-[--color-bg-deep] rounded-lg hover:bg-[--color-accent-hover] transition-colors min-h-[44px] min-w-[44px] font-medium disabled:opacity-50 text-sm"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </main>
  )
}
