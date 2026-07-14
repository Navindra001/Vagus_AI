/** WCAG 2.4.1 — Bypass block skip link. Already in layout.tsx, exported here for reuse. */
export function SkipLink() {
  return (
    <a href="#main-content" className="skip-link">
      Skip to main content
    </a>
  )
}
