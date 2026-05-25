# Zomato AI — Next.js frontend

Next.js UI aligned with the Zomato AI mockup. Talks to the FastAPI backend (Phase 4).

## Prerequisites

- Node.js 18+
- Backend running: `python -m restaurant_rec serve` (port 8000)

## Setup & run (recommended)

From the repo root (installs portable Node on first run if needed):

```powershell
# Terminal 1 — API
python -m restaurant_rec serve

# Terminal 2 — Next.js UI
powershell -ExecutionPolicy Bypass -File .\scripts\start-next-frontend.ps1
```

Open **http://localhost:3000**

## Manual setup (if Node.js is already installed)

```powershell
cd frontend-next
copy .env.local.example .env.local
npm install
npm run dev
```

## Environment

| Variable | Default |
|----------|---------|
| `NEXT_PUBLIC_API_URL` | `http://127.0.0.1:8000` |

## Notes

- **Locality** must match a substring of cities in your dataset (e.g. `Banashankari` for the sample parquet).
- **Budget** maps max ₹ for two → `low` / `medium` / `high` (≤400 / ≤1000 / >1000).
- Run full ingest for more cities: `python -m restaurant_rec ingest`
