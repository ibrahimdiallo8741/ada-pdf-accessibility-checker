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

---

## 2. Post-Prototype Evolution Milestones

### Milestone 5: Webpage Accessibility Ingestion & Screening
- **Objective**: Re-expand the project scope to evaluate live web URLs and HTML DOM trees alongside PDF documents (potentially incorporated into the prototype if time permits).
- **Key Capabilities**:
  - Headless browser rendering integration (`Playwright` / `axe-core`) or lightweight HTML/DOM parser for live web URL evaluation.
  - Unified reporting schema accommodating both PDF and webpage accessibility findings.
  - Dual ingestion interface in the web portal (URL input field alongside PDF file drag-and-drop).
  - Automated HTML WCAG 2.1 AA checks: document title, language tags, image `alt` attributes, heading hierarchy (`<h1>`–`<h6>`), form input labels, and ARIA landmark roles.

### Milestone 6: Deep Semantic Structure Tree Traversal
- **Objective**: Expand `/StructTreeRoot` validation from simple existence checking to full hierarchical tree parsing.
- **Key Capabilities**:
  - Recursive traversal of the PDF Structure Hierarchy (`/K` structure elements).
  - Validation of heading nesting levels (e.g. flagging skipped heading levels like `<H1>` immediately followed by `<H3>`).
  - Table accessibility verification: detecting table elements (`<Table>`) and ensuring header cell tags (`<TH>`) are properly associated with data cells (`<TD>`).
  - List structural integrity (`<L>`, `<LI>`, `<Lbl>`, `<LBody>`).

### Milestone 7: Visual & Contrast Analysis
- **Objective**: Implement visual rendering heuristics for visual accessibility criteria.
- **Key Capabilities**:
  - Page rasterization contrast calculation to evaluate WCAG 2.1 AA Criterion 1.4.3 (Contrast Minimum: 4.5:1 for normal text, 3:1 for large text).
  - Extraction and inspection of vector graphics and paths (PDF drawings not captured by XObject raster extraction).

### Milestone 8: Contextual AI Heuristic Assessment & Alt-Text (REQ-06)
- **Objective**: Augment the screening engine with external cloud AI (LLM / multimodal vision) models to assess accessibility heuristics that cannot be settled deterministically or programmatically.
- **Key Capabilities**:
  - *Contextual Alt-Text Generation*: Extract cropped image regions alongside surrounding paragraph text context and query vision models for candidate descriptions (`WCAG 1.1.1`).
  - *Sensory Instruction Detection*: Semantic text analysis to flag instructions that rely solely on sensory characteristics like shape, color, or spatial orientation (`WCAG 1.3.3`).
  - *Color-Only Reliance Screening*: Multimodal vision assessment of diagrams, charts, and forms to flag states communicated solely through color (`WCAG 1.4.1`).
  - *Content Meaningfulness Heuristics*: AI evaluation of title descriptiveness (`WCAG 2.4.2`), contextual link purpose (`WCAG 2.4.4`), and heading/label clarity (`WCAG 2.4.6`).
  - *Strict Architectural Invariant*: AI suggestions must always be labeled as advisory human recommendations, never automated pass/fail compliance certifications.

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
- [ ] **Milestone 5 (Web Scanning)**: Mock HTTP fixtures evaluating accessible vs. inaccessible HTML DOM trees (validating form labels, heading hierarchy, skip navigation, and ARIA attributes).
- [ ] **Milestone 6 (Structure Trees)**: Curated PDF fixtures with malformed tag hierarchies (e.g., `<Table>` lacking `<TR>`, skipped heading levels `<H1>` immediately followed by `<H3>`).
- [ ] **Milestone 7 (Contrast Engine)**: Synthetic bitmap test fixtures with known RGB color pairs to verify contrast ratio formula accuracy ($21:1$, $4.5:1$, $3.0:1$, and failing ratios).
- [ ] **Milestone 8 (AI Heuristic Isolation)**: Mock AI harness testing fallback behavior when cloud AI endpoints time out or fail, asserting that deterministic checks complete without disruption.
