import type { Metadata } from 'next'
import '../styles/globals.css'
import { Nav } from '@/components/ui/Nav'

export const metadata: Metadata = {
  title: {
    template: '%s — VAGUS AI',
    default: 'VAGUS AI — Clinical Communication Training',
  },
  description: 'Practice patient consultations with AI-powered simulated patients. OSCE exam preparation.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>
        <Nav />
        {children}
      </body>
    </html>
  )
}
