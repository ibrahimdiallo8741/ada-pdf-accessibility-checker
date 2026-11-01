"""Translate the checker's results into the pod's common interface (contract).

pdf_checker.py reports FOUND / REVIEW / INFO per check. The pod contract reports
PASS / ISSUE / NEEDS_HUMAN_REVIEW / COULD_NOT_EVALUATE per finding, with the WCAG
criterion and how the finding was produced. This module is the only place that
knows how one maps to the other, so pdf_checker.py and its report stay unchanged.

Mapping (decided by the team; see docs/API.md):

    check                      FOUND / INFO              REVIEW
    -------------------------  ------------------------  -----------------------
    Document title  (2.4.2)    PASS                      ISSUE
    Document language (3.1.1)  PASS                      ISSUE
    PDF structure  (1.3.1)     NEEDS_HUMAN_REVIEW (a)    ISSUE
    Page N text    (1.3.1)     PASS                      COULD_NOT_EVALUATE (b)
    Page N images  (1.1.1)     PASS                      NEEDS_HUMAN_REVIEW

    (a) a tag tree was found, but its quality is not validated.
    (b) a page with no extractable text may be a scanned image; the tool must not
        report it as accessible.
"""
import re

PASS = "PASS"
ISSUE = "ISSUE"
NEEDS_REVIEW = "NEEDS_HUMAN_REVIEW"
COULD_NOT_EVALUATE = "COULD_NOT_EVALUATE"

DETERMINISTIC = "DETERMINISTIC"
HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"

DISCLAIMER = (
    "This report is an automated screening of a documented subset of WCAG 2.1 Level A "
    "and AA checks for PDF documents. It does not certify ADA or WCAG conformance. "
    "Items marked NEEDS_HUMAN_REVIEW or COULD_NOT_EVALUATE, and any criteria this tool "
    "does not check, require review by a qualified person."
)

_PAGE_CHECK = re.compile(r"^Page (\d+) (text|images)$")


def classify(check):
    """Return (check_id, wcag_criterion, title, location, result, remediation)."""
    name, status = check["check"], check["status"]
    found = status in ("FOUND", "INFO")

    if name == "Document title":
        return ("pdf-title", "2.4.2", "Document has a title", "document",
                PASS if found else ISSUE,
                None if found else "Set the document Title property.")

    if name == "Document language":
        return ("pdf-language", "3.1.1", "Document language is declared", "document",
                PASS if found else ISSUE,
                None if found else "Set the document language in its properties.")

    if name == "PDF structure":
        if found:
            return ("pdf-structure", "1.3.1", "Document has a structure tree", "document",
                    NEEDS_REVIEW,
                    "Review the tags, reading order, headings and tables.")
        return ("pdf-structure", "1.3.1", "Document has a structure tree", "document",
                ISSUE, "Export or remediate the document as a tagged PDF.")

    match = _PAGE_CHECK.match(name)
    if match:
        page, kind = match.group(1), match.group(2)
        location = f"page {page}"
        if kind == "text":
            return ("pdf-page-text", "1.3.1", "Page has extractable text", location,
                    PASS if found else COULD_NOT_EVALUATE,
                    None if found else "Run OCR or provide a text version, then re-scan.")
        return ("pdf-page-images", "1.1.1", "Images have text alternatives", location,
                PASS if found else NEEDS_REVIEW,
                None if found else "Check that each meaningful image has alternative text.")

    # A check this module does not know about is never reported as passing.
    return ("unknown-check", "n/a", name, "document", COULD_NOT_EVALUATE, None)


def build_report(results, scan_id):
    """Return (findings, summary) in the contract's shape for one scan."""
    findings = []
    for number, check in enumerate(results["checks"], start=1):
        check_id, criterion, title, location, result, remediation = classify(check)
        finding = {
            "finding_id": f"{scan_id}-f{number:03d}",
            "check_id": check_id,
            "wcag_criterion": criterion,
            "title": title,
            "description": check["details"],
            "location": location,
            "analysis_method": (HUMAN_REVIEW_REQUIRED if result == NEEDS_REVIEW
                                else DETERMINISTIC),
            "result": result,
        }
        if remediation:
            finding["remediation"] = remediation
        findings.append(finding)
    return findings, summarize(findings)


def failure_report(scan_id, error_name):
    """A report for a scan that was accepted but could not be analyzed."""
    findings = [{
        "finding_id": f"{scan_id}-f001",
        "check_id": "analysis",
        "wcag_criterion": "n/a",
        "title": "Analysis did not complete",
        "description": f"The analysis failed with {error_name}.",
        "location": "document",
        "analysis_method": DETERMINISTIC,
        "result": COULD_NOT_EVALUATE,
    }]
    return findings, summarize(findings)


def summarize(findings):
    def count(result):
        return sum(1 for f in findings if f["result"] == result)

    return {
        "checks": len(findings),
        "passed": count(PASS),
        "issues": count(ISSUE),
        "needs_human_review": count(NEEDS_REVIEW),
        "could_not_evaluate": count(COULD_NOT_EVALUATE),
    }
