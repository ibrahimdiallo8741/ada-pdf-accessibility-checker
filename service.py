"""Web service for the PDF accessibility checker (the pod's common interface).

    POST   /scans/pdf              upload a PDF (multipart field "file")  -> 202
    POST   /scans/web              not implemented by this team           -> 501
    GET    /scans/{scan_id}        status, plus summary and findings once COMPLETED
    GET    /scans/{scan_id}/status status only
    GET    /scans/{scan_id}/results results (409 until COMPLETED)
    DELETE /scans/{scan_id}        delete a scan                          -> 204
    GET    /health                 liveness check

Every route is also served under /api. Run locally with:
    uvicorn service:app --port 8000
"""
import io
import logging
import os
import tempfile
import threading
import time

from fastapi import APIRouter, BackgroundTasks, FastAPI, File, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pypdf import PdfReader

import scan_store
from contract import DISCLAIMER, build_report, failure_report
from pdf_checker import scan_pdf

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("service")

MAX_PDF_BYTES = 25 * 1024 * 1024  # 25 MB, per the acceptance criteria and interface
PDF_TYPES = {"application/pdf", "application/x-pdf"}

# PyMuPDF is not guaranteed to be thread-safe, so scans run one at a time.
_SCAN_LOCK = threading.Lock()

app = FastAPI(title="ADA PDF Accessibility Checker", version="0.3.0")
router = APIRouter()


class ApiError(Exception):
    def __init__(self, status, code, reason, scan_id=None):
        super().__init__(reason)
        self.status = status
        self.code = code
        self.reason = reason
        self.scan_id = scan_id


def error_body(code, reason, scan_id=None):
    # "reason" and "message" both appear in the Phase 2 spec, so both are sent.
    body = {"error": code, "reason": reason, "message": reason}
    if scan_id:
        body["scan_id"] = scan_id
    return body


@app.exception_handler(ApiError)
async def api_error_handler(_: Request, exc: ApiError):
    return JSONResponse(status_code=exc.status,
                        content=error_body(exc.code, exc.reason, exc.scan_id))


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400,
                        content=error_body("INVALID_REQUEST", "The request is not valid."))


def reject(err):
    """Record the scan as REJECTED (state model) and attach its id to the error."""
    record = scan_store.create(status="REJECTED", reason=err.reason)
    log.info("scan_id=%s stage=validate outcome=rejected code=%s", record["scan_id"], err.code)
    err.scan_id = record["scan_id"]
    return err


def status_view(record):
    body = {"scan_id": record["scan_id"], "status": record["status"]}
    if record["status"] == "REJECTED":
        body["reason"] = record["reason"]
    return body


def full_view(record):
    body = status_view(record)
    body["created_at"] = record["created_at"]
    if record["status"] == "COMPLETED":
        body["summary"] = record["summary"]
        body["findings"] = record["findings"]
        body["disclaimer"] = DISCLAIMER
    return body


def get_or_404(scan_id):
    record = scan_store.get(scan_id)
    if record is None:
        raise ApiError(404, "SCAN_NOT_FOUND", "No scan exists with the supplied scan ID.")
    return record


def validate_pdf(file):
    """Return the uploaded bytes, or raise ApiError describing what is wrong."""
    if file is None:
        raise ApiError(400, "INVALID_REQUEST", "A PDF file must be sent in the 'file' field.")

    name = (file.filename or "").lower()
    if (file.content_type or "").lower() not in PDF_TYPES and not name.endswith(".pdf"):
        raise ApiError(415, "UNSUPPORTED_MEDIA_TYPE", "Only PDF files are supported.")

    data = bytearray()
    while True:
        chunk = file.file.read(1024 * 1024)
        if not chunk:
            break
        data.extend(chunk)
        if len(data) > MAX_PDF_BYTES:
            raise ApiError(413, "FILE_TOO_LARGE", "PDF files must not exceed 25 MB.")
    data = bytes(data)

    if b"%PDF-" not in data[:1024]:
        raise ApiError(400, "INVALID_PDF", "The file is not a valid PDF.")
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise ApiError(400, "ENCRYPTED_PDF", "Encrypted PDFs are not supported.")
        if len(reader.pages) == 0:
            raise ApiError(400, "INVALID_PDF", "The PDF contains no pages.")
    except ApiError:
        raise
    except Exception:
        raise ApiError(400, "INVALID_PDF", "The PDF is corrupted or cannot be read.")
    return data


def run_pdf_scan(scan_id, data, display_name):
    """Background job: SUBMITTED -> ANALYZING -> GENERATING_REPORT -> COMPLETED."""
    started = time.perf_counter()
    scan_store.update(scan_id, status="ANALYZING")
    tmp_path = None
    try:
        # The upload only exists on disk while it is analyzed, then it is deleted.
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        with _SCAN_LOCK:
            results = scan_pdf(tmp_path, display_name=display_name)
        findings, summary = build_report(results, scan_id)
    except Exception as exc:  # a failed analysis must not leave a scan stuck
        log.exception("scan_id=%s stage=analyze error=%s", scan_id, type(exc).__name__)
        findings, summary = failure_report(scan_id, type(exc).__name__)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    analyzed = time.perf_counter()
    scan_store.update(scan_id, status="GENERATING_REPORT")
    scan_store.update(scan_id, status="COMPLETED", summary=summary, findings=findings)
    log.info("scan_id=%s stage=analyze duration_ms=%d", scan_id, (analyzed - started) * 1000)
    log.info("scan_id=%s stage=report checks=%d issues=%d review=%d cannot=%d",
             scan_id, summary["checks"], summary["issues"],
             summary["needs_human_review"], summary["could_not_evaluate"])


@router.post("/scans/pdf", status_code=202)
def start_pdf_scan(background: BackgroundTasks, file: UploadFile | None = File(None)):
    try:
        data = validate_pdf(file)
    except ApiError as err:
        raise reject(err)
    record = scan_store.create()
    display_name = os.path.basename(file.filename or "upload.pdf")
    log.info("scan_id=%s stage=accepted bytes=%d", record["scan_id"], len(data))
    background.add_task(run_pdf_scan, record["scan_id"], data, display_name)
    return {"scan_id": record["scan_id"], "status": record["status"]}


@router.post("/scans/web")
def start_web_scan():
    raise ApiError(501, "NOT_IMPLEMENTED",
                   "This service scans PDF documents only; web page scanning is not implemented.")


@router.get("/scans/{scan_id}")
def get_scan(scan_id: str):
    return full_view(get_or_404(scan_id))


@router.get("/scans/{scan_id}/status")
def get_scan_status(scan_id: str):
    return status_view(get_or_404(scan_id))


@router.get("/scans/{scan_id}/results")
def get_scan_results(scan_id: str):
    record = get_or_404(scan_id)
    if record["status"] != "COMPLETED":  # the spec is silent here; 409 is our choice
        raise ApiError(409, "RESULTS_NOT_READY",
                       f"The scan is {record['status']}; results are available when it "
                       "is COMPLETED.")
    return full_view(record)


@router.delete("/scans/{scan_id}", status_code=204)
def delete_scan(scan_id: str):
    get_or_404(scan_id)
    scan_store.delete(scan_id)
    return Response(status_code=204)


app.include_router(router)
app.include_router(router, prefix="/api")


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}
