/**
 * WCAG 4.1.3 — Loading state announced via aria-live.
 */
export function LoadingSpinner({ label = 'Loading...' }: { label?: string }) {
  return (
    <div role="status" aria-live="polite" className="inline-flex items-center gap-2">
      <svg
        className="animate-spin h-5 w-5 text-[--color-accent]"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
      </svg>
      <span className="sr-only">{label}</span>
    </div>
  )
}
