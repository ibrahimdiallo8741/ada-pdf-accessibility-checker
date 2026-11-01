"""Contract tests for the deployed service (new functionality in this phase).

Run against any deployed copy:  BASE_URL=https://host pytest tests/test_api.py

Test names carry the requirement they check. REQ numbers follow Phase 2 Section 3.1;
check them against your pod's current numbering before citing them.
"""
import time

import pytest

from pdfgen import make_pdf, problemset6_like

MB = 1024 * 1024
STATES = {"SUBMITTED", "VALIDATING", "ANALYZING", "GENERATING_REPORT", "COMPLETED", "REJECTED"}
RESULTS = {"PASS", "ISSUE", "NEEDS_HUMAN_REVIEW", "COULD_NOT_EVALUATE"}
FINDING_FIELDS = {"finding_id", "check_id", "wcag_criterion", "title", "description",
                  "location", "analysis_method", "result"}


def check_ids(scan, result):
    return {f["check_id"] for f in scan["findings"] if f["result"] == result}


# --- POST /scans/pdf: accepting input (REQ-03) --------------------------------------
def test_pdf_scan_is_accepted_and_completes(client, scan_pdf):
    response = client.post("/scans/pdf", files={"file": ("a.pdf", make_pdf(), "application/pdf")})
    assert response.status_code == 202
    body = response.json()
    assert body["scan_id"] and body["status"] in STATES
    assert scan_pdf(make_pdf())["status"] == "COMPLETED"


def test_pdf_of_exactly_25_mb_is_accepted(client):
    data = make_pdf(size=25 * MB)
    response = client.post("/scans/pdf", files={"file": ("big.pdf", data, "application/pdf")})
    assert response.status_code == 202, response.text


def test_pdf_over_25_mb_is_rejected_413(client):
    data = make_pdf(size=25 * MB + 1)
    response = client.post("/scans/pdf", files={"file": ("big.pdf", data, "application/pdf")})
    assert response.status_code == 413
    assert response.json()["error"] == "FILE_TOO_LARGE"


# --- failure paths (REQ-12) ---------------------------------------------------------
def test_non_pdf_is_rejected_415(client):
    response = client.post("/scans/pdf", files={"file": ("n.txt", b"hello", "text/plain")})
    assert response.status_code == 415
    assert response.json()["reason"]


def test_corrupted_pdf_is_rejected_400(client):
    data = b"%PDF-1.7\nthis is not a real pdf"
    response = client.post("/scans/pdf", files={"file": ("bad.pdf", data, "application/pdf")})
    assert response.status_code == 400
    assert response.json()["error"] == "INVALID_PDF"


def test_text_file_named_pdf_is_rejected_400(client):
    response = client.post("/scans/pdf",
                           files={"file": ("fake.pdf", b"plain text", "application/pdf")})
    assert response.status_code == 400


def test_missing_file_is_rejected_400(client):
    assert client.post("/scans/pdf").status_code == 400


def test_encrypted_pdf_is_rejected_400(client):
    pypdf = pytest.importorskip("pypdf")
    pytest.importorskip("cryptography")
    import io
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.encrypt("secret")
    buffer = io.BytesIO()
    writer.write(buffer)
    response = client.post("/scans/pdf", files={"file": ("e.pdf", buffer.getvalue(),
                                                        "application/pdf")})
    assert response.status_code == 400
    assert response.json()["error"] == "ENCRYPTED_PDF"


def test_rejected_upload_is_recorded_as_a_rejected_scan(client):
    response = client.post("/scans/pdf", files={"file": ("n.txt", b"x", "text/plain")})
    scan = client.get(f"/scans/{response.json()['scan_id']}").json()
    assert scan["status"] == "REJECTED" and scan["reason"]


def test_web_scanning_is_not_implemented(client):
    response = client.post("/scans/web", json={"url": "https://example.gov"})
    assert response.status_code == 501
    assert response.json()["error"] == "NOT_IMPLEMENTED"


# --- findings are correct (REQ-04, REQ-05) ------------------------------------------
def test_missing_title_language_and_structure_are_reported_as_issues(scan_pdf):
    scan = scan_pdf(make_pdf(title=None, lang=None, tagged=False))
    assert {"pdf-title", "pdf-language", "pdf-structure"} <= check_ids(scan, "ISSUE")


