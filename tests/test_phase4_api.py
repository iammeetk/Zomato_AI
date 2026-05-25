"""Phase 4 API — health, recommend, validation (mocked LLM)."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from restaurant_rec.phase4.api import create_app
from restaurant_rec.phase4.service import RecommendationService
from tests.test_filter import _fixture_df


def _mock_llm(_system: str, _user: str) -> str:
    return json.dumps(
        {
            "summary": "Top Delhi pick",
            "recommendations": [
                {
                    "restaurant_id": "delhi_match",
                    "rank": 1,
                    "explanation": "Strong North Indian match for your budget.",
                },
            ],
        },
    )


@pytest.fixture
def client() -> TestClient:
    svc = RecommendationService(test_df=_fixture_df(), llm_complete=_mock_llm)
    svc.load()
    app = create_app(service=svc)
    with TestClient(app) as test_client:
        yield test_client


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["dataset"] == "loaded"
    assert data["row_count"] == len(_fixture_df())
    assert data["schema_version"]
    assert data["dataset_snapshot_id"] == "test-fixture"


def test_localities_endpoint(client: TestClient) -> None:
    response = client.get("/v1/localities")
    assert response.status_code == 200
    data = response.json()
    assert "metros" in data
    assert "localities" in data
    assert "Bangalore" in data["metros"]
    assert "Banashankari" in data["localities"] or "BTM" in data["localities"]


def test_recommend_success(client: TestClient) -> None:
    payload = {
        "location": "New Delhi",
        "budget": "medium",
        "cuisine": ["North Indian"],
        "min_rating": 4.0,
    }
    response = client.post("/v1/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["used_llm"] is True
    assert data["filter_count"] >= 1
    assert len(data["items"]) >= 1
    item = data["items"][0]
    assert item["restaurant_id"] == "delhi_match"
    assert item["name"] == "Capital Spice"
    assert "North Indian" in item["cuisine"]
    assert item["rating"] == 4.2
    assert item["estimated_cost"] == "₹650"
    assert item["explanation"]


def test_recommend_invalid_input(client: TestClient) -> None:
    payload = {
        "location": "Delhi",
        "budget": "extremely-cheap",
        "cuisine": ["North Indian"],
        "min_rating": 4.0,
    }
    response = client.post("/v1/recommend", json=payload)
    assert response.status_code == 422
