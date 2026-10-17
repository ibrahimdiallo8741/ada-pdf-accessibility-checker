# Future Work & Descoping Log

## 1. Descoping Decision: Web Page Scanning
- **Date:** October 16, 2026
- **Decision:** Descope live webpage / URL scanning (`POST /api/scans/web`, REQ-01, REQ-02) from the immediate prototype scope.
- **Rationale:** Under current project timelines, focusing strictly on PDF accessibility screening ensures a complete, rigorously tested, and validated implementation of document accessibility checks (metadata, structure tree, text extraction, image detection) rather than splitting resources across two distinct format engines.
- **Current Runtime Handling:**
  - `POST /api/scans/web` returns HTTP 422 Unprocessable Entity (or records state `REJECTED`), returning a clear message: `"Webpage scanning is outside current prototype scope; use /api/scans/pdf."`
  - Satisfies **REQ-12** (Invalid and Unsupported Input Handling) and **AC-11** without failing or crashing.

## 2. Planned Future Enhancements

### 2.1 Web Page & URL Accessibility (Post-Prototype)
- Implement HTTP retrieval and HTML DOM parsing (e.g., using `beautifulsoup4`, `playwright`, or `axe-core`).
- Evaluate WCAG 2.1 Level AA web requirements: landmark structure, form labeling, page title, html `lang` attribute, and image `alt` attributes.

### 2.2 Advanced PDF Semantic Inspection
- **Direct Tag Tree Navigation:** Recursive traversal of the PDF `/StructTreeRoot` to inspect heading levels (`<H1>`–`<H6>`), paragraph tags (`<P>`), and list items (`<L>`, `<LI>`).
- **Figure Alt-Text Extraction:** Inspect `/Figure` structure elements to extract and evaluate `/Alt` strings rather than only counting raw raster image XObjects.
- **Table Structure Markup (WCAG 1.3.1, PDF6):** Validate table header (`<TH>`) association with data cells (`<TD>`).
- **Color Contrast Measurement (WCAG 1.4.3):** Analyze foreground text colors against background render colors.

### 2.3 Generative AI-Assisted Semantic Analysis (REQ-06)
- Integrate an LLM provider to evaluate semantic appropriateness of alternative text and explain accessibility barriers in plain language.
- Ensure strict isolation of deterministic checks from AI checks (REQ-05, REQ-14, REQ-15).

## 3. Implementation Roadmap Status
- **Phase 1 (Completed):** Modular core domain models (`Finding`, `ScanSummary`, `ScanResult`), pure WCAG check rules (`core/checks.py`), and in-memory byte streaming coordinator (`core/checker.py`).
- **Phase 2 (Completed):** Automated test runner (`tests/runner.py`) with 9 acceptance assertions against deterministic test fixtures (`tests/fixtures/`).
- **Phase 3 (Pending):** FastAPI web server (`web/app.py`), in-memory scan store (`web/storage.py`), asynchronous lifecycle endpoints (`/api/scans/pdf`, `/api/scans/{scan_id}/status`, `/api/scans/{scan_id}/results`), automated test endpoint (`/api/test-runner`), and browser UI (`web/templates/index.html`).
- **Phase 4 (Pending):** Containerization (`Dockerfile`) and Cloudflare edge deployment.
