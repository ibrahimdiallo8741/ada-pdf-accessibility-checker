# Project Milestones & Evolution Roadmap

> **Executive Summary**: This document tracks the development progression of the ADA Accessibility Compliance Checker across completed prototype milestones and prioritizes planned post-prototype technical enhancements. *(Note: Milestones are tracked independently of academic assignment phases).*

---

## 1. Prototype Milestone Completion Record

| Milestone | Scope & Deliverables | Status | Verification Evidence |
|---|---|---|---|
| **Milestone 1: Core Screening Domain** | • Pure rule-based checks (`core/checks.py`)<br/>• Dual-engine coordinator (`core/checker.py`)<br/>• Strongly typed dataclasses (`core/models.py`)<br/>• Interactive CLI frontend (`pdf_checker.py`) | **Completed** | • CLI successfully screens multi-page PDFs and generates standardized JSON reports.<br/>• Verified against test fixtures `accessible_test.pdf` and `altair.pdf`. |
| **Milestone 2: Automated Acceptance Testing** | • Acceptance test runner (`tests/runner.py`)<br/>• Curated test fixtures (`tests/fixtures/`)<br/>• Test case assertions (AC-01 through AC-18) | **Completed** | • Automated test suite passes 25/25 assertions (`uv run python -m tests.runner`).<br/>• Standardized `TestSuiteSummary` schema. |
| **Milestone 3: Web Application & UI** | • FastAPI asynchronous backend (`web/app.py`)<br/>• In-memory job tracking with 1h TTL (`web/storage.py`)<br/>• Responsive web UI with drag-and-drop (`web/templates/`, `web/static/`)<br/>• In-browser acceptance test trigger (`/api/test-runner`) | **Completed** | • Asynchronous upload, polling, and report download verified in browser.<br/>• Dual `GET`/`POST` support for automated test execution. |
| **Milestone 4: Containerization & Cloud Deployment** | • Production containerization (`Dockerfile`)<br/>• Google Cloud Run serverless deployment<br/>• Cloudflare DNS & Full (Strict) SSL edge proxy<br/>• Edge caching for static web assets | **Completed** | • Cloud Run container boots with dynamic `${PORT:-8080}` and clean signal handling.<br/>• Cloudflare Universal SSL and caching active. |
| **Milestone 5: Webpage Accessibility Ingestion** | • Streaming HTML/DOM parser (`html.parser.HTMLParser`)<br/>• SSRF-guarded async fetcher (`core/web_fetcher.py`)<br/>• WCAG 2.1 Level A rules (title, lang, alt, headings, forms, bypass)<br/>• Dual-mode web portal UI | **Completed** | • Web screening verified: 4/4 web acceptance tests passing.<br/>• Validated on accessible, inaccessible, empty, and SSRF fixtures. |
| **Milestone 6: Deep Semantic Structure Traversal** | • Recursive `/StructTreeRoot` traversal (`core/pdf_struct_parser.py`)<br/>• `/RoleMap` resolution for custom tag aliases<br/>• Heading hierarchy validation (`/H1`..`/H6`)<br/>• Table integrity (`/Table` `/TH` `/TD`) & list consistency (`/L` `/LI`)<br/>• Figure `/Alt` text inspection | **Completed** | • Structure tree suite passes 5/5 assertions.<br/>• Validated on skipped heading hierarchies, unheadered tables, and empty lists. |
| **Milestone 7: Visual & Contrast Analysis** | • In-memory sRGB relative luminance and contrast ratio calculations (`core/contrast_analyzer.py`)<br/>• Text-to-background contrast ($4.5:1$ normal, $3:1$ large)<br/>• Underlying vector graphic fill detection<br/>• Web inline CSS contrast parity (`core/web_checks.py`) | **Completed** | • Contrast suite passes 5/5 assertions.<br/>• Validated on high/low contrast text, navy fill drawing backgrounds, and web inline styles. |
| **Milestone 8: Contextual AI Advisory Heuristics** | • Contextual AI heuristic advisory engine (`core/ai_evaluator.py`)<br/>• Google AI Studio direct REST integration (`gemini-3.5-flash-lite`)<br/>• 100% resilient offline local regex fallback (`_local_heuristic_analyzer`)<br/>• Sensory characteristics (`1.3.3`), uninformative titles (`2.4.2`), color reliance (`1.4.1`) | **Completed** | • AI heuristic suite passes 4/4 assertions.<br/>• Verified live inference (HTTP 200) and deterministic offline fallback. |
| **Spec v2 Testing Compliance & Unified Parity** | • Target-aware Model Coverage (`coverage.model` 18/18 items)<br/>• Live session statement tracking via `coverage.py`<br/>• Strict OpenAPI 3.1 Pydantic validation (`format: uri`, `minLength: 1`)<br/>• Web/PDF feature parity (tables, lists, forms, outlines, contrast) | **Completed** | • Cross-team test suite passes 4/4 assertions.<br/>• Overall test runner passes 47/47 assertions (`uv run python -m tests.runner`). |

