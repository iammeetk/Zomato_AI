"""Versioned system/user prompts for Groq (Phase 3)."""

from __future__ import annotations

import json

from restaurant_rec.config import PROMPT_VERSION
from restaurant_rec.phase2.bundle import CandidateBundle
from restaurant_rec.phase2.preferences import PreferenceDTO

_SYSTEM_TEMPLATE = """You are an expert dining assistant for Indian cities.
You ONLY rank and explain restaurants from the candidate list provided in the user message.
Never invent a restaurant_id that is not in that list. If data is insufficient, say so briefly in the explanation text.

Return exactly one JSON object (no markdown fences, no commentary outside JSON) with this shape:
{{
  "summary": "optional short overview for the user",
  "recommendations": [
    {{
      "restaurant_id": "<id copied from the candidate list>",
      "rank": 1,
      "explanation": "1-3 sentences why this fits the user's preferences"
    }}
  ]
}}

Rules:
- Include at most {top_k} entries in "recommendations", rank starting at 1 (best first).
- Every "restaurant_id" MUST appear in the provided candidates JSON.
- Prefer diverse strong matches when the user named multiple cuisines or notes."""


def build_system_prompt(top_k: int) -> str:
    return _SYSTEM_TEMPLATE.format(top_k=top_k)


def build_user_content(bundle: CandidateBundle, preferences: PreferenceDTO, top_k: int) -> str:
    candidates_payload = [
        {
            "restaurant_id": c.restaurant_id,
            "name": c.name,
            "city": c.city,
            "cuisines": c.cuisines,
            "rating": c.rating,
            "estimated_cost": c.estimated_cost_display,
            "budget_band": c.budget_band,
        }
        for c in bundle.candidates
    ]
    body = {
        "prompt_version": PROMPT_VERSION,
        "user_preferences": preferences.echo_dict(),
        "dataset_snapshot_id": bundle.metadata.dataset_snapshot_id,
        "candidate_count": len(bundle.candidates),
        "desired_top_k": top_k,
        "candidates": candidates_payload,
    }
    return json.dumps(body, ensure_ascii=False, indent=2)
