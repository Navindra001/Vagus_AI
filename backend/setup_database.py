"""
Healthcare Opinion Database — Phase 3
=======================================
Creates the Supabase/PostgreSQL schema and ingests all transcripts
from Phase 2 into structured tables ready for the RAG bot in Phase 4.

Setup:
    pip install supabase python-dotenv

Supabase setup:
    1. Go to supabase.com → New project
    2. Copy your project URL and anon/service key
    3. Create a .env file:
          SUPABASE_URL=https://xxxx.supabase.co
          SUPABASE_KEY=sb_s

Usage:
    python setup_database.py --setup      # Create tables
    python setup_database.py --ingest     # Load all transcripts
    python setup_database.py --setup --ingest  # Do both
    python setup_database.py --stats      # Show what's in the DB
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

TRANSCRIPTS_DIR = Path("healthcare_videos/transcripts")


# ---------------------------------------------------------------------------
# Supabase client
# ---------------------------------------------------------------------------

def get_client():
    try:
        from dotenv import load_dotenv
        if Path(".env1").exists():
            load_dotenv(".env1")
        elif Path("env1").exists():
            load_dotenv("env1")
        else:
            load_dotenv()
    except ImportError:
        pass

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        print("❌  Missing SUPABASE_URL or SUPABASE_KEY in environment/.env")
        sys.exit(1)

    try:
        from supabase import create_client
        return create_client(url, key)
    except ImportError:
        print("❌  supabase not installed. Run: pip install supabase")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Schema SQL
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
-- Enable pgvector for semantic search in Phase 4
create extension if not exists vector;

-- ─────────────────────────────────────────────
-- 1. Videos — one row per collected video
-- ─────────────────────────────────────────────
create table if not exists videos (
    id              text primary key,          -- YouTube video ID
    title           text,
    url             text,
    channel         text,
    duration_secs   integer,
    source_query    text,
    word_count      integer,
    language        text default 'en',
    full_text       text,                      -- complete transcript
    collected_at    timestamptz,
    transcribed_at  timestamptz
);

-- ─────────────────────────────────────────────
-- 2. Segments — timestamped transcript chunks
-- ─────────────────────────────────────────────
create table if not exists segments (
    id              bigserial primary key,
    video_id        text references videos(id) on delete cascade,
    start_secs      float,
    end_secs        float,
    text            text,
    confidence      float,
    is_question     boolean default false
);

-- ─────────────────────────────────────────────
-- 3. Questions — detected interviewer prompts
-- ─────────────────────────────────────────────
create table if not exists questions (
    id              bigserial primary key,
    video_id        text references videos(id) on delete cascade,
    start_secs      float,
    end_secs        float,
    text            text,
    topic           text,                      -- populated by LLM in Phase 4
    healthcare_system text                     -- e.g. NHS, GP, Mental Health
);

-- ─────────────────────────────────────────────
-- 4. Responses — public answers to questions
-- ─────────────────────────────────────────────
create table if not exists responses (
    id              bigserial primary key,
    video_id        text references videos(id) on delete cascade,
    question_id     bigint references questions(id),
    start_secs      float,
    end_secs        float,
    text            text,

    -- Sentiment (populated by Phase 4 analysis)
    sentiment       text,                      -- positive / negative / neutral / mixed
    sentiment_score float,                     -- -1.0 to 1.0
    emotion         text,                      -- frustration / hope / confusion / anger / satisfaction

    -- Demographic (populated when known or inferred)
    speaker_age_group   text,                  -- under_40 / 40_to_60 / over_60
    speaker_gender      text,                  -- male / female / unknown
    speaker_region      text                   -- London / North / Scotland etc
);

-- ─────────────────────────────────────────────
-- 5. Embeddings — for semantic RAG search
-- ─────────────────────────────────────────────
create table if not exists response_embeddings (
    id              bigserial primary key,
    response_id     bigint references responses(id) on delete cascade,
    embedding       vector(1536),              -- OpenAI/Groq embedding dimension
    model           text
);

-- ─────────────────────────────────────────────
-- Indexes for fast lookup
-- ─────────────────────────────────────────────
create index if not exists idx_segments_video    on segments(video_id);
create index if not exists idx_questions_video   on questions(video_id);
create index if not exists idx_responses_video   on responses(video_id);
create index if not exists idx_responses_question on responses(question_id);
create index if not exists idx_responses_sentiment on responses(sentiment);
create index if not exists idx_responses_demo    on responses(speaker_gender, speaker_age_group);
"""


# ---------------------------------------------------------------------------
# Setup tables via Supabase SQL editor (RPC)
# ---------------------------------------------------------------------------

def setup_tables(client):
    """
    Run the schema SQL via Supabase.
    Note: run this SQL directly in Supabase SQL Editor for best results.
    """
    print("\n📋  Schema SQL to run in Supabase SQL Editor:")
    print("=" * 55)
    print("Go to: supabase.com → your project → SQL Editor")
    print("Paste and run the following SQL:\n")
    print(SCHEMA_SQL)
    print("=" * 55)

    # Save schema to file for easy copy-paste
    schema_path = Path("healthcare_videos/schema.sql")
    with open(schema_path, "w", encoding="utf-8") as f:
        f.write(SCHEMA_SQL)
    print(f"\n✅  Schema also saved to: {schema_path}")
    print("    Copy-paste it into Supabase SQL Editor and run it.")


