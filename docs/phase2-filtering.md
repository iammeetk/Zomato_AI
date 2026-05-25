# Phase 2 — Preference contract and deterministic filtering

This document matches [`docs/architecture.md`](./architecture.md) § Phase 2.

## PreferenceDTO (`restaurant_rec.phase2.preferences`)

| Field | Validation |
|-------|------------|
| `location` | Non-empty string after strip. |
| `budget` | `low` \| `medium` \| `high` (see Phase 1 INR bands in `restaurant_rec.config`, shared root config). |
| `cuisine` | One or more tokens (string or list); OR semantics — restaurant matches if **any** token overlaps **any** canonical cuisine (case-insensitive). |
| `min_rating` | 0.0–5.0 inclusive. |
| `additional_preferences` | Optional free text; **echoed** in `CandidateBundle.preferences` for Phase 3 only (no row-level heuristics in Phase 2). |

## Location matching

- Case-insensitive **substring** match against any of: `metro` (e.g. Bangalore, from address), `locality` (e.g. BTM, from HF `location`), `area` (listing hub from `listed_in(city)`), and legacy `city` (= metro when known).
- Users may search a **metro** (`Bangalore`) to include all neighborhoods, or a **locality** (`BTM`, `Banashankari`) for a narrower area.

## Rating policy

- Rows with **null** `aggregate_rating` are **excluded** from results (they cannot satisfy `rating >= min_rating`).
- Rows with a numeric rating strictly below `min_rating` are excluded.

## Budget policy

- Hard filter: `budget_band` must **equal** the user’s budget (`low` / `medium` / `high`).
- Restaurants with `budget_band == unknown` are **excluded** when filtering by budget (no inferred cost).

## Pre-ranking (deterministic)

After filters, rows are sorted by:

1. **Higher** `aggregate_rating` first.
2. **Closer** `cost_for_two` to an ideal INR anchor (`IDEAL_COST_FOR_RANKING` in `restaurant_rec.config` at package root): low≈250, medium≈700, high≈2000.
3. Tie-break: `name`, then `restaurant_id` (stable `mergesort`).

Then the list is capped to `MAX_CANDIDATES_DEFAULT` (30), overridable via `filter_restaurants(..., max_candidates=…)`.

## Candidate bundle

- `metadata.dataset_snapshot_id` comes from `manifest.json` when using `ParquetRestaurantStore`, else caller-supplied / `dataframe-inline` for tests.

## API

- `filter_restaurants(preferences, store)` — `store` is `restaurant_rec.phase1.store.ParquetRestaurantStore` or an in-memory canonical `pandas.DataFrame`.
