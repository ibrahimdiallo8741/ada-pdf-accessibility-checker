import io
import uuid
from pathlib import Path

import pymupdf
from pypdf import PdfReader
from pypdf.errors import PyPdfError

from core.checks import (
    check_language,
    check_page_images,
    check_page_text,
    check_structure,
    check_title,
)
from core.models import Finding, ScanResult, ScanSummary


def screen_pdf(
    source: str | Path | bytes,
    filename: str | None = None,
    scan_id: str | None = None,
) -> ScanResult:
    """Performs deterministic accessibility screening on a PDF file path or raw bytes buffer."""
    if scan_id is None:
        scan_id = f"S-{uuid.uuid4().hex[:8].upper()}"

    if isinstance(source, bytes):
        resolved_name = filename or "document.pdf"
        doc_mu = pymupdf.open(stream=source, filetype="pdf")
        reader_py = PdfReader(io.BytesIO(source))
    else:
        path = Path(source)
        resolved_name = filename or path.name
        doc_mu = pymupdf.open(str(path))
        reader_py = PdfReader(str(path))

    # Authenticate/decrypt documents with standard empty/permissions passwords
    if getattr(doc_mu, "needs_pass", False):
        doc_mu.authenticate("")
    if getattr(reader_py, "is_encrypted", False):
        try:
            reader_py.decrypt("")
        except (PyPdfError, ValueError, AttributeError):
            pass

    findings: list[Finding] = []
    finding_counter = 1

    try:
        pages_count = len(doc_mu)

        # 1. Document title check
        metadata = doc_mu.metadata or {}
        findings.append(check_title(metadata, finding_id=f"F{finding_counter:03d}"))
        finding_counter += 1

        # 2. Document language check
        findings.append(check_language(doc_mu.language, finding_id=f"F{finding_counter:03d}"))
        finding_counter += 1

        # 3. PDF structure tree check
        root_obj = reader_py.root_object
        findings.append(check_structure(root_obj, finding_id=f"F{finding_counter:03d}"))
        finding_counter += 1

        # 4. Per-page text and image checks
        for page_num, page in enumerate(doc_mu.pages(), start=1):
            # Extractable text check
            text = page.get_text()
            findings.append(
                check_page_text(page_num, text, finding_id=f"F{finding_counter:03d}")
            )
            finding_counter += 1

            # Image resources check
            images = page.get_images(full=True)
            findings.append(
                check_page_images(page_num, len(images), finding_id=f"F{finding_counter:03d}")
            )
            finding_counter += 1

    finally:
        doc_mu.close()

    summary = ScanSummary(
        checks=len(findings),
        passed=sum(1 for f in findings if f.status == "Pass"),
        issues=sum(1 for f in findings if f.status == "Issue"),
        human_review=sum(1 for f in findings if f.status == "Needs Human Review"),
        could_not_evaluate=sum(1 for f in findings if f.status == "Could Not Evaluate"),
    )

    return ScanResult(
        scan_id=scan_id,
        file_or_url=resolved_name,
        pages=pages_count,
        summary=summary,
        findings=findings,
    )
