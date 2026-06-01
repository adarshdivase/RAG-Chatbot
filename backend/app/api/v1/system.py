"""Health, readiness, and metrics."""

import time

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.models.schemas import HealthResponse, MetricsResponse, ReadinessResponse
from app.services.rag_engine import get_rag_engine

router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    s = get_settings()
    return HealthResponse(status="ok", environment=s.environment)


@router.get("/ready", response_model=ReadinessResponse)
async def ready() -> ReadinessResponse:
    engine = get_rag_engine()
    pipeline = engine.pipeline
    resp = ReadinessResponse(
        ready=engine.is_ready,
        llm=engine.llm is not None,
        embeddings=engine.embeddings is not None,
        vectorstore=pipeline.vectorstore is not None if pipeline else False,
        document_count=pipeline.document_count if pipeline else 0,
        chunk_count=pipeline.chunk_count if pipeline else 0,
        active_sessions=engine.sessions.active_count,
    )
    if not resp.ready:
        raise HTTPException(status_code=503, detail=resp.model_dump())
    return resp


@router.get("/live")
async def liveness() -> dict:
    return {"alive": True}


@router.get("/metrics", response_model=MetricsResponse)
async def metrics() -> MetricsResponse:
    engine = get_rag_engine()
    uptime = time.time() - engine.metrics["start_time"]
    return MetricsResponse(
        total_requests=engine.metrics["total_requests"],
        total_chat_requests=engine.metrics["total_chat_requests"],
        total_documents=engine.pipeline.document_count if engine.pipeline else 0,
        active_sessions=engine.sessions.active_count,
        uptime_seconds=round(uptime, 1),
    )
