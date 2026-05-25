"""
Phase 2 — deterministic filtering and pre-ranking.

Policies are summarized in ``docs/phase2-filtering.md``.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import pandas as pd

from restaurant_rec.config import (
    COST_BAND_UPPER_LOW,
    COST_BAND_UPPER_MEDIUM,
    IDEAL_COST_FOR_RANKING,
    MAX_CANDIDATES_DEFAULT,
)
from restaurant_rec.phase2.bundle import BundleMetadata, CandidateBundle, CandidateItem
from restaurant_rec.phase2.preferences import PreferenceDTO


@runtime_checkable
class RestaurantDataAccess(Protocol):
    """Abstraction over parquet-backed store (Phase 1) or test fixtures."""

    def load_restaurants_df(self) -> pd.DataFrame:
        """Full canonical restaurants table."""
        ...

    def dataset_snapshot_id(self) -> str:
        """Stable id for manifest / reproducibility."""
        ...


def _row_cuisine_tokens(cell: object) -> set[str]:
    if cell is None or (isinstance(cell, float) and pd.isna(cell)):
        return set()
    # Parquet/pandas often yields numpy.ndarray for list columns
    if hasattr(cell, "tolist") and not isinstance(cell, (str, bytes)):
        try:
            items = cell.tolist()
        except (TypeError, ValueError):
            items = None
        if isinstance(items, list):
            return {str(x).casefold().strip() for x in items if str(x).strip()}
    if isinstance(cell, (list, tuple)):
        return {str(x).casefold().strip() for x in cell if str(x).strip()}
    s = str(cell).strip()
    if not s:
        return set()
    return {s.casefold()}


def _format_cost_display(cost: object) -> str:
    if cost is None or (isinstance(cost, float) and pd.isna(cost)):
        return "Unknown"
    try:
        return f"₹{int(float(cost))}"
    except (TypeError, ValueError):
        return "Unknown"


def _location_match_mask(df: pd.DataFrame, loc: str) -> pd.Series:
    """Match user area against metro, locality, or listing hub (substring, case-insensitive)."""
    if not loc:
        return pd.Series(False, index=df.index)
    columns: list[str] = []
    for col in ("city", "metro", "locality", "area"):
        if col in df.columns:
            columns.append(col)
    if not columns:
        return pd.Series(False, index=df.index)
    combined = df[columns[0]].astype(str).str.casefold()
    for col in columns[1:]:
        combined = combined + " " + df[col].astype(str).str.casefold()
    return combined.str.contains(loc, regex=False, na=False)


def _display_location(row: pd.Series) -> str:
    """Human-readable place for cards and prompts."""
    locality = str(row.get("locality", "") or "").strip()
    metro = str(row.get("metro", "") or row.get("city", "") or "").strip()
    area = str(row.get("area", "") or "").strip()
    if locality and metro and locality.casefold() != metro.casefold():
        return f"{locality}, {metro}"
    if locality:
        return locality
    if metro:
        return metro
    return area


def _apply_hard_filters(df: pd.DataFrame, pref: PreferenceDTO) -> pd.DataFrame:
    if df.empty:
        return df

    user_budget = pref.budget.value
    loc = pref.locality.casefold().strip()
    loc_mask = _location_match_mask(df, loc)

    rating_col = df["aggregate_rating"]
    rating_mask = rating_col.notna() & (rating_col.astype(float) >= pref.min_rating)

    cuisine_tokens = pref.cuisine_tokens_casefold()

    def cuisine_match(cell: object) -> bool:
        return bool(_row_cuisine_tokens(cell) & cuisine_tokens)

    cuisine_mask = df["cuisines"].apply(cuisine_match)

    budget_mask = df["budget_band"].astype(str).str.lower() == user_budget

    filtered = df.loc[loc_mask & rating_mask & cuisine_mask & budget_mask].copy()
    return filtered


def _ranking_key(row: pd.Series, user_budget: str) -> tuple[float, float, str, str]:
    """
    Deterministic pre-ranking (ascending sort):

    1. Higher ``aggregate_rating`` first (negate for ascending tuple sort).
    2. Closer ``cost_for_two`` to the ideal for the user's budget band.
    3. Stable tie-break: ``name``, ``restaurant_id``.
    """
    ideal = float(IDEAL_COST_FOR_RANKING[user_budget])
    r = row["aggregate_rating"]
    rating_f = float(r) if pd.notna(r) else -1.0
    cost = row["cost_for_two"]
    if pd.notna(cost):
        try:
            cost_penalty = abs(float(cost) - ideal)
        except (TypeError, ValueError):
            cost_penalty = 1_000_000.0
    else:
        cost_penalty = 1_000_000.0
    name = str(row.get("name", ""))
    rid = str(row.get("restaurant_id", ""))
    return (-rating_f, cost_penalty, name.casefold(), rid)


def _rows_to_candidates(df: pd.DataFrame) -> list[CandidateItem]:
    items: list[CandidateItem] = []
    for _, row in df.iterrows():
        cell = row["cuisines"]
        if isinstance(cell, (list, tuple)):
            cuisines = [str(x).strip() for x in cell if str(x).strip()]
        else:
            cuisines = [str(cell).strip()] if cell is not None and str(cell).strip() else []

        r = row["aggregate_rating"]
        rating = float(r) if pd.notna(r) else None

        items.append(
            CandidateItem(
                restaurant_id=str(row["restaurant_id"]),
                name=str(row["name"]),
                city=_display_location(row),
                cuisines=cuisines,
                rating=rating,
                estimated_cost_display=_format_cost_display(row.get("cost_for_two")),
                budget_band=str(row["budget_band"]).lower(),
            )
        )
    return items


def filter_restaurants(
    preferences: PreferenceDTO,
    store: RestaurantDataAccess | pd.DataFrame,
    *,
    max_candidates: int | None = None,
    dataset_snapshot_id: str | None = None,
) -> CandidateBundle:
    """
    Apply hard filters, pre-rank, and cap candidates for the LLM.

    Args:
        preferences: Validated user preferences.
        store: Parquet-backed accessor or an in-memory canonical ``DataFrame`` (tests).
        max_candidates: Override default cap from config.
        dataset_snapshot_id: When ``store`` is a bare ``DataFrame``, supply snapshot id;
            ignored when ``store`` implements :class:`RestaurantDataAccess`.
    """
    cap = max_candidates if max_candidates is not None else MAX_CANDIDATES_DEFAULT

    if isinstance(store, pd.DataFrame):
        df = store.copy()
        snap = dataset_snapshot_id or "dataframe-inline"
    else:
        df = store.load_restaurants_df()
        snap = store.dataset_snapshot_id()

    filtered = _apply_hard_filters(df, preferences)
    filter_count = int(len(filtered))

    if filter_count == 0:
        return CandidateBundle(
            preferences=preferences.echo_dict(),
            candidates=[],
            metadata=BundleMetadata(
                filter_count=0,
                returned_count=0,
                dataset_snapshot_id=snap,
            ),
        )

    user_budget = preferences.budget.value
    ranked = filtered.assign(
        _rk=filtered.apply(lambda row: _ranking_key(row, user_budget), axis=1),
    ).sort_values(by="_rk", kind="mergesort").drop(columns=["_rk"])

    capped = ranked.head(cap)
    candidates = _rows_to_candidates(capped)

    return CandidateBundle(
        preferences=preferences.echo_dict(),
        candidates=candidates,
        metadata=BundleMetadata(
            filter_count=filter_count,
            returned_count=len(candidates),
            dataset_snapshot_id=snap,
        ),
    )


def explain_ideal_costs_markdown() -> str:
    """Human-readable tie-break explanation (INR, aligned with Phase 1 bands)."""
    return (
        f"Ideal cost anchors for ranking (not filters): "
        f"low≈{IDEAL_COST_FOR_RANKING['low']} (≤{COST_BAND_UPPER_LOW}), "
        f"medium≈{IDEAL_COST_FOR_RANKING['medium']} (≤{COST_BAND_UPPER_MEDIUM}), "
        f"high≈{IDEAL_COST_FOR_RANKING['high']} (> {COST_BAND_UPPER_MEDIUM}). "
        "Missing cost sorts after same-rated rows with known cost."
    )
