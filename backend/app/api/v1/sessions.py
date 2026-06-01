"""Session management endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import rag_engine
from app.core.security import verify_api_key
from app.models.schemas import SessionInfo
from app.services.rag_engine import RAGEngine

router = APIRouter(prefix="/sessions", tags=["Sessions"], dependencies=[Depends(verify_api_key)])


@router.get("", response_model=list[SessionInfo])
async def list_sessions(engine: RAGEngine = Depends(rag_engine)) -> list[SessionInfo]:
    return [
        SessionInfo(
            session_id=r.session_id,
            message_count=r.message_count,
            created_at=r.created_at,
            last_active=r.last_active,
        )
        for r in engine.sessions.list_sessions()
    ]


@router.get("/{session_id}/history")
async def get_history(session_id: str, engine: RAGEngine = Depends(rag_engine)) -> dict:
    return {"session_id": session_id, "messages": engine.sessions.get_history_messages(session_id)}


@router.delete("/{session_id}")
async def clear_session(session_id: str, engine: RAGEngine = Depends(rag_engine)) -> dict:
    if not engine.sessions.clear(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "cleared", "session_id": session_id}
