"""Read-only access to processed canonical restaurant table."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from restaurant_rec.config import (
    DEFAULT_MANIFEST_NAME,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PARQUET_NAME,
)
from restaurant_rec.phase1.canonical import SCHEMA_VERSION


def default_parquet_path() -> Path:
    return DEFAULT_OUTPUT_DIR / DEFAULT_PARQUET_NAME


def default_manifest_path() -> Path:
    return default_parquet_path().parent / DEFAULT_MANIFEST_NAME


def read_dataset_snapshot_id(manifest_path: Path | None = None) -> str:
    """
    Build a compact snapshot id from ``manifest.json`` (HF revision + ingest time).

    Falls back when the manifest is missing (e.g. ad-hoc parquet).
    """
    path = manifest_path if manifest_path is not None else default_manifest_path()
    if not path.is_file():
        return f"schema-{SCHEMA_VERSION}-no-manifest"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return f"schema-{SCHEMA_VERSION}-invalid-manifest"
    rev = data.get("hf_revision")
    gen = data.get("generated_at", "")
    sv = data.get("schema_version", SCHEMA_VERSION)
    if rev:
        return f"hf:{rev};schema={sv};ingested={gen}"
    return f"schema={sv};ingested={gen}"


class ParquetRestaurantStore:
    """Parquet-backed canonical store (Phase 1 output); implements Phase 2 data access."""

    def __init__(self, parquet_path: Path | str | None = None) -> None:
        self._parquet_path = Path(parquet_path) if parquet_path is not None else default_parquet_path()

    def load_restaurants_df(self) -> pd.DataFrame:
        return load_restaurants(self._parquet_path)

    def dataset_snapshot_id(self) -> str:
        return read_dataset_snapshot_id(self._parquet_path.parent / DEFAULT_MANIFEST_NAME)


def load_restaurants(parquet_path: Path | str | None = None) -> pd.DataFrame:
    """
    Load the canonical restaurants table written by :func:`restaurant_rec.phase1.ingest.run_ingest`.

    Raises:
        FileNotFoundError: If the parquet file does not exist.
    """
    path = Path(parquet_path) if parquet_path is not None else default_parquet_path()
    if not path.is_file():
        raise FileNotFoundError(
            f"No parquet at {path}. Run: python -m restaurant_rec ingest",
        )
    return pd.read_parquet(path)


def get_schema_version() -> str:
    """Semantic version string for the canonical parquet column layout."""
    return SCHEMA_VERSION


def parse_additional_signals(row: pd.Series) -> dict[str, Any]:
    """Decode ``additional_signals_json`` from a dataframe row."""
    raw = row.get("additional_signals_json")
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(str(raw))
    except json.JSONDecodeError:
        return {}


def get_metros(store_df: pd.DataFrame) -> list[str]:
    """Sorted unique metro areas (e.g. Bangalore)."""
    col = "metro" if "metro" in store_df.columns else "city"
    if col not in store_df.columns:
        return []
    values = store_df[col].dropna().unique()
    return sorted(str(v).strip() for v in values if str(v).strip())


def get_localities(store_df: pd.DataFrame) -> list[str]:
    """Sorted unique neighborhoods / listing areas for autocomplete."""
    parts: list[str] = []
    for col in ("locality", "area"):
        if col not in store_df.columns:
            continue
        for v in store_df[col].dropna().unique():
            s = str(v).strip()
            if s:
                parts.append(s)
    if not parts and "city" in store_df.columns:
        for v in store_df["city"].dropna().unique():
            s = str(v).strip()
            if s:
                parts.append(s)
    return sorted(set(parts))


def get_search_areas(store_df: pd.DataFrame) -> dict[str, list[str]]:
    """Metros and localities for UI dropdowns."""
    metros = get_metros(store_df)
    localities = get_localities(store_df)
    return {"metros": metros, "localities": localities}
