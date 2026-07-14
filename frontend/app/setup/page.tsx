'use client'
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

interface Case {
  id: string
  title: string
  patient_name: string
  age: number
  gender: string
  condition: string
  difficulty: string
  specialty: string
}

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export default function SetupPage() {
  const router = useRouter()
  const [cases, setCases] = useState<Case[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState('')
  const [filterSpec, setFilterSpec] = useState('all')
  const [filterDiff, setFilterDiff] = useState('all')

  useEffect(() => {
    fetch(`${API}/api/cases/`)
      .then(r => r.json())
      .then(data => { setCases(data); setLoading(false) })
      .catch(() => {
        setError('Could not load cases. Is the Django server running on port 8000?')
        setLoading(false)
      })
  }, [])

  const filtered = cases.filter(c =>
    (filterSpec === 'all' || c.specialty === filterSpec) &&
    (filterDiff === 'all' || c.difficulty === filterDiff)
  )

  async function startSession() {
    if (!selected || starting) return
    setStarting(true)
    setError('')
    try {
      const r = await fetch(`${API}/api/sessions/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ case_id: selected }),
      })
      if (!r.ok) throw new Error('Failed to create session')
      const { id } = await r.json()
      router.push(`/consult?session=${id}&case=${selected}`)
    } catch {
      setError('Could not start session. Please try again.')
      setStarting(false)
    }
  }

  const difficultyBadge = (d: string) => {
    const map: Record<string, string> = {
      foundation: 'bg-emerald-900 text-emerald-300',
      core:       'bg-amber-900 text-amber-300',
      advanced:   'bg-red-900 text-red-300',
    }
    return map[d] ?? 'bg-gray-800 text-gray-300'
  }

  return (
    <main id="main-content" className="max-w-4xl mx-auto px-6 py-12">
      <h1 className="font-display text-3xl text-[--color-text-primary] mb-2">
        Choose a patient
      </h1>
      <p className="text-[--color-text-secondary] mb-8">
        Select a case to begin your consultation.
      </p>

      {/* ── Filters ─────────────────────────────────────── */}
      <div className="flex gap-4 mb-6 flex-wrap" role="group" aria-label="Filter cases">
        <div>
          <label htmlFor="filter-specialty" className="block text-sm text-[--color-text-secondary] mb-1">
            Specialty
          </label>
          <select
            id="filter-specialty"
            value={filterSpec}
            onChange={e => setFilterSpec(e.target.value)}
            className="bg-[--color-bg-surface] text-[--color-text-primary] border border-[--color-border] rounded-md px-3 py-2 min-h-[44px]"
          >
            <option value="all">All specialties</option>
            <option value="cardiology">Cardiology</option>
            <option value="respiratory">Respiratory</option>
            <option value="psychiatry">Psychiatry</option>
            <option value="endocrine">Endocrine</option>
            <option value="neurology">Neurology</option>
            <option value="musculoskeletal">Musculoskeletal</option>
            <option value="gastro">Gastroenterology</option>
            <option value="general">General Practice</option>
          </select>
        </div>

        <div>
          <label htmlFor="filter-difficulty" className="block text-sm text-[--color-text-secondary] mb-1">
            Difficulty
          </label>
          <select
            id="filter-difficulty"
            value={filterDiff}
            onChange={e => setFilterDiff(e.target.value)}
            className="bg-[--color-bg-surface] text-[--color-text-primary] border border-[--color-border] rounded-md px-3 py-2 min-h-[44px]"
          >
            <option value="all">All levels</option>
            <option value="foundation">Foundation</option>
            <option value="core">Core</option>
            <option value="advanced">Advanced</option>
          </select>
        </div>
      </div>

      {/* ── Error ───────────────────────────────────────── */}
      {error && (
        <p role="alert" className="text-[--color-error] mb-4 p-3 bg-red-950 rounded-lg border border-red-800">
          {error}
        </p>
      )}

      {/* ── Case list ───────────────────────────────────── */}
      {loading ? (
        <p aria-live="polite" className="text-[--color-text-secondary]">Loading cases...</p>
      ) : filtered.length === 0 ? (
        <p className="text-[--color-text-muted]">No cases match your filters.</p>
      ) : (
        <ul
          role="listbox"
          aria-label="Patient cases"
          aria-required="true"
          className="grid md:grid-cols-2 gap-4 mb-8"
        >
          {filtered.map(c => (
            <li
              key={c.id}
              role="option"
              aria-selected={selected === c.id}
              onClick={() => setSelected(c.id)}
              onKeyDown={e => (e.key === 'Enter' || e.key === ' ') && setSelected(c.id)}
              tabIndex={0}
              className={`cursor-pointer rounded-xl p-5 border-2 transition-colors ${
                selected === c.id
                  ? 'border-[--color-accent] bg-[--color-bg-elevated]'
                  : 'border-[--color-border] bg-[--color-bg-surface] hover:border-[--color-accent]'
              }`}
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <h2 className="text-base font-semibold text-[--color-text-primary]">
                  {c.title}
                </h2>
                {/* 1.4.1: difficulty conveyed as text + colour */}
                <span className={`text-xs px-2 py-1 rounded-full font-medium shrink-0 ${difficultyBadge(c.difficulty)}`}>
                  {c.difficulty}
                </span>
              </div>
              <p className="text-sm text-[--color-text-secondary]">{c.condition}</p>
              <p className="text-xs text-[--color-text-muted] mt-1">
                {c.patient_name} · {c.age} · {c.gender} · <span className="capitalize">{c.specialty}</span>
              </p>
            </li>
          ))}
        </ul>
      )}

      {/* ── Action ──────────────────────────────────────── */}
      {!selected && (
        <p id="case-required" className="text-[--color-text-muted] text-sm mb-4">
          Select a patient case above to continue.
        </p>
      )}

      <button
        onClick={startSession}
        disabled={!selected || starting}
        aria-disabled={!selected || starting}
        aria-describedby={!selected ? 'case-required' : undefined}
        aria-busy={starting}
        className="px-8 py-4 bg-[--color-accent] text-[--color-bg-deep] font-semibold rounded-lg hover:bg-[--color-accent-hover] transition-colors min-h-[44px] disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {starting ? 'Starting...' : 'Begin consultation'}
      </button>
    </main>
  )
}
