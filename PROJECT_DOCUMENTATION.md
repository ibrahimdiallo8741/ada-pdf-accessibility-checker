# Technical Documentation — Accessibility Checker

## 1. Current Featureset

The codebase provides an automated command-line screening pipeline for portable document format (PDF) files:

- **CLI File Ingestion:** Accepts relative or absolute file paths from interactive standard input; automatically strips surrounding quotes and whitespace.
- **Dual PDF Parsing Engine:**
  - `pymupdf`: Handles document loading, page traversal, text extraction, document-level metadata reading, language attribute retrieval, and raw image XObject discovery.
  - `pypdf`: Traverses the low-level PDF document catalog dictionary (`/Root`) to detect structural markup elements.
- **Page Traversal & Metrics:** Calculates total page count and runs sequential per-page content scans.
- **Document Metadata Verification:** Screens for presence of title strings in the document information dictionary.
- **Document Language Verification:** Screens for a default natural language tag in the document catalog.
- **Document Structure Tag Detection:** Screens for structural tagging presence via the document catalog's structure tree root.
- **Text Layer Extraction:** Checks every page for non-whitespace character extraction to identify potential raster-only pages.
- **Image Resource Discovery:** Enumerates embedded raster image objects per page.
- **Automated JSON Export:** Generates an output JSON file (`<input_stem>_accessibility_report.json`) in the input document's directory containing execution metrics, check statuses, and review warnings.

---

## 2. Implemented Checks: PDF Documents

The codebase implements 5 automated screening checks for PDF documents. Each check maps to specific WCAG 2.1 Success Criteria:

### Check 1: Document Title
- **Identifier in Code:** `Document title`
- **Scope:** Document-level
- **Relevant WCAG 2.1 Section:** **Success Criterion 2.4.2 Page Titled (Level A)**
- **Relevant PDF Technique:** **PDF18:** Specifying the document title using the Title entry in the document information dictionary of a PDF document
- **Implementation:**
  - Inspects `document.metadata.get("title", "")`.
  - Flags `FOUND` if title string contains non-whitespace characters.
  - Flags `REVIEW` with warning if key is missing, empty, or whitespace-only.
- **Technical Scope & Boundaries:**
  - Confirms text exists within the `/Title` metadata field.
  - Does not evaluate whether title text accurately describes document topic or purpose.
  - Does not verify catalog entry `/ViewerPreferences` setting `/DisplayDocTitle` (which controls whether PDF viewers render the title or filename in the application window bar).

### Check 2: Document Language
- **Identifier in Code:** `Document language`
- **Scope:** Document-level
- **Relevant WCAG 2.1 Section:** **Success Criterion 3.1.1 Language of Page (Level A)**
- **Relevant PDF Technique:** **PDF16:** Setting the default language using the `/Lang` entry in the document catalog of a PDF document
- **Implementation:**
  - Inspects `document.language`.
  - Flags `FOUND` if a language string exists.
  - Flags `REVIEW` with warning if attribute is empty or `None`.
- **Technical Scope & Boundaries:**
  - Confirms existence of a declared language code.
  - Does not parse or validate code syntax against RFC 5646 / BCP 47.
  - Does not verify if declared language matches primary textual content.
  - Does not detect inline passages in other languages (WCAG 3.1.2 Language of Parts).

### Check 3: PDF Structure Tree
- **Identifier in Code:** `PDF structure`
- **Scope:** Document-level
- **Relevant WCAG 2.1 Section:** **Success Criterion 1.3.1 Info and Relationships (Level A)**
- **Relevant PDF Techniques:**
  - **PDF9:** Providing headings by marking content with heading tags in PDF documents
  - **PDF20:** Using Adobe Acrobat to create tagged PDF
  - **PDF3:** Ensuring correct tab and reading order in PDF documents
- **Implementation:**
  - Inspects dictionary keys in `pypdf.PdfReader.trailer["/Root"]`.
  - Flags `FOUND` if `/StructTreeRoot` key is present.
  - Flags `REVIEW` with warning if `/StructTreeRoot` key is missing.
- **Technical Scope & Boundaries:**
  - Confirms document catalog contains a structure tree root pointer.
  - Does not traverse the tree or validate tag semantics (`<H1>`, `<P>`, `<Table>`, `<L>`, `<Figure>`).
  - Does not verify logical reading order or tab navigation sequences.

