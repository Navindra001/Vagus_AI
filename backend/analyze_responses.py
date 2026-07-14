"""
Healthcare Opinion Database — Phase 4
=======================================
LLM analysis pipeline using Groq.

For each question in the DB:
  1. Finds the response segments that follow it (same video, next ~60 secs)
  2. Sends question + response to Groq for structured analysis
  3. Writes results back to the `responses` table

Usage:
    python analyze_responses.py              # Analyse all
    python analyze_responses.py --limit 10   # Test with 10 questions
    python analyze_responses.py --dry-run    # Print without writing to DB
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path


# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------

def get_supabase():
    try:
        from dotenv import load_dotenv
        for name in (".env1", "env1", ".env"):
            if Path(name).exists():
                load_dotenv(name)
                break
    except ImportError:
        pass

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        print("❌  Missing SUPABASE_URL or SUPABASE_KEY")
        sys.exit(1)

    from supabase import create_client
    return create_client(url, key)


def get_groq():
    try:
        from dotenv import load_dotenv
        for name in (".env1", "env1", ".env"):
            if Path(name).exists():
                load_dotenv(name)
                break
    except ImportError:
        pass

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("❌  Missing GROQ_API_KEY")
        sys.exit(1)

    from groq import Groq
    return Groq(api_key=api_key)


# ---------------------------------------------------------------------------
# Fetch data
# ---------------------------------------------------------------------------

def fetch_questions(client, limit=None):
    """Fetch all questions that don't yet have responses."""
    query = (
        client.table("questions")
        .select("id, video_id, start_secs, end_secs, text")
        .order("id")
    )
    if limit:
        query = query.limit(limit)
    result = query.execute()
    return result.data or []


def fetch_response_segments(client, video_id: str, after_secs: float, window_secs: float = 60.0):
    """Fetch segments from the same video that follow the question."""
    end_secs = after_secs + window_secs
    result = (
        client.table("segments")
        .select("text, start_secs, end_secs")
        .eq("video_id", video_id)
        .gte("start_secs", after_secs)
        .lte("start_secs", end_secs)
        .eq("is_question", False)
        .order("start_secs")
        .execute()
    )
    return result.data or []


# ---------------------------------------------------------------------------
# LLM analysis
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert qualitative researcher analysing public opinions about healthcare.

Given a question asked in a video interview and the public responses that followed, extract structured analysis.

Respond ONLY with valid JSON — no preamble, no markdown fences. Use exactly this schema:

{
  "topic": "one of: waiting_times | cost | mental_health | gp_access | staff | quality | comparison | general",
  "healthcare_system": "one of: NHS | GP | Mental_Health | A_and_E | Private | Social_Care | General | Unknown",
  "responses": [
    {
      "text": "verbatim or close paraphrase of the response (max 300 chars)",
      "sentiment": "positive | negative | neutral | mixed",
      "sentiment_score": 0.0,
      "emotion": "satisfaction | frustration | hope | confusion | anger | fear | gratitude | indifference",
      "speaker_age_group": "under_40 | 40_to_60 | over_60 | unknown",
      "speaker_gender": "male | female | unknown",
      "speaker_region": "London | North | Midlands | Scotland | Wales | Unknown"
    }
  ]
}

sentiment_score must be a float between -1.0 (very negative) and 1.0 (very positive).
If response text is empty or irrelevant, return {"topic": "general", "healthcare_system": "Unknown", "responses": []}.
"""


def analyse_with_groq(groq_client, question_text: str, response_text: str) -> dict | None:
    """Call Groq and parse the structured JSON response."""
    if not response_text.strip():
        return None

    user_msg = f"""QUESTION: {question_text}

