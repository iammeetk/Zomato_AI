"""Phase 2 — structured user preferences (PreferenceDTO)."""

from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import AliasChoices, BaseModel, BeforeValidator, ConfigDict, Field, field_validator


def _coerce_cuisine_list(v: object) -> list[str]:
    if v is None:
        return []
    if isinstance(v, str):
        parts = [p.strip() for p in v.replace("|", ",").split(",")]
        return [p for p in parts if p]
    if isinstance(v, (list, tuple)):
        out: list[str] = []
        for item in v:
            if item is None:
                continue
            s = str(item).strip()
            if s:
                out.append(s)
        return out
    raise TypeError("cuisine must be str or list of str")


class UserBudget(str, Enum):
    """End-user budget tier (subset of canonical ``BudgetBand``; excludes ``unknown``)."""

    low = "low"
    medium = "medium"
    high = "high"


class PreferenceDTO(BaseModel):
    """
    Validated preferences before deterministic filtering.

    Location matching policy (see ``docs/phase2-filtering.md``): case-insensitive substring match
    of the user's ``location`` against the canonical ``city`` field (either direction unnecessary —
    we test ``city`` contains ``location`` after normalization).
    """

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    locality: str = Field(
        min_length=1,
        validation_alias=AliasChoices("locality", "location"),
    )
    budget: UserBudget
    cuisine: Annotated[list[str], BeforeValidator(_coerce_cuisine_list)]
    min_rating: Annotated[float, Field(ge=0.0, le=5.0)]
    additional_preferences: str | None = None

    @field_validator("cuisine")
    @classmethod
    def cuisine_non_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("at least one cuisine is required")
        return v

    def cuisine_tokens_casefold(self) -> set[str]:
        """Tokens for OR-style cuisine overlap (case-insensitive)."""
        return {c.casefold().strip() for c in self.cuisine if c.strip()}

    def echo_dict(self) -> dict[str, object]:
        """JSON-friendly dict for CandidateBundle (echo to Phase 3)."""
        return {
            "locality": self.locality,
            "budget": self.budget.value,
            "cuisine": list(self.cuisine),
            "min_rating": self.min_rating,
            "additional_preferences": self.additional_preferences,
        }
