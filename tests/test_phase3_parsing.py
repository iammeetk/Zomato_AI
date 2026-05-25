"""Phase 3 JSON extraction from model text."""

import json

import pytest

from restaurant_rec.phase3.parsing import extract_json_text, parse_llm_recommendations


def test_extract_json_text_strips_fence() -> None:
    raw = """Here you go:
```json
{"recommendations": [{"restaurant_id": "x"}]}
```
"""
    assert '"restaurant_id"' in extract_json_text(raw)


def test_parse_llm_recommendations_object() -> None:
    payload = {
        "summary": "All good",
        "recommendations": [{"restaurant_id": "a", "rank": 1, "explanation": "why"}],
    }
    summary, rows = parse_llm_recommendations(json.dumps(payload))
    assert summary == "All good"
    assert rows == [{"restaurant_id": "a", "rank": 1, "explanation": "why"}]


def test_parse_llm_recommendations_bare_list() -> None:
    payload = [{"restaurant_id": "b"}]
    summary, rows = parse_llm_recommendations(json.dumps(payload))
    assert summary is None
    assert rows == [{"restaurant_id": "b"}]


def test_parse_llm_recommendations_invalid_json() -> None:
    with pytest.raises(json.JSONDecodeError):
        parse_llm_recommendations("not-json")
