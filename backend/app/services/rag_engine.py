"""Enterprise RAG engine with history-aware retrieval."""

import logging
import time
from pathlib import Path

from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from app.config import Settings, get_settings
from app.ingestion.pipeline import IngestionPipeline
from app.models.schemas import ChatResponse, SourceCitation
from app.services.session_manager import SessionManager

logger = logging.getLogger(__name__)

ENTERPRISE_SYSTEM = """You are Aura, an enterprise knowledge assistant for internal teams.

Rules:
- Answer ONLY using the provided context. If the context is insufficient, say you do not have enough information.
- Be professional, concise, and actionable.
- Use bullet points for steps or lists when helpful.
- Do not invent facts, policies, or citations.
- When relevant, mention which source document supports your answer.
"""

CONTEXTUALIZE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Given chat history and the latest user question, rewrite it as a standalone question for retrieval. Do not answer it."),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

QA_PROMPT = ChatPromptTemplate.from_messages([
    ("system", ENTERPRISE_SYSTEM + "\n\nContext:\n{context}"),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])


class RAGEngine:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm: ChatGoogleGenerativeAI | None = None
        self.embeddings: GoogleGenerativeAIEmbeddings | None = None
        self.pipeline: IngestionPipeline | None = None
        self.sessions = SessionManager(settings)
        self._retrieval_chain = None
        self._ready = False
        self.metrics = {
            "total_requests": 0,
            "total_chat_requests": 0,
            "start_time": time.time(),
        }

    @property
    def is_ready(self) -> bool:
        return self._ready

    def initialize(self) -> None:
        if not self.settings.google_api_key:
            logger.error("GOOGLE_API_KEY is required")
            return

        self.llm = ChatGoogleGenerativeAI(
            model=self.settings.gemini_model,
            google_api_key=self.settings.google_api_key,
            temperature=self.settings.llm_temperature,
            max_output_tokens=self.settings.max_output_tokens,
        )
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=self.settings.embedding_model,
            google_api_key=self.settings.google_api_key,
        )
        self.pipeline = IngestionPipeline(self.settings, self.embeddings)
        self.pipeline.build_or_load_vectorstore()
        self._build_chain()
        self._ready = True
        logger.info(
            "RAG engine ready | docs=%d chunks=%d",
            self.pipeline.document_count,
            self.pipeline.chunk_count,
        )

    def _build_chain(self) -> None:
        assert self.llm and self.pipeline and self.pipeline.vectorstore

        retriever = self.pipeline.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": self.settings.retrieval_k, "fetch_k": self.settings.retrieval_k * 3},
        )
        history_aware_retriever = create_history_aware_retriever(
            self.llm, retriever, CONTEXTUALIZE_PROMPT
        )
        question_answer_chain = create_stuff_documents_chain(self.llm, QA_PROMPT)
        self._retrieval_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    def chat(self, message: str, session_id: str, include_sources: bool = True) -> ChatResponse:
        self.metrics["total_requests"] += 1
        self.metrics["total_chat_requests"] += 1

        if not self._ready or not self._retrieval_chain:
            raise RuntimeError("RAG engine not initialized")

        session = self.sessions.get(session_id)
        start = time.perf_counter()

        result = self._retrieval_chain.invoke({
            "input": message,
            "chat_history": session.history.messages,
        })

        answer = result.get("answer", "I could not generate a response.")
        self.sessions.append_exchange(session_id, message, answer)

        sources: list[SourceCitation] = []
        if include_sources:
            for doc in result.get("context", []):
                path = doc.metadata.get("source", "unknown")
                title = doc.metadata.get("filename") or Path(path).name
                sources.append(SourceCitation(
                    title=title,
                    snippet=doc.page_content[:300] + ("…" if len(doc.page_content) > 300 else ""),
                    source_path=str(path),
                    page=doc.metadata.get("page"),
                    metadata=dict(doc.metadata),
                ))

        latency_ms = (time.perf_counter() - start) * 1000
        return ChatResponse(
            response=answer,
            session_id=session_id,
            sources=sources,
            model=self.settings.gemini_model,
            latency_ms=round(latency_ms, 2),
        )

    def reindex(self) -> tuple[int, int, float]:
        if not self.pipeline:
            raise RuntimeError("Pipeline not initialized")
        docs, chunks, duration = self.pipeline.reindex()
        self.sessions.clear_all()
        self._build_chain()
        return docs, chunks, duration

    def shutdown(self) -> None:
        self._ready = False
        logger.info("RAG engine shut down")


_engine: RAGEngine | None = None


def get_rag_engine() -> RAGEngine:
    global _engine
    if _engine is None:
        _engine = RAGEngine(get_settings())
    return _engine
