# ADA PDF Accessibility Checker

Preliminary screening prototype evaluating PDF documents for potential accessibility issues aligned with ADA Title II and WCAG 2.1 Level AA.

> **Disclaimer:** This tool provides automated preliminary screening checks. It is **not** an official ADA or WCAG compliance certification.

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

### 1. Web Portal & REST API
Launch local FastAPI server at `http://localhost:8000`:
```bash
# With uv:
uv run uvicorn web.app:app --reload

# With active virtual environment:
uvicorn web.app:app --reload
```
- **Web UI:** [`http://localhost:8000/`](http://localhost:8000/) — Drag-and-drop upload, status polling, report viewer, and test runner.
- **Interactive OpenAPI Docs:** [`http://localhost:8000/docs`](http://localhost:8000/docs) — Swagger UI.

### 2. Command-Line Interface (CLI)
Interactive terminal scanner generating `<filename>_accessibility_report.json`:
```bash
# With uv:
uv run python pdf_checker.py

# With active virtual environment:
python pdf_checker.py
```

---

## Running Tests

Execute the automated acceptance test runner against AC-01 through AC-18:
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

Detailed architecture, check specifications, and future roadmap in [`docs/`](docs/):
- [`PROJECT_DOCUMENTATION.md`](docs/PROJECT_DOCUMENTATION.md): Feature list, WCAG citations, checks, and limits.
- [`FUTURE_WORK.md`](docs/FUTURE_WORK.md): Descoping log (webpage scan) and future enhancements.
- [`PROJECT_HANDOFF.md`](docs/PROJECT_HANDOFF.md): Original project background and handoff details.
- [`WEB_HOSTING_AND_ARCHITECTURE_PLAN.md`](docs/WEB_HOSTING_AND_ARCHITECTURE_PLAN.md): Cloudflare and container hosting specifications.
- [`AGENTS.md`](AGENTS.md): Contributor conventions and agent development principles.
