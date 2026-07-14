const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
  })
  if (!r.ok) {
    const text = await r.text().catch(() => r.statusText)
    throw new Error(text)
  }
  return r.json() as Promise<T>
}

export const api = {
  getCases: (specialty?: string, difficulty?: string) => {
    const params = new URLSearchParams()
    if (specialty)  params.set('specialty', specialty)
    if (difficulty) params.set('difficulty', difficulty)
    return req<unknown[]>(`/api/cases/?${params}`)
  },

  getCase: (id: string) => req<unknown>(`/api/cases/${id}/`),

  createSession: (case_id: string) =>
    req<{ id: string }>('/api/sessions/', {
      method: 'POST',
      body: JSON.stringify({ case_id }),
    }),

  chat: (sessionId: string, message: string) =>
    req<{ response: string; audio_b64: string; message_count: number }>(
      `/api/sessions/${sessionId}/chat/`,
      { method: 'POST', body: JSON.stringify({ message }) }
    ),

  completeSession: (sessionId: string) =>
    req<{ status: string }>(`/api/sessions/${sessionId}/complete/`, { method: 'POST' }),

  getFeedback: (sessionId: string) =>
    req<unknown>(`/api/feedback/${sessionId}/`, { method: 'POST' }),
}
