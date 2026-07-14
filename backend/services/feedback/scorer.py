"""
Two-stage OSCE feedback generator using Groq.

Stage 1: Structured JSON scoring (run twice at different temps, then average).
Stage 1b: Clinical reasoning — evaluate student's submitted diagnosis + plan.
Stage 2: Narrative prose feedback for the student.
"""
import json
import re
import asyncio

from .rubric import OSCE_RUBRIC
from .checker import check_transcript
from services.llm import llm_complete, llm_complete_json


STAGE_1_PROMPT = """You are a senior medical OSCE examiner.

=== PATIENT CASE ===
{patient_story}

=== FULL TRANSCRIPT ===
{transcript}

=== OBJECTIVE KEYWORD CHECKS (rule-based, use to inform but not override) ===
{keyword_results}

Score each domain 0–10 based on the transcript. Reply ONLY with valid JSON:
{{
  "domain_scores": {{
    "presenting_complaint": 0,
    "history_of_pc": 0,
    "past_medical_history": 0,
    "drug_history": 0,
    "family_history": 0,
    "social_history": 0,
    "ice": 0,
    "systems_review": 0,
    "summarising": 0,
    "communication": 0
  }},
  "missed_questions": ["list of important questions the doctor did not ask"],
  "diagnosis_correct": true,
  "diagnosis_feedback": "brief sentence on their diagnostic reasoning"
}}"""


STAGE_1B_PROMPT = """You are a senior medical OSCE examiner evaluating a student's clinical reasoning.

=== PATIENT CASE (do not reveal to student) ===
Condition: {condition}
Full background: {patient_story}
Expected diagnosis: {expected_diagnosis}

=== FULL CONSULTATION TRANSCRIPT ===
{transcript}

=== STUDENT'S SUBMITTED CLINICAL ASSESSMENT ===
Primary diagnosis: {primary_diagnosis}
Differential diagnoses: {differentials}
Management plan: {management_plan}

Evaluate the student's clinical reasoning. Reply ONLY with valid JSON:
{{
  "primary_diagnosis_correct": true,
  "primary_diagnosis_score": 0,
  "differential_quality_score": 0,
  "management_plan_score": 0,
  "clinical_reasoning_score": 0,
  "primary_diagnosis_feedback": "specific feedback on their primary diagnosis",
  "differential_feedback": "specific feedback on quality and completeness of differentials",
  "management_feedback": "specific feedback on their management plan — what was good, what was missing",
  "safety_netting": true,
  "safety_netting_feedback": "did they mention follow-up, red flags, or safety netting in their plan?"
}}

Score rubric (0–10 each):
- primary_diagnosis_score: 0=wrong, 5=partially correct, 10=correct with good reasoning
- differential_quality_score: relevance, breadth, clinical logic of differentials
- management_plan_score: appropriateness of investigations, treatment, referral, safety netting
- clinical_reasoning_score: overall quality of reasoning linking history to diagnosis to plan"""


STAGE_2_PROMPT = """You are a supportive medical educator giving feedback to a student after a telemedicine OSCE consultation.

Domain scores (out of 10):
{scores}

Clinical reasoning:
- Primary diagnosis: {primary_diagnosis} ({diagnosis_correct})
- Management plan score: {management_plan_score}/10
- Missed history areas: {missed}

Write 4–5 sentences of encouraging, specific, actionable feedback.
Start with one genuine strength from either their history-taking or clinical reasoning.
Then give one specific improvement for history-taking and one for clinical reasoning or management.
End with a motivational closing line.
Be a coach, not just a marker. Use warm, professional language.
Reply with plain prose only — no JSON, no bullet points, no headers."""


async def _score_once(transcript: str, patient_story: str, kw_summary: str, temp: float) -> dict:
    """Run one scoring pass and return parsed JSON."""
    raw = await llm_complete_json(
        messages=[{
            "role": "user",
            "content": STAGE_1_PROMPT.format(
                patient_story=patient_story,
                transcript=transcript,
                keyword_results=kw_summary,
            ),
        }],
        system_prompt="You are a medical OSCE examiner. Respond only in valid JSON.",
        temperature=temp,
        max_tokens=700,
    )
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        return json.loads(m.group()) if m else {}


async def _score_clinical_reasoning(
    transcript: str,
    case,
    primary_diagnosis: str,
    differentials: str,
    management_plan: str,
) -> dict:
    """Stage 1b — evaluate the student's submitted clinical assessment."""
    raw = await llm_complete_json(
        messages=[{
            "role": "user",
            "content": STAGE_1B_PROMPT.format(
                condition=case.condition,
                patient_story=case.patient_story,
                expected_diagnosis=case.expected_diagnosis,
                transcript=transcript,
                primary_diagnosis=primary_diagnosis or "Not provided",
                differentials=differentials or "Not provided",
                management_plan=management_plan or "Not provided",
            ),
        }],
        system_prompt="You are a medical OSCE examiner. Respond only in valid JSON.",
        temperature=0.1,
        max_tokens=800,
    )
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        return json.loads(m.group()) if m else {}


