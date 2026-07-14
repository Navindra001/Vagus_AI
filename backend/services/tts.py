import base64, asyncio
from groq import Groq
import os

def synthesise(text: str, voice: str = "Aaliya-PlayAI") -> str:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    try:
        response = client.audio.speech.create(
            model="playai-tts",
            voice=voice,
            input=text[:500],
        )
        return base64.b64encode(response.content).decode()
    except Exception as e:
        print(f"[TTS] Groq TTS failed: {e}")
        return ""