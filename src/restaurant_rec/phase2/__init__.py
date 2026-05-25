"""Phase 2 — preference validation, deterministic filtering, candidate bundle."""

from restaurant_rec.phase2.bundle import BundleMetadata, CandidateBundle, CandidateItem
from restaurant_rec.phase2.filter_engine import (
    RestaurantDataAccess,
    explain_ideal_costs_markdown,
    filter_restaurants,
)
from restaurant_rec.phase2.preferences import PreferenceDTO, UserBudget

__all__ = [
    "PreferenceDTO",
    "UserBudget",
    "CandidateBundle",
    "CandidateItem",
    "BundleMetadata",
    "RestaurantDataAccess",
    "filter_restaurants",
    "explain_ideal_costs_markdown",
]
