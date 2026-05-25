"""Phase 2 golden tests — deterministic filter + rank order."""

from __future__ import annotations

import pandas as pd
import pytest
from pydantic import ValidationError

from restaurant_rec.config import MAX_CANDIDATES_DEFAULT
from restaurant_rec.phase2.bundle import CandidateBundle
from restaurant_rec.phase2.filter_engine import filter_restaurants
from restaurant_rec.phase2.preferences import PreferenceDTO, UserBudget


def _fixture_df() -> pd.DataFrame:
    """Minimal canonical schema compatible with Phase 1 parquet."""
    return pd.DataFrame(
        [
            {
                "restaurant_id": "low_a",
                "name": "Alpha Chinese",
                "city": "Bangalore",
                "metro": "Bangalore",
                "locality": "Bangalore",
                "area": "Koramangala",
                "cuisines": ["Chinese"],
                "aggregate_rating": 4.0,
                "cost_for_two": 900,
                "budget_band": "medium",
                "additional_signals_json": "{}",
            },
            {
                "restaurant_id": "mid_b",
                "name": "Bravo Italian",
                "city": "Bangalore",
                "metro": "Bangalore",
                "locality": "Indiranagar",
                "area": "Indiranagar",
                "cuisines": ["Italian"],
                "aggregate_rating": 4.5,
                "cost_for_two": 1200,
                "budget_band": "medium",
                "additional_signals_json": "{}",
            },
            {
                "restaurant_id": "mid_c",
                "name": "Charlie Fusion",
                "city": "Bangalore",
                "metro": "Bangalore",
                "locality": "BTM",
                "area": "BTM",
                "cuisines": ["Chinese", "Thai"],
                "aggregate_rating": 4.5,
                "cost_for_two": 700,
                "budget_band": "medium",
                "additional_signals_json": "{}",
            },
            {
                "restaurant_id": "wrong_budget",
                "name": "Cheap Eats",
                "city": "Bangalore",
                "metro": "Bangalore",
                "locality": "HSR",
                "area": "HSR",
                "cuisines": ["Chinese"],
                "aggregate_rating": 4.9,
                "cost_for_two": 200,
                "budget_band": "low",
                "additional_signals_json": "{}",
            },
            {
                "restaurant_id": "null_rating",
                "name": "New Place",
                "city": "Bangalore",
                "metro": "Bangalore",
                "locality": "Jayanagar",
                "area": "Jayanagar",
                "cuisines": ["Chinese"],
                "aggregate_rating": float("nan"),
                "cost_for_two": 700,
                "budget_band": "medium",
                "additional_signals_json": "{}",
            },
            {
                "restaurant_id": "delhi_match",
                "name": "Capital Spice",
                "city": "New Delhi",
                "metro": "New Delhi",
                "locality": "Connaught Place",
                "area": "Connaught Place",
                "cuisines": ["North Indian"],
                "aggregate_rating": 4.2,
                "cost_for_two": 650,
                "budget_band": "medium",
                "additional_signals_json": "{}",
            },
        ]
    )


def test_preference_validation_requires_cuisine() -> None:
    with pytest.raises(ValidationError):
        PreferenceDTO(
            location="X",
            budget=UserBudget.low,
            cuisine=[],
            min_rating=3.0,
        )


def test_filter_single_cuisine_or_branch() -> None:
    df = _fixture_df()
    pref = PreferenceDTO(
        location="Bangalore",
        budget=UserBudget.medium,
        cuisine=["Italian"],
        min_rating=3.0,
    )
    bundle = filter_restaurants(pref, df, dataset_snapshot_id="test-fixture")
    ids = [c.restaurant_id for c in bundle.candidates]
    assert ids == ["mid_b"]
    assert bundle.metadata.filter_count == 1


