"""Phase 3 recommend() — injectable LLM, fallback, sanitization."""

from __future__ import annotations

import json

from restaurant_rec.config import (
    DEFAULT_GROQ_MAX_TOKENS,
    DEFAULT_GROQ_MODEL,
    DEFAULT_GROQ_TEMPERATURE,
    DEFAULT_GROQ_TIMEOUT_SECONDS,
    DEFAULT_RECOMMENDATION_TOP_K,
)
from restaurant_rec.phase2.bundle import BundleMetadata, CandidateBundle, CandidateItem
from restaurant_rec.phase2.preferences import PreferenceDTO, UserBudget
from restaurant_rec.phase3.recommend import recommend
from restaurant_rec.phase3.settings import GroqSettings


def _pref() -> PreferenceDTO:
    return PreferenceDTO(
        location="Bangalore",
        budget=UserBudget.medium,
        cuisine=["Chinese"],
        min_rating=3.0,
    )


def _candidates() -> list[CandidateItem]:
    return [
        CandidateItem(
            restaurant_id="rid_a",
            name="A",
            city="Bangalore",
            cuisines=["Chinese"],
            rating=4.2,
            estimated_cost_display="₹600",
            budget_band="medium",
        ),
        CandidateItem(
            restaurant_id="rid_b",
            name="B",
            city="Bangalore",
            cuisines=["Chinese", "Thai"],
            rating=4.5,
            estimated_cost_display="₹700",
            budget_band="medium",
        ),
    ]


def _bundle(cands: list[CandidateItem]) -> CandidateBundle:
    return CandidateBundle(
        preferences=_pref().echo_dict(),
        candidates=cands,
        metadata=BundleMetadata(
            filter_count=len(cands),
            returned_count=len(cands),
            dataset_snapshot_id="test",
        ),
    )


def test_recommend_empty_bundle() -> None:
    bundle = _bundle([])
    result = recommend(bundle, _pref(), top_k=3)
    assert result.items == []
    assert result.used_llm is False
    assert "empty candidate bundle" in result.warnings[0]


def test_recommend_mock_llm_joins_store_fields() -> None:
    bundle = _bundle(_candidates())

    def llm(_s: str, _u: str) -> str:
        return json.dumps(
            {
                "summary": "Pick of the day",
                "recommendations": [
                    {
                        "restaurant_id": "rid_b",
                        "rank": 1,
                        "explanation": "Higher rating and great fit.",
                    },
                ],
            },
        )

    result = recommend(bundle, _pref(), top_k=2, llm_complete=llm)
    assert result.used_llm is True
    assert result.summary == "Pick of the day"
    assert len(result.items) == 2
    assert result.items[0].restaurant_id == "rid_b"
    assert result.items[0].name == "B"
    assert result.items[0].rating == 4.5
    assert result.items[0].estimated_cost == "₹700"
    assert "Higher rating" in result.items[0].explanation
    assert result.items[1].restaurant_id == "rid_a"


def test_recommend_drops_hallucinated_id_and_warns() -> None:
    bundle = _bundle(_candidates())

    def llm(_s: str, _u: str) -> str:
        return json.dumps(
            {
                "recommendations": [
                    {"restaurant_id": "nope", "explanation": "fake"},
                    {"restaurant_id": "rid_a", "explanation": "real"},
                ],
            },
        )

    result = recommend(bundle, _pref(), top_k=2, llm_complete=llm)
    assert result.used_llm is True
    assert any("nope" in w for w in result.warnings)
    assert result.items[0].restaurant_id == "rid_a"


def test_recommend_inject_malformed_json_fallback() -> None:
    bundle = _bundle(_candidates())

    def llm(_s: str, _u: str) -> str:
        return "not valid json {{{"

    result = recommend(bundle, _pref(), top_k=2, llm_complete=llm)
    assert result.used_llm is False
    assert len(result.items) == 2
    assert result.items[0].restaurant_id == "rid_a"


def test_recommend_without_api_key_uses_fallback() -> None:
    bundle = _bundle(_candidates())
    cfg = GroqSettings(
        api_key=None,
        model=DEFAULT_GROQ_MODEL,
        temperature=DEFAULT_GROQ_TEMPERATURE,
        max_tokens=DEFAULT_GROQ_MAX_TOKENS,
        timeout_seconds=DEFAULT_GROQ_TIMEOUT_SECONDS,
        recommendation_top_k=DEFAULT_RECOMMENDATION_TOP_K,
    )
    result = recommend(bundle, _pref(), top_k=2, settings=cfg, llm_complete=None)
    assert result.used_llm is False
    assert any("GROQ_API_KEY" in w for w in result.warnings)
    assert len(result.items) == 2
