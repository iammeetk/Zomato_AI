"""Restaurant recommendation package — phased layout (``phase1`` … ``phase3``)."""

from restaurant_rec.phase1 import (
    SCHEMA_VERSION,
    BudgetBand,
    ParquetRestaurantStore,
    load_restaurants,
    print_ingest_report,
    run_ingest,
)
from restaurant_rec.phase1.store import (
    default_manifest_path,
    default_parquet_path,
    get_schema_version,
    parse_additional_signals,
    read_dataset_snapshot_id,
)
from restaurant_rec.phase2 import (
    BundleMetadata,
    CandidateBundle,
    CandidateItem,
    PreferenceDTO,
    RestaurantDataAccess,
    UserBudget,
    explain_ideal_costs_markdown,
    filter_restaurants,
)
from restaurant_rec.phase3 import (
    GroqSettings,
    RecommendationItem,
    RecommendationResult,
    load_project_dotenv,
    recommend,
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
    "PreferenceDTO",
    "UserBudget",
    "CandidateBundle",
    "CandidateItem",
    "BundleMetadata",
    "RestaurantDataAccess",
    "filter_restaurants",
    "explain_ideal_costs_markdown",
    "recommend",
    "RecommendationItem",
    "RecommendationResult",
    "GroqSettings",
    "load_project_dotenv",
]