def test_filter_cuisine_or_semantics_multiple_tokens() -> None:
    df = _fixture_df()
    pref = PreferenceDTO(
        location="Bangalore",
        budget=UserBudget.medium,
        cuisine=["Italian", "Chinese"],
        min_rating=3.0,
    )
    bundle = filter_restaurants(pref, df, dataset_snapshot_id="test-fixture")
    ids = [c.restaurant_id for c in bundle.candidates]
    # Rank: 4.5 @700 (mid_c — closest to ideal medium ~700), 4.5 @1200 (mid_b), 4.0 @900 (low_a)
    assert ids == ["mid_c", "mid_b", "low_a"]
    assert bundle.metadata.filter_count == 3


def test_budget_band_excludes_unknown_and_wrong_tier() -> None:
    df = _fixture_df()
    pref = PreferenceDTO(
        location="Bangalore",
        budget=UserBudget.medium,
        cuisine=["Chinese"],
        min_rating=3.0,
    )
    bundle = filter_restaurants(pref, df, dataset_snapshot_id="test-fixture")
    ids = {c.restaurant_id for c in bundle.candidates}
    assert "wrong_budget" not in ids
    assert "null_rating" not in ids


def test_location_substring_delhi() -> None:
    df = _fixture_df()
    pref = PreferenceDTO(
        location="Delhi",
        budget=UserBudget.medium,
        cuisine=["North Indian"],
        min_rating=4.0,
    )
    bundle = filter_restaurants(pref, df, dataset_snapshot_id="test-fixture")
    assert [c.restaurant_id for c in bundle.candidates] == ["delhi_match"]


def test_zero_matches_empty_bundle() -> None:
    df = _fixture_df()
    pref = PreferenceDTO(
        location="Chennai",
        budget=UserBudget.high,
        cuisine=["Seafood"],
        min_rating=4.5,
    )
    bundle = filter_restaurants(pref, df, dataset_snapshot_id="test-fixture")
    assert bundle.candidates == []
    assert bundle.metadata.filter_count == 0
    assert bundle.metadata.returned_count == 0
    assert isinstance(bundle, CandidateBundle)


def test_max_candidates_cap() -> None:
    df = pd.concat([_fixture_df()] * 5, ignore_index=True)
    df["restaurant_id"] = [f"r{i}" for i in range(len(df))]
    pref = PreferenceDTO(
        location="Bangalore",
        budget=UserBudget.medium,
        cuisine=["Chinese"],
        min_rating=3.0,
    )
    bundle = filter_restaurants(pref, df, max_candidates=2, dataset_snapshot_id="x")
    assert len(bundle.candidates) == 2
    assert bundle.metadata.filter_count >= 2


def test_default_cap_matches_config() -> None:
    assert MAX_CANDIDATES_DEFAULT == 30


def test_filter_cuisine_numpy_array_column() -> None:
    """Parquet loads list columns as numpy.ndarray — must still match tokens."""
    import numpy as np

    df = pd.DataFrame(
        [
            {
                "restaurant_id": "np_row",
                "name": "Array Cafe",
                "city": "Bangalore",
                "metro": "Bangalore",
                "locality": "Banashankari",
                "area": "Banashankari",
                "cuisines": np.array(["Chinese", "Thai"]),
                "aggregate_rating": 4.2,
                "cost_for_two": 700,
                "budget_band": "medium",
                "additional_signals_json": "{}",
            },
        ],
    )
    pref = PreferenceDTO(
        location="Banashankari",
        budget=UserBudget.medium,
        cuisine=["Chinese"],
        min_rating=4.0,
    )
    bundle = filter_restaurants(pref, df, dataset_snapshot_id="test-fixture")
    assert bundle.metadata.filter_count == 1
    assert bundle.candidates[0].restaurant_id == "np_row"


def test_filter_metro_bangalore_matches_neighborhoods() -> None:
    """Searching 'Bangalore' should include rows in BTM, HSR, etc."""
    df = _fixture_df()
    pref = PreferenceDTO(
        location="Bangalore",
        budget=UserBudget.medium,
        cuisine=["Chinese"],
        min_rating=3.0,
    )
    bundle = filter_restaurants(pref, df, dataset_snapshot_id="test-fixture")
    ids = {c.restaurant_id for c in bundle.candidates}
    assert "mid_c" in ids
    assert "low_a" in ids
    assert bundle.metadata.filter_count >= 2