---

## 2. Post-Prototype Evolution Milestones

### Milestone 5: Webpage Accessibility Ingestion & Screening (Completed)
- **Objective**: Re-expand the project scope to evaluate live web URLs and HTML DOM trees alongside PDF documents.
- **Key Capabilities**:
  - In-memory streaming HTML/DOM parser (`html.parser.HTMLParser`) for live web URL evaluation (`POST /api/scans/web`).
  - Strict SSRF guarding against loopback, link-local, and private subnets (`core/web_fetcher.py`).
  - Unified reporting schema accommodating both PDF and webpage accessibility findings (`core/models.py`).
  - Dual ingestion interface in the web portal (URL input field alongside PDF file drag-and-drop).
  - Automated HTML WCAG 2.1 AA checks: document title (`2.4.2`), language tags (`3.1.1`), image `alt` attributes (`1.1.1`), heading hierarchy (`1.3.1`), form input labels (`1.3.1`/`4.1.2`), and bypass landmarks / skip links (`2.4.1`).

### Milestone 6: Deep Semantic Structure Tree Traversal (Completed)
- **Objective**: Expand `/StructTreeRoot` validation from simple existence checking to full hierarchical tree parsing.
- **Key Capabilities**:
  - Recursive traversal of the PDF Structure Hierarchy (`/K` structure elements) in `core/pdf_struct_parser.py`.
  - Full `/RoleMap` alias resolution for custom document authoring tool tags.
  - Validation of heading nesting levels (e.g. flagging skipped heading levels like `<H1>` immediately followed by `<H3>`).
  - Table accessibility verification: detecting table elements (`<Table>`) and ensuring header cell tags (`<TH>`) are properly associated with data cells (`<TD>`).
  - List structural integrity (`<L>`, `<LI>`, `<Lbl>`, `<LBody>`).
  - Figure alternative text inspection (`/Figure` `/Alt` vs `/Artifact`).

### Milestone 7: Visual & Contrast Analysis (Completed)
- **Objective**: Implement visual rendering heuristics for visual accessibility criteria without writing raster files to disk.
- **Key Capabilities**:
  - In-memory sRGB relative luminance and contrast ratio calculations according to WCAG 2.1 AA specifications in `core/contrast_analyzer.py`.
  - Evaluates WCAG 2.1 AA Criterion 1.4.3 (Contrast Minimum: 4.5:1 for normal text, 3:1 for large text).
  - Inspects text spans via PyMuPDF alongside enclosing vector drawing rectangles (`page.get_drawings()`) to accurately establish background color.
  - Full feature parity on Web: parses inline CSS `color` and `background-color` styles to evaluate web text contrast (`core/web_checks.py::check_web_contrast`).

### Milestone 8: Contextual AI Heuristic Assessment & Advisory Engine (Completed)
- **Objective**: Augment the screening engine with contextual AI heuristics to assess qualitative accessibility barriers that cannot be settled deterministically.
- **Key Capabilities**:
  - *Direct REST Transport*: Direct HTTP client queries to Google AI Studio (`gemini-3.5-flash-lite`) via `httpx` with zero heavy SDK overhead.
  - *Sensory Instruction Detection*: Evaluates WCAG 1.3.3 by flagging instructions that rely solely on sensory characteristics like shape, color, or spatial orientation.
  - *Color-Only Reliance Screening*: Evaluates WCAG 1.4.1 by detecting sentences or data points communicated solely through color.
  - *Uninformative Title Detection*: Evaluates WCAG 2.4.2 & 2.4.6 by identifying generic software placeholders (e.g. `"Untitled Document"`, `"Scan001"`, `"Report"`).
  - *100% Resilient Local Fallback*: Built-in regex heuristic analyzer (`_local_heuristic_analyzer`) guarantees uninterrupted operation with identical finding schemas when network is offline or API keys are unavailable.
  - *Strict Invariant*: All AI findings are advisory (`analysis_method="AI"`, `status="Needs Human Review"`), never certifying compliance.

