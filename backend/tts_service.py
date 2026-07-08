"""TTS synthesis — calls the OpenAI TTS API directly via httpx.

Works with any OpenAI-compatible key (OpenAI sk-... or a proxy that supports
the /v1/audio/speech endpoint). Returns base64-encoded MP3 audio.
"""
from __future__ import annotations
import os
import base64
import logging

log = logging.getLogger(__name__)

_TTS_URL = "https://api.openai.com/v1/audio/speech"
_MAX_CHARS = 4000


async def synthesize_speech_base64(text: str, voice: str = "nova", model: str = "tts-1") -> str | None:
    """Return base64-encoded MP3 audio for the given text, or None on failure."""
    key = os.environ.get("LLM_API_KEY", "").strip()
    if not key:
        log.warning("LLM_API_KEY not set — TTS unavailable")
        return None

    # Gemini keys don't support OpenAI TTS — skip gracefully
    if key.startswith("AIza"):
        log.info("Gemini key detected — TTS requires an OpenAI key; skipping audio")
        return None

    if len(text) > _MAX_CHARS:
        text = text[:_MAX_CHARS]

    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as c:
            r = await c.post(
                _TTS_URL,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json={"model": model, "voice": voice, "input": text},
            )
            r.raise_for_status()
            return base64.b64encode(r.content).decode("utf-8")
    except Exception as e:
        log.warning("TTS synthesis failed: %s", e)
        return None
