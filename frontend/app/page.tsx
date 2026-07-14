import Link from 'next/link'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Clinical Communication Training',
}

export default function LandingPage() {
  return (
    <main id="main-content" className="min-h-screen flex flex-col">
      {/* ── Hero ──────────────────────────────────────────── */}
      <section
        aria-labelledby="hero-heading"
        className="flex-1 flex items-center justify-center px-6 py-24"
      >
        <div className="max-w-2xl text-center">
          <p className="text-[--color-accent] text-sm font-semibold uppercase tracking-widest mb-4">
            VAGUS AI
          </p>
          <h1
            id="hero-heading"
            className="font-display text-4xl md:text-5xl text-[--color-text-primary] mb-6 leading-tight"
          >
            Practice consultations.<br />Build clinical confidence.
          </h1>
          <p className="text-[--color-text-secondary] text-lg mb-10 leading-relaxed">
            Realistic AI patients that respond naturally to your questions.
            Detailed OSCE-aligned feedback after every consultation.
          </p>
          <Link
            href="/setup"
            className="inline-flex items-center justify-center px-8 py-4 bg-[--color-accent] text-[--color-bg-deep] font-semibold rounded-lg hover:bg-[--color-accent-hover] transition-colors min-h-[44px]"
          >
            Start a consultation
          </Link>
        </div>
      </section>

      {/* ── Features ──────────────────────────────────────── */}
      <section
        aria-labelledby="features-heading"
        className="bg-[--color-bg-surface] px-6 py-16"
      >
        <h2
          id="features-heading"
          className="text-2xl text-[--color-text-primary] text-center mb-12 font-display"
        >
          Built for medical training
        </h2>
        <ul
          role="list"
          className="max-w-4xl mx-auto grid md:grid-cols-3 gap-8"
        >
          {[
            {
              title: '11 Patient Cases',
              desc: 'Across cardiology, respiratory, psychiatry, neurology and more.',
            },
            {
              title: 'Voice & Text',
              desc: 'Speak naturally or type your questions — Groq responds in under a second.',
            },
            {
              title: 'OSCE Feedback',
              desc: '10-domain scoring with narrative coaching aligned to medical school rubrics.',
            },
          ].map(f => (
            <li key={f.title} className="bg-[--color-bg-deep] rounded-xl p-6">
              <h3 className="text-lg font-semibold text-[--color-text-primary] mb-2">{f.title}</h3>
              <p className="text-[--color-text-secondary] text-base">{f.desc}</p>
            </li>
          ))}
        </ul>
      </section>

      {/* ── Footer ────────────────────────────────────────── */}
      <footer className="px-6 py-6 text-center text-[--color-text-muted] text-sm">
        VAGUS AI — Virtual AI Guided Understanding Simulator
      </footer>
    </main>
  )
}