---

## 3. Required Testing Enhancements (AC & REQ Verification Roadmap)

To ensure all Acceptance Criteria (AC-01 through AC-18) and core Requirements (REQ-01 through REQ-18) are robustly satisfied under edge cases and scaling, the following test suites are planned for implementation:

### 3.1 Edge-Case & Boundary Fixtures (AC-01, AC-02, AC-11, REQ-03, REQ-12)
- [x] **Zero-Byte & Corrupted Header Rejection**: Test suite verifying that 0-byte files, truncated PDF headers, or corrupted cross-reference tables (`/XRef`) return clean `Could Not Evaluate` findings rather than unhandled server errors.
- [x] **Encrypted & Password-Protected Documents**: Fixture testing documents protected with user/owner passwords to verify that password-locked files are intercepted gracefully with remediation guidance ("Provide unencrypted document").
- [x] **Extreme Scale / Multi-Page Stress Test**: Benchmark test running against a 100+ page document to assert sub-linear memory consumption and ensure processing times remain within Cloud Run HTTP request timeout thresholds (60s).
- [x] **Page Boundary Accuracy (AC-15)**: Multi-page fixture asserting that findings reported on Page $N$ exactly map to Page $N$ without 0-index/1-index off-by-one errors.

### 3.2 Security & Zero-Disk Retention Verification (AC-02, REQ-16, REQ-17)
- [x] **Filesystem Isolation Audit**: Automated test using filesystem watchers or OS path monitoring during a screening run to assert that 0 bytes are written to `/tmp`, the project directory, or any local storage during upload and analysis.
- [x] **Memory Buffer Deallocation**: Heap inspection test asserting that `io.BytesIO` references and PyMuPDF document instances are garbage-collected immediately upon job completion.

### 3.3 Asynchronous Concurrency & TTL Expiration (AC-05, AC-06, AC-10, REQ-10)
- [x] **Concurrent Ingestion Stress Test**: Asynchronous harness dispatching 10 simultaneous upload requests to `/api/scans/pdf` to verify thread safety in [`web/storage.py`](../web/storage.py) and absence of race conditions.
- [x] **Job Eviction / TTL Automated Verification (AC-13)**: Unit test with simulated timestamps asserting that completed scan jobs older than 3600 seconds (1 hour) are evicted from memory.
- [x] **API Contract & HTTP Status Suite**: Automated verification of HTTP responses: `202 Accepted` on upload, `200 OK` on polling/results, `404 Not Found` on unknown job IDs, and `422 Unprocessable Entity` on non-PDF uploads.

### 3.4 Cross-Team Testing ConOps Verification (docs/student-facing-spec.md)
- [x] **System Role Lifecycle**: Test verifying `POST /system/test/setup` creates and returns `session_id`, prevents duplicates (`409 Conflict`), and `GET /system/test/report` serves code coverage structure.
- [x] **Dual-Mount API Conformity**: Test verifying project screening API is reachable under both `/api` and `/system/api` base URLs.
- [x] **Tester Communication Handling**: Test asserting URL scheme validation (`400`) and target connection timeout/unreachable classification (`source: communication`).
- [x] **Tester Execution & Coverage Suite**: Full async test executing T-01 through T-10, asserting outcomes, component coverage (4/4), and system coverage (10/10).

### 3.5 Milestone-Specific Verification Suites
- [x] **Milestone 5 (Web Scanning)**: Mock HTTP fixtures evaluating accessible vs. inaccessible HTML DOM trees (validating form labels, heading hierarchy, skip navigation, and ARIA attributes in `tests/test_web_scanner.py`).
- [x] **Milestone 6 (Structure Trees)**: Curated PDF fixtures with malformed tag hierarchies (skipped heading levels `<H1>` to `<H3>`, unheadered tables, broken list nesting, figure `/Alt` text in `tests/test_phase5_milestones.py`).
- [x] **Milestone 7 (Contrast Engine)**: Relative luminance formulas, sRGB text-to-background contrast ($21:1$, $4.5:1$, $3.0:1$), background vector drawing fills, and Web inline CSS contrast.
- [x] **Milestone 8 (AI Heuristic Isolation)**: Sensory characteristics, uninformative titles, and color reliance tested with live Google AI Studio REST calls and deterministic offline fallback.

---

## 4. Phase 5 Design Requirements Traceability Matrix (`coverage.model`)

