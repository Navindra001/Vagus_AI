"""
Rule-based transcript checker.
Checks for keyword evidence of each OSCE domain in the doctor's turns.
"""
from .rubric import OSCE_RUBRIC


def check_transcript(transcript: str) -> dict[str, bool | None]:
    """
    Scan the transcript for keyword evidence per domain.

    Only examines lines starting with "Doctor:".

    Returns:
        Dict mapping domain_key → True (found) | False (not found) | None (LLM-only domain).
    """
    doctor_text = " ".join(
        line.replace("Doctor:", "").lower()
        for line in transcript.split("\n")
        if line.startswith("Doctor:")
    )

    results: dict[str, bool | None] = {}
    for domain in OSCE_RUBRIC["domains"]:
        kw_groups = domain["keywords"]
        if not kw_groups:
            results[domain["key"]] = None   # LLM-only — no rule check
            continue
        # All groups must have at least one matching keyword
        results[domain["key"]] = all(
            any(kw in doctor_text for kw in group)
            for group in kw_groups
        )

    return results
