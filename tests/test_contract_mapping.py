"""Tests for contract.py: how checker results become contract findings.

These need no PDF library, so they run anywhere. The inputs are results dictionaries
written out by hand from the confirmed problemset6.pdf run in the handoff.
"""
import contract

PROBLEMSET6 = {
    "file": "problemset6.pdf",
    "pages": 2,
    "checks": [
        {"check": "Document title", "status": "FOUND",
         "details": "Title found: Microsoft Word - Assignment-6"},
        {"check": "Document language", "status": "REVIEW",
         "details": "No document language specified."},
        {"check": "PDF structure", "status": "REVIEW",
         "details": "No PDF structure tree found."},
        {"check": "Page 1 text", "status": "REVIEW",
         "details": "No extractable text found. Manual review needed."},
        {"check": "Page 1 images", "status": "INFO",
         "details": "No embedded image resources detected."},
        {"check": "Page 2 text", "status": "REVIEW",
         "details": "No extractable text found. Manual review needed."},
        {"check": "Page 2 images", "status": "REVIEW",
         "details": "1 image resource(s) found. Check whether meaningful images have alt text."},
    ],
    "warnings": [],
}


def by_check(findings):
    return [(f["check_id"], f["location"], f["result"]) for f in findings]


def test_problemset6_mapping():
    findings, summary = contract.build_report(PROBLEMSET6, "scan-x")
    assert by_check(findings) == [
        ("pdf-title", "document", "PASS"),
        ("pdf-language", "document", "ISSUE"),
        ("pdf-structure", "document", "ISSUE"),
        ("pdf-page-text", "page 1", "COULD_NOT_EVALUATE"),
        ("pdf-page-images", "page 1", "PASS"),
        ("pdf-page-text", "page 2", "COULD_NOT_EVALUATE"),
        ("pdf-page-images", "page 2", "NEEDS_HUMAN_REVIEW"),
    ]
    assert summary == {"checks": 7, "passed": 2, "issues": 2,
                       "needs_human_review": 1, "could_not_evaluate": 2}


def test_wcag_criteria():
    findings, _ = contract.build_report(PROBLEMSET6, "scan-x")
    criteria = {f["check_id"]: f["wcag_criterion"] for f in findings}
    assert criteria == {"pdf-title": "2.4.2", "pdf-language": "3.1.1",
                        "pdf-structure": "1.3.1", "pdf-page-text": "1.3.1",
                        "pdf-page-images": "1.1.1"}


def test_a_found_structure_tree_still_needs_human_review():
    findings, _ = contract.build_report(
        {"checks": [{"check": "PDF structure", "status": "FOUND",
                     "details": "Structure tree found. Tag quality needs review."}]},
        "scan-x")
    assert findings[0]["result"] == "NEEDS_HUMAN_REVIEW"
    assert findings[0]["analysis_method"] == "HUMAN_REVIEW_REQUIRED"


def test_a_page_without_text_is_never_reported_as_passing():
    findings, _ = contract.build_report(
        {"checks": [{"check": "Page 1 text", "status": "REVIEW", "details": "none"}]},
        "scan-x")
    assert findings[0]["result"] != "PASS"


def test_unknown_check_is_never_reported_as_passing():
    findings, summary = contract.build_report(
        {"checks": [{"check": "Brand new check", "status": "FOUND", "details": "x"}]},
        "scan-x")
    assert findings[0]["result"] == "COULD_NOT_EVALUATE"
    assert summary["passed"] == 0


def test_finding_fields_and_unique_ids():
    findings, _ = contract.build_report(PROBLEMSET6, "scan-x")
    required = {"finding_id", "check_id", "wcag_criterion", "title", "description",
                "location", "analysis_method", "result"}
    for finding in findings:
        assert required <= set(finding)
        assert finding["result"] in {"PASS", "ISSUE", "NEEDS_HUMAN_REVIEW",
                                     "COULD_NOT_EVALUATE"}
        assert finding["analysis_method"] in {"DETERMINISTIC", "HUMAN_REVIEW_REQUIRED"}
    assert len({f["finding_id"] for f in findings}) == len(findings)
    assert all(f["finding_id"].startswith("scan-x-") for f in findings)


def test_issues_and_reviews_carry_remediation_advice():
    findings, _ = contract.build_report(PROBLEMSET6, "scan-x")
    for finding in findings:
        if finding["result"] in ("ISSUE", "NEEDS_HUMAN_REVIEW", "COULD_NOT_EVALUATE"):
            assert finding.get("remediation")


def test_summary_counts_add_up():
    findings, summary = contract.build_report(PROBLEMSET6, "scan-x")
    assert summary["checks"] == len(findings)
    assert (summary["passed"] + summary["issues"] + summary["needs_human_review"]
            + summary["could_not_evaluate"]) == summary["checks"]


def test_same_input_gives_same_findings():
    assert (contract.build_report(PROBLEMSET6, "scan-x")
            == contract.build_report(PROBLEMSET6, "scan-x"))


def test_failure_report_is_a_single_could_not_evaluate_finding():
    findings, summary = contract.failure_report("scan-x", "RuntimeError")
    assert len(findings) == 1 and findings[0]["result"] == "COULD_NOT_EVALUATE"
    assert summary["could_not_evaluate"] == 1 and summary["passed"] == 0


def test_the_disclaimer_does_not_certify_compliance():
    text = contract.DISCLAIMER.lower()
    assert "does not certify" in text
    assert "qualified person" in text