In accordance with [`docs/student-facing-specv2.md`](student-facing-specv2.md) and [`docs/SPEC_V2_DIFF_ANALYSIS.md`](SPEC_V2_DIFF_ANALYSIS.md), all 18 design requirements established for Phase 5 are fully implemented and evaluated in the automated test suite:

| REQ ID | Requirement Title | Primary Implementation Source | Verification Test Cases | Status |
|---|---|---|---|:---:|
| **REQ-01** | Webpage Accessibility Ingestion | `core/web_fetcher.py`, `core/web_checker.py` | `test_web_accessible_fixture`, `test_web_ssrf_and_invalid_schemes` | **Covered** |
| **REQ-02** | PDF Multipart Ingestion Stream | `web/app.py`, `core/checker.py` | `test_accessible_fixture`, `test_in_memory_bytes` | **Covered** |
| **REQ-03** | Core Rule Evaluation & Scaling | `core/checks.py`, `core/checker.py` | `test_scale_multipage`, `fixture_altair.pdf`, `fixture_long.pdf` | **Covered** |
| **REQ-04** | Semantic Structure & Contrast | `core/pdf_struct_parser.py`, `core/contrast_analyzer.py` | `test_m6_heading_hierarchy_skipped_levels`, `test_m7_text_contrast_passing_and_failing`, `test_p53_web_contrast_passing` | **Covered** |
| **REQ-05** | Image Alternative Content | `core/checks.py`, `core/web_checks.py`, `core/pdf_struct_parser.py` | `test_image_resource_detection`, `test_web_inaccessible_fixture`, `test_m6_figure_alt_text_evaluation` | **Covered** |
| **REQ-06** | Contextual Advisory Heuristics | `core/ai_evaluator.py` | `test_m8_sensory_characteristics_detection`, `test_m8_uninformative_title_detection`, `test_m8_color_only_reliance_detection`, `test_m8_offline_resilience_fallback` | **Covered** |
| **REQ-07** | Finding Traceability & Location | `core/models.py`, `core/checker.py` | `test_finding_traceability_schema` | **Covered** |
| **REQ-08** | Remediation Completeness | `core/checks.py`, `core/web_checks.py`, `core/ai_evaluator.py` | `test_remediation_guidance_completeness` | **Covered** |
| **REQ-09** | Remediation Guidance Quality | `core/checks.py`, `core/pdf_struct_parser.py` | `test_remediation_guidance_completeness` | **Covered** |
| **REQ-10** | Summary Calculation & Concurrency | `core/checker.py`, `web/storage.py` | `test_summary_calculation_integrity`, `test_concurrent_ingestion_stress` | **Covered** |
| **REQ-11** | Robust Error Handling & SSRF | `core/web_fetcher.py`, `core/checker.py` | `test_malformed_corrupted_input`, `test_web_ssrf_and_invalid_schemes` | **Covered** |
| **REQ-12** | Corrupted Stream Resilience | `core/checker.py`, `core/web_checker.py` | `test_zero_byte_rejection`, `test_corrupt_header_rejection`, `test_web_empty_html_resilience` | **Covered** |
| **REQ-13** | Job Lifecycle & Expiration | `web/storage.py` | `test_job_ttl_expiration` | **Covered** |
| **REQ-14** | WCAG 2.1 AA Technical Accuracy | `core/checks.py`, `core/contrast_analyzer.py`, `core/pdf_struct_parser.py` | `test_m7_contrast_math_unit_tests`, `test_m6_table_structural_integrity`, `test_m6_list_consistency` | **Covered** |
| **REQ-15** | Unified API & Spec Compliance | `web/app.py`, `web/cross_team_routes.py` | `test_api_contract_and_statuses`, `test_system_dual_mount_api`, `test_system_setup_and_report_lifecycle` | **Covered** |
| **REQ-16** | Zero-Disk Privacy Invariant | `core/checker.py`, `web/app.py` | `test_filesystem_isolation_audit`, `test_memory_buffer_deallocation` | **Covered** |
| **REQ-17** | Data Minimization Invariant | `core/checker.py`, `web/storage.py` | `test_filesystem_isolation_audit`, `test_job_ttl_expiration` | **Covered** |
| **REQ-18** | Repeatability & Verification | `core/checker.py`, `tests/runner.py` | `test_deterministic_repeatability`, `test_tester_run_and_report_lifecycle` | **Covered** |

**Total Design Model Requirements**: 18  
**Total Evaluated Requirements**: 18  
**Model Coverage Metric**: `18 / 18` (100.0%)

