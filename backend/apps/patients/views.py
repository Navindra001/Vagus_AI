from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from services.stt import transcribe


@api_view(["POST"])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser])
def speech_to_text(request):
    """
    Accept an audio file upload and return a transcript.
    Used by the VoiceInput frontend component.
    """
    audio_file = request.FILES.get("audio")
    if not audio_file:
        return Response({"error": "No audio file provided"}, status=400)

    audio_bytes = audio_file.read()
    mime_type   = audio_file.content_type or "audio/webm"

    try:
        transcript = transcribe(audio_bytes, mime_type)
        return Response({"transcript": transcript})
    except Exception as e:
        return Response({"error": f"Transcription failed: {str(e)}"}, status=500)
