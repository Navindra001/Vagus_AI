from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import ConsultationSession
from apps.cases.models import PatientCase
from services.patient import build_system_prompt
from services.llm import llm_complete
from services.tts import synthesise
import asyncio


@api_view(["POST"])
@permission_classes([AllowAny])
def create_session(request):
    """Create a new consultation session for the given case_id."""
    case_id = request.data.get("case_id")
    if not case_id:
        return Response({"error": "case_id required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        case = PatientCase.objects.get(pk=case_id)
    except PatientCase.DoesNotExist:
        return Response({"error": "Case not found"}, status=status.HTTP_404_NOT_FOUND)

    session = ConsultationSession.objects.create(case=case)
    return Response({"id": str(session.id)}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def chat(request, session_id):
    """
    Send a student message to the simulated patient.
    Returns the patient's reply + optional TTS audio.
    """
    try:
        session = ConsultationSession.objects.get(pk=session_id, status="active")
    except ConsultationSession.DoesNotExist:
        return Response({"error": "Session not found or already complete"}, status=404)

    student_message = request.data.get("message", "").strip()
    if not student_message:
        return Response({"error": "message required"}, status=400)

    # Append student message to history
    session.messages.append({"role": "user", "content": student_message})

    # Build system prompt from case
    system_prompt = build_system_prompt({
        "patient_name": session.case.patient_name,
        "patient_story": session.case.patient_story,
        "age": session.case.age,
        "gender": session.case.gender,
        "condition": session.case.condition,
        "patient_role": session.case.patient_role,
    })

    # Call Groq (run async in sync context)
    loop = asyncio.new_event_loop()
    try:
        patient_reply = loop.run_until_complete(
            llm_complete(
                messages=session.messages,
                system_prompt=system_prompt,
                temperature=0.35,
                max_tokens=200,
            )
        )
    finally:
        loop.close()

    # Append patient reply to history
    session.messages.append({"role": "assistant", "content": patient_reply})
    session.save()

    # Synthesise TTS audio (non-blocking — returns "" if Kokoro not installed)
    audio_b64 = synthesise(patient_reply)

    return Response({
        "response": patient_reply,
        "audio_b64": audio_b64,
        "message_count": len(session.messages),
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def complete_session(request, session_id):
    """Mark session as complete so feedback can be generated."""
    try:
        session = ConsultationSession.objects.get(pk=session_id)
    except ConsultationSession.DoesNotExist:
        return Response({"error": "Session not found"}, status=404)

    session.status = "complete"
    session.ended_at = timezone.now()
    session.save()
    return Response({"status": "complete"})


@api_view(["GET"])
@permission_classes([AllowAny])
def get_session(request, session_id):
    """Retrieve session details."""
    try:
        session = ConsultationSession.objects.get(pk=session_id)
    except ConsultationSession.DoesNotExist:
        return Response({"error": "Session not found"}, status=404)

    return Response({
        "id": str(session.id),
        "case_id": str(session.case.id),
        "status": session.status,
        "message_count": len(session.messages),
        "started_at": session.started_at,
        "ended_at": session.ended_at,
    })
