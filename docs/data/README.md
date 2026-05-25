# Data layer — Phase 1

This folder documents how the Hugging Face **ManikaSaini/zomato-restaurant-recommendation** dataset maps into the canonical parquet written by `restaurant_rec.phase1.ingest`.

## Output artifacts

| Path | Description |
|------|--------------|
| `data/processed/restaurants.parquet` | Canonical restaurants table (generated; not committed). |
| `data/processed/manifest.json` | Row counts, optional HF revision, null-rate summary, timestamps. |

Generate them:

```bash
python -m restaurant_rec ingest
```

## Hugging Face → canonical column mapping

| HF column | Canonical field | Notes |
|-----------|-------------------|--------|
| *(derived)* | `restaurant_id` | SHA-256 hex (first 16 chars) of `name|city|address|url`. |
| `name` | `name` | Whitespace-normalized; missing → `"Unknown"`. |
| `address` | `metro` | Metro parsed from address (e.g. Bangalore, New Delhi). |
| `location` | `locality` | Neighborhood (BTM, Banashankari, HSR, …). |
| `listed_in(city)` | `area` | Listing hub / block name. |
| *(derived)* | `city` | `metro` if set, else `locality` (backward compatible). |
| `cuisines` | `cuisines` | Split on comma/pipe/slash; trimmed; deduplicated case-insensitively. |
| `rate` | `aggregate_rating` | Leading float parsed (e.g. `4.2/5` → `4.2`). `NEW`, `-`, empty → null. |
| `approx_cost(for two people)` | `cost_for_two` | Digits extracted as INR integer; unparseable → null. |
| *(derived)* | `budget_band` | From `cost_for_two`: ≤400 `low`, ≤1000 `medium`, else `high`; null cost → `unknown`. |
| *(derived)* | `additional_signals_json` | JSON object with grounded extras only (see below). |

### `additional_signals_json` contents

Subset of source columns, only when non-empty:

| Key | Source |
|-----|--------|
| `online_order` | `online_order` |
| `book_table` | `book_table` |
| `rest_type` | `rest_type` |
| `dish_liked` | `dish_liked` |
| `votes` | `votes` |
| `listed_in_type` | `listed_in(type)` |
| `menu_item_excerpt` | First 500 chars of `menu_item` |
| `reviews_excerpt` | First 400 chars of `reviews_list` |

HF columns loaded but **not** duplicated as top-level canonical columns (kept only inside signals or ID hash): `url`, `address`, `phone`, full `reviews_list`, full `menu_item`.

## Null / quality policy

- **Rows:** No rows are dropped during ingest; downstream filters (Phase 2) handle empty cities or missing ratings.
- **`aggregate_rating`:** Null when the dataset rate is not a numeric aggregate.
- **`cost_for_two`:** Null when cost text has no digits → `budget_band` = `unknown`.
- **Idempotency:** Re-running ingest overwrites the same parquet and manifest paths.

## Schema version

`restaurant_rec.phase1.canonical.SCHEMA_VERSION` and `manifest.json` → `schema_version` track breaking layout changes (currently `"1"`).

## Sample query (pandas)

After ingest:

```python
from restaurant_rec.phase1.store import load_restaurants

df = load_restaurants()
bangalore = df[df["city"].str.contains("Bangalore", case=False, na=False)]
rated = bangalore[bangalore["aggregate_rating"].fillna(0) >= 4.0]
```

See `tests/test_store_query.py` for an automated variant using a temp parquet file.

Filtering and preference validation are documented in [`docs/phase2-filtering.md`](../phase2-filtering.md).
