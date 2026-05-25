"""Load HF dataset, transform to canonical schema, write parquet + manifest."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from datasets import load_dataset

from restaurant_rec.config import (
    DATASET_NAME,
    DEFAULT_MANIFEST_NAME,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PARQUET_NAME,
    HF_COLUMNS,
)
from restaurant_rec.phase1.canonical import SCHEMA_VERSION
from restaurant_rec.phase1.transform import transform_row


def compute_null_rates(df: pd.DataFrame) -> dict[str, float]:
    n = len(df)
    if n == 0:
        return {}
    rates: dict[str, float] = {}
    for col in df.columns:
        nulls = df[col].isna().sum()
        rates[col] = float(nulls) / float(n)
    return rates


def run_ingest(
    *,
    revision: str | None = None,
    output_dir: Path | None = None,
    parquet_name: str = DEFAULT_PARQUET_NAME,
    manifest_name: str = DEFAULT_MANIFEST_NAME,
    limit_rows: int | None = None,
) -> dict[str, Any]:
    """
    Full ingestion pipeline. Idempotent: overwrites parquet and manifest.

    Args:
        revision: Optional Hugging Face git revision for reproducibility.
        output_dir: Defaults to ``data/processed`` under project root.
        limit_rows: If set, only process the first N rows (tests / debugging).
    """
    out_dir = output_dir or DEFAULT_OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = out_dir / parquet_name
    manifest_path = out_dir / manifest_name

    ds = load_dataset(
        DATASET_NAME,
        split="train",
        revision=revision,
    )
    if limit_rows is not None:
        ds = ds.select(range(min(limit_rows, len(ds))))

    raw_df = ds.to_pandas()
    missing = [c for c in HF_COLUMNS if c not in raw_df.columns]
    if missing:
        raise ValueError(
            f"Dataset {DATASET_NAME!r} missing expected columns: {missing}. "
            f"Found: {list(raw_df.columns)}",
        )
    raw_records = raw_df[HF_COLUMNS].to_dict("records")
    rows = [transform_row(r) for r in raw_records]
    df = pd.DataFrame(rows)
    df.to_parquet(parquet_path, index=False)

    null_rates = compute_null_rates(df)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "hf_dataset": DATASET_NAME,
        "hf_revision": revision,
        "row_count": int(len(df)),
        "parquet_path": str(parquet_path.resolve()),
        "manifest_path": str(manifest_path.resolve()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "null_rates": null_rates,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return {
        "parquet_path": parquet_path,
        "manifest_path": manifest_path,
        "manifest": manifest,
        "dataframe": df,
    }


def print_ingest_report(result: dict[str, Any]) -> None:
    m = result["manifest"]
    print(f"Wrote parquet: {result['parquet_path']}")
    print(f"Wrote manifest: {result['manifest_path']}")
    print(f"Rows: {m['row_count']}  schema_version={m['schema_version']}  revision={m['hf_revision']!r}")
    print("Null rates (sample):")
    nr = m["null_rates"]
    for key in ("aggregate_rating", "cost_for_two", "city"):
        if key in nr:
            print(f"  {key}: {nr[key]:.4f}")
