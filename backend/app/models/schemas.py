"""API request/response models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str = Field(default="default", min_length=1, max_length=128)
    include_sources: bool = True


class SourceCitation(BaseModel):
    title: str
    snippet: str
    source_path: str
    page: int | None = None
    relevance_score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: list[SourceCitation] = Field(default_factory=list)
    model: str
    latency_ms: float


class DocumentInfo(BaseModel):
    filename: str
    size_bytes: int
    extension: str
    modified_at: datetime


class DocumentListResponse(BaseModel):
    documents: list[DocumentInfo]
    total: int


class UploadResponse(BaseModel):
    status: str
    message: str
    filename: str
    size_bytes: int
    chunks_indexed: int


class ReindexResponse(BaseModel):
    status: str
    message: str
    documents_loaded: int
    chunks_indexed: int
    duration_ms: float


class SessionInfo(BaseModel):
    session_id: str
    message_count: int
    created_at: datetime
    last_active: datetime


class HealthResponse(BaseModel):
    status: str
    environment: str


class ReadinessResponse(BaseModel):
    ready: bool
    llm: bool
    embeddings: bool
    vectorstore: bool
    document_count: int
    chunk_count: int
    active_sessions: int


class MetricsResponse(BaseModel):
    total_requests: int
    total_chat_requests: int
    total_documents: int
    active_sessions: int
    uptime_seconds: float
