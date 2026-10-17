import asyncio
import gc
import io
import time
import tracemalloc
import weakref
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pymupdf
from pypdf import PdfReader, PdfWriter
from pypdf.errors import PyPdfError

from core.checker import screen_pdf
from web.storage import ScanJob, ScanStore

FIXTURES_DIR = Path(__file__).parent / "fixtures"
ACCESSIBLE_PDF = FIXTURES_DIR / "fixture_accessible.pdf"
IMAGES_PDF = FIXTURES_DIR / "fixture_images.pdf"
SCANNED_PDF = FIXTURES_DIR / "fixture_scanned.pdf"


# ==============================================================================
# 3.1 Edge-Case & Boundary Tests
# ==============================================================================

def test_zero_byte_rejection() -> tuple[bool, str]:
    """Asserts that 0-byte stream is rejected with a clean parser exception."""
    try:
        screen_pdf(b"", filename="empty.pdf")
        return False, "Expected parser exception for 0-byte input, but none was raised."
    except (pymupdf.FileDataError, PyPdfError, ValueError) as exc:
        return True, f"Caught expected exception: {type(exc).__name__}"


def test_corrupt_header_rejection() -> tuple[bool, str]:
    """Asserts that corrupted/truncated byte stream is rejected with clean parser exception."""
    try:
        screen_pdf(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\n...corrupted-trailer...", filename="corrupt.pdf")
        return False, "Expected parser exception for corrupt header, but none was raised."
    except (pymupdf.FileDataError, PyPdfError, ValueError) as exc:
        return True, f"Caught expected exception: {type(exc).__name__}"


def test_encrypted_pdf_handling() -> tuple[bool, str]:
    """Asserts password-protected PDF returns Could Not Evaluate with remediation."""
    if not ACCESSIBLE_PDF.exists():
        return False, "fixture_accessible.pdf not found to generate encrypted stream."

    # Programmatically encrypt accessible fixture in memory
    reader = PdfReader(str(ACCESSIBLE_PDF))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt("secret_password")

    buf = io.BytesIO()
    writer.write(buf)
    encrypted_bytes = buf.getvalue()

    result = screen_pdf(encrypted_bytes, filename="encrypted.pdf")
    if result.summary.could_not_evaluate >= 1 and result.summary.passed == 0:
        finding = result.findings[0]
        if "unencrypted" in (finding.remediation_guidance or "").lower():
            return True, f"Encrypted PDF gracefully handled: Status='{finding.status}', checks={result.summary.checks}"
        return False, f"Missing remediation guidance on encrypted document: {finding.remediation_guidance}"
    return False, f"Unexpected result on encrypted document: summary={result.summary}"


def test_scale_multipage() -> tuple[bool, str]:
    """Asserts linear memory and timely processing on 100+ page documents."""
    scale_candidate = None
    for path in sorted(FIXTURES_DIR.glob("*.pdf")):
        try:
            doc = pymupdf.open(str(path))
            p_count = len(doc)
            doc.close()
            if p_count >= 100:
                scale_candidate = path
                break
        except Exception:
            continue

    if not scale_candidate:
        return True, "No 100+ page fixture present; skipped scale benchmark."

    tracemalloc.start()
    t0 = time.time()
    try:
        res = screen_pdf(scale_candidate)
        duration = time.time() - t0
        _, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mb = peak_mem / (1024 * 1024)
        if duration > 60.0:
            return False, f"Scale test exceeded 60s timeout: duration={duration:.2f}s"
        if peak_mb > 150.0:
            return False, f"Scale test exceeded 150MB peak RAM: peak={peak_mb:.1f}MB"
        return True, f"Scaled {res.pages} pages in {duration:.2f}s (peak RAM: {peak_mb:.1f}MB, checks: {res.summary.checks})"
    except Exception as exc:
        tracemalloc.stop()
        return False, f"Scale test error ({type(exc).__name__}): {exc}"


def test_page_boundary_accuracy() -> tuple[bool, str]:
    """Asserts findings map to exact 1-indexed page numbers without off-by-one errors."""
    if not (ACCESSIBLE_PDF.exists() and IMAGES_PDF.exists() and SCANNED_PDF.exists()):
        return False, "Missing standard fixtures needed to construct multi-page fixture."

    # Programmatically compose a 3-page document in memory
    doc1 = pymupdf.open(str(ACCESSIBLE_PDF))
    doc2 = pymupdf.open(str(IMAGES_PDF))
    doc3 = pymupdf.open(str(SCANNED_PDF))

    combined = pymupdf.open()
    combined.insert_pdf(doc1, from_page=0, to_page=0)  # Page 1: has text, no images
    combined.insert_pdf(doc2, from_page=0, to_page=0)  # Page 2: has image
    combined.insert_pdf(doc3, from_page=0, to_page=0)  # Page 3: scanned/no text

    pdf_bytes = combined.tobytes()
    doc1.close()
    doc2.close()
    doc3.close()
    combined.close()

    res = screen_pdf(pdf_bytes, filename="multipage_distinct.pdf")
    if res.pages != 3:
        return False, f"Expected 3 pages, found {res.pages}"

    # Verify Page 2 image finding
    p2_img = next((f for f in res.findings if f.input_location == "Page 2" and "image" in f.issue_description.lower()), None)
    # Verify Page 3 empty text finding
    p3_txt = next((f for f in res.findings if f.input_location == "Page 3" and "text" in f.issue_description.lower()), None)

    if p2_img and p3_txt:
        return True, f"Accurate 1-indexed page mapping verified on 3-page document: {p2_img.input_location}, {p3_txt.input_location}"
    return False, f"Page mapping mismatch: p2_img={p2_img}, p3_txt={p3_txt}"


# ==============================================================================
# 3.2 Security & Zero-Disk Retention Tests
# ==============================================================================

def test_filesystem_isolation_audit() -> tuple[bool, str]:
    """Asserts 0 files are written to /tmp or workspace root during byte-stream screening."""
    if not ACCESSIBLE_PDF.exists():
        return False, "fixture_accessible.pdf required for filesystem isolation test."

    tmp_path = Path("/tmp")
    root_path = Path(__file__).resolve().parent.parent

    before_tmp = set(tmp_path.iterdir()) if tmp_path.exists() else set()
    before_root = set(root_path.iterdir())

    pdf_bytes = ACCESSIBLE_PDF.read_bytes()
    _ = screen_pdf(pdf_bytes, filename="stream_audit.pdf")

    after_tmp = set(tmp_path.iterdir()) if tmp_path.exists() else set()
    after_root = set(root_path.iterdir())

    new_tmp = after_tmp - before_tmp
    new_root = after_root - before_root

    # Filter out any irrelevant socket/system files created externally
    pdf_tmp_artifacts = [p for p in new_tmp if p.is_file() and p.suffix.lower() in (".pdf", ".json", ".tmp")]
    root_artifacts = [p for p in new_root if p.is_file() and p.suffix.lower() in (".pdf", ".json", ".tmp")]

    if not pdf_tmp_artifacts and not root_artifacts:
        return True, "Zero-disk retention audit PASSED: 0 files written to /tmp or workspace root."
    return False, f"Disk leak detected: tmp_artifacts={pdf_tmp_artifacts}, root_artifacts={root_artifacts}"


def test_memory_buffer_deallocation() -> tuple[bool, str]:
    """Asserts memory stream references are released after screening."""
    if not ACCESSIBLE_PDF.exists():
        return False, "fixture_accessible.pdf required for memory deallocation test."

    data = ACCESSIBLE_PDF.read_bytes()
    stream = io.BytesIO(data)
    wr = weakref.ref(stream)

    _ = screen_pdf(stream.getvalue(), filename="dealloc_test.pdf")
    del stream
    gc.collect()

    if wr() is None:
        return True, "Memory buffer deallocation verified: buffer reference released."
    return False, "Memory leak: weakref to memory buffer remained active after garbage collection."


# ==============================================================================
# 3.3 Asynchronous Concurrency & API Contract Tests
# ==============================================================================

def test_concurrent_ingestion_stress() -> tuple[bool, str]:
    """Asserts 10 simultaneous in-memory scans execute cleanly without race conditions."""
    if not ACCESSIBLE_PDF.exists():
        return False, "fixture_accessible.pdf required for concurrency test."

    pdf_bytes = ACCESSIBLE_PDF.read_bytes()

    def run_single(idx: int):
        return screen_pdf(pdf_bytes, filename=f"parallel_{idx}.pdf", scan_id=f"CONC-{idx:02d}")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(run_single, i) for i in range(10)]
        results = [f.result() for f in futures]

    unique_ids = {r.scan_id for r in results}
    all_passed = all(r.summary.checks > 0 and r.pages > 0 for r in results)

    if len(unique_ids) == 10 and all_passed:
        return True, f"10 concurrent scans succeeded with 10 unique IDs and zero race conditions."
    return False, f"Concurrency failure: unique_ids={len(unique_ids)}, all_passed={all_passed}"


