"""Extract structured recommendations from raw LLM text."""

from __future__ import annotations

import json
import re
from typing import Any

_FENCE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def extract_json_text(raw: str) -> str:
    """Strip optional ```json fences; otherwise return stripped input."""
    text = raw.strip()
    m = _FENCE.search(text)
    if m:
        return m.group(1).strip()
    return text


def parse_llm_recommendations(raw: str) -> tuple[str | None, list[dict[str, Any]]]:
    """
    Parse model output into ``(summary, recommendation dicts)``.

    Accepts either a JSON object with ``recommendations`` / ``items``, or a bare JSON array.
    """
    text = extract_json_text(raw)
    data: Any = json.loads(text)
    if isinstance(data, list):
        return None, [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        summary = data.get("summary")
        summary_out = str(summary) if summary is not None else None
        recs = data.get("recommendations") or data.get("items") or []
        if not isinstance(recs, list):
            return summary_out, []
        return summary_out, [x for x in recs if isinstance(x, dict)]
    return None, []
