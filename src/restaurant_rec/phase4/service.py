"""Phase 4 — orchestrate filter → LLM → authoritative store join."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
import pandas as pd

from restaurant_rec.config import PROMPT_VERSION
from restaurant_rec.phase1.store import (
    ParquetRestaurantStore,
    get_schema_version,
    get_search_areas,
)
from restaurant_rec.phase2.filter_engine import RestaurantDataAccess, filter_restaurants
from restaurant_rec.phase2.preferences import PreferenceDTO
from restaurant_rec.phase3.models import RecommendationItem, RecommendationResult
from restaurant_rec.phase3.recommend import recommend
from restaurant_rec.phase3.settings import GroqSettings
from restaurant_rec.phase4.schemas import HealthCheckResponse, RecommendResponse

logger = logging.getLogger(__name__)

LlmComplete = Callable[[str, str], str]


class _DataFrameStore:
    """In-memory store for tests."""

    def __init__(self, df: pd.DataFrame, snapshot_id: str = "test-fixture") -> None:
        self._df = df
        self._snapshot_id = snapshot_id

    def load_restaurants_df(self) -> pd.DataFrame:
        return self._df

    def dataset_snapshot_id(self) -> str:
        return self._snapshot_id


def _format_cost_display(cost: object) -> str:
    if cost is None or (isinstance(cost, float) and pd.isna(cost)):
        return "Unknown"
    try:
        return f"₹{int(float(cost))}"
    except (TypeError, ValueError):
        return "Unknown"


def _cuisine_display(cell: object) -> str:
    if cell is None or (isinstance(cell, float) and pd.isna(cell)):
        return ""
    if isinstance(cell, (list, tuple)):
        return ", ".join(str(x).strip() for x in cell if str(x).strip())
    return str(cell).strip()


def join_store_fields(
    result: RecommendationResult,
    store_df: pd.DataFrame,
) -> RecommendationResult:
    """Overwrite display fields from the canonical store (Phase 4 step 6)."""
    if not result.items or store_df.empty:
        return result

    indexed = store_df.set_index("restaurant_id", drop=False)
    joined: list[RecommendationItem] = []
    for item in result.items:
        if item.restaurant_id not in indexed.index:
            joined.append(item)
            continue
        row = indexed.loc[item.restaurant_id]
        if isinstance(row, pd.DataFrame):
            row = row.iloc[0]
        rating_raw = row.get("aggregate_rating")
        rating = float(rating_raw) if rating_raw is not None and not pd.isna(rating_raw) else None
        joined.append(
            item.model_copy(
                update={
                    "name": str(row.get("name", item.name)),
                    "cuisine": _cuisine_display(row.get("cuisines")) or item.cuisine,
                    "rating": rating,
                    "estimated_cost": _format_cost_display(row.get("cost_for_two")),
                },
            ),
        )
    return result.model_copy(update={"items": joined})


@dataclass
class _Timing:
    filter_ms: float = 0.0
    recommend_ms: float = 0.0
    join_ms: float = 0.0


class RecommendationService:
    """Application service: validation → filter → recommend → store join."""

    def __init__(
        self,
        store: RestaurantDataAccess | None = None,
        *,
        test_df: pd.DataFrame | None = None,
        llm_complete: LlmComplete | None = None,
        settings: GroqSettings | None = None,
    ) -> None:
        if test_df is not None:
            store = _DataFrameStore(test_df)
        self._store_accessor = store
        self._store_df: pd.DataFrame | None = None
        self._llm_complete = llm_complete
        self._settings = settings

    @property
    def is_loaded(self) -> bool:
        return self._store_df is not None

    def load(self) -> None:
        accessor = self._store_accessor or ParquetRestaurantStore()
        self._store_df = accessor.load_restaurants_df()
        self._store_accessor = accessor
        logger.info(
            "dataset_loaded rows=%s snapshot=%s",
            len(self._store_df),
            accessor.dataset_snapshot_id(),
        )

    def _require_store(self) -> tuple[RestaurantDataAccess, pd.DataFrame]:
        if self._store_df is None or self._store_accessor is None:
            raise RuntimeError("Dataset not loaded")
        return self._store_accessor, self._store_df

    def health(self) -> HealthCheckResponse:
        if not self.is_loaded:
            return HealthCheckResponse(
                status="ok",
                dataset="not_loaded",
                schema_version=get_schema_version(),
                prompt_version=PROMPT_VERSION,
            )
        accessor, df = self._require_store()
        warning = None
        if len(df) < 100:
            warning = (
                f"Only {len(df)} restaurants loaded — run full ingest: "
                "python -m restaurant_rec ingest"
            )
        return HealthCheckResponse(
            status="ok",
            dataset="loaded",
            schema_version=get_schema_version(),
            dataset_snapshot_id=accessor.dataset_snapshot_id(),
            row_count=len(df),
            prompt_version=PROMPT_VERSION,
            warning=warning,
        )

    def list_search_areas(self) -> dict[str, list[str]]:
        _, df = self._require_store()
        return get_search_areas(df)

    def recommend(
        self,
        preferences: PreferenceDTO,
        *,
        top_k: int | None = None,
    ) -> RecommendResponse:
        accessor, df = self._require_store()
        timing = _Timing()

        t0 = time.perf_counter()
        bundle = filter_restaurants(preferences, accessor)
        timing.filter_ms = (time.perf_counter() - t0) * 1000

        meta = bundle.metadata
        if not bundle.candidates:
            logger.info(
                "recommend_empty locality=%s filter_count=0 filter_ms=%.1f",
                preferences.locality,
                timing.filter_ms,
            )
            return RecommendResponse(
                items=[],
                summary=None,
                used_llm=False,
                warnings=["empty candidate bundle"],
                filter_count=meta.filter_count,
                returned_count=0,
                dataset_snapshot_id=meta.dataset_snapshot_id,
                message="No restaurants matched your filters. Try relaxing locality, cuisine, or min_rating.",
            )

        cfg = self._settings if self._settings is not None else GroqSettings.from_env()
        t1 = time.perf_counter()
        result = recommend(
            bundle,
            preferences,
            top_k=top_k,
            settings=cfg,
            llm_complete=self._llm_complete,
        )
        timing.recommend_ms = (time.perf_counter() - t1) * 1000

        t2 = time.perf_counter()
        result = join_store_fields(result, df)
        timing.join_ms = (time.perf_counter() - t2) * 1000

        logger.info(
            "recommend_done locality=%s filter_count=%s returned=%s used_llm=%s "
            "filter_ms=%.1f recommend_ms=%.1f join_ms=%.1f",
            preferences.locality,
            meta.filter_count,
            meta.returned_count,
            result.used_llm,
            timing.filter_ms,
            timing.recommend_ms,
            timing.join_ms,
        )

        return RecommendResponse(
            items=result.items,
            summary=result.summary,
            used_llm=result.used_llm,
            warnings=result.warnings,
            filter_count=meta.filter_count,
            returned_count=meta.returned_count,
            dataset_snapshot_id=meta.dataset_snapshot_id,
            message=None,
        )
