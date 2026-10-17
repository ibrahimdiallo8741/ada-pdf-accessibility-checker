from pathlib import Path
from typing import Annotated

import pymupdf
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pypdf.errors import PyPdfError

from core.checker import screen_pdf
from tests.runner import run_automated_suite
from web.storage import store

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB per api.md

app = FastAPI(
    title="ADA PDF Accessibility Screening API",
    description="Automated screening prototype aligned with ADA Title II and WCAG 2.1 Level AA.",
    version="0.1.0",
)

STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

INDEX_HTML_PATH = Path(__file__).parent / "templates" / "index.html"


class WebScanRequest(BaseModel):
    url: str


def process_pdf_scan(scan_id: str, content: bytes, filename: str):
    """Background task executing deterministic PDF accessibility screening."""
    try:
        store.update_status(scan_id, status="ANALYZING")
        scan_result = screen_pdf(content, filename=filename, scan_id=scan_id)
        store.update_status(scan_id, status="COMPLETED", result=scan_result)
    except (pymupdf.FileDataError, PyPdfError, ValueError, TypeError, KeyError, AttributeError) as exc:
        store.update_status(scan_id, status="REJECTED", error=f"PDF parsing error ({type(exc).__name__}): {exc}")
    except Exception as exc:  # noqa: BLE001
        store.update_status(scan_id, status="REJECTED", error=f"Unexpected error ({type(exc).__name__}): {exc}")


@app.get("/", response_class=HTMLResponse, tags=["Web UI"])
async def get_index():
    """Serves the interactive screening portal and automated test runner."""
    if INDEX_HTML_PATH.exists():
        return HTMLResponse(content=INDEX_HTML_PATH.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>ADA PDF Accessibility Checker API</h1><p>Visit <a href='/docs'>/docs</a></p>")


@app.post("/api/scans/pdf", status_code=202, tags=["Scans"])
async def start_pdf_scan(
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File()],
):
    """Submits a PDF for asynchronous accessibility screening (REQ-02, REQ-03, REQ-12, REQ-15)."""
    # 1. Validate file format / MIME
    filename = file.filename or "document.pdf"
    if not filename.lower().endswith(".pdf"):
        return JSONResponse(
            status_code=415,
            content={"error": "UNSUPPORTED_MEDIA_TYPE", "message": "Only PDF files are supported."},
        )

    # 2. Read bytes and enforce 25 MB limit
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        return JSONResponse(
            status_code=413,
            content={"error": "PAYLOAD_TOO_LARGE", "message": "File exceeds maximum supported size of 25 MB."},
        )

    if len(content) == 0:
        return JSONResponse(
            status_code=400,
            content={"error": "EMPTY_FILE", "message": "Submitted PDF file contains 0 bytes."},
        )

    # 3. Create scan job and dispatch background analysis
    scan_job = store.create_scan()
    background_tasks.add_task(process_pdf_scan, scan_job.scan_id, content, filename)

    return JSONResponse(
        status_code=202,
        content={"scan_id": scan_job.scan_id, "status": "ANALYZING"},
    )


@app.post("/api/scans/web", status_code=422, tags=["Scans"])
async def start_web_scan(request: WebScanRequest):
    """Web scan endpoint (descoped for prototype per REQ-12 and FUTURE_WORK.md)."""
    return JSONResponse(
        status_code=422,
        content={
            "error": "UNSUPPORTED_PAGE",
            "message": "Webpage scanning is outside current prototype scope. Please use /api/scans/pdf.",
        },
    )


@app.get("/api/scans/{scan_id}/status", tags=["Scans"])
async def get_scan_status(scan_id: str):
    """Returns the current processing status of a scan job (REQ-12, REQ-13, REQ-18)."""
    job = store.get_scan(scan_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail={"error": "SCAN_NOT_FOUND", "message": f"Scan with ID '{scan_id}' does not exist."},
        )
    return {"scan_id": job.scan_id, "status": job.status, "error": job.error}


@app.get("/api/scans/{scan_id}/results", tags=["Scans"])
async def get_scan_results(scan_id: str):
    """Retrieves completed accessibility findings and summary counts (REQ-06–REQ-10, REQ-17)."""
    job = store.get_scan(scan_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail={"error": "SCAN_NOT_FOUND", "message": f"Scan with ID '{scan_id}' does not exist."},
        )
    if job.status == "REJECTED":
        raise HTTPException(
            status_code=400,
            detail={"error": "SCAN_REJECTED", "message": job.error or "Scan was rejected due to unreadable file."},
        )
    if job.status != "COMPLETED" or job.result is None:
        raise HTTPException(
            status_code=409,
            detail={"error": "SCAN_NOT_READY", "message": f"Scan is in state '{job.status}'. Results not yet available."},
        )
    return job.result.to_dict()


@app.post("/api/test-runner", tags=["Test Runner"])
async def trigger_automated_tests():
    """Runs automated acceptance test suite against curated test fixtures (AC-01 through AC-18)."""
    summary = run_automated_suite()
    return summary.to_dict()
