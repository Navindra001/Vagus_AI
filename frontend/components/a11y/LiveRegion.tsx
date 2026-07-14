'use client'
import { useEffect, useRef } from 'react'

interface LiveRegionProps {
  message: string
  type?: 'status' | 'alert'  // status = polite, alert = assertive
  clearAfter?: number         // ms — auto-clear transient messages
}

/**
 * WCAG 4.1.3 — Status messages conveyed to assistive technologies
 * without the element receiving focus.
 */
export function LiveRegion({ message, type = 'status', clearAfter }: LiveRegionProps) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!ref.current || !message) return
    // Briefly clear so screen readers re-announce the same string
    ref.current.textContent = ''
    const t1 = setTimeout(() => {
      if (ref.current) ref.current.textContent = message
    }, 50)
    const t2 = clearAfter
      ? setTimeout(() => { if (ref.current) ref.current.textContent = '' }, clearAfter)
      : null
    return () => { clearTimeout(t1); if (t2) clearTimeout(t2) }
  }, [message, clearAfter])

  return (
    <div
      ref={ref}
      role={type}
      aria-live={type === 'alert' ? 'assertive' : 'polite'}
      aria-atomic="true"
      className="sr-only"
    />
  )
}
