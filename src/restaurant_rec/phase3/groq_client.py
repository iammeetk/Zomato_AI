"""Groq Inference API via OpenAI-compatible client."""

from __future__ import annotations

from openai import OpenAI

from restaurant_rec.config import GROQ_API_BASE
from restaurant_rec.phase3.settings import GroqSettings


def chat_completion(system_prompt: str, user_content: str, settings: GroqSettings) -> str:
    """
    Run a single chat completion on Groq.

    Raises:
        ValueError: If ``GROQ_API_KEY`` is missing in settings.
        openai.APIError / APIConnectionError: On transport or HTTP errors.
    """
    if not settings.api_key:
        raise ValueError("GROQ_API_KEY is not set")
    client = OpenAI(
        api_key=settings.api_key,
        base_url=GROQ_API_BASE,
        timeout=settings.timeout_seconds,
    )
    response = client.chat.completions.create(
        model=settings.model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
    )
    choice = response.choices[0].message
    if choice is None or choice.content is None:
        return ""
    return choice.content.strip()
