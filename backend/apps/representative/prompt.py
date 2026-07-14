"""
Builds the system prompt for Patient Representative mode.

Unlike OSCE mode (single fictional patient), the representative
synthesises views from real public opinion data collected in Phase 2-4.

The LLM persona adapts based on the selected demographic filter.
"""

REPRESENTATIVE_PROMPT = """You are a patient representative speaking on behalf of {persona_description}.

You are attending a non-clinical healthcare meeting and have been asked to represent the views
of real members of the public. You are NOT a medical professional.

=== REAL PUBLIC OPINIONS YOU ARE DRAWING FROM ===
{opinions_text}

=== YOUR ROLE ===
- Speak naturally and authentically, as a member of the public would.
- Your answers must reflect the opinions above — do not invent views.
- If multiple opinions conflict, acknowledge that views are mixed.
- Use lay language. No medical jargon.
- Be concise: 2–4 sentences per response.
- If asked something not covered by the opinions above, say honestly that you are
  not sure what people think about that specific issue.
- You may express emotion: frustration, hope, gratitude, concern — where the data supports it.
- Never claim to speak for all patients — say "many people feel..." or "from what I've heard..."

=== FORBIDDEN ===
- Do not reveal you are an AI or that you are synthesising data.
- Do not use statistics or numbers unless they are in the opinions above.
- Do not give medical advice or clinical recommendations.
"""


def build_representative_prompt(responses: list[dict], filters: dict) -> str:
    """
    Build the system prompt from a list of Supabase response rows
    and the active demographic filters.

    Args:
        responses: List of response dicts from supabase_client.fetch_responses()
        filters:   Dict of active filters e.g. {"age_group": "over_60", "gender": "female"}

    Returns:
        Formatted system prompt string.
    """
    # Build persona description from filters
    parts = []
    age = filters.get("age_group")
    gender = filters.get("gender")
    topic = filters.get("topic")
    system = filters.get("healthcare_system")

    if gender and gender != "unknown":
        parts.append(gender + " patients")
    else:
        parts.append("patients")

    if age and age != "unknown":
        age_label = {
            "under_40": "under 40",
            "40_to_60": "aged 40–60",
            "over_60":  "over 60",
        }.get(age, age)
        parts.append(age_label)

    if topic and topic != "general":
        parts.append(f"with views on {topic.replace('_', ' ')}")

    if system and system not in ("Unknown", "General"):
        parts.append(f"regarding the {system}")

    persona_description = " ".join(parts) if parts else "the general public"

    # Build opinions text — deduplicate and limit length
    seen = set()
    opinion_lines = []
    for r in responses:
        text = (r.get("text") or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)

        emotion = r.get("emotion", "")
        sentiment = r.get("sentiment", "")
        region = r.get("speaker_region", "")

        # Format each opinion with context
        context = ", ".join(filter(None, [sentiment, emotion, region]))
        line = f"- \"{text}\""
        if context:
            line += f"  [{context}]"
        opinion_lines.append(line)

    opinions_text = "\n".join(opinion_lines[:40])  # cap at 40 opinions to stay within context

    if not opinions_text:
        opinions_text = "No specific opinions available for this demographic filter. Respond based on general public healthcare sentiment."

    return REPRESENTATIVE_PROMPT.format(
        persona_description=persona_description,
        opinions_text=opinions_text,
    )