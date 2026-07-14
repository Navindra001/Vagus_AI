# VAGUS AI — Virtual AI Guided Understanding Simulator

AI-powered medical patient simulation platform for clinical communication
training and OSCE exam preparation.

## Stack

| Layer    | Technology                                    |
|----------|-----------------------------------------------|
| LLM      | **Groq** — Llama 3.3 70B (replaces Ollama)   |
| Backend  | Django 4.2 + DRF + Channels                  |
| Frontend | Next.js 14 (TypeScript, Tailwind CSS)         |
| STT      | faster-whisper (local CPU)                    |
| TTS      | Kokoro ONNX (local, optional)                 |
| DB       | PostgreSQL                                    |
| Cache    | Redis                                         |

---

## Quick start

### 1 — Get a Groq API key (free)

1. Visit <https://console.groq.com> and sign up.
2. Create an API key.
3. Copy it — you'll need it in step 3.

### 2 — Start PostgreSQL & Redis

```bash
# Docker (quickest)
docker run -d --name pg -e POSTGRES_USER=vagus -e POSTGRES_PASSWORD=vagus_dev \
  -e POSTGRES_DB=vagus -p 5432:5432 postgres:16
docker run -d --name redis -p 6379:6379 redis:7
```

### 3 — Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Set your Groq API key
cp .env .env.local
# Edit .env.local — paste your GROQ_API_KEY

python manage.py migrate
python manage.py seed_cases      # loads 11 patient cases
python manage.py runserver
```

The API is now at `http://localhost:8000`.

### 4 — Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000`.

---

## Key change: Ollama → Groq

| Before (Ollama)                         | After (Groq)                              |
|-----------------------------------------|-------------------------------------------|
| Local model, slow on CPU                | Cloud inference, ~250 tokens/sec          |
| `ollama run llama3.3`                   | `GROQ_API_KEY=...` in `.env`              |
| `httpx.AsyncClient` → `http://localhost:11434` | `AsyncGroq(api_key=...)` SDK       |
| No JSON mode                            | `response_format={"type":"json_object"}` |

All changes are in `backend/services/llm.py`. The rest of the codebase is
unchanged — `llm_complete()` and `llm_complete_json()` are drop-in
replacements for the Ollama calls.

---

## Project structure

```
vagus/
├── backend/
│   ├── core/            Django project settings, URLs, ASGI
│   ├── apps/
│   │   ├── cases/       PatientCase model + seed command (11 cases)
│   │   ├── sessions/    ConsultationSession model + chat endpoint
│   │   ├── feedback/    Feedback generation endpoint
│   │   ├── patients/    STT upload endpoint
│   │   └── users/       JWT auth
│   └── services/
│       ├── llm.py       ← Groq client (was Ollama)
│       ├── stt.py       faster-whisper
│       ├── tts.py       Kokoro ONNX
│       ├── patient.py   system prompt builder
│       └── feedback/
│           ├── rubric.py    10-domain OSCE rubric
│           ├── checker.py   keyword rule checks
│           └── scorer.py    two-stage Groq scorer
└── frontend/
    ├── app/
    │   ├── page.tsx         Landing
    │   ├── setup/           Case selection
    │   ├── consult/         Live consultation
    │   └── feedback/[id]/   OSCE feedback & radar chart
    ├── components/
    │   ├── a11y/            LiveRegion, FocusTrap, SkipLink
    │   ├── chat/            ChatBox
    │   ├── voice/           VoiceInput
    │   └── ui/              Button, LoadingSpinner
    └── lib/
        ├── api.ts
        └── hooks/           useVoice, useAudio
```

---

## OSCE Scoring

The two-stage Groq scorer (`services/feedback/scorer.py`):

1. **Stage 1** — Runs twice at different temperatures (0.1 and 0.3) and
   averages domain scores to reduce variance. Uses Groq JSON mode for
   structured output.
2. **Stage 2** — Generates narrative prose feedback for the student.

Ten domains scored 0–10: Presenting Complaint, History of PC, Past Medical
History, Drug History & Allergies, Family History, Social History, ICE,
Systems Review, Summarising, Communication.

Pass mark: 60 · Distinction: 80.

---

## Accessibility (WCAG 2.1 AA)

- Skip link on every page (2.4.1)
- Minimum 44 × 44 px touch targets (2.5.5)
- Focus ring via `:focus-visible` (2.4.7)
- `aria-live` regions for chat + status messages (4.1.3)
- Colour + text for all status indicators (1.4.1)
- `prefers-reduced-motion` respected (2.3.3)
- All contrast ratios verified ≥ 4.5:1 (1.4.3)
