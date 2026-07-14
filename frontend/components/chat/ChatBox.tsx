'use client'
import { useEffect, useRef } from 'react'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

interface ChatBoxProps {
  messages: Message[]
  isLoading?: boolean
}

/**
 * WCAG compliance:
 * - 1.3.1: messages in <article> elements
 * - 4.1.3: new messages announced via aria-live="polite"
 * - 2.4.3: auto-scroll preserves focus order (scroll only, no focus move)
 */
export function ChatBox({ messages, isLoading }: ChatBoxProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages.length, isLoading])

  return (
    <section
      aria-label="Consultation transcript"
      className="flex flex-col h-full overflow-hidden"
    >
      <ol
        aria-live="polite"       /* 4.1.3 — new messages announced */
        aria-label="Messages"
        className="flex-1 overflow-y-auto flex flex-col gap-4 p-4 list-none m-0"
      >
        {messages.map(msg => (
          <li key={msg.id}>
            <article
              aria-label={`${msg.role === 'user' ? 'You' : 'Patient'} said`}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[75%] rounded-xl px-4 py-3 ${
                  msg.role === 'user'
                    ? 'bg-[--color-accent] text-[--color-bg-deep]'
                    : 'bg-[--color-bg-surface] text-[--color-text-primary]'
                }`}
              >
                {/* 1.3.1 — role in text too, not just position/colour */}
                <span className="sr-only">
                  {msg.role === 'user' ? 'You: ' : 'Patient: '}
                </span>
                <p className="text-base leading-relaxed m-0">{msg.content}</p>
                <time
                  dateTime={msg.timestamp}
                  className="text-xs opacity-60 mt-1 block"
                >
                  {new Date(msg.timestamp).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </time>
              </div>
            </article>
          </li>
        ))}

        {isLoading && (
          <li aria-label="Patient is responding">
            <div className="flex justify-start">
              <div className="bg-[--color-bg-surface] rounded-xl px-4 py-3">
                <span className="sr-only">Patient is typing...</span>
                <div className="flex gap-1" aria-hidden="true">
                  {[0, 1, 2].map(i => (
                    <span
                      key={i}
                      className="w-2 h-2 rounded-full bg-[--color-text-secondary] animate-bounce"
                      style={{ animationDelay: `${i * 0.15}s` }}
                    />
                  ))}
                </div>
              </div>
            </div>
          </li>
        )}
      </ol>

      <div ref={bottomRef} aria-hidden="true" />
    </section>
  )
}
