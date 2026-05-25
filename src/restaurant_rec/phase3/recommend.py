"""Phase 3 orchestration: Groq completion, parse, join store fields, fallback."""

from __future__ import annotations

from collections.abc import Callable

from restaurant_rec.phase2.bundle import CandidateBundle, CandidateItem
from restaurant_rec.phase2.preferences import PreferenceDTO
from restaurant_rec.phase3.groq_client import chat_completion
from restaurant_rec.phase3.models import RecommendationItem, RecommendationResult
from restaurant_rec.phase3.parsing import parse_llm_recommendations
from restaurant_rec.phase3.prompts import build_system_prompt, build_user_content
from restaurant_rec.phase3.settings import GroqSettings


def _template_explanation(preferences: PreferenceDTO, c: CandidateItem) -> str:
    cuisines = ", ".join(c.cuisines)
    return (
        f"Strong match for your {preferences.budget.value} budget and {cuisines} in {c.city}. "
        f"Rated {c.rating} with estimated cost {c.estimated_cost_display}."
    )


def _item_from_candidate(
    c: CandidateItem,
    preferences: PreferenceDTO,
    explanation: str,
    rank: int,
) -> RecommendationItem:
    return RecommendationItem(
        restaurant_id=c.restaurant_id,
        name=c.name,
        cuisine=", ".join(c.cuisines),
        rating=c.rating,
        estimated_cost=c.estimated_cost_display,
        explanation=explanation,
        rank=rank,
    )


def _fallback_result(
    bundle: CandidateBundle,
    preferences: PreferenceDTO,
    top_k: int,
    warnings: list[str],
) -> RecommendationResult:
    items: list[RecommendationItem] = []
    for i, c in enumerate(bundle.candidates[:top_k], start=1):
        items.append(
            _item_from_candidate(
                c,
                preferences,
                _template_explanation(preferences, c),
                i,
            ),
        )
    return RecommendationResult(items=items, summary=None, used_llm=False, warnings=warnings)


def _sanitize_llm_rows(
    rec_rows: list[dict],
    by_id: dict[str, CandidateItem],
    preferences: PreferenceDTO,
    top_k: int,
    warnings: list[str],
) -> list[RecommendationItem]:
    """Keep valid ids in model order; template explanation if the model omits text."""
    seen: set[str] = set()
    items: list[RecommendationItem] = []
    for row in rec_rows:
        if len(items) >= top_k:
            break
        rid = str(row.get("restaurant_id", "")).strip()
        if rid not in by_id:
            if rid:
                warnings.append(f"dropped unknown restaurant_id from model output: {rid!r}")
            continue
        if rid in seen:
            continue
        seen.add(rid)
        c = by_id[rid]
        expl = str(row.get("explanation", "")).strip()
        if not expl:
            expl = _template_explanation(preferences, c)
        items.append(_item_from_candidate(c, preferences, expl, len(items) + 1))
    return items


def _backfill(
    items: list[RecommendationItem],
    bundle: CandidateBundle,
    preferences: PreferenceDTO,
    top_k: int,
) -> list[RecommendationItem]:
    """Append candidates in Phase 2 order until ``top_k``, then renumber ranks."""
    seen = {i.restaurant_id for i in items}
    out = list(items)
    for c in bundle.candidates:
        if len(out) >= top_k:
            break
        if c.restaurant_id in seen:
            continue
        seen.add(c.restaurant_id)
        out.append(
            _item_from_candidate(
                c,
                preferences,
                _template_explanation(preferences, c),
                len(out) + 1,
            ),
        )
    trimmed = out[:top_k]
    return [it.model_copy(update={"rank": idx + 1}) for idx, it in enumerate(trimmed)]


def recommend(
    bundle: CandidateBundle,
    preferences: PreferenceDTO,
    *,
    top_k: int | None = None,
    settings: GroqSettings | None = None,
    llm_complete: Callable[[str, str], str] | None = None,
) -> RecommendationResult:
    """
    Rank and explain candidates using Groq, with deterministic fallback.

    Args:
        bundle: Output of Phase 2.
        preferences: Same DTO used to build the bundle (for typed API layers).
        top_k: Max recommendations; defaults to ``settings.recommendation_top_k``.
        settings: Groq + defaults; loaded via :meth:`GroqSettings.from_env` when omitted.
        llm_complete: ``(system_prompt, user_content) -> raw model text`` for tests.
    """
    cfg = settings if settings is not None else GroqSettings.from_env()
    k = top_k if top_k is not None else cfg.recommendation_top_k
    k = max(1, k)
    warnings: list[str] = []

    if not bundle.candidates:
        return RecommendationResult(
            items=[],
            summary=None,
            used_llm=False,
            warnings=["empty candidate bundle"],
        )

    by_id = {c.restaurant_id: c for c in bundle.candidates}

    def run_fallback() -> RecommendationResult:
        return _fallback_result(bundle, preferences, k, list(warnings))

    if llm_complete is not None:
        try:
            system = build_system_prompt(k)
            user = build_user_content(bundle, preferences, k)
            raw = llm_complete(system, user)
            summary, rows = parse_llm_recommendations(raw)
            items = _sanitize_llm_rows(rows, by_id, preferences, k, warnings)
            items = _backfill(items, bundle, preferences, k)
            return RecommendationResult(
                items=items,
                summary=summary,
                used_llm=True,
                warnings=warnings,
            )
        except Exception as exc:
            warnings.append(f"llm_complete failed: {exc}")
            return run_fallback()

    if not cfg.api_key:
        warnings.append("GROQ_API_KEY not set; using deterministic template explanations")
        return run_fallback()

    try:
        system = build_system_prompt(k)
        user = build_user_content(bundle, preferences, k)
        raw = chat_completion(system, user, cfg)
        if not raw:
            warnings.append("empty completion from Groq")
            return run_fallback()
        summary, rows = parse_llm_recommendations(raw)
        items = _sanitize_llm_rows(rows, by_id, preferences, k, warnings)
        items = _backfill(items, bundle, preferences, k)
        return RecommendationResult(
            items=items,
            summary=summary,
            used_llm=True,
            warnings=warnings,
        )
    except Exception as exc:
        warnings.append(f"Groq request or parse failed: {exc}")
        return run_fallback()
