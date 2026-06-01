"""Thread-safe conversational session store with TTL."""

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage

from app.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class SessionRecord:
    session_id: str
    history: InMemoryChatMessageHistory = field(default_factory=InMemoryChatMessageHistory)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_active: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def message_count(self) -> int:
        return len(self.history.messages)


class SessionManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._sessions: dict[str, SessionRecord] = {}
        self._lock = threading.RLock()

    def get(self, session_id: str) -> SessionRecord:
        with self._lock:
            self._evict_expired()
            if session_id not in self._sessions:
                if len(self._sessions) >= self.settings.max_sessions:
                    self._evict_oldest()
                self._sessions[session_id] = SessionRecord(session_id=session_id)
            record = self._sessions[session_id]
            record.last_active = datetime.now(timezone.utc)
            return record

    def clear(self, session_id: str) -> bool:
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False

    def clear_all(self) -> None:
        with self._lock:
            self._sessions.clear()

    def list_sessions(self) -> list[SessionRecord]:
        with self._lock:
            self._evict_expired()
            return list(self._sessions.values())

    @property
    def active_count(self) -> int:
        with self._lock:
            return len(self._sessions)

    def _evict_expired(self) -> None:
        now = datetime.now(timezone.utc)
        ttl = self.settings.session_ttl_seconds
        expired = [
            sid
            for sid, rec in self._sessions.items()
            if (now - rec.last_active).total_seconds() > ttl
        ]
        for sid in expired:
            del self._sessions[sid]
            logger.debug("Evicted expired session %s", sid)

    def _evict_oldest(self) -> None:
        if not self._sessions:
            return
        oldest = min(self._sessions.values(), key=lambda r: r.last_active)
        del self._sessions[oldest.session_id]
        logger.warning("Evicted oldest session %s (max sessions reached)", oldest.session_id)

    def get_history_messages(self, session_id: str) -> list[dict]:
        record = self.get(session_id)
        out = []
        for msg in record.history.messages:
            role = "user" if isinstance(msg, HumanMessage) else "assistant"
            out.append({"role": role, "content": msg.content})
        return out

    def append_exchange(self, session_id: str, question: str, answer: str) -> None:
        record = self.get(session_id)
        record.history.add_user_message(question)
        record.history.add_ai_message(answer)
