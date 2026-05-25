"""Phase 4 — FastAPI application service layer."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from restaurant_rec.config import FRONTEND_DIR
from restaurant_rec.phase2.preferences import PreferenceDTO
from restaurant_rec.phase4.schemas import (
    HealthCheckResponse,
    LocalitiesResponse,
    RecommendResponse,
)
from restaurant_rec.phase4.service import LlmComplete, RecommendationService

_SERVICE: RecommendationService | None = None


def get_service(request: Request) -> RecommendationService:
    svc = getattr(request.app.state, "service", None)
    if svc is None or not svc.is_loaded:
        raise HTTPException(status_code=503, detail="Dataset not loaded yet.")
    return svc


def create_app(
    *,
    service: RecommendationService | None = None,
    llm_complete: LlmComplete | None = None,
) -> FastAPI:
    """
    Build the FastAPI app.

    Pass a pre-built ``service`` (tests) or ``llm_complete`` mock; otherwise the
    dataset is loaded from parquet on startup.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        global _SERVICE
        svc = service or RecommendationService(llm_complete=llm_complete)
        if not svc.is_loaded:
            svc.load()
        app.state.service = svc
        _SERVICE = svc
        yield
        app.state.service = None
        _SERVICE = None

    application = FastAPI(
        title="Restaurant Recommendation API",
        description="Phase 4 — filter, Groq LLM, store-backed recommendations",
        version="1.0.0",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/health", response_model=HealthCheckResponse)
    def health_check(request: Request) -> HealthCheckResponse:
        svc: RecommendationService | None = getattr(request.app.state, "service", None)
        if svc is None:
            return HealthCheckResponse(status="ok", dataset="not_loaded")
        return svc.health()

    @application.get("/v1/localities", response_model=LocalitiesResponse)
    def get_all_localities(svc: RecommendationService = Depends(get_service)) -> LocalitiesResponse:
        areas = svc.list_search_areas()
        return LocalitiesResponse(**areas)

    @application.post("/v1/recommend", response_model=RecommendResponse)
    def get_recommendations(
        preferences: PreferenceDTO,
        svc: RecommendationService = Depends(get_service),
    ) -> RecommendResponse:
        try:
            return svc.recommend(preferences)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            logger = __import__("logging").getLogger(__name__)
            logger.exception("recommend_failed")
            raise HTTPException(status_code=500, detail="Recommendation failed") from exc

    if FRONTEND_DIR.is_dir():
        application.mount(
            "/",
            StaticFiles(directory=str(FRONTEND_DIR), html=True),
            name="frontend",
        )

    return application


# Default app for uvicorn: restaurant_rec.phase4.api:app
app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run(
        "restaurant_rec.phase4.api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()
