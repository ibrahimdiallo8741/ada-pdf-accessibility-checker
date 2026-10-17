# Architecture Decision Log (ADRs)

> **Executive Summary**: This log records significant architectural and design choices made during development. Each record details the context, the decision taken, its technical justification, and consequences.

---

## ADR-001: PDF-Only Scope Focus & Web Scanning Descoping

- **Date**: 2026-10-16
- **Status**: Accepted
- **Context**: The project was originally conceived with dual requirements covering both webpage accessibility and document accessibility (REQ-01, REQ-02). However, digital PDF accessibility carries unique structural requirements (ISO 32000-1 tagged PDF trees, XObject raster models, embedded metadata dictionaries) that differ fundamentally from HTML DOM tree parsing. Attempting to support both within a prototype timeline risked superficial coverage across both media.
- **Decision**: Explicitly descope web URL and HTML scanning. Dedicate 100% of engineering effort toward building an accurate, extensible, and high-performance PDF screening engine.
- **Consequences**:
  - Web URL scanning is logged in [`docs/ROADMAP.md`](file:///home/deltadizzy/Desktop/Programming/Python/ada-pdf-accessibility-checker/docs/ROADMAP.md) for post-prototype exploration.
  - Project interfaces (CLI, REST API, Web UI) are streamlined around file upload and byte-stream ingestion.

---

## ADR-002: Dual PDF Engine Architecture (`pymupdf` + `pypdf`)

- **Date**: 2026-10-16
- **Status**: Accepted
- **Context**: Evaluating PDF accessibility requires two distinct capabilities:
  1. High-speed content extraction (digital character layers, raster image extraction, page enumeration).
  2. Direct inspection of internal low-level PDF document catalog dictionaries (`/StructTreeRoot`, `/Lang`, `/ViewerPreferences`).
  Python libraries typically excel at one but struggle with the other. Pure-Python `pypdf` excels at parsing low-level object dictionaries, while C-backed `pymupdf` (MuPDF) is orders of magnitude faster at text extraction and image resource indexing.
- **Decision**: Implement a coordinated dual-engine model in [`core/checker.py`](file:///home/deltadizzy/Desktop/Programming/Python/ada-pdf-accessibility-checker/core/checker.py):
  - Use `pypdf.PdfReader` for catalog dictionary inspection (`check_language`, `check_structure`, catalog title fallbacks).
  - Use `pymupdf.open()` for page-level text extraction (`check_page_text`) and image resource enumeration (`check_page_images`).
- **Consequences**:
  - High screening throughput with native C-speed rendering.
  - Low-level PDF dictionary access without brittle custom byte parsing.
  - Requires `cryptography>=3.1.0` dependency to support standard AES permissions decryption in `pypdf`.

---

## ADR-003: Hosting Platform Selection: Google Cloud Run + Cloudflare Edge

- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: The web screening service required deployment to an accessible public endpoint on a zero-budget free tier while supporting Python 3.13, C-extensions (`pymupdf`), ephemeral container scaling, and SSL security. A formal multi-vendor comparison evaluated Oracle Cloud VPS, AWS Lambda, Render, and Google Cloud Run (documented in [`docs/CLOUD_HOSTING_COMPARISON.md`](file:///home/deltadizzy/Desktop/Programming/Python/ada-pdf-accessibility-checker/docs/CLOUD_HOSTING_COMPARISON.md)).
- **Decision**: Select **Google Cloud Run (Fully Managed)** paired with **Cloudflare Edge Proxy (Free Tier)**.
  - *Cloud Run*: Scale-to-zero container runtime (512 MiB RAM, 1 vCPU, 2M free requests/month, 360,000 vCPU-seconds free/month). Zero idle cost and zero server maintenance.
  - *Cloudflare*: Universal SSL Full (Strict), custom DNS proxying, automated HTTPS redirection, edge asset caching (`/static/*`), and zero-cost egress protection.
- **Consequences**:
  - Containerization via standard [`Dockerfile`](file:///home/deltadizzy/Desktop/Programming/Python/ada-pdf-accessibility-checker/Dockerfile) ensures local/cloud runtime parity.
  - Cold starts take 2–4 seconds after idling; mitigated by Cloudflare edge caching for static assets.
  - Cloudflare Full (Strict) mode requires Cloud Run to provision Google-managed origin certificates before proxy activation.

---

## ADR-004: Strict Tooling & Dependency Isolation via `uv`

- **Date**: 2026-10-16
- **Status**: Accepted
- **Context**: Team members and automated CI/agent environments use varied operating systems (Windows Command Prompt, Linux, macOS). Traditional `pip install -r requirements.txt` workflows lead to dependency drift, missing lockfile pinning, and environment fragmentation.
- **Decision**: Standardize all development, testing, and deployment workflows on the `uv` toolchain (`pyproject.toml` and `uv.lock`). Maintain `requirements.txt` strictly as a synchronized export for compatibility.
- **Consequences**:
  - Sub-second deterministic environment installation across all developer and CI machines.
  - AI agents and contributors execute unified commands (`uv run python -m tests.runner`, `uv run uvicorn web.app:app`).
