'use client'
import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer } from 'recharts'
import { LiveRegion } from '@/components/a11y/LiveRegion'

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

const DOMAIN_LABELS: Record<string, string> = {
  presenting_complaint: 'Presenting Complaint',
  history_of_pc:        'History of PC',
  past_medical_history: 'Past Medical History',
  drug_history:         'Drug History & Allergies',
  family_history:       'Family History',
  social_history:       'Social History',
  ice:                  'ICE',
  systems_review:       'Systems Review',
  summarising:          'Summarising',
  communication:        'Communication',
}

interface FeedbackData {
  overall_score:               number
  history_score:               number
  domain_scores:               Record<string, number>
  missed_questions:            string[]
  diagnosis_correct:           boolean
  diagnosis_feedback:          string
  narrative_feedback:          string
  keyword_checks:              Record<string, boolean | null>
  clinical_reasoning_score:    number
  primary_diagnosis_correct:   boolean
  primary_diagnosis_score:     number
  differential_quality_score:  number
  management_plan_score:       number
  reasoning_score:             number
  primary_diagnosis_feedback:  string
  differential_feedback:       string
  management_feedback:         string
  safety_netting:              boolean
  safety_netting_feedback:     string
  submitted_primary_diagnosis: string
  submitted_differentials:     string
  submitted_management_plan:   string
}

// ─── Sub-components (unchanged) ──────────────────────────────────────────────

function ScoreBadge({ score, label }: { score: number; label?: string }) {
  const grade = score >= 80 ? 'Distinction' : score >= 60 ? 'Pass' : 'Below Pass'
  const color =
    score >= 80 ? 'bg-emerald-900 text-emerald-300 border-emerald-700' :
    score >= 60 ? 'bg-amber-900 text-amber-300 border-amber-700' :
                  'bg-red-900 text-red-300 border-red-700'
  return (
    <div className={`inline-flex flex-col items-center px-5 py-3 rounded-xl border ${color}`}>
      <span className="text-3xl font-bold">{score}%</span>
      <span className="text-xs font-medium mt-0.5 opacity-80">{label ?? grade}</span>
    </div>
  )
}

function MiniScore({ score, label }: { score: number; label: string }) {
  const color = score >= 8 ? 'text-emerald-400' : score >= 6 ? 'text-amber-400' : 'text-red-400'
  return (
    <div className="flex items-center justify-between py-2">
      <span className="text-sm text-[--color-text-secondary]">{label}</span>
      <div className="flex items-center gap-2">
        <div className="w-20 h-1.5 bg-[--color-bg-deep] rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full ${score >= 8 ? 'bg-emerald-500' : score >= 6 ? 'bg-amber-500' : 'bg-red-500'}`}
            style={{ width: `${score * 10}%` }}
          />
        </div>
        <span className={`text-sm font-semibold ${color} w-10 text-right`}>{score}/10</span>
      </div>
    </div>
  )
}

