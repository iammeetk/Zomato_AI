# Restaurant recommendation (M1)

Phase 1 loads the [Zomato restaurant dataset](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation) from Hugging Face, normalizes it into a canonical schema, and writes `data/processed/restaurants.parquet`.

Phase 2 applies **validated preferences** and deterministic filters, producing a **candidate bundle** for the LLM ([`docs/phase2-filtering.md`](docs/phase2-filtering.md)).

## Package layout (`src/restaurant_rec`)

| Path | Phase |
|------|--------|
| `config.py` | Shared settings (paths, dataset id, band thresholds, caps). |
| `cli.py`, `__main__.py` | Cross-phase CLI entrypoints. |
| `phase1/` | Ingestion, canonical schema, transforms, Parquet store. |
| `phase2/` | Preferences, candidate bundle models, deterministic filter engine. |
| `phase3/` | Groq chat completion, prompt templates, parse/sanitize, `recommend()`. |
| `phase4/` | FastAPI service: filter → Groq → store join (`service.py`, `api.py`). |

Most symbols are still re-exported from `restaurant_rec` for convenience.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Optional: copy `.env.example` to `.env` and set `HF_TOKEN` if needed.

## Ingest

```powershell
python -m restaurant_rec ingest
python -m restaurant_rec ingest --revision 5738e9eda2fad49ad51c6e0ed26e761d9b947133
```

Use **full ingest** (no `--limit-rows`) so you get all ~51k restaurants. A tiny parquet (e.g. 2 rows) only supports one locality. After ingest, search **Bangalore** for the whole city or **BTM** / **Banashankari** for a neighborhood.

Column mapping and schema: [`docs/data/README.md`](docs/data/README.md).

## Candidate filtering (Phase 2)

After ingest:

```powershell
python -m restaurant_rec candidates --location Bangalore --budget medium --cuisine Chinese --min-rating 4
python -m restaurant_rec candidates -l "New Delhi" -b low -c North Indian -c Mughlai --notes "family-friendly"
```

## Groq recommendations (Phase 3)

1. Add `GROQ_API_KEY` to `.env` (see [`.env.example`](.env.example)).
2. Run end-to-end (Phase 2 → Groq → joined results):

```powershell
python -m restaurant_rec recommend -l Bangalore -b medium -c Chinese --min-rating 4 --top-k 5
```

If the key is missing or Groq errors, the CLI still returns **`used_llm: false`** and **template explanations** from Phase 2 ordering.

## HTTP API (Phase 4)

After ingest, start the server:

```powershell
python -m restaurant_rec serve
```

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Service and dataset status |
| `GET /v1/localities` | Cities available in the store |
| `POST /v1/recommend` | Preference JSON → ranked recommendations |

Example:

```powershell
curl -X POST http://127.0.0.1:8000/v1/recommend -H "Content-Type: application/json" -d "{\"location\":\"Bangalore\",\"budget\":\"medium\",\"cuisine\":[\"Chinese\"],\"min_rating\":4}"
```

OpenAPI UI: `http://127.0.0.1:8000/docs`. Architecture: [`docs/phase-wise-architecture.md`](docs/phase-wise-architecture.md).

## Web UI (Phase 5)

### Next.js (recommended for enhancement)

```powershell
# Terminal 1 — API
python -m restaurant_rec ingest
python -m restaurant_rec serve

# Terminal 2 — UI (Zomato AI-style Next.js)
powershell -ExecutionPolicy Bypass -File .\scripts\start-next-frontend.ps1
```

Open **http://localhost:3000** (API at `http://127.0.0.1:8000`). The script installs portable Node + npm on first run. See [`frontend-next/README.md`](frontend-next/README.md).

### Legacy static UI

The API also serves `frontend/` at **http://127.0.0.1:8000/** when using `serve` alone.

## Tests

```powershell
pytest
```

Integration test (downloads data): `pytest -m integration`.
