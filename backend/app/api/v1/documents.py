"""Document management endpoints."""

import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.config import get_settings
from app.core.deps import rag_engine
from app.core.security import verify_api_key
from app.models.schemas import DocumentInfo, DocumentListResponse, ReindexResponse, UploadResponse
from app.services.rag_engine import RAGEngine

router = APIRouter(prefix="/documents", tags=["Documents"], dependencies=[Depends(verify_api_key)])


@router.get("", response_model=DocumentListResponse)
async def list_documents(engine: RAGEngine = Depends(rag_engine)) -> DocumentListResponse:
    items = engine.pipeline.list_documents() if engine.pipeline else []
    docs = [
        DocumentInfo(
            filename=i["filename"],
            size_bytes=i["size_bytes"],
            extension=i["extension"],
            modified_at=datetime.fromtimestamp(i["modified_at"], tz=timezone.utc),
        )
        for i in items
    ]
    return DocumentListResponse(documents=docs, total=len(docs))


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    engine: RAGEngine = Depends(rag_engine),
) -> UploadResponse:
    settings = get_settings()
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")

    ext = Path(file.filename).suffix.lower()
    if ext not in settings.allowed_ext_set:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported type {ext}. Allowed: {', '.join(sorted(settings.allowed_ext_set))}",
        )

    content = await file.read()
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_file_size_mb}MB limit")

    safe_name = os.path.basename(file.filename)
    dest = settings.data_dir / safe_name
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)

    docs, chunks, _ = engine.reindex()
    return UploadResponse(
        status="success",
        message=f"Uploaded and indexed '{safe_name}'",
        filename=safe_name,
        size_bytes=len(content),
        chunks_indexed=chunks,
    )


@router.delete("/{filename}")
async def delete_document(filename: str, engine: RAGEngine = Depends(rag_engine)) -> dict:
    if not engine.pipeline or not engine.pipeline.delete_document(filename):
        raise HTTPException(status_code=404, detail="Document not found")
    docs, chunks, duration = engine.reindex()
    return {
        "status": "deleted",
        "filename": os.path.basename(filename),
        "documents_remaining": docs,
        "chunks_indexed": chunks,
        "duration_ms": duration,
    }


@router.post("/reindex", response_model=ReindexResponse)
async def reindex(engine: RAGEngine = Depends(rag_engine)) -> ReindexResponse:
    docs, chunks, duration = engine.reindex()
    return ReindexResponse(
        status="success",
        message="Knowledge base reindexed successfully",
        documents_loaded=docs,
        chunks_indexed=chunks,
        duration_ms=round(duration, 2),
    )
