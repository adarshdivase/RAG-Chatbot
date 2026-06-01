"""Chat endpoints."""

from fastapi import APIRouter, Depends

from app.core.deps import rag_engine
from app.core.security import verify_api_key
from app.models.schemas import ChatRequest, ChatResponse
from app.services.rag_engine import RAGEngine

router = APIRouter(prefix="/chat", tags=["Chat"], dependencies=[Depends(verify_api_key)])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, engine: RAGEngine = Depends(rag_engine)) -> ChatResponse:
    return engine.chat(
        message=request.message,
        session_id=request.session_id,
        include_sources=request.include_sources,
    )
