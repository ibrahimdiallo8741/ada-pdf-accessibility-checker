"""In-memory scan store.

Scans live only in process memory. They are lost on restart, and the oldest are
dropped once MAX_SCANS is exceeded. Uploaded PDF bytes are never kept here.
"""
import os
import threading
import uuid
from collections import OrderedDict
from datetime import datetime, timezone

MAX_SCANS = int(os.getenv("MAX_SCANS", "1000"))

_lock = threading.Lock()
_scans = OrderedDict()


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def create(status="SUBMITTED", reason=None):
    scan_id = "scan-" + uuid.uuid4().hex[:12]
    record = {
        "scan_id": scan_id,
        "status": status,
        "reason": reason,
        "created_at": now_iso(),
        "summary": None,
        "findings": None,
    }
    with _lock:
        _scans[scan_id] = record
        while len(_scans) > MAX_SCANS:
            _scans.popitem(last=False)
    return dict(record)


def get(scan_id):
    with _lock:
        record = _scans.get(scan_id)
        return dict(record) if record else None


def update(scan_id, **fields):
    with _lock:
        record = _scans.get(scan_id)
        if record is not None:  # the scan may have been deleted while it ran
            record.update(fields)


def delete(scan_id):
    with _lock:
        return _scans.pop(scan_id, None) is not None
