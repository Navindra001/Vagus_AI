'use client'
import { useEffect, useRef } from 'react'

const FOCUSABLE = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(', ')

/**
 * WCAG 2.1.2 — No keyboard trap inside modals.
 * Traps Tab/Shift+Tab within children; Escape calls onClose.
 */
export function FocusTrap({
  children,
  active,
  onClose,
}: {
  children: React.ReactNode
  active: boolean
  onClose?: () => void
}) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!active || !ref.current) return
    const container = ref.current
    const focusable = Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE))
    const first = focusable[0]
    const last  = focusable[focusable.length - 1]
    first?.focus()

    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') { onClose?.(); return }
      if (e.key !== 'Tab') return
      if (e.shiftKey) {
        if (document.activeElement === first) { e.preventDefault(); last?.focus() }
      } else {
        if (document.activeElement === last)  { e.preventDefault(); first?.focus() }
      }
    }

    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [active, onClose])

  return <div ref={ref}>{children}</div>
}
