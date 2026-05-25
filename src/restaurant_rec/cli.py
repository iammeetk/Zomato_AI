"""CLI entrypoints."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from restaurant_rec.phase1.ingest import print_ingest_report, run_ingest
from restaurant_rec.phase1.store import ParquetRestaurantStore
from restaurant_rec.phase2.filter_engine import filter_restaurants
from restaurant_rec.phase2.preferences import PreferenceDTO, UserBudget
from restaurant_rec.phase3.recommend import recommend

app = typer.Typer(no_args_is_help=True)


@app.callback()
def _cli_root() -> None:
    """Restaurant recommendation CLI (Phases 1–3)."""
    return


@app.command("ingest")
def ingest_cmd(
    revision: Optional[str] = typer.Option(
        None,
        "--revision",
        help="Hugging Face git revision (commit SHA) for reproducible snapshots.",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        help="Directory for restaurants.parquet and manifest.json (default: data/processed).",
    ),
    limit_rows: Optional[int] = typer.Option(
        None,
        "--limit-rows",
        help="Process only the first N rows (debugging).",
    ),
) -> None:
    """Download the Zomato HF dataset, normalize it, and write parquet + manifest."""
    result = run_ingest(
        revision=revision,
        output_dir=output_dir,
        limit_rows=limit_rows,
    )
    print_ingest_report(result)


@app.command("candidates")
def candidates_cmd(
    location: str = typer.Option(..., "--location", "-l", help="City substring, case-insensitive."),
    budget: UserBudget = typer.Option(..., "--budget", "-b", case_sensitive=False),
    cuisine: list[str] = typer.Option(
        ...,
        "--cuisine",
        "-c",
        help="Cuisine token (repeat flag for OR semantics).",
    ),
    min_rating: float = typer.Option(
        3.0,
        "--min-rating",
        help="Minimum aggregate rating (null ratings excluded).",
    ),
    additional_preferences: Optional[str] = typer.Option(
        None,
        "--notes",
        help="Free-text preferences (passed through to Phase 3 only).",
    ),
    max_candidates: Optional[int] = typer.Option(
        None,
        "--max",
        help="Override default cap on candidates returned.",
    ),
    parquet_path: Optional[Path] = typer.Option(
        None,
        "--parquet",
        help="Optional path to restaurants.parquet (default: data/processed).",
    ),
) -> None:
    """Run deterministic filters and print CandidateBundle JSON (Phase 2)."""
    pref = PreferenceDTO(
        location=location,
        budget=budget,
        cuisine=cuisine,
        min_rating=min_rating,
        additional_preferences=additional_preferences,
    )
    store = ParquetRestaurantStore(parquet_path)
    bundle = filter_restaurants(pref, store, max_candidates=max_candidates)
    typer.echo(bundle.model_dump_json(indent=2))


@app.command("recommend")
def recommend_cmd(
    location: str = typer.Option(..., "--location", "-l", help="City substring, case-insensitive."),
    budget: UserBudget = typer.Option(..., "--budget", "-b", case_sensitive=False),
    cuisine: list[str] = typer.Option(
        ...,
        "--cuisine",
        "-c",
        help="Cuisine token (repeat for OR semantics).",
    ),
    min_rating: float = typer.Option(
        3.0,
        "--min-rating",
        help="Minimum aggregate rating (null ratings excluded).",
    ),
    additional_preferences: Optional[str] = typer.Option(
        None,
        "--notes",
        help="Free-text preferences for the model.",
    ),
    max_candidates: Optional[int] = typer.Option(
        None,
        "--max",
        help="Phase 2 cap on candidates passed to the LLM.",
    ),
    top_k: Optional[int] = typer.Option(
        None,
        "--top-k",
        help="Max recommendations returned (default: RECOMMENDATION_TOP_K or 5).",
    ),
    parquet_path: Optional[Path] = typer.Option(
        None,
        "--parquet",
        help="Optional path to restaurants.parquet (default: data/processed).",
    ),
) -> None:
    """Run Phase 2 filter + Phase 3 Groq ranking; print RecommendationResult JSON."""
    pref = PreferenceDTO(
        location=location,
        budget=budget,
        cuisine=cuisine,
        min_rating=min_rating,
        additional_preferences=additional_preferences,
    )
    store = ParquetRestaurantStore(parquet_path)
    bundle = filter_restaurants(pref, store, max_candidates=max_candidates)
    result = recommend(bundle, pref, top_k=top_k)
    typer.echo(result.model_dump_json(indent=2))


@app.command("serve")
def serve_cmd(
    host: str = typer.Option("0.0.0.0", "--host", help="Bind address."),
    port: int = typer.Option(8000, "--port", "-p", help="HTTP port."),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload (dev)."),
) -> None:
    """Run Phase 4 FastAPI server (requires ingested parquet)."""
    import uvicorn

    uvicorn.run(
        "restaurant_rec.phase4.api:app",
        host=host,
        port=port,
        reload=reload,
    )


def main() -> None:
    app()


if __name__ == "__main__":
    main()
