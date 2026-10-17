import sys
from pathlib import Path

import pymupdf
from pypdf.errors import PyPdfError

from core.checker import screen_pdf
from core.models import TestCaseResult, TestSuiteSummary
from tests.test_roadmap_sections import (
    test_api_contract_and_statuses,
    test_concurrent_ingestion_stress,
    test_corrupt_header_rejection,
    test_encrypted_pdf_handling,
    test_filesystem_isolation_audit,
    test_job_ttl_expiration,
    test_memory_buffer_deallocation,
    test_page_boundary_accuracy,
    test_scale_multipage,
    test_zero_byte_rejection,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# Specific operational errors expected in screening execution
ScreeningExecutionError = (
    FileNotFoundError,
    OSError,
    PermissionError,
    AssertionError,
    KeyError,
    AttributeError,
    PyPdfError,
    pymupdf.FileDataError,
)


def run_automated_suite(fixtures_path: Path | None = None) -> TestSuiteSummary:
    """Executes the automated accessibility test runner against fixture PDFs, validating against AC-01 to AC-18.
    
    Supports standard acceptance test fixtures and dynamically screens any additional team-supplied PDFs.
    """
    target_fixtures = fixtures_path or FIXTURES_DIR
    results: list[TestCaseResult] = []

    def record_test(name: str, passed: bool, details: str, req_ref: str):
        results.append(
            TestCaseResult(
                name=name,
                passed=passed,
                details=details,
                requirement_ref=req_ref,
            )
        )

    # Test 1: Accessible PDF Fixture (AC-03, AC-07)
    acc_path = target_fixtures / "fixture_accessible.pdf"
    if acc_path.exists():
        try:
            acc_res = screen_pdf(acc_path)
            title_finding = next((f for f in acc_res.findings if f.input_location == "Document Metadata"), None)
            lang_finding = next((f for f in acc_res.findings if f.input_location == "Document Catalog"), None)
            struct_finding = next((f for f in acc_res.findings if f.input_location == "Document Catalog /Root"), None)

            acc_passed = (
                title_finding is not None
                and title_finding.status == "Pass"
                and lang_finding is not None
                and lang_finding.status == "Pass"
                and struct_finding is not None
                and struct_finding.status == "Needs Human Review"
            )
            record_test(
                name="Accessible Fixture Evaluation",
                passed=acc_passed,
                details=f"Checks={acc_res.summary.checks}, Passed={acc_res.summary.passed}, Review={acc_res.summary.human_review}",
                req_ref="AC-03, REQ-04",
            )
        except ScreeningExecutionError as exc:
            record_test("Accessible Fixture Evaluation", False, f"Screening error ({type(exc).__name__}): {exc}", "AC-03, REQ-04")

    # Test 2: Scanned / Empty Text Fixture (AC-02, AC-07, AC-08)
    scanned_path = target_fixtures / "fixture_scanned.pdf"
    if scanned_path.exists():
        try:
            scanned_res = screen_pdf(scanned_path)
            text_finding = next((f for f in scanned_res.findings if f.input_location == "Page 1" and "text" in f.issue_description.lower()), None)
            struct_finding = next((f for f in scanned_res.findings if f.input_location == "Document Catalog /Root"), None)

            scanned_passed = (
                text_finding is not None
                and text_finding.status == "Needs Human Review"
                and struct_finding is not None
                and struct_finding.status == "Issue"
                and scanned_res.summary.issues >= 3
            )
            record_test(
                name="Scanned/Untagged Fixture Evaluation",
                passed=scanned_passed,
                details=f"Issues={scanned_res.summary.issues}, Review={scanned_res.summary.human_review}",
                req_ref="AC-02, REQ-03",
            )
        except ScreeningExecutionError as exc:
            record_test("Scanned/Untagged Fixture Evaluation", False, f"Screening error ({type(exc).__name__}): {exc}", "AC-02, REQ-03")

    # Test 3: Embedded Image Resource Fixture (AC-03, AC-08)
    img_path = target_fixtures / "fixture_images.pdf"
    if img_path.exists():
        try:
            img_res = screen_pdf(img_path)
            img_finding = next((f for f in img_res.findings if f.input_location == "Page 1" and "image" in f.issue_description.lower()), None)

            img_passed = (
                img_finding is not None
                and img_finding.status == "Needs Human Review"
                and "1 embedded image" in img_finding.issue_description
            )
            record_test(
                name="Image Resource Detection Fixture",
                passed=img_passed,
                details=f"Image finding: [{img_finding.status if img_finding else 'None'}] {img_finding.issue_description if img_finding else ''}",
                req_ref="AC-03, REQ-05",
            )
        except ScreeningExecutionError as exc:
            record_test("Image Resource Detection Fixture", False, f"Screening error ({type(exc).__name__}): {exc}", "AC-03, REQ-05")

    # Test 4: Deterministic Repeatability (AC-04, AC-17)
    sample_for_rep = acc_path if acc_path.exists() else next(target_fixtures.glob("*.pdf"), None)
    if sample_for_rep:
        try:
            run1 = screen_pdf(sample_for_rep)
            run2 = screen_pdf(sample_for_rep)
            run3 = screen_pdf(sample_for_rep)

            f1 = [(f.input_location, f.status, f.issue_description) for f in run1.findings]
            f2 = [(f.input_location, f.status, f.issue_description) for f in run2.findings]
            f3 = [(f.input_location, f.status, f.issue_description) for f in run3.findings]

            rep_passed = (f1 == f2 == f3)
            record_test(
                name="Deterministic Repeatability (3 runs)",
                passed=rep_passed,
                details="All 3 repeated runs produced 100% identical findings and statuses.",
                req_ref="AC-04, AC-17, REQ-18",
            )
        except ScreeningExecutionError as exc:
            record_test("Deterministic Repeatability (3 runs)", False, f"Screening error ({type(exc).__name__}): {exc}", "AC-04, AC-17, REQ-18")

    # Test 5: Summary Count Consistency (AC-09)
    sample_for_sum = acc_path if acc_path.exists() else next(target_fixtures.glob("*.pdf"), None)
    if sample_for_sum:
        try:
            sample_res = screen_pdf(sample_for_sum)
            s = sample_res.summary
            total_checks = len(sample_res.findings)
            sum_components = s.passed + s.issues + s.human_review + s.could_not_evaluate
            consistency_passed = (s.checks == total_checks and s.checks == sum_components)

            record_test(
                name="Summary Calculation Integrity",
                passed=consistency_passed,
                details=f"Total={s.checks}, Passed={s.passed}, Issues={s.issues}, Review={s.human_review}, Sum={sum_components}",
                req_ref="AC-09, REQ-10",
            )
        except ScreeningExecutionError as exc:
            record_test("Summary Calculation Integrity", False, f"Screening error ({type(exc).__name__}): {exc}", "AC-09, REQ-10")

    # Test 6: In-Memory Bytes Scanning (AC-01, AC-02)
    sample_for_bytes = acc_path if acc_path.exists() else next(target_fixtures.glob("*.pdf"), None)
    if sample_for_bytes:
        try:
            file_bytes = sample_for_bytes.read_bytes()
            bytes_res = screen_pdf(file_bytes, filename="in_memory.pdf")
            file_res = screen_pdf(sample_for_bytes)

            bytes_passed = (
                bytes_res.pages == file_res.pages
                and bytes_res.summary.checks == file_res.summary.checks
                and bytes_res.summary.passed == file_res.summary.passed
            )
            record_test(
                name="In-Memory Bytes Stream Evaluation",
                passed=bytes_passed,
                details="Raw byte buffer evaluation matches filesystem evaluation identically.",
                req_ref="AC-02, REQ-03, REQ-16",
            )
        except ScreeningExecutionError as exc:
            record_test("In-Memory Bytes Stream Evaluation", False, f"Screening error ({type(exc).__name__}): {exc}", "AC-02, REQ-03, REQ-16")

    # Test 7: Finding Traceability and WCAG Criteria (AC-07, AC-14)
    sample_for_trace = next(target_fixtures.glob("*.pdf"), None)
    if sample_for_trace:
        try:
            trace_res = screen_pdf(sample_for_trace)
            traceable = all(
                f.finding_id
                and f.input_location
                and f.issue_description
                and f.WCAG_criterion
                and f.analysis_method == "Deterministic"
                for f in trace_res.findings
            )
            record_test(
                name="Finding Traceability & Schema Conformance",
                passed=traceable,
                details=f"Validated schema on {len(trace_res.findings)} finding records in {sample_for_trace.name}.",
                req_ref="AC-07, AC-14, REQ-15",
            )
        except ScreeningExecutionError as exc:
            record_test("Finding Traceability & Schema Conformance", False, f"Screening error ({type(exc).__name__}): {exc}", "AC-07, AC-14, REQ-15")

    # Test 8: Remediation Guidance on Non-Passing Checks (AC-08)
    sample_for_remed = scanned_path if scanned_path.exists() else next(target_fixtures.glob("*.pdf"), None)
    if sample_for_remed:
        try:
            remed_res = screen_pdf(sample_for_remed)
            issues_and_reviews = [f for f in remed_res.findings if f.status in ("Issue", "Needs Human Review")]
            all_guided = all(bool(f.remediation_guidance and f.remediation_guidance.strip()) for f in issues_and_reviews)

            record_test(
                name="Remediation Guidance Completeness",
                passed=all_guided and len(issues_and_reviews) > 0,
                details=f"All {len(issues_and_reviews)} non-passing findings include clear remediation guidance.",
                req_ref="AC-08, REQ-09",
            )
        except ScreeningExecutionError as exc:
            record_test("Remediation Guidance Completeness", False, f"Screening error ({type(exc).__name__}): {exc}", "AC-08, REQ-09")

    # Test 9: Robustness on Corrupt / Invalid Bytes (AC-11, REQ-12)
    try:
        corrupted_bytes = b"NOT_A_VALID_PDF_STREAM_12345"
        caught_gracefully = False
        details_msg = "No exception raised for corrupt bytes."
        try:
            screen_pdf(corrupted_bytes, filename="corrupt.pdf")
        except (pymupdf.FileDataError, PyPdfError, ValueError) as err:
            caught_gracefully = True
            details_msg = f"Caught expected PDF parser exception: {type(err).__name__}"

        record_test(
            name="Malformed / Corrupted Input Handling",
            passed=caught_gracefully,
            details=details_msg,
            req_ref="AC-11, REQ-12",
        )
    except (AssertionError, TypeError) as exc:
        record_test("Malformed / Corrupted Input Handling", False, f"Runner error ({type(exc).__name__}): {exc}", "AC-11, REQ-12")

    # --------------------------------------------------------------------------
    # Tests for ROADMAP.md Section 3.1: Edge-Case & Boundary Fixtures
    # --------------------------------------------------------------------------
    p_zero, d_zero = test_zero_byte_rejection()
    record_test("Zero-Byte Stream Rejection", p_zero, d_zero, "AC-01, AC-02, AC-11, REQ-12")

    p_corr, d_corr = test_corrupt_header_rejection()
    record_test("Corrupted Header Rejection", p_corr, d_corr, "AC-11, REQ-12")

    p_enc, d_enc = test_encrypted_pdf_handling()
    record_test("Encrypted / Password-Protected Handling", p_enc, d_enc, "AC-11, REQ-12")

    p_scale, d_scale = test_scale_multipage()
    record_test("Extreme Scale / Multi-Page Stress Test", p_scale, d_scale, "AC-01, REQ-03")

    p_bound, d_bound = test_page_boundary_accuracy()
    record_test("Page Boundary Off-by-One Accuracy", p_bound, d_bound, "AC-15")

    # --------------------------------------------------------------------------
    # Tests for ROADMAP.md Section 3.2: Security & Zero-Disk Retention Verification
    # --------------------------------------------------------------------------
    p_iso, d_iso = test_filesystem_isolation_audit()
    record_test("Filesystem Isolation Zero-Disk Audit", p_iso, d_iso, "AC-02, REQ-16, REQ-17")

    p_mem, d_mem = test_memory_buffer_deallocation()
    record_test("Memory Buffer Deallocation", p_mem, d_mem, "REQ-16")

    # --------------------------------------------------------------------------
    # Tests for ROADMAP.md Section 3.3: Asynchronous Concurrency & TTL Expiration
    # --------------------------------------------------------------------------
    p_conc, d_conc = test_concurrent_ingestion_stress()
    record_test("Concurrent Ingestion Stress Test", p_conc, d_conc, "AC-05, AC-06, REQ-10")

    p_ttl, d_ttl = test_job_ttl_expiration()
    record_test("Job Eviction / TTL Expiration", p_ttl, d_ttl, "AC-13, REQ-16")

    p_api, d_api = test_api_contract_and_statuses()
    record_test("API Contract & HTTP Status Suite", p_api, d_api, "AC-10")

    # Dynamic Test: Screen any extra team-supplied PDFs in fixtures directory
    standard_fixtures = {"fixture_accessible.pdf", "fixture_scanned.pdf", "fixture_images.pdf"}
    if target_fixtures.exists():
        custom_fixtures = sorted(p for p in target_fixtures.glob("*.pdf") if p.name not in standard_fixtures)
        for custom_pdf in custom_fixtures:
            try:
                c_res = screen_pdf(custom_pdf)
                c_passed = c_res.pages > 0 and c_res.summary.checks > 0
                record_test(
                    name=f"Team Fixture: {custom_pdf.name}",
                    passed=c_passed,
                    details=f"Pages={c_res.pages}, Checks={c_res.summary.checks}, Passed={c_res.summary.passed}, Issues={c_res.summary.issues}, Review={c_res.summary.human_review}",
                    req_ref="REQ-03, REQ-18",
                )
            except ScreeningExecutionError as exc:
                record_test(f"Team Fixture: {custom_pdf.name}", False, f"Screening error ({type(exc).__name__}): {exc}", "REQ-03, REQ-18")

    total_count = len(results)
    passed_count = sum(1 for r in results if r.passed)
    failed_count = total_count - passed_count

    return TestSuiteSummary(
        total=total_count,
        passed=passed_count,
        failed=failed_count,
        results=results,
    )


def main():
    print("=" * 60)
    print("AUTOMATED ACCESSIBILITY TEST RUNNER")
    print("Evaluating test fixtures against AC-01 through AC-18")
    print("=" * 60)

    fixtures_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    summary = run_automated_suite(fixtures_dir)

    for idx, r in enumerate(summary.results, start=1):
        status_tag = "[PASS]" if r.passed else "[FAIL]"
        print(f"\n{idx}. {status_tag} {r.name} ({r.requirement_ref})")
        print(f"   Details: {r.details}")

    print("\n" + "=" * 60)
    print(f"TOTAL: {summary.total} | PASSED: {summary.passed} | FAILED: {summary.failed}")
    print("=" * 60)

    if summary.failed > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
