"""Phase 3 — recommendation output models (Phase 4/5 contract)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RecommendationItem(BaseModel):
    """One displayed recommendation with store-backed facts + LLM (or template) prose."""

    restaurant_id: str
    name: str
    cuisine: str = Field(description="Display string (e.g. comma-separated cuisines).")
    rating: float | None
    estimated_cost: str
    explanation: str
    rank: int = Field(ge=1)


class RecommendationResult(BaseModel):
    """Result of ``recommend()`` after Groq (or fallback)."""

    items: list[RecommendationItem]
    summary: str | None = None
    used_llm: bool
    warnings: list[str] = Field(default_factory=list)
