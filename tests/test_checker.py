"""Regression tests for the existing checker (pdf_checker.py).

These pin down what the command-line tool already did before the service existed, so
that adding the service cannot silently change it. Each fixture's properties are set
explicitly in tests/pdfgen.py, so the expected results are known independently of the
code under test.
"""
import json

import pytest

import pdf_checker
from pdfgen import accessible_test_like, make_pdf, problemset6_like


@pytest.fixture
def pdf_file(tmp_path):
    def write(data, name="sample.pdf"):
        path = tmp_path / name
        path.write_bytes(data)
        return path
    return write


def statuses(results):
    return [(c["check"], c["status"]) for c in results["checks"]]


# --- the confirmed example run from the handoff (problemset6.pdf) ------------------
def test_problemset6_like_matches_the_confirmed_run(pdf_file):
    results = pdf_checker.scan_pdf(pdf_file(problemset6_like()))
    assert results["pages"] == 2
    assert statuses(results) == [
        ("Document title", "FOUND"),
        ("Document language", "REVIEW"),
        ("PDF structure", "REVIEW"),
        ("Page 1 text", "REVIEW"),
        ("Page 1 images", "INFO"),
        ("Page 2 text", "REVIEW"),
        ("Page 2 images", "REVIEW"),
    ]
    assert len(results["checks"]) == 7       # "7 checks performed"
    assert len(results["warnings"]) == 5     # "5 items needing review"
    assert "Microsoft Word - Assignment-6" in results["checks"][0]["details"]
    assert "1 image resource(s) found" in results["checks"][6]["details"]


def test_accessible_test_like_matches_the_earlier_run(pdf_file):
    results = pdf_checker.scan_pdf(pdf_file(accessible_test_like()))
    assert results["pages"] == 1
    assert statuses(results) == [
        ("Document title", "REVIEW"),        # the file had no title
        ("Document language", "FOUND"),
        ("PDF structure", "FOUND"),
        ("Page 1 text", "FOUND"),
        ("Page 1 images", "INFO"),
    ]
    assert "en" in results["checks"][1]["details"]


# --- the report schema must not change ----------------------------------------------
def test_result_schema_is_unchanged(pdf_file):
    results = pdf_checker.scan_pdf(pdf_file(make_pdf(pages=3)))
    assert set(results) == {"file", "pages", "checks", "warnings"}
    assert results["file"] == "sample.pdf"
    for check in results["checks"]:
        assert set(check) == {"check", "status", "details"}
        assert check["status"] in {"FOUND", "REVIEW", "INFO"}
    assert len(results["checks"]) == 3 + 2 * 3   # title, language, structure + 2 per page


def test_warnings_are_exactly_the_review_details(pdf_file):
    results = pdf_checker.scan_pdf(pdf_file(problemset6_like()))
    review_details = [c["details"] for c in results["checks"] if c["status"] == "REVIEW"]
    assert results["warnings"] == review_details


def test_display_name_overrides_the_file_name(pdf_file):
    results = pdf_checker.scan_pdf(pdf_file(make_pdf()), display_name="report.pdf")
    assert results["file"] == "report.pdf"


def test_scan_is_deterministic(pdf_file):
    path = pdf_file(problemset6_like())
    assert pdf_checker.scan_pdf(path) == pdf_checker.scan_pdf(path)


# --- command-line behavior ----------------------------------------------------------
def test_cli_prints_the_same_report_and_saves_json(pdf_file, capsys):
    path = pdf_file(problemset6_like(), "problemset6.pdf")
    results = pdf_checker.check_pdf(str(path))
    out = capsys.readouterr().out

    assert "PDF ACCESSIBILITY CHECKER" in out
    assert "PDF opened successfully!" in out
    assert "Number of pages: 2" in out
    assert "\nChecking page 1...\nPage 1 text: No extractable text found." in out
    assert "Page 2 images: 1 image resource(s) found." in out
    assert "Checks performed: 7" in out
    assert "Items needing review: 5" in out
    assert "It does not certify ADA or WCAG compliance." in out

    report = path.with_name("problemset6_accessibility_report.json")
    assert report.exists()
    assert json.loads(report.read_text(encoding="utf-8")) == results


def test_cli_can_skip_writing_the_report(pdf_file):
    path = pdf_file(make_pdf(), "quiet.pdf")
    pdf_checker.check_pdf(str(path), write_report=False)
    assert not path.with_name("quiet_accessibility_report.json").exists()


def test_cli_reports_a_missing_file_without_crashing(tmp_path, capsys):
    assert pdf_checker.check_pdf(str(tmp_path / "missing.pdf")) is None
    assert "rror" in capsys.readouterr().out


def test_scan_pdf_raises_for_a_missing_file(tmp_path):
    with pytest.raises(Exception):
        pdf_checker.scan_pdf(str(tmp_path / "missing.pdf"))
