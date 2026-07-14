"""
Healthcare Video Transcription Pipeline — Phase 2
===================================================
Reads the metadata collected in Phase 1, downloads each video,
extracts audio, and transcribes it using Groq Whisper API.
Saves transcripts + timestamps ready for Phase 3 (database).

Setup:
    pip install yt-dlp groq pydub requests

Usage:
    python transcribe_videos.py --groq-key YOUR_GROQ_KEY
    python transcribe_videos.py --groq-key YOUR_GROQ_KEY --limit 5
    python transcribe_videos.py --groq-key YOUR_GROQ_KEY --video-id nEJGc_Z-TwQ
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

COLLECTION_DIR  = Path("healthcare_videos")
TRANSCRIPTS_DIR = Path("healthcare_videos/transcripts")
AUDIO_TEMP_DIR  = Path("healthcare_videos/audio_temp")
LOGS_DIR        = Path("healthcare_videos/logs")

GROQ_WHISPER_MODEL = "whisper-large-v3"
GROQ_API_URL       = "https://api.groq.com/openai/v1/audio/transcriptions"

# Groq max file size is 25MB — we chunk longer audio
MAX_AUDIO_MB = 24


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def setup_dirs():
    for d in [TRANSCRIPTS_DIR, AUDIO_TEMP_DIR, LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def load_metadata() -> list:
    """Load all video metadata JSON files from Phase 1."""
    meta_dir = COLLECTION_DIR / "metadata"
    if not meta_dir.exists():
        print("❌  No metadata folder found. Run collect_videos.py first.")
        sys.exit(1)

    items = []
    for f in sorted(meta_dir.glob("*.json")):
        try:
            with open(f, encoding="utf-8") as fp:
                items.append(json.load(fp))
        except Exception as e:
            print(f"  ⚠️  Could not read {f.name}: {e}")
    return items


# ---------------------------------------------------------------------------
# Audio extraction
# ---------------------------------------------------------------------------

def download_audio(url: str, video_id: str, cookies_file: str = None) -> Path | None:
    """
    Download audio-only stream from YouTube using yt-dlp.
    Returns path to the downloaded audio file.
    """
    out_path = AUDIO_TEMP_DIR / f"{video_id}.%(ext)s"
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--format", "bestaudio[ext=m4a]/bestaudio/best",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "5",          # medium quality — smaller file
        "--output", str(out_path),
        "--no-playlist",
        "--quiet",
    ]
    if cookies_file:
        cmd += ["--cookies", cookies_file]
    cmd.append(url)

    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
        # Find the output file (extension may vary)
        for ext in ["mp3", "m4a", "webm", "ogg"]:
            p = AUDIO_TEMP_DIR / f"{video_id}.{ext}"
            if p.exists():
                return p
    except subprocess.CalledProcessError as e:
        print(f"  ⚠️  yt-dlp error: {e.stderr.decode()[:200]}")
    except subprocess.TimeoutExpired:
        print(f"  ⚠️  Download timed out")
    return None


def get_file_size_mb(path: Path) -> float:
    return path.stat().st_size / (1024 * 1024)


# ---------------------------------------------------------------------------
# Groq Whisper transcription
# ---------------------------------------------------------------------------

def transcribe_with_groq(audio_path: Path, groq_key: str,
                          language: str = "en") -> dict | None:
    """
    Send audio file to Groq Whisper API.
    Returns dict with text + segments (word-level timestamps).
    """
    import requests

    size_mb = get_file_size_mb(audio_path)
    print(f"  🎙  Transcribing {audio_path.name} ({size_mb:.1f} MB)...")

    try:
        with open(audio_path, "rb") as f:
            resp = requests.post(
                GROQ_API_URL,
                headers={"Authorization": f"Bearer {groq_key}"},
                files={"file": (audio_path.name, f, "audio/mpeg")},
                data={
                    "model":            GROQ_WHISPER_MODEL,
                    "language":         language,
                    "response_format":  "verbose_json",  # includes timestamps
                    "temperature":      0,
                },
                timeout=120,
            )

        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"  ⚠️  Groq API error {resp.status_code}: {resp.text[:200]}")
            return None

    except Exception as e:
        print(f"  ⚠️  Transcription error: {e}")
        return None


# ---------------------------------------------------------------------------
# Transcript processing
# ---------------------------------------------------------------------------

def build_transcript_record(meta: dict, groq_response: dict) -> dict:
    """
    Combine video metadata + Groq transcript into a single structured record
    ready to be inserted into the database in Phase 3.
    """
    segments = groq_response.get("segments", [])

    # Extract clean segments with timestamps
    clean_segments = []
    for seg in segments:
        clean_segments.append({
            "start":       round(seg.get("start", 0), 2),
            "end":         round(seg.get("end", 0), 2),
            "text":        seg.get("text", "").strip(),
            "confidence":  round(1 - seg.get("no_speech_prob", 0), 3),
        })

    # Detect likely questions in the transcript
    full_text = groq_response.get("text", "")
    questions = detect_questions(clean_segments)

    return {
        # Video identity
        "video_id":      meta["video_id"],
        "title":         meta["title"],
        "url":           meta["url"],
        "channel":       meta.get("channel"),
        "duration_secs": meta.get("duration_secs"),
        "source_query":  meta.get("source_query"),

        # Transcript
        "full_text":     full_text,
        "segments":      clean_segments,
        "language":      groq_response.get("language", "en"),
        "word_count":    len(full_text.split()),

        # Extracted questions (ready for Phase 3 question-answer pairing)
        "questions_detected": questions,

        # Metadata
        "transcribed_at": datetime.now(timezone.utc).isoformat(),
        "model":          GROQ_WHISPER_MODEL,
    }


def detect_questions(segments: list) -> list:
    """
    Find segments that contain questions — these are the prompts
    interviewers asked the public.
    """
    questions = []
    for seg in segments:
        text = seg["text"].strip()
        # Simple heuristic: ends with ? or starts with question words
        if text.endswith("?") or any(
            text.lower().startswith(w)
            for w in ["what", "how", "do you", "did you", "would you",
                      "have you", "why", "when", "where", "who", "which",
                      "are you", "is it", "could you", "can you"]
        ):
            questions.append({
                "start": seg["start"],
                "end":   seg["end"],
                "text":  text,
            })
    return questions


def save_transcript(record: dict):
    vid_id = record["video_id"]
    out_path = TRANSCRIPTS_DIR / f"{vid_id}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    return out_path


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def process_video(meta: dict, groq_key: str, cookies_file: str = None) -> bool:
    vid_id = meta["video_id"]
    title  = (meta.get("title") or "")[:60]

    # Skip if already transcribed
    existing = TRANSCRIPTS_DIR / f"{vid_id}.json"
    if existing.exists():
        print(f"  ✅  Already done — {title}")
        return True

    print(f"\n{'─'*55}")
    print(f"  📹  {title}")
    print(f"       {meta['url']}")

    # Step 1: Download audio
    print(f"  ⬇️   Downloading audio...")
    audio_path = download_audio(meta["url"], vid_id, cookies_file)
    if not audio_path:
        print(f"  ❌  Audio download failed — skipping")
        return False

    size_mb = get_file_size_mb(audio_path)
    if size_mb > MAX_AUDIO_MB:
        print(f"  ⚠️  File too large ({size_mb:.1f}MB > {MAX_AUDIO_MB}MB) — skipping")
        audio_path.unlink(missing_ok=True)
        return False

    # Step 2: Transcribe
    groq_response = transcribe_with_groq(audio_path, groq_key)
    if not groq_response:
        audio_path.unlink(missing_ok=True)
        return False

    # Step 3: Build and save record
    record = build_transcript_record(meta, groq_response)
    out_path = save_transcript(record)

    word_count = record["word_count"]
    q_count    = len(record["questions_detected"])
    print(f"  ✅  {word_count} words · {q_count} questions detected")
    print(f"       Saved → {out_path.name}")

    # Cleanup audio temp file
    audio_path.unlink(missing_ok=True)
    return True


def run_pipeline(groq_key: str, limit: int = None,
                 video_id: str = None, cookies_file: str = None):
    setup_dirs()

    all_meta = load_metadata()
    if not all_meta:
        print("❌  No metadata found. Run collect_videos.py first.")
        return

    # Filter to specific video if requested
    if video_id:
        all_meta = [m for m in all_meta if m["video_id"] == video_id]
        if not all_meta:
            print(f"❌  Video ID {video_id} not found in metadata.")
            return

    if limit:
        all_meta = all_meta[:limit]

    print("=" * 55)
    print("  Healthcare Transcription Pipeline")
    print("=" * 55)
    print(f"  Videos to process: {len(all_meta)}")
    print(f"  Model: Groq {GROQ_WHISPER_MODEL}")
    print(f"  Output: {TRANSCRIPTS_DIR}")
    print("=" * 55)

    success = 0
    failed  = 0

    for i, meta in enumerate(all_meta, 1):
        print(f"\n[{i}/{len(all_meta)}]", end=" ")
        ok = process_video(meta, groq_key, cookies_file)
        if ok:
            success += 1
        else:
            failed += 1

    # Final summary
    print(f"\n{'='*55}")
    print(f"  ✅  Transcribed: {success}")
    print(f"  ❌  Failed:      {failed}")
    print(f"  📁  Transcripts → {TRANSCRIPTS_DIR.resolve()}")
    print(f"\n  Next step: run database pipeline (Phase 3)")

    # Save run log
    log = {
        "run_at":    datetime.now(timezone.utc).isoformat(),
        "total":     len(all_meta),
        "success":   success,
        "failed":    failed,
        "model":     GROQ_WHISPER_MODEL,
    }
    log_path = LOGS_DIR / f"transcription_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Transcribe healthcare opinion videos using Groq Whisper"
    )
    parser.add_argument("--groq-key",  required=True, help="Groq API key")
    parser.add_argument("--limit",     type=int, help="Max videos to process")
    parser.add_argument("--video-id",  help="Process a single video by ID")
    parser.add_argument("--cookies",   dest="cookies_file", help="Path to cookies.txt")
    args = parser.parse_args()

    run_pipeline(
        groq_key     = args.groq_key,
        limit        = args.limit,
        video_id     = args.video_id,
        cookies_file = args.cookies_file,
    )


if __name__ == "__main__":
    main()