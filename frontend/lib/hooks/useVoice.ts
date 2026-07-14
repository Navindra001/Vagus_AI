'use client'
import { useState, useCallback, useRef } from 'react'

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export type VoiceState = 'idle' | 'recording' | 'processing' | 'error'

export function useVoice(onTranscript: (text: string) => void) {
  const [state, setState] = useState<VoiceState>('idle')
  const [error, setError] = useState('')
  const mrRef = useRef<MediaRecorder | null>(null)

  const start = useCallback(async () => {
    setError('')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mr = new MediaRecorder(stream)
      const chunks: BlobPart[] = []

      mr.ondataavailable = e => chunks.push(e.data)
      mr.onstop = async () => {
        stream.getTracks().forEach(t => t.stop())
        setState('processing')
        const blob = new Blob(chunks, { type: 'audio/webm' })
        const form = new FormData()
        form.append('audio', blob, 'recording.webm')
        try {
          const r = await fetch(`${API}/api/stt/`, { method: 'POST', body: form })
          const { transcript } = await r.json()
          onTranscript(transcript)
          setState('idle')
        } catch {
          setError('Transcription failed — please type instead.')
          setState('error')
        }
      }

      mr.start()
      mrRef.current = mr
      setState('recording')
    } catch {
      setError('Microphone access denied.')
      setState('error')
    }
  }, [onTranscript])

  const stop = useCallback(() => {
    mrRef.current?.stop()
    mrRef.current = null
  }, [])

  const toggle = useCallback(() => {
    if (state === 'recording') stop()
    else start()
  }, [state, start, stop])

  return { state, error, toggle }
}