# ---------------------------------------------------------------------------
# Ingest transcripts
# ---------------------------------------------------------------------------

def load_transcripts() -> list:
    if not TRANSCRIPTS_DIR.exists():
        print("❌  No transcripts folder. Run transcribe_videos.py first.")
        sys.exit(1)
    files = sorted(TRANSCRIPTS_DIR.glob("*.json"))
    records = []
    for f in files:
        try:
            with open(f, encoding="utf-8") as fp:
                records.append(json.load(fp))
        except Exception as e:
            print(f"  ⚠️  Could not read {f.name}: {e}")
    return records


def ingest_video(client, record: dict) -> bool:
    vid_id = record["video_id"]
    title  = (record.get("title") or "")[:60]

    try:
        # 1. Upsert video row
        client.table("videos").upsert({
            "id":            vid_id,
            "title":         record.get("title"),
            "url":           record.get("url"),
            "channel":       record.get("channel"),
            "duration_secs": record.get("duration_secs"),
            "source_query":  record.get("source_query"),
            "word_count":    record.get("word_count"),
            "language":      record.get("language", "en"),
            "full_text":     record.get("full_text"),
            "transcribed_at": record.get("transcribed_at"),
        }).execute()

        # 2. Insert segments (delete existing first to avoid dupes)
        client.table("segments").delete().eq("video_id", vid_id).execute()
        segments = record.get("segments", [])
        if segments:
            seg_rows = []
            for seg in segments:
                text = seg.get("text", "").strip()
                is_q = text.endswith("?") or any(
                    text.lower().startswith(w)
                    for w in ["what", "how", "do you", "did you", "would you",
                              "have you", "why", "when", "where", "who", "which"]
                )
                seg_rows.append({
                    "video_id":   vid_id,
                    "start_secs": seg.get("start"),
                    "end_secs":   seg.get("end"),
                    "text":       text,
                    "confidence": seg.get("confidence"),
                    "is_question": is_q,
                })
            # Insert in batches of 100
            for i in range(0, len(seg_rows), 100):
                client.table("segments").insert(seg_rows[i:i+100]).execute()

        # 3. Insert detected questions
        client.table("questions").delete().eq("video_id", vid_id).execute()
        questions = record.get("questions_detected", [])
        if questions:
            q_rows = [{
                "video_id":   vid_id,
                "start_secs": q.get("start"),
                "end_secs":   q.get("end"),
                "text":       q.get("text", "").strip(),
            } for q in questions]
            client.table("questions").insert(q_rows).execute()

        q_count   = len(questions)
        seg_count = len(segments)
        print(f"  ✅  {title}")
        print(f"       {seg_count} segments · {q_count} questions")
        return True

    except Exception as e:
        print(f"  ❌  {title}: {e}")
        return False


def ingest_all(client):
    records = load_transcripts()
    if not records:
        print("❌  No transcripts found.")
        return

    print(f"\n📥  Ingesting {len(records)} transcripts into Supabase...")
    print("=" * 55)

    success = 0
    failed  = 0

    for i, record in enumerate(records, 1):
        print(f"\n[{i}/{len(records)}]", end=" ")
        ok = ingest_video(client, record)
        if ok:
            success += 1
        else:
            failed += 1

    print(f"\n{'='*55}")
    print(f"  ✅  Ingested: {success}")
    print(f"  ❌  Failed:   {failed}")
    print(f"\n  Next step: run LLM analysis pipeline (Phase 4)")


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def show_stats(client):
    print("\n📊  Database stats:")
    print("=" * 55)

    try:
        videos    = client.table("videos").select("id", count="exact").execute()
        segments  = client.table("segments").select("id", count="exact").execute()
        questions = client.table("questions").select("id", count="exact").execute()
        responses = client.table("responses").select("id", count="exact").execute()

        print(f"  Videos:    {videos.count}")
        print(f"  Segments:  {segments.count}")
        print(f"  Questions: {questions.count}")
        print(f"  Responses: {responses.count}")

        # Sample questions
        sample_qs = client.table("questions").select("text, video_id").limit(5).execute()
        if sample_qs.data:
            print(f"\n  Sample questions detected:")
            for q in sample_qs.data:
                print(f"    • {q['text'][:80]}")

    except Exception as e:
        print(f"  ⚠️  Error fetching stats: {e}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Set up Supabase database and ingest healthcare transcripts"
    )
    parser.add_argument("--setup",   action="store_true", help="Print schema SQL to run in Supabase")
    parser.add_argument("--ingest",  action="store_true", help="Ingest all transcripts into DB")
    parser.add_argument("--stats",   action="store_true", help="Show database statistics")
    args = parser.parse_args()

    if not any([args.setup, args.ingest, args.stats]):
        parser.print_help()
        return

    if args.setup:
        setup_tables(None)

    if args.ingest or args.stats:
        client = get_client()
        if args.ingest:
            ingest_all(client)
        if args.stats:
            show_stats(client)


if __name__ == "__main__":
    main()