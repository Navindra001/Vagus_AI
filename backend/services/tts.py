"""
Text-to-speech service using Kokoro ONNX (local, no API key needed).
Falls back gracefully if Kokoro models are not installed.
"""
import base64
import tempfile
import os

_kokoro = None


def get_kokoro():
    global _kokoro
    if _kokoro is None:
        try:
            from kokoro_onnx import Kokoro
            _kokoro = Kokoro("kokoro-v0_19.onnx", "voices.bin")
        except Exception as e:
            print(f"[TTS] Kokoro unavailable: {e}. Audio will be disabled.")
            _kokoro = "unavailable"
    return _kokoro


def synthesise(text: str, voice: str = "af_sarah") -> str:
    """
    Synthesise text to speech.

    Args:
        text:  Text to speak.
        voice: Kokoro voice ID (default: af_sarah — British female).

    Returns:
        Base64-encoded WAV string, or empty string if TTS unavailable.
    """
    kokoro = get_kokoro()
    if kokoro == "unavailable":
        return ""

    import soundfile as sf
    samples, sr = kokoro.create(text, voice=voice, speed=1.0, lang="en-us")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    sf.write(tmp.name, samples, sr)
    try:
        with open(tmp.name, "rb") as f:
            return base64.b64encode(f.read()).decode()
    finally:
        os.unlink(tmp.name)
