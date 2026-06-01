"""FastAPI dependencies."""

from app.services.rag_engine import RAGEngine, get_rag_engine


def rag_engine() -> RAGEngine:
    engine = get_rag_engine()
    if not engine.is_ready:
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail="RAG engine is not ready. Check GOOGLE_API_KEY and logs.")
    return engine
