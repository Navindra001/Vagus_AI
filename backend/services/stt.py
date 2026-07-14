"""
Speech-to-text service using faster-whisper (local, CPU-friendly).
"""
from faster_whisper import WhisperModel
import tempfile
import os

_model = None


def get_whisper() -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel("medium", device="cpu", compute_type="int8")
    return _model


def transcribe(audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
    """
    Transcribe audio bytes to text.

    Args:
        audio_bytes: Raw audio data.
        mime_type:   MIME type of the audio (audio/wav or audio/webm).

    Returns:
        Transcribed text string.
    """
    suffix = ".wav" if "wav" in mime_type else ".webm"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(audio_bytes)
    tmp.close()
    try:
        model = get_whisper()
        segments, _ = model.transcribe(tmp.name, beam_size=5)
        return " ".join(s.text for s in segments).strip()
    finally:
        os.unlink(tmp.name)
