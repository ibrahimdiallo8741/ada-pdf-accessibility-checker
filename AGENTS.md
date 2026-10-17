# AI Agent Directives — ADA PDF Accessibility Checker

## 1. Mission & Scope
- **Domain**: PDF files only (webpage and URL scanning is explicitly descoped).
- **Tool Nature**: Preliminary screening prototype, **not** an official ADA Title II or WCAG compliance certification engine.
- **Privacy Invariant**: Strictly in-memory processing. User PDFs must stream through memory buffers (`io.BytesIO`) and never be written to disk, `/tmp`, or exfiltrated to external services (REQ-16, REQ-17).

## 2. Non-Negotiable Screening Rules
- **Statuses**: Use only `Pass`, `Issue`, `Needs Human Review`, `Could Not Evaluate`. Never state that a PDF "passes" or "fails" ADA/WCAG compliance.
- **Remediation**: Every `Issue`, `Needs Human Review`, or `Could Not Evaluate` finding MUST include actionable remediation guidance.
- **Screening Boundaries**:
  - `/StructTreeRoot` presence proves a structural root dictionary exists, **not** correct semantic tagging or logical reading order.
  - Discovering image resources does **not** evaluate alternative text (`/Alt`) presence or quality.
  - Digital text extraction confirms extractable character streams, **not** screen-reader usability.
- **No Hallucinations**: Do not claim checks evaluate criteria beyond their programmatic implementation.

## 3. Authoritative Technical References
- **Architecture, Contracts, & Ingress**: [`docs/ARCHITECTURE.md`](file:///home/deltadizzy/Desktop/Programming/Python/ada-pdf-accessibility-checker/docs/ARCHITECTURE.md)
- **Check Logic & Remediation Catalog**: [`docs/WCAG_CHECKS_REFERENCE.md`](file:///home/deltadizzy/Desktop/Programming/Python/ada-pdf-accessibility-checker/docs/WCAG_CHECKS_REFERENCE.md)
- **Architecture Decision Records (ADRs)**: [`docs/DECISION_LOG.md`](file:///home/deltadizzy/Desktop/Programming/Python/ada-pdf-accessibility-checker/docs/DECISION_LOG.md)
- **Project Milestones & Future Evolution**: [`docs/ROADMAP.md`](file:///home/deltadizzy/Desktop/Programming/Python/ada-pdf-accessibility-checker/docs/ROADMAP.md)
- **Hosting Evaluation Benchmark**: [`docs/CLOUD_HOSTING_COMPARISON.md`](file:///home/deltadizzy/Desktop/Programming/Python/ada-pdf-accessibility-checker/docs/CLOUD_HOSTING_COMPARISON.md)

## 4. Contributor & Agent Working Rules
1. **Inspection First**: Inspect relevant code in `core/`, `web/`, or `tests/` before modifying behavior.
2. **Tooling & Environments**: Use `uv` exclusively (`uv run ...`, `uv add ...`). Do not use unpinned `pip` or create alternate virtualenvs.
3. **Preserve Contracts**: Do not break domain models in `core/models.py` or REST schemas in `web/app.py`.
4. **Documentation Synchronization**: When code, architecture, or roadmap items change, immediately update the corresponding docs in `docs/` and references in `README.md`.

## 5. Verification Commands & Definition of Done
Work is complete only when:
```bash
uv run python -m tests.runner     # Must pass 10/10 acceptance tests
uv run python pdf_checker.py      # CLI execution remains functional
uv run uvicorn web.app:app        # Web API & UI boots cleanly
```
