"""
Patient Representative API endpoints.

POST /api/representative/chat/
    Body: { message, history, filters }
    Returns: { response }

GET  /api/representative/topics/
    Returns: { topics, healthcare_systems }
"""
import asyncio

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from services.llm import llm_complete
from .supabase_client import fetch_responses, get_topic_summary
from .prompt import build_representative_prompt


@api_view(["GET"])
@permission_classes([AllowAny])
def topic_summary(request):
    """
    Returns available topics and healthcare systems with response counts.
    Used to populate frontend filter dropdowns.
    """
    try:
        summary = get_topic_summary()
        return Response(summary)
    except RuntimeError as e:
        return Response({"error": str(e)}, status=503)


@api_view(["POST"])
@permission_classes([AllowAny])
def chat(request):
    """
    Send a question to the Patient Representative.

    Body:
        message  (str)  — the question from the meeting attendee
        history  (list) — previous turns [{"role": "user"|"assistant", "content": "..."}]
        filters  (dict) — demographic/topic filters:
                          { topic, healthcare_system, sentiment, age_group, gender }

    Returns:
        { response: str }
    """
    message = (request.data.get("message") or "").strip()
    if not message:
        return Response({"error": "message required"}, status=400)

    history = request.data.get("history") or []
    filters = request.data.get("filters") or {}

    # Fetch relevant real opinions from Supabase
    try:
        responses = fetch_responses(
            query=message,
            topic=filters.get("topic"),
            healthcare_system=filters.get("healthcare_system"),
            sentiment=filters.get("sentiment"),
            age_group=filters.get("age_group"),
            gender=filters.get("gender"),
            limit=50,
        )
    except RuntimeError as e:
        return Response({"error": str(e)}, status=503)

    # Build system prompt from real opinions + filters
    system_prompt = build_representative_prompt(responses, filters)

    # Build message history
    messages = [*history, {"role": "user", "content": message}]

    # Call Groq
    loop = asyncio.new_event_loop()
    try:
        reply = loop.run_until_complete(
            llm_complete(
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.45,   # slightly higher than OSCE — more natural variation
                max_tokens=250,
            )
        )
    finally:
        loop.close()

    return Response({"response": reply})
@api_view(["GET"])
@permission_classes([AllowAny])
def debug_env(request):
    import os
    return Response({
        "supabase_url": bool(os.environ.get("SUPABASE_URL")),
        "supabase_key": bool(os.environ.get("SUPABASE_KEY")),
        "groq_key": bool(os.environ.get("GROQ_API_KEY")),
    })