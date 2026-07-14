'use client'
import { useState, useCallback } from 'react'
import { Mic, Square } from 'lucide-react'
import { Button } from '../ui/Button'
import { LiveRegion } from '../a11y/LiveRegion'

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

interface VoiceInputProps {
  onTranscript: (text: string) => void
  disabled?: boolean
}

/**
 * WCAG compliance:
 * - 1.4.1: recording state uses icon + label + colour (not colour alone)
 * - 4.1.3: status announced via LiveRegion
 * - 2.1.1: Space/Enter starts/stops recording
 * - 1.4.2: no auto-playing audio
 */
export function VoiceInput({ onTranscript, disabled }: VoiceInputProps) {
  const [recording, setRecording] = useState(false)
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null)
  const [statusMsg, setStatusMsg] = useState('')
  const [error, setError] = useState('')

  const start = useCallback(async () => {
    setError('')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mr = new MediaRecorder(stream)
      const chunks: BlobPart[] = []

      mr.ondataavailable = e => chunks.push(e.data)
      mr.onstop = async () => {
        const blob = new Blob(chunks, { type: 'audio/webm' })
        stream.getTracks().forEach(t => t.stop())
        setStatusMsg('Processing speech...')

        // Send to Django STT endpoint
        try {
          const form = new FormData()
          form.append('audio', blob, 'recording.webm')
          const r = await fetch(`${API}/api/stt/`, { method: 'POST', body: form })
          if (r.ok) {
            const { transcript } = await r.json()
            onTranscript(transcript)
            setStatusMsg('Transcription complete.')
          } else {
            // Fallback — placeholder so session can continue without STT
            setStatusMsg('Transcription unavailable. Please type instead.')
          }
        } catch {
          setStatusMsg('Could not reach STT service. Please type instead.')
        }
      }

      mr.start()
      setMediaRecorder(mr)
      setRecording(true)
      setStatusMsg('Recording started. Press Stop when finished.')
    } catch {
      setError('Microphone access denied. Please allow microphone access and try again.')
    }
  }, [onTranscript])

  const stop = useCallback(() => {
    mediaRecorder?.stop()
    setMediaRecorder(null)
    setRecording(false)
    setStatusMsg('Recording stopped.')
  }, [mediaRecorder])

  return (
    <div className="flex items-center gap-3">
      {/* 4.1.3 — status live regions */}
      <LiveRegion message={statusMsg} type="status" clearAfter={4000} />
      <LiveRegion message={error} type="alert" />

      <Button
        variant={recording ? 'danger' : 'secondary'}
        onClick={recording ? stop : start}
        disabled={disabled}
        aria-label={recording ? 'Stop recording' : 'Start voice recording'}
        aria-pressed={recording}
      >
        {/* 1.4.1 — icon + label, not colour alone */}
        {recording ? (
          <><Square size={18} aria-hidden="true" /><span>Stop</span></>
        ) : (
          <><Mic size={18} aria-hidden="true" /><span>Speak</span></>
        )}
      </Button>

      {/* Visible recording indicator — 1.4.1 */}
      {recording && (
        <span
          className="flex items-center gap-2 text-[--color-error] text-sm"
          aria-hidden="true"
        >
          <span className="w-2 h-2 rounded-full bg-[--color-error] animate-pulse" />
          Recording
        </span>
      )}

      {error && (
        <p role="alert" className="text-[--color-error] text-sm">{error}</p>
      )}
    </div>
  )
}
