"""Prove filters can run against the canonical store (architecture Phase 1 verification)."""

from __future__ import annotations

import json

import pandas as pd

from restaurant_rec.phase1.canonical import SCHEMA_VERSION
from restaurant_rec.phase1.store import get_schema_version, load_restaurants


def test_get_schema_version() -> None:
    assert get_schema_version() == SCHEMA_VERSION


def test_load_restaurants_sample_query(tmp_path) -> None:
    rows = [
        {
            "restaurant_id": "a",
            "name": "North Hub",
            "city": "Bangalore",
            "cuisines": ["Chinese", "North Indian"],
            "aggregate_rating": 4.2,
            "cost_for_two": 800,
            "budget_band": "medium",
            "additional_signals_json": json.dumps({}),
        },
        {
            "restaurant_id": "b",
            "name": "Delhi Diner",
            "city": "New Delhi",
            "cuisines": ["Mughlai"],
            "aggregate_rating": 3.8,
            "cost_for_two": 1200,
            "budget_band": "high",
            "additional_signals_json": json.dumps({}),
        },
    ]
    path = tmp_path / "restaurants.parquet"
    pd.DataFrame(rows).to_parquet(path, index=False)

    df = load_restaurants(path)
    bangalore = df[df["city"].str.contains("Bangalore", case=False, na=False)]
    assert len(bangalore) == 1
    rated = bangalore[bangalore["aggregate_rating"] >= 4.0]
    assert len(rated) == 1
    assert rated.iloc[0]["name"] == "North Hub"
