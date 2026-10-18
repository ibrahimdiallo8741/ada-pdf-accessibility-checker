# ADA PDF Accessibility Checker

Preliminary screening prototype evaluating PDF documents for potential accessibility issues aligned with ADA Title II and WCAG 2.1 Level AA.

> **Disclaimer:** This tool provides automated preliminary screening checks. It is **not** an official ADA or WCAG compliance certification.

---
## Live Deployment

|Access via|Main application|Testing endpoint|System Base URL|Tester Base URL|
|----------|----------------|----------------|---------------|---------------|
|Cloudflare|https://adacheck.deltadizzy.org|https://adacheck.deltadizzy.org/api/test-runner|https://adacheck.deltadizzy.org/system|https://adacheck.deltadizzy.org/tester|
|Google Cloud|https://ada-compliance-checker-295390844193.us-central1.run.app|https://ada-compliance-checker-295390844193.us-central1.run.app/api/test-runner|https://ada-compliance-checker-295390844193.us-central1.run.app/system|https://ada-compliance-checker-295390844193.us-central1.run.app/tester|


---

## Prerequisites

- **Python:** 3.13+
- **Tooling:** [`uv`](https://docs.astral.sh/uv/) (recommended) or standard Python `venv` + `pip`

---

## Local Setup

### Option 1: Using `uv` (Recommended)
```bash
git clone https://github.com/ibrahimdiallo8741/ada-pdf-accessibility-checker.git
cd ada-pdf-accessibility-checker
uv sync
```

### Option 2: Standard `venv` & `pip`
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

---

## Running the Application

### 1. Web Portal and API
Launch local server at `http://localhost:8000`:
```bash
# With uv:
uv run uvicorn web.app:app --reload

# With active virtual environment:
uvicorn web.app:app --reload
```
- **Web UI:** [`http://localhost:8000/`](http://localhost:8000/) — Drag-and-drop upload, status polling, report viewer, and test runner.
- **Interactive OpenAPI Docs:** [`http://localhost:8000/docs`](http://localhost:8000/docs) — Swagger UI.

### 2. Command-Line Interface (CLI)
Interactive terminal program to generate `<filename>_accessibility_report.json`:
```bash
# With uv:
uv run python pdf_checker.py

# With active virtual environment:
python pdf_checker.py
```

---

## Running Tests

Execute the automated test runner against all Acceptance Criteria:
```bash
# With uv:
uv run python -m tests.runner

# With active virtual environment:
python -m tests.runner
```

Screen custom PDFs dropped into `tests/fixtures/` or via path:
```bash
uv run python -m tests.runner path/to/custom_pdfs/
```

---

## Documentation

Consolidated architectural, technical, and compliance specifications in [`docs/`](docs/):
- [`ARCHITECTURE.md`](docs/ARCHITECTURE.md): System design, component structure, data models, REST API, privacy invariants, and Cloud Run + Cloudflare topology.
- [`WCAG_CHECKS_REFERENCE.md`](docs/WCAG_CHECKS_REFERENCE.md): Technical check definitions, WCAG 2.1 AA citations, boundaries, status enums, and remediation guidance catalog.
- [`WCAG_TAXONOMY.md`](docs/WCAG_TAXONOMY.md): Complete coverage taxonomy of all 50 WCAG 2.1 Level A & AA criteria (implemented, planned, out-of-scope, N/A).
- [`DECISION_LOG.md`](docs/DECISION_LOG.md): Architectural Decision Records (ADRs 001–004) detailing scope, parser engine, hosting, and tooling choices.
- [`ROADMAP.md`](docs/ROADMAP.md): Project milestone completion record (Milestones 1–4) and planned post-prototype enhancements.
- [`CROSS_TEAM_TESTING_PLAN.md`](docs/CROSS_TEAM_TESTING_PLAN.md): Step-by-step API test execution plan for self-testing and cross-testing under the shared testing ConOps.
- [`CLOUD_HOSTING_COMPARISON.md`](docs/CLOUD_HOSTING_COMPARISON.md): Multi-vendor hosting assessment and free-tier trade-off evaluation.
- [`AGENTS.md`](AGENTS.md): Contributor conventions, agent directives, and verification rules.
