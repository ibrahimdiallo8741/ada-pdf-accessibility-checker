# AI Agent Instructions — ADA PDF Accessibility Checker

## Mission
Contribute to a student team project that screens PDF files for potential accessibility issues relevant to ADA Title II digital accessibility and WCAG 2.1 Level AA. The **current scope is PDF files only**, not websites or URLs. The tool is a **preliminary screening prototype**, not an ADA/WCAG certification engine.

## Project location and status
- GitHub repository: `https://github.com/ibrahimdiallo8741/ada-pdf-accessibility-checker`
- Main branch: `main`
- Last user-confirmed pushed commit: `b4cde35` — `Complete PDF accessibility screening prototype` (October 16, 2026).
- Team collaboration is via GitHub; collaborators have been invited.
- **Before changing code, inspect the repository's current files.** This document is a handoff from the development conversation, not an independently audited snapshot of the live repository.

## Current architecture
- `pdf_checker.py`: Python command-line program. Prompts for a PDF file path, scans the file, prints findings, and saves a JSON report beside the input PDF.
- `requirements.txt`: Python dependencies; inspect its actual contents rather than assuming versions.
- `README.md`: Existing repository overview; update as necessary.
- `.gitignore`: Existing Git ignore rules. Do not commit `.venv/` or sensitive/test documents by accident.
- A `.venv` environment was created locally on Windows. The project was developed using VS Code and Git for Windows.
- Python libraries used by the current scanner: `pymupdf` (PyMuPDF) and `pypdf`; `pathlib` and `json` are Python standard-library modules.
- A web upload interface (`app.py`/Streamlit) was discussed but **has not been demonstrated as implemented or tested** in the user's existing repository. Do not claim it exists without checking.

## Current program logic
The last shared version of `pdf_checker.py` uses a `check_pdf(file_path)` function that:
1. Opens the PDF with `pymupdf.open(file_path)` and loads it with `pypdf.PdfReader(file_path)`.
2. Counts pages.
3. Checks whether document metadata contains a nonempty title.
4. Checks whether a document language is declared (`document.language`).
5. Checks for `/StructTreeRoot` in the PDF catalog, indicating presence of a structure tree.
6. For each page, uses `page.get_text().strip()` to look for extractable text.
7. For each page, uses `page.get_images(full=True)` to identify embedded image resources and flags those for alt-text review.
8. Collects results in a dictionary with `file`, `pages`, `checks`, and `warnings`; each check has `check`, `status`, and `details`.
9. Writes `<input_stem>_accessibility_report.json` beside the input PDF.
10. Prints a summary including number of checks and review items.

Statuses in the shared implementation: `FOUND`, `REVIEW`, and `INFO`. These are **screening labels, not compliance determinations**.

## Confirmed manual tests
- `accessible_test.pdf`: Earlier CLI version reported 1 page, extractable text, English document language, a PDF structure tree, and missing title. This is only a *test filename*; do not infer that it is fully accessible.
- `problemset6.pdf`: Updated scanner successfully processed 2 pages and generated `problemset6_accessibility_report.json`. It reported title `Microsoft Word - Assignment-6`, missing declared language, missing structure tree, no extractable text on either page, no image resources on page 1, and 1 image resource on page 2. Summary: **7 checks, 5 items requiring review**.
- The user confirmed a successful Git push to `main` for commit `b4cde35`.
- These tests are manual CLI runs. Automated unit tests, screen-reader usability tests, and independent accessibility validation have **not been established**.

## Non-negotiable accuracy rules
- **Do not say a PDF passes or fails ADA/WCAG based solely on these checks.** Report `potential issue`, `found`, or `manual review required`.
- Structure-tree presence does not prove correct semantic tagging, reading order, heading structure, table markup, or meaningful alternative text.
- `page.get_images(full=True)` reports PDF image resources; it does **not** verify alt text, and does not reliably enumerate every visually meaningful graphic.
- Extractable text does not guarantee correct reading order or screen-reader usability. Lack of extractable text is a warning, not conclusive evidence of noncompliance.
- A PDF's title metadata is not equivalent to verifying that a PDF viewer displays the document title appropriately.
- Missing metadata or tags should be described as findings needing review, not legal conclusions.
- Do not send user PDFs or private file contents to external services without permission.
- Do not silently expand the project to URL/website scanning. Confirm with the team before changing scope.

## Working conventions for contributors
1. Read `README.md`, `PROJECT_HANDOFF.md`, `pdf_checker.py`, and `requirements.txt` before modifying code.
2. Keep existing working checks and JSON output functional unless an explicitly approved change requires otherwise.
3. Make small, explainable changes and use clear beginner-friendly Python. The instructor allows AI assistance, but the team must understand and explain the logic.
4. Prefer a new feature branch and pull request for group contributions; coordinate before pushing to `main`.
5. Test with both a text-based PDF and a scan/image-based PDF, including error cases (missing file, invalid PDF). Never commit personal PDFs unless the team approves.
6. Include exact commands, expected results, and a plain-English explanation of any new feature.
7. Document limitations and distinguish completed functionality from proposals.
8. Preserve or update the JSON schema intentionally; note any breaking changes.
9. Avoid broad refactors and new frameworks unless they are required by the course rubric.
10. Never commit `.venv`, credentials, access tokens, or sensitive PDFs.

## Local setup (Windows Command Prompt)
```bat
python --version
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python pdf_checker.py
```
Enter a real absolute path to a PDF when prompted. The app prints results and saves a JSON report alongside that PDF. On PowerShell, activation may be restricted by execution policy; Command Prompt activation worked during initial setup.

## Next priorities
1. Confirm current code and requirements match the repository.
2. Preserve the working prototype and existing tests.
3. Help the team prepare the **Phase 3 document** using the actual instructor rubric (not yet supplied in this handoff).
4. Add features only if the rubric or team requests them. Possible future enhancements: readable report formatting, robust validation/error handling, tagged-PDF inspection, meaningful alt-text evaluation, and a web interface; **none should be represented as already complete**.

## Definition of done for any new contribution
Code runs locally; existing checks still work; changes are tested with evidence; documentation reflects actual behavior; accessibility claims are carefully qualified; team can explain the logic; and work is committed via an agreed GitHub workflow.