RESPONSES: {response_text[:2000]}"""

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.2,
            max_tokens=1000,
        )
        raw = completion.choices[0].message.content.strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        return json.loads(raw)

    except json.JSONDecodeError as e:
        print(f"    ⚠️  JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"    ⚠️  Groq error: {e}")
        return None


# ---------------------------------------------------------------------------
# Write results
# ---------------------------------------------------------------------------

def write_responses(client, question: dict, analysis: dict, dry_run: bool = False):
    """Insert response rows and update question topic/healthcare_system."""
    q_id      = question["id"]
    video_id  = question["video_id"]
    start     = question.get("end_secs") or question.get("start_secs", 0)

    # Update question metadata
    topic   = analysis.get("topic", "general")
    hc_sys  = analysis.get("healthcare_system", "Unknown")

    if not dry_run:
        client.table("questions").update({
            "topic": topic,
            "healthcare_system": hc_sys,
        }).eq("id", q_id).execute()

    responses = analysis.get("responses", [])
    inserted  = 0

    for i, r in enumerate(responses):
        text = (r.get("text") or "").strip()
        if not text:
            continue

        row = {
            "video_id":          video_id,
            "question_id":       q_id,
            "start_secs":        start + i * 5,   # approximate
            "end_secs":          start + i * 5 + 5,
            "text":              text[:500],
            "sentiment":         r.get("sentiment", "neutral"),
            "sentiment_score":   float(r.get("sentiment_score", 0.0)),
            "emotion":           r.get("emotion", "indifference"),
            "speaker_age_group": r.get("speaker_age_group", "unknown"),
            "speaker_gender":    r.get("speaker_gender", "unknown"),
            "speaker_region":    r.get("speaker_region", "Unknown"),
        }

        if dry_run:
            print(f"      [DRY RUN] Would insert: {text[:60]}... | {row['sentiment']} ({row['sentiment_score']})")
        else:
            client.table("responses").insert(row).execute()
        inserted += 1

    return inserted


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_pipeline(limit=None, dry_run=False):
    print("\n🔬  Phase 4: LLM Analysis Pipeline")
    print("=" * 55)

    supabase = get_supabase()
    groq     = get_groq()

    questions = fetch_questions(supabase, limit=limit)
    print(f"  Found {len(questions)} questions to analyse")
    if dry_run:
        print("  [DRY RUN mode — nothing will be written to DB]")
    print()

    total_responses = 0
    success = 0
    skipped = 0

    for i, q in enumerate(questions, 1):
        q_text   = q["text"]
        video_id = q["video_id"]
        end_secs = q.get("end_secs") or q.get("start_secs", 0)

        print(f"[{i}/{len(questions)}] {q_text[:70]}")

        # Fetch following segments
        segments = fetch_response_segments(supabase, video_id, end_secs)
        if not segments:
            print("    ⏭️  No response segments found — skipping")
            skipped += 1
            continue

        response_text = " ".join(s["text"] for s in segments)

        # Analyse with Groq
        analysis = analyse_with_groq(groq, q_text, response_text)
        if not analysis:
            print("    ⚠️  Analysis failed — skipping")
            skipped += 1
            continue

        # Write to DB
        n = write_responses(supabase, q, analysis, dry_run=dry_run)
        total_responses += n
        success += 1

        topic  = analysis.get("topic", "?")
        hc_sys = analysis.get("healthcare_system", "?")
        print(f"    ✅  {n} responses | topic: {topic} | system: {hc_sys}")

        # Rate limit: ~30 req/min on Groq free tier
        time.sleep(1.0)

    print(f"\n{'='*55}")
    print(f"  ✅  Questions analysed: {success}")
    print(f"  ⏭️  Skipped:            {skipped}")
    print(f"  💬  Responses written:  {total_responses}")
    print(f"\n  Next step: build the RAG chatbot (Phase 5)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Phase 4 — LLM analysis of healthcare opinions"
    )
    parser.add_argument("--limit",   type=int, default=None, help="Only analyse N questions (for testing)")
    parser.add_argument("--dry-run", action="store_true",    help="Print results without writing to DB")
    args = parser.parse_args()

    run_pipeline(limit=args.limit, dry_run=args.dry_run)