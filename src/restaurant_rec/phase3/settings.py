"""Groq / Phase 3 settings loaded from environment and optional ``.env``."""

from __future__ import annotations

import os
from dataclasses import dataclass

from restaurant_rec.config import (
    DEFAULT_GROQ_MAX_TOKENS,
    DEFAULT_GROQ_MODEL,
    DEFAULT_GROQ_TEMPERATURE,
    DEFAULT_GROQ_TIMEOUT_SECONDS,
    DEFAULT_RECOMMENDATION_TOP_K,
    PROJECT_ROOT,
)


def load_project_dotenv() -> None:
    """Load ``.env`` from repo root if ``python-dotenv`` is available."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    path = PROJECT_ROOT / ".env"
    if path.is_file():
        load_dotenv(path, override=False)


@dataclass(frozen=True)
class GroqSettings:
    """Runtime knobs for Groq chat completions."""

    api_key: str | None
    model: str
    temperature: float
    max_tokens: int
    timeout_seconds: float
    recommendation_top_k: int

    @classmethod
    def from_env(cls) -> GroqSettings:
        load_project_dotenv()
        return cls(
            api_key=(os.getenv("GROQ_API_KEY") or "").strip() or None,
            model=os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL),
            temperature=float(os.getenv("GROQ_TEMPERATURE", str(DEFAULT_GROQ_TEMPERATURE))),
            max_tokens=int(os.getenv("GROQ_MAX_TOKENS", str(DEFAULT_GROQ_MAX_TOKENS))),
            timeout_seconds=float(
                os.getenv("GROQ_TIMEOUT_SECONDS", str(DEFAULT_GROQ_TIMEOUT_SECONDS)),
            ),
            recommendation_top_k=int(
                os.getenv("RECOMMENDATION_TOP_K", str(DEFAULT_RECOMMENDATION_TOP_K)),
            ),
        )
