"""
Healthcare Opinion Video Collector — YouTube Data API v3
=========================================================
Uses the official YouTube API to search for public opinion videos
on healthcare topics, then downloads them with yt-dlp.

Setup:
    1. Get a free YouTube Data API v3 key from console.cloud.google.com
    2. pip install yt-dlp requests
    3. python collect_videos.py --api-key YOUR_KEY --metadata-only

Usage:
    python collect_videos.py --api-key YOUR_KEY --metadata-only
    python collect_videos.py --api-key YOUR_KEY
    python collect_videos.py --api-key YOUR_KEY --topic "NHS waiting times" --max 10
    python collect_videos.py --python n.py --api-key YOUR_KEY_HERE --metadata-only-key YOUR_KEY --url "https://www.youtube.com/watch?v=XXXX"
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import requests

OUTPUT_DIR = Path("healthcare_videos")
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL  = "https://www.googleapis.com/youtube/v3/videos"

MIN_DURATION_SECS = 30
MAX_DURATION_SECS = 600

DEFAULT_SEARCH_QUERIES = [
    "public opinion NHS healthcare UK",
    "people talk about NHS experience",
    "patient experience NHS vox pop",
    "UK public views on NHS",
    "NHS waiting times public views",
    "GP access problems public opinion",
    "mental health NHS public views",
    "people react to healthcare system UK",
    "healthcare opinions members of public",
    "what do people think about NHS",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def setup_dirs(base: Path) -> dict:
    dirs = {
        "videos":    base / "videos",
        "metadata":  base / "metadata",
        "logs":      base / "logs",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def iso8601_to_seconds(duration: str) -> int:
    """Convert YouTube ISO 8601 duration (PT4M13S) to seconds."""
    import re
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration or "")
    if not match:
        return 0
    h = int(match.group(1) or 0)
    m = int(match.group(2) or 0)
    s = int(match.group(3) or 0)
    return h * 3600 + m * 60 + s


# ---------------------------------------------------------------------------
# YouTube API search
# ---------------------------------------------------------------------------

def search_youtube(query: str, api_key: str, max_results: int = 10) -> list:
    """Return list of video IDs from YouTube search."""
    params = {
        "part":       "id",
        "q":          query,
        "type":       "video",
        "maxResults": min(max_results, 50),
        "relevanceLanguage": "en",
        "regionCode": "GB",
        "key":        api_key,
    }
    resp = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return [item["id"]["videoId"] for item in data.get("items", [])]


def get_video_details(video_ids: list, api_key: str) -> list:
    """Fetch full metadata for a list of video IDs."""
    if not video_ids:
        return []
    params = {
        "part": "snippet,contentDetails,statistics",
        "id":   ",".join(video_ids),
        "key":  api_key,
    }
    resp = requests.get(YOUTUBE_VIDEO_URL, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json().get("items", [])


def extract_metadata(item: dict, source_query: str = "") -> dict:
    snippet = item.get("snippet", {})
    stats   = item.get("statistics", {})
    details = item.get("contentDetails", {})
    duration_secs = iso8601_to_seconds(details.get("duration", ""))
    return {
        "video_id":      item["id"],
        "title":         snippet.get("title"),
        "description":   (snippet.get("description") or "")[:500],
        "channel":       snippet.get("channelTitle"),
        "published_at":  snippet.get("publishedAt"),
        "duration_secs": duration_secs,
        "view_count":    int(stats.get("viewCount", 0) or 0),
        "like_count":    int(stats.get("likeCount", 0) or 0),
        "url":           f"https://www.youtube.com/watch?v={item['id']}",
        "tags":          snippet.get("tags") or [],
        "source_query":  source_query,
        "collected_at":  datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# yt-dlp downloader
# ---------------------------------------------------------------------------

def download_video(url: str, dirs: dict, cookies_file: str = None):
    try:
        import yt_dlp
    except ImportError:
        print("  yt-dlp not installed — skipping download")
        return

    opts = {
        "outtmpl":          str(dirs["videos"] / "%(id)s.%(ext)s"),
        "format":           "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]/best",
        "writeautomaticsub": True,
        "subtitleslangs":   ["en"],
        "subtitlesformat":  "vtt",
        "nooverwrites":     True,
        "quiet":            True,
        "retries":          3,
    }
    if cookies_file:
        opts["cookiefile"] = cookies_file

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
    except Exception as e:
        print(f"  ⚠️  Download error: {e}")


# ---------------------------------------------------------------------------
# Core collector
# ---------------------------------------------------------------------------

def collect(queries: list, api_key: str, dirs: dict,
            max_per_query: int, metadata_only: bool,
            cookies_file: str = None) -> list:

    all_metadata = []
    seen_ids = set()

    for query in queries:
        print(f"\n🔍  {query}")
        try:
            video_ids = search_youtube(query, api_key, max_per_query)
            if not video_ids:
                print("    No results")
                continue

            items = get_video_details(video_ids, api_key)

            for item in items:
                vid_id = item["id"]
                if vid_id in seen_ids:
                    continue

                meta = extract_metadata(item, source_query=query)
                dur  = meta["duration_secs"]

                if dur < MIN_DURATION_SECS:
                    print(f"    ⏭  Too short ({dur}s) — {meta['title'][:50]}")
                    continue
                if dur > MAX_DURATION_SECS:
                    print(f"    ⏭  Too long  ({dur}s) — {meta['title'][:50]}")
                    continue

                seen_ids.add(vid_id)
                all_metadata.append(meta)

                # Save per-video JSON
                meta_path = dirs["metadata"] / f"{vid_id}.json"
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2, ensure_ascii=False)

                status = "📋" if metadata_only else "⬇️ "
                print(f"    {status} [{dur}s] {meta['title'][:60]}")
                print(f"       {meta['url']}")

                if not metadata_only:
                    download_video(meta["url"], dirs, cookies_file)

        except requests.HTTPError as e:
            if e.response.status_code == 403:
                print(f"    ❌ API key error — check your key or quota")
            else:
                print(f"    ⚠️  HTTP error: {e}")
        except Exception as e:
            print(f"    ⚠️  Error: {e}")

    return all_metadata


def collect_url(url: str, api_key: str, dirs: dict,
                metadata_only: bool, cookies_file: str = None) -> list:
    """Process a single YouTube URL."""
    vid_id = url.split("v=")[-1].split("&")[0]
    print(f"\n📥  Fetching: {url}")
    try:
        items = get_video_details([vid_id], api_key)
        if not items:
            print("    No data returned")
            return []
        meta = extract_metadata(items[0], source_query="direct_url")
        meta_path = dirs["metadata"] / f"{vid_id}.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        print(f"    ✅ [{meta['duration_secs']}s] {meta['title']}")
        if not metadata_only:
            download_video(url, dirs, cookies_file)
        return [meta]
    except Exception as e:
        print(f"    ⚠️  Error: {e}")
        return []


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def save_summary(all_metadata: list, dirs: dict):
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    summary_path = dirs["logs"] / f"collection_{ts}.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(all_metadata, f, indent=2, ensure_ascii=False)

    total_mins = sum(m.get("duration_secs", 0) for m in all_metadata) // 60
    print(f"\n{'='*55}")
    print(f"  ✅  Collected {len(all_metadata)} videos ({total_mins} mins total)")
    print(f"  📁  Metadata → {dirs['metadata']}")
    print(f"  📊  Summary  → {summary_path}")
    print(f"\n  Next step: run transcription pipeline (Phase 2)")
    return summary_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Collect public healthcare opinion videos from YouTube"
    )
    parser.add_argument("--api-key",  required=True, help="YouTube Data API v3 key")
    parser.add_argument("--topic",    help="Custom search topic")
    parser.add_argument("--url",      help="Process a single YouTube URL")
    parser.add_argument("--max",      type=int, default=5, help="Max results per query")
    parser.add_argument("--metadata-only", action="store_true", help="Skip video download")
    parser.add_argument("--output",   default=str(OUTPUT_DIR), help="Output directory")
    parser.add_argument("--cookies",  dest="cookies_file", help="Path to cookies.txt")
    args = parser.parse_args()

    base_dir = Path(args.output)
    dirs = setup_dirs(base_dir)

    print("=" * 55)
    print("  Healthcare Opinion Video Collector")
    print("=" * 55)
    print(f"  Output:   {base_dir.resolve()}")
    print(f"  Mode:     {'metadata only' if args.metadata_only else 'full download'}")

    if args.url:
        results = collect_url(args.url, args.api_key, dirs,
                              args.metadata_only, args.cookies_file)
    else:
        queries = [args.topic] if args.topic else DEFAULT_SEARCH_QUERIES
        print(f"  Queries:  {len(queries)}  ·  Max per query: {args.max}")
        print("=" * 55)
        results = collect(queries, args.api_key, dirs,
                          args.max, args.metadata_only, args.cookies_file)

    if results:
        save_summary(results, dirs)
    else:
        print("\n⚠️  No videos collected.")


if __name__ == "__main__":
    main()