"""Phase 1 — Hugging Face ingestion, canonical schema, Parquet store."""

from restaurant_rec.phase1.canonical import SCHEMA_VERSION, BudgetBand
from restaurant_rec.phase1.ingest import print_ingest_report, run_ingest
from restaurant_rec.phase1.store import (
    ParquetRestaurantStore,
    default_manifest_path,
    default_parquet_path,
    get_schema_version,
    load_restaurants,
    parse_additional_signals,
    read_dataset_snapshot_id,
)

__all__ = [
    "SCHEMA_VERSION",
    "BudgetBand",
    "run_ingest",
    "print_ingest_report",
    "ParquetRestaurantStore",
    "load_restaurants",
    "get_schema_version",
    "parse_additional_signals",
    "read_dataset_snapshot_id",
    "default_parquet_path",
    "default_manifest_path",
]
