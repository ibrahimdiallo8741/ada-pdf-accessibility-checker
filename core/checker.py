import io
import logging
import time
import uuid
from pathlib import Path

import pymupdf
from pypdf import PdfReader
from pypdf.errors import PyPdfError

from core.ai_evaluator import evaluate_ai_heuristics
from core.checks import (
    check_language,
    check_page_images,
    check_page_text,
    check_pdf_form_fields,
    check_pdf_outlines,
    check_structure,
    check_title,
)
from core.contrast_analyzer import analyze_graphical_contrast, analyze_page_contrast
from core.models import Finding, ScanResult, ScanSummary
from core.pdf_struct_parser import parse_structure_tree

logger = logging.getLogger("adacheck.pdf")


def screen_pdf(
    source: str | Path | bytes,
    filename: str | None = None,
    scan_id: str | None = None,
) -> ScanResult:
    """Performs deterministic accessibility screening on a PDF file path or raw bytes buffer."""
    t0 = time.perf_counter()
    if scan_id is None:
        scan_id = f"S-{uuid.uuid4().hex[:8].upper()}"

    if isinstance(source, bytes):
        resolved_name = filename or "document.pdf"
        byte_size = len(source)
        doc_mu = pymupdf.open(stream=source, filetype="pdf")
        reader_py = PdfReader(io.BytesIO(source))
    else:
        path = Path(source)
        resolved_name = filename or path.name
        byte_size = path.stat().st_size if path.exists() else 0
        doc_mu = pymupdf.open(str(path))
        reader_py = PdfReader(str(path))

    logger.info("PDF scan [%s] started: filename='%s', size=%d bytes", scan_id, resolved_name, byte_size)

    # Authenticate/decrypt documents with standard empty/permissions passwords
    if getattr(doc_mu, "needs_pass", False):
        doc_mu.authenticate("")
    if getattr(reader_py, "is_encrypted", False):
        try:
            reader_py.decrypt("")
        except (PyPdfError, ValueError, AttributeError):
            pass

    # Detect if document remains password-locked
    if getattr(doc_mu, "needs_pass", False) or getattr(reader_py, "is_encrypted", False):
        try:
            _ = reader_py.root_object
        except (PyPdfError, ValueError, AttributeError, KeyError):
            p_count = len(doc_mu) if (doc_mu and not getattr(doc_mu, "is_closed", False)) else 0
            doc_mu.close()
            finding = Finding(
                finding_id="F001",
                input_location="Document Catalog",
                issue_description="The PDF document is password-protected or encrypted.",
                WCAG_criterion="General Accessibility",
                analysis_method="Deterministic",
                status="Could Not Evaluate",
                remediation_guidance="Ensure the PDF file is unencrypted, valid, and not password protected, then retry screening.",
            )
            return ScanResult(
                scan_id=scan_id,
                file_or_url=resolved_name,
                pages=p_count,
                summary=ScanSummary(checks=1, passed=0, issues=0, human_review=0, could_not_evaluate=1),
                findings=[finding],
            )

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

        # Deep Semantic Structure Tree Traversal (Milestone 6)
        if root_obj and "/StructTreeRoot" in root_obj:
            struct_findings, finding_counter = parse_structure_tree(
                root_obj, start_counter=finding_counter
            )
            findings.extend(struct_findings)

        # Navigational outlines check (WCAG 2.4.1 Bypass Blocks for multi-page documents)
        outline_finding = check_pdf_outlines(root_obj, pages_count, finding_id=f"F{finding_counter:03d}")
        if outline_finding:
            findings.append(outline_finding)
            finding_counter += 1

        # Interactive form fields check (WCAG 1.3.1 & 4.1.2)
        form_findings = check_pdf_form_fields(root_obj, finding_id=f"F{finding_counter:03d}")
        for ff in form_findings:
            findings.append(ff)
            finding_counter += 1

        # 4. Per-page text and image checks
        page_texts: list[tuple[str, str]] = []
        for page_num, page in enumerate(doc_mu.pages(), start=1):
            # Extractable text check
            text = page.get_text()
            if len(page_texts) < 10:
                page_texts.append((f"Page {page_num}", text[:500]))
            elif len(page_texts) < 30 and any(w in text.lower() for w in ("click", "press", "green", "red", "blue", "above", "below")):
                page_texts.append((f"Page {page_num}", text[:300]))

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

            # Visual & Contrast Analysis (Milestone 7)
            contrast_finding = analyze_page_contrast(
                page, page_num, finding_id=f"F{finding_counter:03d}"
            )
            findings.append(contrast_finding)
            finding_counter += 1

            graphical_finding = analyze_graphical_contrast(
                page, page_num, finding_id=f"F{finding_counter:03d}"
            )
            if graphical_finding:
                findings.append(graphical_finding)
                finding_counter += 1

        # 5. Contextual AI Heuristics (Milestone 8)
        title_val = (metadata.get("title") or "").strip()
        ai_findings, finding_counter = evaluate_ai_heuristics(
            title=title_val,
            content_items=page_texts,
            start_counter=finding_counter,
        )
        findings.extend(ai_findings)

    finally:
        doc_mu.close()

    summary = ScanSummary(
        checks=len(findings),
        passed=sum(1 for f in findings if f.status == "Pass"),
        issues=sum(1 for f in findings if f.status == "Issue"),
        human_review=sum(1 for f in findings if f.status == "Needs Human Review"),
        could_not_evaluate=sum(1 for f in findings if f.status == "Could Not Evaluate"),
    )

    elapsed_ms = (time.perf_counter() - t0) * 1000
    logger.info(
        "PDF scan [%s] completed in %.1fms: %d pages, %d checks (Pass=%d, Issue=%d, Review=%d, CouldNotEval=%d)",
        scan_id,
        elapsed_ms,
        pages_count,
        summary.checks,
        summary.passed,
        summary.issues,
        summary.human_review,
        summary.could_not_evaluate,
    )

    return ScanResult(
        scan_id=scan_id,
        file_or_url=resolved_name,
        pages=pages_count,
        summary=summary,
        findings=findings,
    )
