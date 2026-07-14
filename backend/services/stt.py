"""
Speech-to-text using Groq Whisper API.
No local model needed — uses the same GROQ_API_KEY as the LLM.
"""
import os
import tempfile
from groq import Groq

def transcribe(audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
    client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
    suffix = ".wav" if "wav" in mime_type else ".webm"

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(audio_bytes)
    tmp.close()

    try:
        with open(tmp.name, "rb") as f:
            transcription = client.audio.transcriptions.create(
                file=(tmp.name, f.read()),
                model="whisper-large-v3-turbo",
                response_format="text",
            )
        return transcription.strip() if isinstance(transcription, str) else transcription.text.strip()
    finally:
        os.unlink(tmp.name)