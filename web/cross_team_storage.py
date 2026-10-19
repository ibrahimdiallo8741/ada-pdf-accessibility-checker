import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SystemSession:
    """Session tracked by the System under test."""
    session_id: str
    setup_data: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


@dataclass
class TesterSession:
    """Session tracked by the Tester executing a test suite."""
    session_id: str
    target_url: str
    status: str = "prepared"  # "prepared" | "running" | "completed" | "aborted"
    results: list[dict[str, Any]] = field(default_factory=list)
    coverage: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    completed_at: float | None = None
    abort_message: str | None = None


class CrossTeamSessionStore:
    """Thread-safe in-memory registry for both System and Tester sessions."""

    def __init__(self, ttl_seconds: int = 7200):
        self._lock = threading.Lock()
        self._system_sessions: dict[str, SystemSession] = {}
        self._tester_sessions: dict[str, TesterSession] = {}
        self._ttl_seconds = ttl_seconds

    # --- System Role Methods ---

    def register_system_session(self, session_id: str, setup_data: dict[str, Any] | None = None) -> SystemSession:
        with self._lock:
            self._prune_expired_locked()
            if session_id in self._system_sessions:
                raise ValueError(f"Session '{session_id}' already exists.")
            session = SystemSession(
                session_id=session_id,
                setup_data=setup_data or {},
            )
            self._system_sessions[session_id] = session
            return session

    def get_system_session(self, session_id: str) -> SystemSession | None:
        with self._lock:
            return self._system_sessions.get(session_id)

    # --- Tester Role Methods ---

    def create_tester_session(self, target_url: str, custom_id: str | None = None) -> TesterSession:
        with self._lock:
            self._prune_expired_locked()
            session_id = custom_id or f"run-{uuid.uuid4().hex[:12]}"
            if session_id in self._tester_sessions:
                raise ValueError(f"Tester session '{session_id}' already exists.")
            clean_url = target_url.rstrip("/")
            session = TesterSession(session_id=session_id, target_url=clean_url)
            self._tester_sessions[session_id] = session
            return session

    def get_tester_session(self, session_id: str) -> TesterSession | None:
        with self._lock:
            return self._tester_sessions.get(session_id)

    def mark_tester_running(self, session_id: str) -> TesterSession:
        with self._lock:
            session = self._tester_sessions.get(session_id)
            if not session:
                raise KeyError(f"Tester session '{session_id}' not found.")
            if session.status != "prepared":
                raise ValueError(f"Tester session '{session_id}' has already run or is currently running (status='{session.status}').")
            session.status = "running"
            return session

    def complete_tester_session(
        self,
        session_id: str,
        results: list[dict[str, Any]],
        coverage: dict[str, Any],
    ) -> TesterSession:
        with self._lock:
            session = self._tester_sessions.get(session_id)
            if not session:
                raise KeyError(f"Tester session '{session_id}' not found.")
            session.status = "completed"
            session.results = results
            session.coverage = coverage
            session.completed_at = time.time()
            return session

    def abort_tester_session(
        self,
        session_id: str,
        results: list[dict[str, Any]],
        coverage: dict[str, Any],
        message: str,
    ) -> TesterSession:
        with self._lock:
            session = self._tester_sessions.get(session_id)
            if not session:
                raise KeyError(f"Tester session '{session_id}' not found.")
            session.status = "aborted"
            session.results = results
            session.coverage = coverage
            session.completed_at = time.time()
            session.abort_message = message
            return session

    def _prune_expired_locked(self):
        now = time.time()
        sys_expired = [
            sid for sid, s in self._system_sessions.items()
            if now - s.created_at > self._ttl_seconds
        ]
        for sid in sys_expired:
            del self._system_sessions[sid]

        tester_expired = [
            sid for sid, s in self._tester_sessions.items()
            if now - s.created_at > self._ttl_seconds
        ]
        for sid in tester_expired:
            del self._tester_sessions[sid]


cross_store = CrossTeamSessionStore()
