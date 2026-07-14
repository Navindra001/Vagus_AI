from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.sessions.models import ConsultationSession
from services.feedback.scorer import generate_feedback
import asyncio


@api_view(["POST", "GET"])
@permission_classes([AllowAny])
def get_feedback(request, session_id):
    try:
        session = ConsultationSession.objects.select_related('case').get(pk=session_id)
    except ConsultationSession.DoesNotExist:
        return Response({"error": "Session not found"}, status=404)

    if not session.messages:
        return Response({"error": "No messages in session"}, status=400)

    primary_diagnosis = ""
    differentials     = ""
    management_plan   = ""

    if request.method == "POST" and request.data:
        primary_diagnosis = request.data.get("primary_diagnosis", "").strip()
        differentials     = request.data.get("differentials", "").strip()
        management_plan   = request.data.get("management_plan", "").strip()

    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(
            generate_feedback(
                session,
                primary_diagnosis=primary_diagnosis,
                differentials=differentials,
                management_plan=management_plan,
            )
        )
    finally:
        loop.close()

    return Response(result)