def test_a_well_formed_pdf_has_no_issues(scan_pdf):
    scan = scan_pdf(make_pdf(title="Annual report", lang="en-US", tagged=True))
    assert check_ids(scan, "ISSUE") == set()
    assert "pdf-structure" in check_ids(scan, "NEEDS_HUMAN_REVIEW")  # tag quality unchecked


def test_known_properties_match_the_confirmed_problemset6_run(scan_pdf):
    scan = scan_pdf(problemset6_like())
    assert scan["summary"] == {"checks": 7, "passed": 2, "issues": 2,
                               "needs_human_review": 1, "could_not_evaluate": 2}


def test_image_only_pdf_is_not_treated_as_accessible(scan_pdf):
    scan = scan_pdf(make_pdf(text=None, title="T", lang="en", tagged=True))
    assert "pdf-page-text" in check_ids(scan, "COULD_NOT_EVALUATE")
    assert "pdf-page-text" not in check_ids(scan, "PASS")


def test_images_are_flagged_for_human_review(scan_pdf):
    scan = scan_pdf(make_pdf(images=(1,)))
    assert "pdf-page-images" in check_ids(scan, "NEEDS_HUMAN_REVIEW")


def test_findings_repeat_exactly(scan_pdf):
    def strip(scan):
        return [{k: v for k, v in f.items() if k != "finding_id"} for f in scan["findings"]]
    data = make_pdf(pages=3, images=(2,))
    runs = [strip(scan_pdf(data)) for _ in range(3)]
    assert runs[0] == runs[1] == runs[2]


# --- the report (REQ-08, REQ-10, REQ-11) --------------------------------------------
def test_finding_schema(scan_pdf):
    scan = scan_pdf(make_pdf(pages=2, images=(2,)))
    assert scan["findings"]
    ids = set()
    for finding in scan["findings"]:
        assert FINDING_FIELDS <= set(finding)
        assert finding["result"] in RESULTS
        assert finding["analysis_method"] in {"DETERMINISTIC", "HUMAN_REVIEW_REQUIRED"}
        assert all(isinstance(finding[k], str) and finding[k] for k in FINDING_FIELDS)
        ids.add(finding["finding_id"])
    assert len(ids) == len(scan["findings"])


def test_summary_matches_the_findings(scan_pdf):
    scan = scan_pdf(make_pdf(pages=3, text_pages=(1,), images=(2, 3)))
    findings, summary = scan["findings"], scan["summary"]

    def count(result):
        return sum(1 for f in findings if f["result"] == result)

    assert summary["checks"] == len(findings)
    assert summary["passed"] == count("PASS")
    assert summary["issues"] == count("ISSUE")
    assert summary["needs_human_review"] == count("NEEDS_HUMAN_REVIEW")
    assert summary["could_not_evaluate"] == count("COULD_NOT_EVALUATE")


def test_report_does_not_certify_compliance(scan_pdf):
    scan = scan_pdf(make_pdf(title="T", lang="en", tagged=True))
    assert "does not certify" in scan["disclaimer"].lower()


# --- other operations ---------------------------------------------------------------
def test_status_and_results_endpoints(client, scan_pdf):
    scan_id = scan_pdf(make_pdf())["scan_id"]
    status = client.get(f"/scans/{scan_id}/status")
    assert status.status_code == 200 and status.json()["status"] == "COMPLETED"
    results = client.get(f"/scans/{scan_id}/results")
    assert results.status_code == 200 and results.json()["summary"]


def test_unknown_scan_returns_404(client):
    for path in ("/scans/nope", "/scans/nope/status", "/scans/nope/results"):
        response = client.get(path)
        assert response.status_code == 404
        assert response.json()["error"] == "SCAN_NOT_FOUND"
    assert client.delete("/scans/nope").status_code == 404


def test_delete_removes_the_scan(client, scan_pdf):
    scan_id = scan_pdf(make_pdf())["scan_id"]
    assert client.delete(f"/scans/{scan_id}").status_code == 204
    assert client.get(f"/scans/{scan_id}").status_code == 404


def test_api_prefix_is_also_served(client):
    assert client.get("/api/scans/nope").status_code == 404


def test_health_endpoint(client):
    assert client.get("/health").json() == {"status": "ok"}


# --- performance (REQ-19) -----------------------------------------------------------
def test_initial_results_within_60_seconds(scan_pdf):
    start = time.time()
    scan = scan_pdf(make_pdf(pages=20, size=5 * MB))
    assert scan["status"] == "COMPLETED"
    assert time.time() - start < 60