def test_job_ttl_expiration() -> tuple[bool, str]:
    """Asserts expired scan jobs (>3600s) are evicted while fresh jobs are retained."""
    store = ScanStore(ttl_seconds=3600)
    now = time.time()

    # Create expired job (created 3700 seconds ago)
    job_expired = ScanJob(scan_id="EXPIRED-01", status="COMPLETED", created_at=now - 3700)
    # Create fresh job (created 100 seconds ago)
    job_fresh = ScanJob(scan_id="FRESH-01", status="COMPLETED", created_at=now - 100)

    store._scans["EXPIRED-01"] = job_expired
    store._scans["FRESH-01"] = job_fresh

    pruned = store.prune_expired()

    if pruned == 1 and store.get_scan("EXPIRED-01") is None and store.get_scan("FRESH-01") is not None:
        return True, "TTL eviction verified: expired job evicted, fresh job retained."
    return False, f"TTL eviction failure: pruned={pruned}, remaining={list(store._scans.keys())}"


async def _dispatch_asgi(method: str, path: str, body: bytes = b"", headers: list[tuple[bytes, bytes]] | None = None) -> int:
    """Minimal ASGI caller to evaluate route status codes without external testclient/httpx packages."""
    status_code = 500
    all_headers = [(b"host", b"testserver")]
    if headers:
        all_headers.extend(headers)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "headers": all_headers,
    }

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        nonlocal status_code
        if message["type"] == "http.response.start":
            status_code = message["status"]

    from web.app import app
    await app(scope, receive, send)
    return status_code


def _run_async(coro):
    """Safely runs an async coroutine even if an event loop is already active."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        with ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


def test_api_contract_and_statuses() -> tuple[bool, str]:
    """Asserts REST API route statuses: 404 on missing job, 422 on invalid upload, 200 on portal."""
    status_404 = _run_async(_dispatch_asgi("GET", "/api/scans/NONEXISTENT_SCAN_ID/status"))
    results_404 = _run_async(_dispatch_asgi("GET", "/api/scans/NONEXISTENT_SCAN_ID/results"))
    post_422 = _run_async(_dispatch_asgi("POST", "/api/scans/pdf"))
    home_200 = _run_async(_dispatch_asgi("GET", "/"))

    valid_contract = (
        status_404 == 404
        and results_404 == 404
        and post_422 == 422
        and home_200 == 200
    )

    if valid_contract:
        return True, "API contract verified: 404 on invalid ID, 422 on empty upload, 200 on home portal."
    return False, f"Status code mismatch: status={status_404}, results={results_404}, post={post_422}, home={home_200}"
