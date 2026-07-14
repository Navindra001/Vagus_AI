"""
Text-to-speech using Groq TTS API.
Returns base64-encoded MP3 audio.
"""
import os
import base64
from groq import Groq

def synthesise(text: str, voice: str = "Aaliyah") -> str:
    if not text.strip():
        return ""
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
        response = client.audio.speech.create(
            model="playai-tts",
            voice=voice,
            input=text,
            response_format="mp3",
        )
        return base64.b64encode(response.content).decode()
    except Exception as e:
        print(f"[TTS] Groq TTS failed: {e}")
        return ""