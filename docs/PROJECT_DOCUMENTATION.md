# Technical Documentation — Accessibility Checker

## 1. Current Featureset

The codebase provides an automated accessibility screening engine, asynchronous REST API, interactive web portal, and test runner for Portable Document Format (PDF) files:

- **CLI File Ingestion (`pdf_checker.py`):** Accepts relative or absolute file paths from interactive standard input; automatically strips surrounding quotes and whitespace.
- **Dual PDF Engine Parser (`core/checker.py`):**
  - `pymupdf`: Handles document loading, page traversal, text extraction, document-level metadata reading, language attribute retrieval, and raw image XObject discovery.
  - `pypdf`: Traverses the low-level PDF document catalog dictionary (`/Root` via `reader.root_object`) to detect structural markup elements.
- **Dual Ingestion Sources (Paths & In-Memory Bytes):** `screen_pdf` accepts both filesystem paths and raw `bytes` buffers, allowing direct memory screening for web uploads without writing temporary files to disk.
- **Standardized Domain Contracts (`core/models.py`):** Strongly-typed dataclasses (`Finding`, `ScanSummary`, `ScanResult`, `TestCaseResult`, `TestSuiteSummary`) adhering directly to the `api/api.md` schema with native JSON serialization.
- **FastAPI Web Service (`web/app.py`):** Asynchronous REST API strictly implementing `api/api.md` endpoints (`POST /api/scans/pdf`, `POST /api/scans/web`, `GET /api/scans/{scan_id}/status`, `GET /api/scans/{scan_id}/results`, `POST /api/test-runner`) with interactive Swagger documentation (`/docs`).
- **In-Memory Scan Job Store (`web/storage.py`):** Thread-safe asynchronous job tracker enforcing a 1-hour expiration policy for uploaded file data (REQ-16).
- **Interactive Browser Portal (`web/templates/index.html`):** Single-page web application featuring drag-and-drop PDF uploads, client-side size checks, live status polling, tabular findings display, JSON report export, and one-click acceptance test execution.
- **Document Metadata Verification:** Screens for presence of title strings in the document information dictionary.
- **Document Language Verification:** Screens for a default natural language tag in the document catalog.
- **Document Structure Tag Detection:** Screens for structural tagging presence via the document catalog's structure tree root (`/StructTreeRoot`).
- **Text Layer Extraction:** Checks every page for non-whitespace character extraction to identify potential raster-only pages lacking an OCR layer.
- **Image Resource Discovery:** Enumerates embedded raster image objects per page.
- **Remediation Guidance:** Generates actionable remediation instructions for all non-passing checks.
- **Automated Test Runner Subsystem (`tests/runner.py`):** Comprehensive automated test harness running 9 acceptance assertions against curated test fixtures (`tests/fixtures/`) validating AC-01 through AC-18.
- **Automated JSON Export:** Generates an output JSON file (`<input_stem>_accessibility_report.json`) containing execution metrics, check statuses, and review warnings.

---

## 2. Implemented Checks: PDF Documents

The codebase implements 5 automated screening checks for PDF documents. Each check maps to specific WCAG 2.1 Success Criteria and assigns one of the standardized statuses: `Pass`, `Issue`, `Needs Human Review`, or `Could Not Evaluate`.

### Check 1: Document Title
- **Identifier in Code:** `check_title` (Finding ID: `F001`)
- **Scope:** Document-level
- **Relevant WCAG 2.1 Section:** **Success Criterion 2.4.2 Page Titled (Level A)**
- **Relevant PDF Technique:** **PDF18:** Specifying the document title using the Title entry in the document information dictionary of a PDF document
- **Implementation:**
  - Inspects `metadata.get("title")`.
  - Flags `Pass` if title string contains non-whitespace characters.
  - Flags `Issue` if key is missing, empty, or whitespace-only. Provides remediation guidance.
- **Technical Scope & Boundaries:**
  - Confirms text exists within the `/Title` metadata field.
  - Does not evaluate whether title text accurately describes document topic or purpose.
  - Does not verify catalog entry `/ViewerPreferences` setting `/DisplayDocTitle` (which controls whether PDF viewers render the title or filename in the application window bar).

