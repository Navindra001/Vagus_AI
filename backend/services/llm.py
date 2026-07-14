"""
LLM service — powered by Groq (replaces Ollama).

Groq offers free-tier access to Llama 3.3 70B with very fast inference.
Get your API key at: https://console.groq.com
Set GROQ_API_KEY in backend/.env
"""
import asyncio
from groq import AsyncGroq
from django.conf import settings


def _get_client() -> AsyncGroq:
    return AsyncGroq(api_key=settings.GROQ_API_KEY)


async def llm_complete(
    messages: list[dict],
    system_prompt: str,
    temperature: float = 0.35,
    max_tokens: int = 200,
) -> str:
    """
    Send a chat completion request to Groq.

    Args:
        messages:      List of {"role": "user"|"assistant", "content": "..."} dicts.
        system_prompt: Injected as the system message.
        temperature:   Sampling temperature (0.0–1.0).
        max_tokens:    Maximum tokens to generate.

    Returns:
        The assistant reply as a plain string.
    """
    client = _get_client()

    groq_messages = [
        {"role": "system", "content": system_prompt},
        *messages,
    ]

    response = await client.chat.completions.create(
        model=settings.GROQ_MODEL,          # default: llama-3.3-70b-versatile
        messages=groq_messages,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=0.80,
        stream=False,
    )

    return response.choices[0].message.content.strip()


async def llm_complete_json(
    messages: list[dict],
    system_prompt: str,
    temperature: float = 0.1,
    max_tokens: int = 600,
) -> str:
    """
    Same as llm_complete but requests JSON output mode.
    Use for structured scoring / feedback responses.
    """
    client = _get_client()

    groq_messages = [
        {"role": "system", "content": system_prompt},
        *messages,
    ]

    response = await client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=groq_messages,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=0.80,
        stream=False,
        response_format={"type": "json_object"},   # Groq JSON mode
    )

    return response.choices[0].message.content.strip()
