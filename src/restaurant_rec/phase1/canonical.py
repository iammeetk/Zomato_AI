"""Canonical schema version and budget band enum."""

from enum import Enum

SCHEMA_VERSION = "2"


class BudgetBand(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    unknown = "unknown"