### Check 2: Document Language
- **Identifier in Code:** `check_language` (Finding ID: `F002`)
- **Scope:** Document-level
- **Relevant WCAG 2.1 Section:** **Success Criterion 3.1.1 Language of Page (Level A)**
- **Relevant PDF Technique:** **PDF16:** Setting the default language using the `/Lang` entry in the document catalog of a PDF document
- **Implementation:**
  - Inspects `document.language` (or catalog `/Lang` entry).
  - Flags `Pass` if a language string exists.
  - Flags `Issue` if attribute is empty or `None`. Provides remediation guidance.
- **Technical Scope & Boundaries:**
  - Confirms existence of a declared language code.
  - Does not parse or validate code syntax against RFC 5646 / BCP 47.
  - Does not verify if declared language matches primary textual content.
  - Does not detect inline passages in other languages (WCAG 3.1.2 Language of Parts).

### Check 3: PDF Structure Tree
- **Identifier in Code:** `check_structure` (Finding ID: `F003`)
- **Scope:** Document-level
- **Relevant WCAG 2.1 Section:** **Success Criterion 1.3.1 Info and Relationships (Level A)**
- **Relevant PDF Techniques:**
  - **PDF9:** Providing headings by marking content with heading tags in PDF documents
  - **PDF20:** Using Adobe Acrobat to create tagged PDF
  - **PDF3:** Ensuring correct tab and reading order in PDF documents
- **Implementation:**
  - Inspects dictionary keys in `reader.root_object`.
  - Flags `Needs Human Review` if `/StructTreeRoot` key is present, confirming tag existence while signaling that tag quality requires review.
  - Flags `Issue` if `/StructTreeRoot` key is missing. Provides remediation guidance.
- **Technical Scope & Boundaries:**
  - Confirms document catalog contains a structure tree root pointer.
  - Does not traverse the tree or validate tag semantics (`<H1>`, `<P>`, `<Table>`, `<L>`, `<Figure>`).
  - Does not verify logical reading order or tab navigation sequences.

### Check 4: Extractable Text
- **Identifier in Code:** `check_page_text` (Finding ID: `F004+`)
- **Scope:** Page-level (executed for each page)
- **Relevant WCAG 2.1 Section:**
  - **Success Criterion 1.4.5 Images of Text (Level AA)**
  - **Success Criterion 1.1.1 Non-text Content (Level A)**
- **Relevant PDF Technique:** **PDF7:** Performing OCR on a scanned PDF document to provide actual text
- **Implementation:**
  - Calls `page.get_text().strip()`.
  - Flags `Pass` if extracted string length > 0.
  - Flags `Needs Human Review` if extracted string is empty. Provides remediation guidance (suggesting OCR).
- **Technical Scope & Boundaries:**
  - Detects pages lacking digital text streams (such as unscanned flat images).
  - Does not check reading order linearity, font encoding, or Unicode character mapping tables (ToUnicode).

### Check 5: Embedded Image Resources
- **Identifier in Code:** `check_page_images` (Finding ID: `F005+`)
- **Scope:** Page-level (executed for each page)
- **Relevant WCAG 2.1 Section:** **Success Criterion 1.1.1 Non-text Content (Level A)**
- **Relevant PDF Technique:** **PDF1:** Applying text alternatives to images with the `Alt` entry in PDF documents
- **Implementation:**
  - Calls `page.get_images(full=True)`.
  - Flags `Needs Human Review` if image count > 0. Details resource count and remediation guidance.
  - Flags `Pass` if image count == 0.
- **Technical Scope & Boundaries:**
  - Identifies embedded raster XObjects in page resource dictionaries.
  - Does not extract or inspect `/Alt` attribute strings in structural tags.
  - Does not classify images as decorative artifacts versus informative content.
  - Does not detect vector illustrations, path drawings, or canvas shapes.

---

## 3. Implemented Checks: Web Pages

| Check Name | Implementation Status | Relevant WCAG Section | Technical Description |
|---|---|---|---|
| *(None)* | **Not Implemented (Descoped)** | N/A | Webpage scanning is descoped for the prototype (see `FUTURE_WORK.md`). |

- **Current Implementation Scope:** 0 checks implemented.
- **Technical Boundary:** Codebase focuses on PDF documents. `POST /api/scans/web` returns HTTP 422 / `REJECTED` per REQ-12.

---

## 4. Web API & Interface Architecture

