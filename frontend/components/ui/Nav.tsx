'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const links = [
  { href: '/setup',          label: 'OSCE Trainer' },
  { href: '/representative', label: 'Patient Representative' },
]

export function Nav() {
  const pathname = usePathname()

  // Hide nav during active consultation and feedback (full-screen pages)
  if (pathname.startsWith('/consult') || pathname.startsWith('/feedback')) return null

  return (
    <nav
      aria-label="Main navigation"
      className="border-b border-[--color-border] bg-[--color-bg-surface] px-6 py-3 flex items-center gap-8"
    >
      <span className="text-sm font-semibold text-[--color-text-primary] tracking-wide mr-4">
        VAGUS AI
      </span>
      {links.map(({ href, label }) => {
        const active = pathname.startsWith(href)
        return (
          <Link
            key={href}
            href={href}
            className={`text-sm transition-colors min-h-[44px] flex items-center ${
              active
                ? 'text-[--color-accent] font-medium'
                : 'text-[--color-text-secondary] hover:text-[--color-text-primary]'
            }`}
          >
            {label}
          </Link>
        )
      })}
    </nav>
  )
}
