import threading
import time
from dataclasses import dataclass, field

from core.models import ScanResult, ScanStatus


@dataclass
class ScanJob:
    scan_id: str
    status: ScanStatus
    result: ScanResult | None = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)


class ScanStore:
    """Thread-safe in-memory store for asynchronous scan jobs."""

    def __init__(self, ttl_seconds: int = 3600):
        self._lock = threading.Lock()
        self._scans: dict[str, ScanJob] = {}
        self._counter = 1
        self._ttl_seconds = ttl_seconds

    def create_scan(self, custom_id: str | None = None) -> ScanJob:
        with self._lock:
            self._prune_expired_locked()
            if custom_id:
                scan_id = custom_id
            else:
                scan_id = f"S{self._counter:03d}"
                self._counter += 1

            job = ScanJob(scan_id=scan_id, status="ANALYZING")
            self._scans[scan_id] = job
            return job

    def get_scan(self, scan_id: str) -> ScanJob | None:
        with self._lock:
            return self._scans.get(scan_id)

    def update_status(
        self,
        scan_id: str,
        status: ScanStatus,
        result: ScanResult | None = None,
        error: str | None = None,
    ) -> ScanJob | None:
        with self._lock:
            job = self._scans.get(scan_id)
            if job:
                job.status = status
                if result is not None:
                    job.result = result
                if error is not None:
                    job.error = error
            return job

    def _prune_expired_locked(self):
        now = time.time()
        expired_keys = [
            sid for sid, job in self._scans.items()
            if now - job.created_at > self._ttl_seconds
        ]
        for sid in expired_keys:
            del self._scans[sid]


# Global in-memory instance
store = ScanStore()
