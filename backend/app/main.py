"""FastAPI application factory."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.api.v1 import system
from app.api.v1.router import api_router
from app.config import get_settings
from app.core.logging import setup_logging
from app.core.middleware import RequestContextMiddleware
from app.services.rag_engine import get_rag_engine

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address, default_limits=[])


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    settings = get_settings()
    logger.info("Starting %s [%s]", settings.app_name, settings.environment)
    engine = get_rag_engine()
    engine.initialize()
    yield
    engine.shutdown()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description="Enterprise Retrieval-Augmented Generation API powered by Gemini and ChromaDB.",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    limiter.default_limits = [f"{settings.rate_limit_per_minute}/minute"]
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Response-Time-Ms"],
    )

    app.include_router(api_router)
    app.include_router(system.router)

    # Legacy routes (v1 compatibility for existing frontends)
    @app.post("/chat")
    @limiter.limit(f"{settings.rate_limit_per_minute}/minute")
    async def legacy_chat(request: Request):
        from app.models.schemas import ChatRequest

        body = await request.json()
        req = ChatRequest(**body)
        engine = get_rag_engine()
        if not engine.is_ready:
            return JSONResponse(status_code=503, content={"detail": "Not ready"})
        result = engine.chat(req.message, req.session_id, req.include_sources)
        return result.model_dump()

    @app.post("/reindex_kb")
    async def legacy_reindex():
        engine = get_rag_engine()
        docs, chunks, duration = engine.reindex()
        return {
            "status": "success",
            "message": "Reindexed",
            "documents_indexed": docs,
            "chunks_indexed": chunks,
            "duration_ms": duration,
        }

    @app.get("/")
    async def root():
        return {
            "service": settings.app_name,
            "docs": "/docs",
            "api": "/api/v1",
        }

    return app


app = create_app()
