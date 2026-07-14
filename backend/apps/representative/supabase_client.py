import os
from functools import lru_cache


@lru_cache(maxsize=1)
def get_supabase():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in backend/.env")
    from supabase import create_client
    return create_client(url, key)


@lru_cache(maxsize=1)
def _get_model():
    from fastembed import TextEmbedding
    return TextEmbedding("BAAI/bge-small-en-v1.5")


def _embed(text: str) -> list[float]:
    return list(_get_model().embed([text]))[0].tolist()


def fetch_responses(
    query: str = None,
    topic: str = None,
    healthcare_system: str = None,
    sentiment: str = None,
    age_group: str = None,
    gender: str = None,
    limit: int = 40,
) -> list[dict]:
    client = get_supabase()

    if query:
        try:
            result = client.rpc("match_responses", {
                "query_embedding":   _embed(query),
                "match_count":       limit,
                "filter_age":        age_group or None,
                "filter_gender":     gender or None,
                "filter_sentiment":  sentiment or None,
            }).execute()
            return result.data or []
        except Exception as e:
            print(f"[RAG] vector search failed ({e}), falling back to filters")

    q = (
        client.table("responses")
        .select("text, sentiment, sentiment_score, emotion, "
                "speaker_age_group, speaker_gender, speaker_region, "
                "questions(text, topic, healthcare_system)")
        .limit(limit)
    )
    if sentiment:         q = q.eq("sentiment", sentiment)
    if age_group:         q = q.eq("speaker_age_group", age_group)
    if gender:            q = q.eq("speaker_gender", gender)
    if topic:             q = q.eq("questions.topic", topic)
    if healthcare_system: q = q.eq("questions.healthcare_system", healthcare_system)
    return q.execute().data or []


def get_topic_summary() -> dict:
    client = get_supabase()
    rows = client.table("questions").select("topic, healthcare_system").execute().data or []
    topics, systems = {}, {}
    for row in rows:
        t = row.get("topic") or "general"
        s = row.get("healthcare_system") or "Unknown"
        topics[t] = topics.get(t, 0) + 1
        systems[s] = systems.get(s, 0) + 1
    return {"topics": topics, "healthcare_systems": systems}