'use client'
import { useState, useEffect, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { ChatBox, Message } from '@/components/chat/ChatBox'
import { VoiceInput } from '@/components/voice/VoiceInput'
import { LiveRegion } from '@/components/a11y/LiveRegion'

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

function ConsultContent() {
  const params    = useSearchParams()
  const router    = useRouter()
  const sessionId = params.get('session')
  const caseId    = params.get('case')

  const [messages, setMessages]     = useState<Message[]>([])
  const [textInput, setTextInput]   = useState('')
  const [caseData, setCaseData]     = useState<{ patient_name: string; title: string } | null>(null)
  const [loading, setLoading]       = useState(false)
  const [ending, setEnding]         = useState(false)
  const [statusMsg, setStatusMsg]   = useState('')

  useEffect(() => {
    if (!caseId) return
    fetch(`${API}/api/cases/${caseId}/`)
      .then(r => r.json())
      .then(setCaseData)
  }, [caseId])

  async function sendMessage(content: string) {
    if (!content.trim() || loading) return
    const userMsg: Message = {
      id: Math.random().toString(36).slice(2),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMsg])
    setTextInput('')
    setLoading(true)
    setStatusMsg('Waiting for patient response...')

    try {
      const history = messages.map(m => ({ role: m.role, content: m.content }))
      const r = await fetch(`${API}/api/sessions/${sessionId}/chat/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: content, history }),
      })
      const data = await r.json()

      const patientMsg: Message = {
        id: Math.random().toString(36).slice(2),
        role: 'assistant',
        content: data.response,
        timestamp: new Date().toISOString(),
      }
      setMessages(prev => [...prev, patientMsg])
      setStatusMsg('Patient responded.')

      if (data.audio_b64) {
        const audio = new Audio(`data:audio/mpeg;base64,${data.audio_b64}`)
        audio.play().catch(() => {/* ignore autoplay policy blocks */})
      }
    } catch {
      setStatusMsg('Could not reach the server. Please check your connection.')
    } finally {
      setLoading(false)
    }
  }

  async function endConsultation() {
    if (ending) return
    setEnding(true)
    setStatusMsg('Ending consultation and generating feedback...')
    try {
      await fetch(`${API}/api/sessions/${sessionId}/complete/`, { method: 'POST' })
      router.push(`/feedback/${sessionId}`)
    } catch {
      setStatusMsg('Could not end session. Please try again.')
      setEnding(false)
    }
  }

  return (
    <main
      id="main-content"
      className="flex h-screen bg-[--color-bg-deep] overflow-hidden"
    >
      <LiveRegion message={statusMsg} type="status" clearAfter={5000} />

      {/* ── Avatar sidebar — desktop only ─────────────── */}
      <aside
        aria-hidden="true"
        className="w-[300px] shrink-0 bg-[--color-bg-surface] border-r border-[--color-border] hidden md:flex flex-col items-center justify-center gap-4 p-8"
      >
        <div className="w-24 h-24 rounded-full bg-[--color-bg-elevated] flex items-center justify-center text-4xl">
          🏥
        </div>
        {caseData && (
          <>
            <p className="text-lg font-semibold text-[--color-text-primary] text-center">
              {caseData.patient_name}
            </p>
            <p className="text-sm text-[--color-text-muted] text-center">
              {caseData.title}
            </p>
          </>
        )}
        <p className="text-xs text-[--color-text-muted] text-center mt-4">
          Powered by Groq · Llama 3.3 70B
        </p>
      </aside>

      {/* ── Chat panel ────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-h-0 min-w-0">

        {/* Header */}
        <header className="border-b border-[--color-border] px-4 md:px-6 py-3 md:py-4 flex items-center justify-between gap-3 shrink-0">
          <div className="min-w-0">
            <h1 className="text-base md:text-lg font-semibold text-[--color-text-primary] truncate">
              {caseData?.patient_name ?? 'Loading patient...'}
            </h1>
            <p className="text-xs md:text-sm text-[--color-text-secondary] truncate hidden sm:block">
              {caseData?.title}
            </p>
          </div>
          <button
            onClick={endConsultation}
            disabled={ending}
            aria-busy={ending}
            className="shrink-0 px-3 md:px-4 py-2 border border-[--color-border] text-[--color-text-secondary] rounded-lg hover:text-[--color-text-primary] hover:border-[--color-accent] transition-colors min-h-[44px] text-xs md:text-sm disabled:opacity-50 whitespace-nowrap"
          >
            {ending ? 'Ending...' : 'End & get feedback'}
          </button>
        </header>

        {/* Messages */}
        <div className="flex-1 min-h-0">
          {messages.length === 0 && !loading ? (
            <div className="flex items-center justify-center h-full text-[--color-text-muted] text-sm p-6 text-center">
              <p>
                Introduce yourself and ask the patient what brings them in today.
                <br />
                <span className="text-xs mt-1 block">Press Enter to send · Shift+Enter for new line</span>
              </p>
            </div>
          ) : (
            <ChatBox messages={messages} isLoading={loading} />
          )}
        </div>

        {/* Input area */}
        <div
          className="border-t border-[--color-border] p-3 md:p-4 shrink-0 bg-[--color-bg-surface]"
          role="region"
          aria-label="Send a message"
        >
          <div className="flex gap-2 md:gap-3 items-end">
            <div className="flex-1 min-w-0">
              <label htmlFor="chat-input" className="sr-only">
                Type your question to the patient
              </label>
              <textarea
                id="chat-input"
                value={textInput}
                onChange={e => setTextInput(e.target.value)}
                onKeyDown={e => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    sendMessage(textInput)
                  }
                }}
                placeholder="Type your question…"
                rows={2}
                disabled={loading}
                aria-disabled={loading}
                className="w-full bg-[--color-bg-deep] text-[--color-text-primary] border border-[--color-border] rounded-lg px-3 md:px-4 py-2 md:py-3 resize-none placeholder:text-[--color-text-muted] focus:outline-none focus:border-[--color-accent] text-sm md:text-base"
              />
            </div>
            <button
              onClick={() => sendMessage(textInput)}
              disabled={loading || !textInput.trim()}
              aria-label="Send message"
              className="shrink-0 px-3 md:px-4 py-2 md:py-3 bg-[--color-accent] text-[--color-bg-deep] rounded-lg hover:bg-[--color-accent-hover] transition-colors min-h-[44px] min-w-[44px] font-medium disabled:opacity-50 text-sm"
            >
              Send
            </button>
            <VoiceInput
              onTranscript={text => sendMessage(text)}
              disabled={loading}
            />
          </div>
        </div>
      </div>
    </main>
  )
}

export default function ConsultPage() {
  return (
    <Suspense fallback={<p className="p-8 text-[--color-text-secondary]">Loading consultation...</p>}>
      <ConsultContent />
    </Suspense>
  )
}
