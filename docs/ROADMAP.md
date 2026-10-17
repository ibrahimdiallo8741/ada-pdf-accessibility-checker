# Project Milestones & Evolution Roadmap

> **Executive Summary**: This document tracks the development progression of the ADA PDF Accessibility Checker across completed prototype milestones and prioritizes planned post-prototype technical enhancements. *(Note: Milestones are tracked independently of academic assignment phases).*

---

## 1. Prototype Milestone Completion Record

| Milestone | Scope & Deliverables | Status | Verification Evidence |
|---|---|---|---|
| **Milestone 1: Core Screening Domain** | • Pure rule-based checks (`core/checks.py`)<br/>• Dual-engine coordinator (`core/checker.py`)<br/>• Strongly typed dataclasses (`core/models.py`)<br/>• Interactive CLI frontend (`pdf_checker.py`) | **Completed** | • CLI successfully screens multi-page PDFs and generates standardized JSON reports.<br/>• Verified against `accessible_test.pdf` and `problemset6.pdf`. |
| **Milestone 2: Automated Acceptance Testing** | • Acceptance test runner (`tests/runner.py`)<br/>• Curated test fixtures (`tests/fixtures/`)<br/>• Test case assertions (AC-01 through AC-18) | **Completed** | • Automated test suite passes 10/10 assertions (`uv run python -m tests.runner`).<br/>• Standardized `TestSuiteSummary` schema. |
| **Milestone 3: Web Application & UI** | • FastAPI asynchronous backend (`web/app.py`)<br/>• In-memory job tracking with 1h TTL (`web/storage.py`)<br/>• Responsive web UI with drag-and-drop (`web/templates/`, `web/static/`)<br/>• In-browser acceptance test trigger (`/api/test-runner`) | **Completed** | • Asynchronous upload, polling, and report download verified in browser.<br/>• Dual `GET`/`POST` support for automated test execution. |
| **Milestone 4: Containerization & Cloud Deployment** | • Production containerization (`Dockerfile`)<br/>• Google Cloud Run serverless deployment<br/>• Cloudflare DNS & Full (Strict) SSL edge proxy<br/>• Edge caching for static web assets | **Completed** | • Cloud Run container boots with dynamic `${PORT:-8080}` and clean signal handling.<br/>• Cloudflare Universal SSL and caching active. |

---

## 2. Post-Prototype Evolution Milestones

### Milestone 5: Deep Semantic Structure Tree Traversal
- **Objective**: Expand `/StructTreeRoot` validation from simple existence checking to full hierarchical tree parsing.
- **Key Capabilities**:
  - Recursive traversal of the PDF Structure Hierarchy (`/K` structure elements).
  - Validation of heading nesting levels (e.g. flagging skipped heading levels like `<H1>` immediately followed by `<H3>`).
  - Table accessibility verification: detecting table elements (`<Table>`) and ensuring header cell tags (`<TH>`) are properly associated with data cells (`<TD>`).
  - List structural integrity (`<L>`, `<LI>`, `<Lbl>`, `<LBody>`).

### Milestone 6: Visual & Contrast Analysis
- **Objective**: Implement visual rendering heuristics for visual accessibility criteria.
- **Key Capabilities**:
  - Page rasterization contrast calculation to evaluate WCAG 2.1 AA Criterion 1.4.3 (Contrast Minimum: 4.5:1 for normal text, 3:1 for large text).
  - Extraction and inspection of vector graphics and paths (PDF drawings not captured by XObject raster extraction).

### Milestone 7: Contextual AI Alt-Text Assistance (REQ-06)
- **Objective**: Augment the screening engine with optional, assistive AI capabilities without sacrificing deterministic reliability.
- **Key Capabilities**:
  - Extract cropped image regions alongside surrounding paragraph text context.
  - Query local or cloud vision models to draft candidate alternative text descriptions.
  - Maintain strict architectural separation: AI suggestions must remain explicitly labeled as human advisory recommendations, never automated pass/fail determinations.

### Milestone 8: Ingestion Pipeline Extensions
- **Objective**: Re-evaluate multi-format document and webpage ingestion if project scope expands beyond PDFs.
- **Key Capabilities**:
  - Headless browser rendering integration (`Playwright` / `axe-core`) for live web URL evaluation.
  - Multi-file batch processing and asynchronous webhook notification callbacks for high-volume scanning pipelines.
