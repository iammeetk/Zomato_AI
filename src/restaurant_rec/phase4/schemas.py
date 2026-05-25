"""Phase 4 — HTTP response models."""

from __future__ import annotations

from pydantic import BaseModel, Field

from restaurant_rec.config import PROMPT_VERSION
from restaurant_rec.phase3.models import RecommendationResult


class HealthCheckResponse(BaseModel):
    status: str
    dataset: str
    schema_version: str | None = None
    dataset_snapshot_id: str | None = None
    row_count: int | None = None
    prompt_version: str = PROMPT_VERSION
    warning: str | None = None


class LocalitiesResponse(BaseModel):
    metros: list[str] = Field(default_factory=list)
    localities: list[str] = Field(default_factory=list)


class RecommendResponse(RecommendationResult):
    """Recommendation payload plus Phase 4 orchestration metadata."""

    filter_count: int = Field(ge=0, description="Rows matching hard filters before cap.")
    returned_count: int = Field(ge=0, description="Candidates sent to Phase 3.")
    dataset_snapshot_id: str | None = None
    message: str | None = Field(
        default=None,
        description="User-facing hint when no candidates or partial pipeline notes.",
    )
