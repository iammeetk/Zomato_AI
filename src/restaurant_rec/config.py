"""Paths and tunable thresholds for ingestion."""

from pathlib import Path

# Repository root (cwd is safe for Streamlit Cloud and local runs from root)
PROJECT_ROOT = Path.cwd()
FRONTEND_DIR = PROJECT_ROOT / "frontend"

DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_PARQUET_NAME = "restaurants.parquet"
DEFAULT_MANIFEST_NAME = "manifest.json"

DATASET_NAME = "ManikaSaini/zomato-restaurant-recommendation"

# INR thresholds for cost_for_two → budget_band (inclusive upper bound for low/medium)
COST_BAND_UPPER_LOW = 400
COST_BAND_UPPER_MEDIUM = 1000

# Phase 2 — cap candidates passed to the LLM (Phase 3)
MAX_CANDIDATES_DEFAULT = 30

# Phase 3 — Groq + recommendation output
GROQ_API_BASE = "https://api.groq.com/openai/v1"
DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"
DEFAULT_GROQ_TEMPERATURE = 0.35
DEFAULT_GROQ_MAX_TOKENS = 1_024
DEFAULT_GROQ_TIMEOUT_SECONDS = 60.0
DEFAULT_RECOMMENDATION_TOP_K = 5

PROMPT_VERSION = "3.1"

# INR anchors for pre-ranking only (closer to ideal sorts earlier within same rating)
IDEAL_COST_FOR_RANKING: dict[str, int] = {
    "low": 250,
    "medium": 700,
    "high": 2000,
}

# Columns to load from Hugging Face (reduces memory)
HF_COLUMNS = [
    "url",
    "address",
    "name",
    "online_order",
    "book_table",
    "rate",
    "votes",
    "phone",
    "location",
    "rest_type",
    "dish_liked",
    "cuisines",
    "approx_cost(for two people)",
    "reviews_list",
    "menu_item",
    "listed_in(type)",
    "listed_in(city)",
]