async def generate_feedback(
    session,
    primary_diagnosis: str = "",
    differentials: str = "",
    management_plan: str = "",
) -> dict:
    """
    Generate structured + narrative feedback for a completed session.

    Args:
        session:            ConsultationSession ORM object with .messages and .case.
        primary_diagnosis:  Student's submitted primary diagnosis.
        differentials:      Student's submitted differential diagnoses.
        management_plan:    Student's submitted management plan.

    Returns:
        Dict with history scores, clinical reasoning scores, and narrative feedback.
    """
    transcript = "\n".join([
        f"{'Doctor' if m['role'] == 'user' else 'Patient'}: {m['content']}"
        for m in (session.messages or [])
    ])

    keyword_results = check_transcript(transcript)
    kw_summary = "\n".join(
        f"  {k}: {'FOUND' if v else ('NOT FOUND' if v is False else 'N/A (LLM only)')}"
        for k, v in keyword_results.items()
    )

    # Stage 1 + 1b — run concurrently
    (r1, r2), cr = await asyncio.gather(
        asyncio.gather(
            _score_once(transcript, session.case.patient_story, kw_summary, 0.1),
            _score_once(transcript, session.case.patient_story, kw_summary, 0.3),
        ),
        _score_clinical_reasoning(
            transcript,
            session.case,
            primary_diagnosis,
            differentials,
            management_plan,
        ),
    )

    domain_scores: dict[str, int] = {}
    for domain in OSCE_RUBRIC["domains"]:
        k = domain["key"]
        s1 = (r1.get("domain_scores") or {}).get(k, 0)
        s2 = (r2.get("domain_scores") or {}).get(k, 0)
        domain_scores[k] = round((s1 + s2) / 2)

    history_score      = round(sum(domain_scores.values()) / len(domain_scores) * 10)
    missed             = r1.get("missed_questions", [])
    diagnosis_correct  = r1.get("diagnosis_correct", False)
    diagnosis_feedback = r1.get("diagnosis_feedback", "")

    cr_primary_score      = cr.get("primary_diagnosis_score", 0)
    cr_differential_score = cr.get("differential_quality_score", 0)
    cr_management_score   = cr.get("management_plan_score", 0)
    cr_reasoning_score    = cr.get("clinical_reasoning_score", 0)
    clinical_score        = round((cr_primary_score + cr_differential_score + cr_management_score + cr_reasoning_score) / 4 * 10)

    # 60% history, 40% clinical reasoning
    overall_score = round(history_score * 0.6 + clinical_score * 0.4)

    scores_str = "\n".join(f"  {k}: {v}/10" for k, v in domain_scores.items())
    narrative = await llm_complete(
        messages=[{
            "role": "user",
            "content": STAGE_2_PROMPT.format(
                scores=scores_str,
                missed=", ".join(missed) if missed else "none",
                primary_diagnosis=primary_diagnosis or "not submitted",
                diagnosis_correct="correct" if cr.get("primary_diagnosis_correct") else "incorrect",
                management_plan_score=cr_management_score,
            ),
        }],
        system_prompt="You are a supportive medical educator. Reply in plain prose only.",
        temperature=0.6,
        max_tokens=400,
    )

    return {
        "overall_score":               overall_score,
        "history_score":               history_score,
        "domain_scores":               domain_scores,
        "missed_questions":            missed,
        "diagnosis_correct":           diagnosis_correct,
        "diagnosis_feedback":          diagnosis_feedback,
        "narrative_feedback":          narrative,
        "keyword_checks":              keyword_results,
        "clinical_reasoning_score":    clinical_score,
        "primary_diagnosis_correct":   cr.get("primary_diagnosis_correct", False),
        "primary_diagnosis_score":     cr_primary_score,
        "differential_quality_score":  cr_differential_score,
        "management_plan_score":       cr_management_score,
        "reasoning_score":             cr_reasoning_score,
        "primary_diagnosis_feedback":  cr.get("primary_diagnosis_feedback", ""),
        "differential_feedback":       cr.get("differential_feedback", ""),
        "management_feedback":         cr.get("management_feedback", ""),
        "safety_netting":              cr.get("safety_netting", False),
        "safety_netting_feedback":     cr.get("safety_netting_feedback", ""),
        "submitted_primary_diagnosis": primary_diagnosis,
        "submitted_differentials":     differentials,
        "submitted_management_plan":   management_plan,
    }