### Check 4: Extractable Text
- **Identifier in Code:** `Page <N> text`
- **Scope:** Page-level (executed for each page)
- **Relevant WCAG 2.1 Section:**
  - **Success Criterion 1.4.5 Images of Text (Level AA)**
  - **Success Criterion 1.1.1 Non-text Content (Level A)**
- **Relevant PDF Technique:** **PDF7:** Performing OCR on a scanned PDF document to provide actual text
- **Implementation:**
  - Calls `page.get_text().strip()`.
  - Flags `FOUND` if extracted string length > 0.
  - Flags `REVIEW` with warning if extracted string is empty.
- **Technical Scope & Boundaries:**
  - Detects pages lacking digital text streams (such as unscanned flat images).
  - Does not check reading order linearity, font encoding, or Unicode character mapping tables (ToUnicode).

### Check 5: Embedded Image Resources
- **Identifier in Code:** `Page <N> images`
- **Scope:** Page-level (executed for each page)
- **Relevant WCAG 2.1 Section:** **Success Criterion 1.1.1 Non-text Content (Level A)**
- **Relevant PDF Technique:** **PDF1:** Applying text alternatives to images with the `Alt` entry in PDF documents
- **Implementation:**
  - Calls `page.get_images(full=True)`.
  - Flags `REVIEW` with warning if image count > 0.
  - Flags `INFO` if image count == 0.
- **Technical Scope & Boundaries:**
  - Identifies embedded raster XObjects in page resource dictionaries.
  - Does not extract or inspect `/Alt` attribute strings in structural tags.
  - Does not classify images as decorative artifacts versus informative content.
  - Does not detect vector illustrations, path drawings, or canvas shapes.

---

## 3. Implemented Checks: Web Pages

| Check Name | Implementation Status | Relevant WCAG Section | Technical Description |
|---|---|---|---|
| *(None)* | **Not Implemented** | N/A | Codebase does not contain web page or HTML scanning routines. |

- **Current Implementation Scope:** 0 checks implemented.
- **Technical Boundary:** The codebase does not include HTTP networking clients, HTML DOM parsers, or headless browser automation interfaces.

---

## 4. Unimplemented Major Features

The following features represent capabilities not yet present in the codebase:

### 4.1 Interface & Delivery
- **Web-Based Graphical User Interface:** Browser-based interface (e.g., Streamlit, FastAPI, or Flask) supporting drag-and-drop file uploads and interactive report visualization.
- **Web Page / URL Accessibility Analysis:** Network crawler and HTML document scanner to analyze live web endpoints against WCAG 2.1 Level AA (e.g., automated DOM evaluation, form control labeling, landmarks, ARIA markup).

### 4.2 Structural & Semantic PDF Inspection
- **Structure Tree Traversal and Validation:** Recursive parser for `/StructTreeRoot` to verify hierarchical nesting and structural validity.
- **Alternative Text Extraction and Evaluation:** Direct extraction of `/Alt` strings from `/Figure` structure elements to confirm alt text presence and length.
- **Heading Level Hierarchy Analysis (WCAG 1.3.1, PDF9):** Validation of heading levels (`<H1>` through `<H6>`) to ensure no skipped heading levels.
- **Data Table Structure Validation (WCAG 1.3.1, PDF6):** Inspection of `<Table>` structures to verify header cells (`<TH>`) correctly associate with data cells (`<TD>`) via scope or ID attributes.
- **Artifact Tag Discrimination (WCAG 1.1.1, PDF4):** Verification that background and decorative graphics are tagged with `/Artifact` so assistive tech ignores them.
- **Visual Contrast Analysis (WCAG 1.4.3 Level AA):** Computational measurement of foreground text color values against background bounding box colors.
- **Interactive Form Field Verification (WCAG 1.3.1, 4.1.2):** Inspection of AcroForm dictionaries for accessible names, descriptions, and tooltip attributes.
- **Document Navigation & Bookmarks (WCAG 2.4.5):** Verification that multi-page documents include an outline dictionary (`/Outlines`) with navigation bookmarks.

### 4.3 Testing & Reporting
- **Multi-Format Report Exporters:** Exporters for human-readable formats (e.g., standalone HTML summaries, Markdown summaries, or PDF summary cards).
- **Automated Test Suite:** Integration of a test framework (e.g., `pytest`) with automated test cases covering diverse PDF formats, corrupt inputs, and edge-case documents.

