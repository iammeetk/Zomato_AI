"""Optional integration test against Hugging Face (network)."""

from __future__ import annotations

import pytest

from restaurant_rec.phase1.ingest import run_ingest


@pytest.mark.integration
def test_ingest_hf_subset(tmp_path) -> None:
    result = run_ingest(
        revision="5738e9eda2fad49ad51c6e0ed26e761d9b947133",
        output_dir=tmp_path,
        limit_rows=25,
    )
    df = result["dataframe"]
    assert len(df) == 25
    assert set(df.columns) == {
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
    assert result["manifest_path"].is_file()
    assert result["parquet_path"].is_file()
