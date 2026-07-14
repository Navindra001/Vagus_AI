'use client'
import { useCallback, useRef } from 'react'

/**
 * Plays base64-encoded WAV audio from TTS responses.
 * Respects prefers-reduced-motion (audio still plays — only animations are suppressed).
 */
export function useAudio() {
  const currentRef = useRef<HTMLAudioElement | null>(null)

  const play = useCallback((b64: string) => {
    // Stop any currently playing audio
    if (currentRef.current) {
      currentRef.current.pause()
      currentRef.current = null
    }
    if (!b64) return
    const audio = new Audio(`data:audio/wav;base64,${b64}`)
    currentRef.current = audio
    audio.play().catch(() => {/* browser may block autoplay */})
  }, [])

  const stop = useCallback(() => {
    currentRef.current?.pause()
    currentRef.current = null
  }, [])

  return { play, stop }
}
