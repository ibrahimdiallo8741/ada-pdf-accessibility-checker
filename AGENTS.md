# AI Agent Instructions — ADA PDF Accessibility Checker

## Mission
Contribute to a student team project that screens PDF files for potential accessibility issues relevant to ADA Title II digital accessibility and WCAG 2.1 Level AA. The **current scope is PDF files only**, not websites or URLs. The tool is a **preliminary screening prototype**, not an ADA/WCAG certification engine.

## Project location and status
- GitHub repository: `https://github.com/ibrahimdiallo8741/ada-pdf-accessibility-checker`
- Main branch: `main`
- Last user-confirmed pushed commit: `b4cde35` — `Complete PDF accessibility screening prototype` (October 16, 2026). If a subsequent commit is currently the latest, update this bullet point accordingly.
- Team collaboration is via GitHub; collaborators have been invited.
- **Before changing code, inspect the repository's current files.** This document is a handoff from the development conversation, not an independently audited snapshot of the live repository.

## Current architecture
- `core/`: Core screening engine decoupled from user interface and delivery mechanisms.
  - `core/models.py`: Strongly-typed dataclasses (`Finding`, `ScanSummary`, `ScanResult`, `TestCaseResult`, `TestSuiteSummary`) adhering to the `api/api.md` schema.
  - `core/checks.py`: Pure rule-based screening checks mapping to WCAG criteria and providing actionable remediation guidance.
  - `core/checker.py`: Screening coordinator (`screen_pdf`) accepting both filesystem paths and raw memory byte streams.
- `tests/`: Automated testing subsystem.
  - `tests/fixtures/`: Curated test sample PDFs (`fixture_accessible.pdf`, `fixture_scanned.pdf`, `fixture_images.pdf`).
  - `tests/runner.py`: Automated test runner executing acceptance checks (AC-01 through AC-18).
- `web/`: FastAPI web application and user interface.
  - `web/app.py`: REST routes matching `api/api.md` specifications and automated test runner trigger.
  - `web/storage.py`: Thread-safe in-memory scan job tracker with 1-hour expiration (REQ-16).
  - `web/templates/index.html`: Zero-dependency web UI for drag-and-drop screening, polling, report download, and test runner.
- `pdf_checker.py`: Python command-line program delegating to `core.checker.screen_pdf()`. Prompts for a PDF file path, prints findings, and saves a JSON report beside the input PDF.
- `requirements.txt` / `pyproject.toml`: Python dependencies managed via uv/pip; contains `pymupdf` and `pypdf`.
- `README.md`: Repository overview and developer quick reference.
- `docs/`: Project documentation directory.
  - `docs/PROJECT_DOCUMENTATION.md`: Technical documentation of current featureset, implemented checks, WCAG citations, and roadmap items.
  - `docs/FUTURE_WORK.md`: Log of descoped items (e.g. web scanning) and planned future enhancements.
  - `docs/PROJECT_HANDOFF.md`: Project orientation, background, and initial state.
  - `docs/WEB_HOSTING_AND_ARCHITECTURE_PLAN.md`: Architecture specification and hosting plan.
  - `docs/CLOUD_HOSTING_COMPARISON.md`: Multi-vendor cloud hosting assessment and free-tier comparison.
- `.gitignore`: Existing Git ignore rules. Do not commit `.venv/` or sensitive/test documents by accident.

## Current program logic
The current engine in `core/checker.py` and CLI in `pdf_checker.py`:
1. Opens the PDF with `pymupdf.open(...)` (path or memory buffer) and `pypdf.PdfReader(...)`.
2. Counts pages.
3. Checks whether document metadata contains a nonempty title (`check_title`).
4. Checks whether a document language is declared (`check_language`).
5. Checks for `/StructTreeRoot` via `reader.root_object` (`check_structure`).
6. For each page, checks extractable text via `page.get_text()` (`check_page_text`).
7. For each page, checks image resources via `page.get_images(full=True)` (`check_page_images`).
8. Collects findings in standardized dataclasses conforming to `api/api.md`.
9. Writes `<input_stem>_accessibility_report.json` beside the input PDF.
10. Prints a summary including performed checks, passed checks, issues, and human review items.