function CorrectnessBadge({ correct }: { correct: boolean }) {
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
      correct ? 'bg-emerald-900 text-emerald-300' : 'bg-red-900 text-red-300'
    }`}>
      <span aria-hidden="true">{correct ? '✓' : '✗'}</span>
      {correct ? 'Correct' : 'Incorrect'}
    </span>
  )
}

// ─── Pre-feedback submission screen ──────────────────────────────────────────

interface SubmissionFormProps {
  onSubmit: (primary: string, differentials: string, management: string) => void
}

function SubmissionForm({ onSubmit }: SubmissionFormProps) {
  const [primary, setPrimary]           = useState('')
  const [differentials, setDifferentials] = useState('')
  const [management, setManagement]     = useState('')
  const [attempted, setAttempted]       = useState(false)

  function handleSubmit() {
    setAttempted(true)
    if (!primary.trim()) return
    onSubmit(primary.trim(), differentials.trim(), management.trim())
  }

  return (
    <main
      id="main-content"
      className="min-h-screen flex items-center justify-center px-4 py-12 bg-[--color-bg-deep]"
    >
      <div className="w-full max-w-lg">

        {/* Header */}
        <div className="mb-8 text-center">
          <div className="w-14 h-14 rounded-full bg-[--color-bg-surface] border border-[--color-border] flex items-center justify-center text-2xl mx-auto mb-4">
            🩺
          </div>
          <h1 className="text-2xl font-semibold text-[--color-text-primary] mb-2">
            Before we score your consultation…
          </h1>
          <p className="text-sm text-[--color-text-secondary]">
            Submit your clinical assessment. This is evaluated as part of your OSCE score.
          </p>
        </div>

        <div className="bg-[--color-bg-surface] rounded-2xl border border-[--color-border] divide-y divide-[--color-border] overflow-hidden">

          {/* Required: Primary diagnosis */}
          <div className="p-5">
            <label
              htmlFor="primary-diagnosis"
              className="block text-sm font-semibold text-[--color-text-primary] mb-1"
            >
              Primary diagnosis
              <span className="ml-1 text-red-400" aria-label="required">*</span>
            </label>
            <p className="text-xs text-[--color-text-muted] mb-3">
              What is the most likely diagnosis based on your consultation?
            </p>
            <input
              id="primary-diagnosis"
              type="text"
              value={primary}
              onChange={e => setPrimary(e.target.value)}
              placeholder="e.g. Atrial fibrillation"
              aria-required="true"
              aria-invalid={attempted && !primary.trim() ? 'true' : 'false'}
              className={`w-full bg-[--color-bg-deep] text-[--color-text-primary] border rounded-lg px-4 py-3 text-sm placeholder:text-[--color-text-muted] focus:outline-none focus:border-[--color-accent] transition-colors ${
                attempted && !primary.trim()
                  ? 'border-red-500'
                  : 'border-[--color-border]'
              }`}
            />
            {attempted && !primary.trim() && (
              <p role="alert" className="text-xs text-red-400 mt-1">
                A primary diagnosis is required to generate your feedback.
              </p>
            )}
          </div>

          {/* Optional: Differentials */}
          <div className="p-5">
            <label
              htmlFor="differentials"
              className="block text-sm font-semibold text-[--color-text-primary] mb-1"
            >
              Differential diagnoses
              <span className="ml-2 text-xs text-[--color-text-muted] font-normal">Optional</span>
            </label>
            <p className="text-xs text-[--color-text-muted] mb-3">
              List other diagnoses you considered, one per line.
            </p>
            <textarea
              id="differentials"
              value={differentials}
              onChange={e => setDifferentials(e.target.value)}
              placeholder={"e.g. SVT\nAnxiety\nThyrotoxicosis"}
              rows={3}
              className="w-full bg-[--color-bg-deep] text-[--color-text-primary] border border-[--color-border] rounded-lg px-4 py-3 text-sm placeholder:text-[--color-text-muted] focus:outline-none focus:border-[--color-accent] resize-none transition-colors"
            />
          </div>

          {/* Optional: Management plan */}
          <div className="p-5">
            <label
              htmlFor="management-plan"
              className="block text-sm font-semibold text-[--color-text-primary] mb-1"
            >
              Management plan
              <span className="ml-2 text-xs text-[--color-text-muted] font-normal">Optional</span>
            </label>
            <p className="text-xs text-[--color-text-muted] mb-3">
              How would you investigate and manage this patient?
            </p>
            <textarea
              id="management-plan"
              value={management}
              onChange={e => setManagement(e.target.value)}
              placeholder={"e.g. ECG to confirm diagnosis\nRate control with beta-blocker\nAnticoagulation — calculate CHA₂DS₂-VASc\nRefer to cardiology"}
              rows={4}
              className="w-full bg-[--color-bg-deep] text-[--color-text-primary] border border-[--color-border] rounded-lg px-4 py-3 text-sm placeholder:text-[--color-text-muted] focus:outline-none focus:border-[--color-accent] resize-none transition-colors"
            />
          </div>
        </div>

        <button
          onClick={handleSubmit}
          className="w-full mt-6 py-3 bg-[--color-accent] text-[--color-bg-deep] rounded-xl font-semibold hover:bg-[--color-accent-hover] transition-colors min-h-[48px] text-base"
        >
          Submit &amp; get feedback
        </button>

        <p className="text-center text-xs text-[--color-text-muted] mt-4">
          Optional fields are still scored — leaving them blank will result in 0 for those domains.
        </p>
      </div>
    </main>
  )
}

// ─── Main feedback page ───────────────────────────────────────────────────────

export default function FeedbackPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const router        = useRouter()

  // Gate: null = not yet submitted, object = submitted values
  const [submission, setSubmission] = useState<{
    primary: string; differentials: string; management: string
  } | null>(null)

  const [data, setData]       = useState<FeedbackData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  // Only fetch feedback once the learner has submitted the form
  useEffect(() => {
    if (!submission || !sessionId) return
    setLoading(true)
    fetch(`${API}/api/feedback/${sessionId}/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        primary_diagnosis: submission.primary,
        differentials:     submission.differentials,
        management_plan:   submission.management,
      }),
    })
      .then(r => {
        if (!r.ok) throw new Error('Feedback generation failed')
        return r.json()
      })
      .then(d => { setData(d); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [submission, sessionId])

  // ── Step 1: intercept form ────────────────────────────────────────────────
  if (!submission) {
    return (
      <SubmissionForm
        onSubmit={(primary, differentials, management) =>
          setSubmission({ primary, differentials, management })
        }
      />
    )
  }

  // ── Step 2: loading ───────────────────────────────────────────────────────
  if (loading) {
    return (
      <main id="main-content" className="min-h-screen flex items-center justify-center">
        <div role="status" aria-live="polite" className="text-center">
          <div className="w-12 h-12 border-4 border-[--color-accent] border-t-transparent rounded-full animate-spin mx-auto mb-6" aria-hidden="true" />
          <p className="text-[--color-text-secondary] text-lg font-medium">Generating OSCE feedback…</p>
          <p className="text-[--color-text-muted] text-sm mt-2">Scoring history-taking across 10 domains</p>
          <p className="text-[--color-text-muted] text-sm">Evaluating clinical reasoning and management plan</p>
        </div>
      </main>
    )
  }

  // ── Step 3: error ─────────────────────────────────────────────────────────
  if (error || !data) {
    return (
      <main id="main-content" className="min-h-screen flex items-center justify-center px-6">
        <div role="alert" className="text-center max-w-md">
          <p className="text-[--color-error] text-lg mb-4">{error || 'Could not load feedback.'}</p>
          <button
            onClick={() => router.push('/setup')}
            className="px-6 py-3 bg-[--color-accent] text-[--color-bg-deep] rounded-lg font-semibold min-h-[44px]"
          >
            Try another case
          </button>
        </div>
      </main>
    )
  }

  // ── Step 4: results (unchanged layout) ───────────────────────────────────
  const radarData = Object.entries(data.domain_scores).map(([key, score]) => ({
    subject: DOMAIN_LABELS[key]?.replace(' & Allergies', '') ?? key,
    score,
    fullMark: 10,
  }))

  return (
    <main id="main-content" className="max-w-4xl mx-auto px-4 md:px-6 py-10 md:py-12">
      <LiveRegion message={`Feedback loaded. Overall score: ${data.overall_score} percent.`} type="status" />

      {/* Header */}
      <div className="flex items-start justify-between mb-10 flex-wrap gap-6">
        <div>
          <h1 className="font-display text-2xl md:text-3xl text-[--color-text-primary] mb-2">OSCE Feedback Report</h1>
          <p className="text-[--color-text-secondary]">History-taking · Clinical reasoning · Management</p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          <div className="text-center">
            <p className="text-xs text-[--color-text-muted] mb-1">History</p>
            <ScoreBadge score={data.history_score} label="History" />
          </div>
          <div className="text-center">
            <p className="text-xs text-[--color-text-muted] mb-1">Reasoning</p>
            <ScoreBadge score={data.clinical_reasoning_score} label="Reasoning" />
          </div>
          <div className="text-center">
            <p className="text-xs text-[--color-text-muted] mb-1">Overall</p>
            <ScoreBadge score={data.overall_score} />
          </div>
        </div>
      </div>

      {/* Examiner narrative */}
      <section aria-labelledby="narrative-heading" className="mb-10">
        <h2 id="narrative-heading" className="text-xl font-semibold text-[--color-text-primary] mb-4">Examiner's comments</h2>
        <blockquote className="bg-[--color-bg-surface] border-l-4 border-[--color-accent] rounded-r-xl px-6 py-5">
          <p className="text-[--color-text-primary] text-base leading-relaxed italic">{data.narrative_feedback}</p>
        </blockquote>
      </section>

      {/* Clinical reasoning */}
      <section aria-labelledby="reasoning-heading" className="mb-10">
        <h2 id="reasoning-heading" className="text-xl font-semibold text-[--color-text-primary] mb-4">Clinical Reasoning</h2>
        <div className="bg-[--color-bg-surface] rounded-xl border border-[--color-border] divide-y divide-[--color-border]">

          <div className="p-5">
            <div className="flex items-start justify-between gap-4 mb-2">
              <div>
                <p className="text-sm font-medium text-[--color-text-muted] uppercase tracking-wider mb-1">Primary Diagnosis</p>
                <p className="text-base font-semibold text-[--color-text-primary]">
                  {data.submitted_primary_diagnosis || <span className="italic text-[--color-text-muted]">Not submitted</span>}
                </p>
              </div>
              <CorrectnessBadge correct={data.primary_diagnosis_correct} />
            </div>
            <p className="text-sm text-[--color-text-secondary] mt-2">{data.primary_diagnosis_feedback}</p>
            <div className="mt-3">
              <MiniScore score={data.primary_diagnosis_score} label="Diagnosis score" />
            </div>
          </div>

          <div className="p-5">
            <p className="text-sm font-medium text-[--color-text-muted] uppercase tracking-wider mb-2">Differential Diagnoses</p>
            {data.submitted_differentials
              ? <p className="text-sm text-[--color-text-primary] whitespace-pre-line mb-2">{data.submitted_differentials}</p>
              : <p className="text-sm italic text-[--color-text-muted] mb-2">Not submitted</p>
            }
            <p className="text-sm text-[--color-text-secondary]">{data.differential_feedback}</p>
            <div className="mt-3">
              <MiniScore score={data.differential_quality_score} label="Differential quality" />
            </div>
          </div>

          <div className="p-5">
            <p className="text-sm font-medium text-[--color-text-muted] uppercase tracking-wider mb-2">Management Plan</p>
            {data.submitted_management_plan
              ? <p className="text-sm text-[--color-text-primary] whitespace-pre-line mb-2">{data.submitted_management_plan}</p>
              : <p className="text-sm italic text-[--color-text-muted] mb-2">Not submitted</p>
            }
            <p className="text-sm text-[--color-text-secondary]">{data.management_feedback}</p>
            <div className="mt-3 divide-y divide-[--color-border]">
              <MiniScore score={data.management_plan_score} label="Management plan" />
              <MiniScore score={data.reasoning_score} label="Overall clinical reasoning" />
            </div>
            <div className={`mt-3 flex items-start gap-3 p-3 rounded-lg ${
              data.safety_netting ? 'bg-emerald-950 border border-emerald-800' : 'bg-amber-950 border border-amber-800'
            }`}>
              <span className="text-lg" aria-hidden="true">{data.safety_netting ? '🛡️' : '⚠️'}</span>
              <div>
                <p className={`text-sm font-medium ${data.safety_netting ? 'text-emerald-300' : 'text-amber-300'}`}>
                  Safety netting: {data.safety_netting ? 'Present' : 'Missing'}
                </p>
                <p className="text-xs text-[--color-text-secondary] mt-0.5">{data.safety_netting_feedback}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Radar + domain scores */}
      <div className="grid md:grid-cols-2 gap-8 mb-10">
        <section aria-labelledby="radar-heading">
          <h2 id="radar-heading" className="text-xl font-semibold text-[--color-text-primary] mb-4">History-taking overview</h2>
          <div className="bg-[--color-bg-surface] rounded-xl p-4" aria-hidden="true">
            <ResponsiveContainer width="100%" height={280}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#0A7A9A" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#A8D5E2', fontSize: 10 }} />
                <Radar name="Score" dataKey="score" stroke="#02C39A" fill="#02C39A" fillOpacity={0.25} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
          <p className="sr-only">{radarData.map(d => `${d.subject}: ${d.score} out of 10`).join(', ')}</p>
        </section>

        <section aria-labelledby="domains-heading">
          <h2 id="domains-heading" className="text-xl font-semibold text-[--color-text-primary] mb-4">Domain scores</h2>
          <ul role="list" className="flex flex-col gap-2">
            {Object.entries(data.domain_scores).map(([key, score]) => {
              const pct = (score / 10) * 100
              const barColor = score >= 8 ? 'bg-emerald-500' : score >= 6 ? 'bg-amber-500' : 'bg-red-500'
              return (
                <li key={key} className="bg-[--color-bg-surface] rounded-lg px-4 py-3">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm text-[--color-text-secondary]">{DOMAIN_LABELS[key] ?? key}</span>
                    <span className="text-sm font-semibold text-[--color-text-primary]">{score}/10</span>
                  </div>
                  <div
                    className="h-1.5 bg-[--color-bg-deep] rounded-full overflow-hidden"
                    role="progressbar"
                    aria-valuenow={score}
                    aria-valuemin={0}
                    aria-valuemax={10}
                    aria-label={`${DOMAIN_LABELS[key]}: ${score} out of 10`}
                  >
                    <div className={`h-full rounded-full transition-all ${barColor}`} style={{ width: `${pct}%` }} />
                  </div>
                </li>
              )
            })}
          </ul>
        </section>
      </div>

      {/* Missed questions */}
      {data.missed_questions.length > 0 && (
        <section aria-labelledby="missed-heading" className="mb-10">
          <h2 id="missed-heading" className="text-xl font-semibold text-[--color-text-primary] mb-4">Questions you didn't ask</h2>
          <ul role="list" className="bg-[--color-bg-surface] rounded-xl divide-y divide-[--color-border]">
            {data.missed_questions.map((q, i) => (
              <li key={i} className="px-5 py-3 text-[--color-text-secondary] text-sm flex items-start gap-3">
                <span className="text-[--color-error] mt-0.5 shrink-0" aria-hidden="true">–</span>
                {q}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Actions */}
      <div className="flex gap-4 flex-wrap">
        <button
          onClick={() => router.push('/setup')}
          className="px-6 py-3 bg-[--color-accent] text-[--color-bg-deep] rounded-lg font-semibold hover:bg-[--color-accent-hover] transition-colors min-h-[44px]"
        >
          Try another case
        </button>
        <button
          onClick={() => window.print()}
          className="px-6 py-3 border border-[--color-border] text-[--color-text-secondary] rounded-lg hover:border-[--color-accent] hover:text-[--color-text-primary] transition-colors min-h-[44px]"
        >
          Print / Save PDF
        </button>
      </div>
    </main>
  )
}
