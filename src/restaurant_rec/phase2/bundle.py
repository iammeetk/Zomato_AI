"""Phase 2 — CandidateBundle payload for the LLM layer (Phase 3)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class BundleMetadata(BaseModel):
    """Counts and provenance for downstream prompts and UI."""

    filter_count: int = Field(ge=0, description="Rows passing all hard filters.")
    returned_count: int = Field(ge=0, description="Candidates after cap (≤ filter_count).")
    dataset_snapshot_id: str = Field(description="Pinned dataset snapshot / manifest id.")


class CandidateItem(BaseModel):
    """One row in the bounded candidate list."""

    restaurant_id: str
    name: str
    city: str
    cuisines: list[str]
    rating: float | None = Field(description="Aggregate rating; null excluded by filters.")
    estimated_cost_display: str
    budget_band: str


class CandidateBundle(BaseModel):
    """Structured output of Phase 2."""

    preferences: dict[str, object]
    candidates: list[CandidateItem]
    metadata: BundleMetadata
