"""
Text-to-speech using Edge TTS (Microsoft, free, no API key).
Returns base64-encoded MP3 audio.
"""
import asyncio
import base64
import tempfile
import os
import edge_tts

VOICE = "en-GB-SoniaNeural"  # British female — matches VAGUS AI clinical context

async def _synthesise_async(text: str) -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tmp.close()
    try:
        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(tmp.name)
        with open(tmp.name, "rb") as f:
            return base64.b64encode(f.read()).decode()
    finally:
        os.unlink(tmp.name)

def synthesise(text: str, voice: str = VOICE) -> str:
    """
    Synthesise text to speech.
    Returns base64-encoded MP3 string, or empty string on failure.
    """
    if not text.strip():
        return ""
    try:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, _synthesise_async(text))
                    return future.result(timeout=15)
        except RuntimeError:
            pass
        return asyncio.run(_synthesise_async(text))
    except Exception as e:
        print(f"[TTS] Edge TTS failed: {e}")
        return ""