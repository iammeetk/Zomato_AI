"""Map Hugging Face Zomato rows to the canonical parquet schema."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from restaurant_rec.config import COST_BAND_UPPER_LOW, COST_BAND_UPPER_MEDIUM
from restaurant_rec.phase1.canonical import BudgetBand

LISTED_CITY_KEY = "listed_in(city)"
APPROX_COST_KEY = "approx_cost(for two people)"

_WS_RE = re.compile(r"\s+")

# Substrings in ``address`` → canonical metro label (order: longer phrases first).
_METRO_FROM_ADDRESS: tuple[tuple[str, str], ...] = (
    ("new delhi", "New Delhi"),
    ("bengaluru", "Bangalore"),
    ("bangalore", "Bangalore"),
    ("mumbai", "Mumbai"),
    ("gurgaon", "Gurgaon"),
    ("gurugram", "Gurgaon"),
    ("noida", "Noida"),
    ("hyderabad", "Hyderabad"),
    ("chennai", "Chennai"),
    ("kolkata", "Kolkata"),
    ("pune", "Pune"),
    ("delhi", "Delhi"),
)


def normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    return _WS_RE.sub(" ", s)


def normalize_city(value: str | None) -> str:
    """Stable display casing for city matching (Phase 2)."""
    s = normalize_text(value)
    if not s:
        return ""
    return s.title()


def resolve_metro(row: dict[str, Any]) -> str:
    """Metro area (e.g. Bangalore) parsed from address when present."""
    addr = normalize_text(str(row.get("address") or ""))
    if not addr:
        return ""
    folded = addr.casefold()
    for needle, label in _METRO_FROM_ADDRESS:
        if needle in folded:
            return label
    return ""


def resolve_locality(row: dict[str, Any]) -> str:
    """Neighborhood / area from HF ``location`` (e.g. BTM, Banashankari)."""
    loc = row.get("location")
    if loc is None:
        return ""
    return normalize_city(str(loc).strip())


def resolve_area(row: dict[str, Any]) -> str:
    """Listing hub from ``listed_in(city)`` (e.g. Koramangala 5th Block)."""
    listed = row.get(LISTED_CITY_KEY)
    if listed is None:
        return ""
    return normalize_city(str(listed).strip())


def resolve_city(row: dict[str, Any]) -> str:
    """Backward-compatible alias: metro when known, else locality."""
    metro = resolve_metro(row)
    if metro:
        return metro
    return resolve_locality(row)


def stable_restaurant_id(name: str, city: str, address: str, url: str) -> str:
    payload = f"{name}|{city}|{address}|{url}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def parse_aggregate_rating(raw: object) -> float | None:
    """
    Dataset `rate` is a string (e.g. '4.1/5', 'NEW', '-').
    Policy: unparseable values → null (do not invent ratings).
    """
    if raw is None:
        return None
    if isinstance(raw, float):
        return float(raw) if raw == raw else None  # NaN check
    s = str(raw).strip()
    if not s:
        return None
    upper = s.upper()
    if upper in {"NEW", "-", "NAN", "NONE"}:
        return None
    m = re.match(r"^\s*(\d+(?:\.\d+)?)", s)
    if not m:
        return None
    val = float(m.group(1))
    if val < 0 or val > 5:
        return None
    return val


def parse_cost_for_two(raw: object) -> int | None:
    """Parse `approx_cost(for two people)` numeric INR amount."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        if isinstance(raw, float) and raw != raw:
            return None
        return int(raw)
    s = str(raw).strip()
    if not s:
        return None
    digits = re.sub(r"[^\d]", "", s)
    if not digits:
        return None
    return int(digits)


def cost_to_budget_band(cost: int | None) -> BudgetBand:
    if cost is None:
        return BudgetBand.unknown
    if cost <= COST_BAND_UPPER_LOW:
        return BudgetBand.low
    if cost <= COST_BAND_UPPER_MEDIUM:
        return BudgetBand.medium
    return BudgetBand.high


def parse_cuisines(raw: object) -> list[str]:
    if raw is None:
        return []
    s = normalize_text(str(raw))
    if not s:
        return []
    parts = [normalize_text(p) for p in re.split(r"[,|/]", s)]
    out: list[str] = []
    seen: set[str] = set()
    for p in parts:
        if not p:
            continue
        key = p.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def build_additional_signals(row: dict[str, Any]) -> dict[str, Any]:
    signals: dict[str, Any] = {}
    for key in ("online_order", "book_table", "rest_type", "dish_liked"):
        val = row.get(key)
        t = normalize_text(str(val)) if val is not None else ""
        if t:
            signals[key] = t
    votes = row.get("votes")
    if votes is not None:
        try:
            signals["votes"] = int(votes)
        except (TypeError, ValueError):
            pass
    lt = row.get("listed_in(type)")
    t = normalize_text(str(lt)) if lt is not None else ""
    if t:
        signals["listed_in_type"] = t
    menu = row.get("menu_item")
    if menu is not None and normalize_text(str(menu)):
        excerpt = normalize_text(str(menu))
        signals["menu_item_excerpt"] = excerpt[:500]
    rev = row.get("reviews_list")
    if rev is not None and normalize_text(str(rev)):
        excerpt = normalize_text(str(rev))
        signals["reviews_excerpt"] = excerpt[:400]
    return signals


def transform_row(row: dict[str, Any]) -> dict[str, Any]:
    """Single HF row dict → canonical flat dict (JSON-serializable values)."""
    metro = resolve_metro(row)
    locality = resolve_locality(row)
    area = resolve_area(row)
    city = metro or locality or area
    name = normalize_text(str(row.get("name"))) if row.get("name") is not None else ""
    if not name:
        name = "Unknown"
    address = normalize_text(str(row.get("address"))) if row.get("address") is not None else ""
    url = normalize_text(str(row.get("url"))) if row.get("url") is not None else ""
    cuisines = parse_cuisines(row.get("cuisines"))
    rating = parse_aggregate_rating(row.get("rate"))
    cost = parse_cost_for_two(row.get(APPROX_COST_KEY))
    band = cost_to_budget_band(cost)
    rid = stable_restaurant_id(name, f"{locality}|{city}", address, url)
    signals = build_additional_signals(row)
    return {
        "restaurant_id": rid,
        "name": name,
        "city": city,
        "metro": metro,
        "locality": locality,
        "area": area,
        "cuisines": cuisines,
        "aggregate_rating": rating,
        "cost_for_two": cost,
        "budget_band": band.value,
        "additional_signals_json": json.dumps(signals, ensure_ascii=False),
    }
