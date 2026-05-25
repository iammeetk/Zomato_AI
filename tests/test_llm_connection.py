"""Live Groq LLM connectivity checks (requires GROQ_API_KEY in .env)."""

from __future__ import annotations

import pytest

from restaurant_rec.phase2.bundle import BundleMetadata, CandidateBundle, CandidateItem
from restaurant_rec.phase2.preferences import PreferenceDTO, UserBudget
from restaurant_rec.phase3.groq_client import chat_completion
from restaurant_rec.phase3.recommend import recommend
from restaurant_rec.phase3.settings import GroqSettings, load_project_dotenv

pytestmark = pytest.mark.live_llm


@pytest.fixture(scope="module")
def groq_settings() -> GroqSettings:
    load_project_dotenv()
    settings = GroqSettings.from_env()
    if not settings.api_key:
        pytest.skip("GROQ_API_KEY is not set — add it to .env to run live LLM tests")
    return settings


def test_api_key_loaded_from_env(groq_settings: GroqSettings) -> None:
    assert groq_settings.api_key
    assert len(groq_settings.api_key) > 10
    assert groq_settings.model


def test_chat_completion_returns_non_empty(groq_settings: GroqSettings) -> None:
    reply = chat_completion(
        system_prompt="You are a connectivity probe. Reply briefly.",
        user_content="Say exactly: CONNECTED",
        settings=groq_settings,
    )
    assert isinstance(reply, str)
    assert reply.strip()


def test_chat_completion_responds_to_instruction(groq_settings: GroqSettings) -> None:
    reply = chat_completion(
        system_prompt="Reply with one word only, no punctuation.",
        user_content="What is 2+2? Answer with the number as a word.",
        settings=groq_settings,
    )
    assert "four" in reply.lower() or "4" in reply


def test_recommend_end_to_end_with_live_llm(groq_settings: GroqSettings) -> None:
    prefs = PreferenceDTO(
        locality="Bangalore",
        budget=UserBudget.medium,
        cuisine=["Chinese"],
        min_rating=3.0,
    )
    candidates = [
        CandidateItem(
            restaurant_id="live_a",
            name="Golden Dragon",
            city="Bangalore",
            cuisines=["Chinese"],
            rating=4.3,
            estimated_cost_display="₹600",
            budget_band="medium",
        ),
        CandidateItem(
            restaurant_id="live_b",
            name="Spice Route",
            city="Bangalore",
            cuisines=["Chinese", "Thai"],
            rating=4.1,
            estimated_cost_display="₹550",
            budget_band="medium",
        ),
    ]
    bundle = CandidateBundle(
        preferences=prefs.echo_dict(),
        candidates=candidates,
        metadata=BundleMetadata(
            filter_count=2,
            returned_count=2,
            dataset_snapshot_id="live-test",
        ),
    )
    result = recommend(bundle, prefs, top_k=2, settings=groq_settings)
    assert result.used_llm is True, result.warnings
    assert len(result.items) >= 1
    assert result.items[0].restaurant_id in {"live_a", "live_b"}
    assert result.summary