Statuses in the implementation: `Pass`, `Issue`, `Needs Human Review`, `Could Not Evaluate`. These are **screening labels, not compliance determinations**.

## Confirmed manual tests
- `accessible_test.pdf`: Earlier CLI version reported 1 page, extractable text, English document language, a PDF structure tree, and missing title. This is only a *test filename*; do not infer that it is fully accessible.
- `problemset6.pdf`: Scanner successfully processed 2 pages and generated accessibility report.
- `test.pdf`: 12 pages scanned; 27 checks performed (15 pass, 2 issues, 10 human review, 0 errors).
- Automated test suite (`python -m tests.runner`): 9 acceptance tests passed across 3 test fixtures (`fixture_accessible.pdf`, `fixture_scanned.pdf`, `fixture_images.pdf`).

## Non-negotiable accuracy rules
- **Do not say a PDF passes or fails ADA/WCAG based solely on these checks.** Report `Pass`, `Issue`, `Needs Human Review`, or `Could Not Evaluate`.
- Structure-tree presence does not prove correct semantic tagging, reading order, heading structure, table markup, or meaningful alternative text.
- `page.get_images(full=True)` reports PDF image resources; it does **not** verify alt text, and does not reliably enumerate every visually meaningful graphic.
- Extractable text does not guarantee correct reading order or screen-reader usability. Lack of extractable text is a warning, not conclusive evidence of noncompliance.
- A PDF's title metadata is not equivalent to verifying that a PDF viewer displays the document title appropriately.
- Missing metadata or tags should be described as findings needing review, not legal conclusions.
- Do not send user PDFs or private file contents to external services without permission.
- Do not silently expand the project to URL/website scanning. Confirm with the team before changing scope.

## Working conventions for contributors
1. Read `README.md`, `docs/PROJECT_HANDOFF.md`, `pdf_checker.py`, and `pyproject.toml` before modifying code.
2. Keep existing working checks and JSON output functional unless an explicitly approved change requires otherwise.
3. Make small, explainable changes and use clear beginner-friendly Python. The instructor allows AI assistance, but the team must understand and explain the logic.
4. Prefer a new feature branch and pull request for group contributions; coordinate before pushing to `main`.
5. Test with both a text-based PDF and a scan/image-based PDF, including error cases (missing file, invalid PDF). Never commit personal PDFs unless the team approves.
6. Include exact commands, expected results, and a plain-English explanation of any new feature.
7. Document limitations and distinguish completed functionality from proposals.
8. Preserve or update the JSON schema intentionally; note any breaking changes.
9. Avoid broad refactors and new frameworks unless they are required by the course rubric.
10. Never commit `.venv`, credentials, access tokens, or sensitive PDFs.
11. **Documentation Synchronization:** Keep `docs/PROJECT_DOCUMENTATION.md`, `docs/FUTURE_WORK.md`, and `AGENTS.md` up to date whenever features or phases are planned, descoped, or implemented. Reflect current code state, active architecture, test results, and limitations across all three files.

## Local setup (Windows Command Prompt)
```bat
python --version
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python pdf_checker.py
```
Or with `uv`:
```bash
uv run python pdf_checker.py
uv run python -m tests.runner
uv run uvicorn web.app:app --reload
```

## Next priorities
1. Execute Google Cloud Run container deployment (`gcloud run deploy --source .`).
2. Configure custom domain mapping and Cloudflare Full (Strict) DNS proxy.
3. Review team testing submissions and evaluate candidate custom test PDFs.

## Definition of done for any new contribution
Code runs locally; existing checks still work; changes are tested with evidence; documentation reflects actual behavior; accessibility claims are carefully qualified; team can explain the logic; and work is committed via an agreed GitHub workflow.