### 4.1 Endpoints Specification (`web/app.py`)
- `GET /`: Serves the interactive single-page web UI (`web/templates/index.html`).
- `POST /api/scans/pdf`: Multipart file upload (25 MB max limit). Returns HTTP 202 with `{"scan_id": str, "status": "ANALYZING"}`.
- `POST /api/scans/web`: Returns HTTP 422 with explanation that web scanning is descoped for prototype (REQ-12).
- `GET /api/scans/{scan_id}/status`: Returns current lifecycle state (`VALIDATING`, `ANALYZING`, `COMPLETED`, `REJECTED`).
- `GET /api/scans/{scan_id}/results`: Returns completed `ScanResult` containing summary metrics and findings.
- `POST /api/test-runner`: Triggers acceptance test suite across fixtures and returns `TestSuiteSummary`.
- `GET /docs`: Interactive OpenAPI / Swagger UI.

---

## 5. Automated Testing Subsystem

The codebase includes an automated test runner (`tests/runner.py`) executable via CLI or HTTP API:
```bash
python -m tests.runner
# or via uv:
uv run python -m tests.runner
```
It validates 9 acceptance criteria against deterministic PDF fixtures located in `tests/fixtures/`:
1. `fixture_accessible.pdf`: Asserts that fully formed documents pass title, language, text, and image checks while flagging structure for review.
2. `fixture_scanned.pdf`: Asserts that unscanned/untagged documents flag missing text, title, language, and structure issues.
3. `fixture_images.pdf`: Asserts image resource discovery and review flag assignment.
4. **Deterministic Repeatability:** Asserts that 3 identical runs produce 100% identical findings (AC-04, AC-17).
5. **Summary Consistency:** Asserts `summary.checks == len(findings) == passed + issues + human_review + could_not_evaluate` (AC-09).
6. **In-Memory Streaming:** Asserts raw `bytes` evaluation matches disk evaluation (AC-02, REQ-16).
7. **Traceability:** Asserts every finding includes `finding_id`, `input_location`, and `WCAG_criterion` (AC-07, AC-14).
8. **Remediation Completeness:** Asserts all non-passing checks contain actionable remediation guidance (AC-08).
9. **Error Resilience:** Asserts corrupted streams are handled safely without unhandled crashes (AC-11, REQ-12).

---

## 6. Unimplemented Major Features

The following features represent capabilities not yet present in the codebase:

### 6.1 Containerization & Deployment (Phase 4)
- **Production Containerization:** `Dockerfile` based on `python:3.13-slim` runnable via Docker/Docker Compose on Oracle Cloud Infrastructure (OCI) Always Free VPS (`VM.Standard.E2.1.Micro` or `VM.Standard.A1.Flex`).
- **Edge Proxy & Tunnel Configuration:** Cloudflare free tier Tunnel (`cloudflared`) with zero open inbound ports, automatic SSL, DDoS mitigation, and edge caching.
- **Production Containerization:** `Dockerfile` based on `python:3.13-slim` deployed to Google Cloud Run (Free Tier) with 512 MiB RAM and scale-to-zero autoscaling.
- **Edge Proxy & DNS Configuration:** Cloudflare free tier CNAME proxy with Full (Strict) SSL encryption, DDoS mitigation, and edge caching for static assets.

### 6.2 Structural & Semantic PDF Inspection
- **Structure Tree Traversal and Validation:** Recursive parser for `/StructTreeRoot` to verify hierarchical nesting and structural validity.
- **Alternative Text Extraction and Evaluation:** Direct extraction of `/Alt` strings from `/Figure` structure elements to confirm alt text presence and length.
- **Heading Level Hierarchy Analysis (WCAG 1.3.1, PDF9):** Validation of heading levels (`<H1>` through `<H6>`) to ensure no skipped heading levels.
- **Data Table Structure Validation (WCAG 1.3.1, PDF6):** Inspection of `<Table>` structures to verify header cells (`<TH>`) correctly associate with data cells (`<TD>`) via scope or ID attributes.
- **Artifact Tag Discrimination (WCAG 1.1.1, PDF4):** Verification that background and decorative graphics are tagged with `/Artifact` so assistive tech ignores them.
- **Visual Contrast Analysis (WCAG 1.4.3 Level AA):** Computational measurement of foreground text color values against background bounding box colors.
- **Interactive Form Field Verification (WCAG 1.3.1, 4.1.2):** Inspection of AcroForm dictionaries for accessible names, descriptions, and tooltip attributes.
- **Document Navigation & Bookmarks (WCAG 2.4.5):** Verification that multi-page documents include an outline dictionary (`/Outlines`) with navigation bookmarks.

### 6.3 AI-Assisted Accessibility Analysis (REQ-06)
- GenAI integration for contextual alt-text assessment and plain-language explanation of barriers.
