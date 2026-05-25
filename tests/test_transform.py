"""Unit tests for HF → canonical transforms."""

import json

import pytest

from restaurant_rec.phase1.canonical import BudgetBand
from restaurant_rec.phase1.transform import (
    APPROX_COST_KEY,
    LISTED_CITY_KEY,
    cost_to_budget_band,
    parse_aggregate_rating,
    parse_cost_for_two,
    parse_cuisines,
    transform_row,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("4.2/5", 4.2),
        ("3", 3.0),
        ("NEW", None),
        ("-", None),
        ("", None),
        (None, None),
    ],
)
def test_parse_aggregate_rating(raw: object, expected: float | None) -> None:
    assert parse_aggregate_rating(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("800", 800),
        ("Rs.1,200", 1200),
        ("", None),
        (None, None),
    ],
)
def test_parse_cost_for_two(raw: object, expected: int | None) -> None:
    assert parse_cost_for_two(raw) == expected


def test_cost_to_budget_band() -> None:
    assert cost_to_budget_band(300) == BudgetBand.low
    assert cost_to_budget_band(400) == BudgetBand.low
    assert cost_to_budget_band(401) == BudgetBand.medium
    assert cost_to_budget_band(1000) == BudgetBand.medium
    assert cost_to_budget_band(1001) == BudgetBand.high
    assert cost_to_budget_band(None) == BudgetBand.unknown


def test_parse_cuisines_splits_and_dedupes() -> None:
    assert parse_cuisines("Chinese, North Indian") == ["Chinese", "North Indian"]
    assert parse_cuisines("Chinese | chinese") == ["Chinese"]


def test_transform_row_schema_keys() -> None:
    row = {
        "url": "https://example.com/r1",
        "address": "1 MG Road",
        "name": " Test Café ",
        "online_order": "Yes",
        "book_table": "No",
        "rate": "4.5/5",
        "votes": 42,
        "phone": "12345",
        "location": "Bangalore",
        "rest_type": "Casual Dining",
        "dish_liked": "Pasta",
        "cuisines": "Italian, Cafe",
        APPROX_COST_KEY: "600",
        "reviews_list": "",
        "menu_item": "",
        "listed_in(type)": "Delivery",
        LISTED_CITY_KEY: "Bangalore",
    }
    out = transform_row(row)
    expected_keys = {
        "restaurant_id",
        "name",
        "city",
        "metro",
        "locality",
        "area",
        "cuisines",
        "aggregate_rating",
        "cost_for_two",
        "budget_band",
        "additional_signals_json",
    }
    assert set(out.keys()) == expected_keys
    assert out["name"] == "Test Café"
    assert out["locality"] == "Bangalore"
    assert out["area"] == "Bangalore"
    assert out["aggregate_rating"] == 4.5
    assert out["cost_for_two"] == 600
    assert out["budget_band"] == "medium"
    signals = json.loads(out["additional_signals_json"])
    assert signals["votes"] == 42
    assert signals["online_order"] == "Yes"
