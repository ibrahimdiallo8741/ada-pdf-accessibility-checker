# WCAG Checks & Remediation Reference

> **Executive Summary**: This document specifies the 5 rule-based screening checks implemented in the ADA PDF Accessibility Checker. It defines the mapping to WCAG 2.1 Level AA and ADA Title II technical criteria, evaluation boundaries, status classification rules, and standard remediation guidance.

---

## 1. Non-Negotiable Screening Principles

1. **Preliminary Screening vs. Legal Certification**:
   Automated checks evaluate technical heuristics. They can detect common accessibility barriers, but **cannot guarantee or certify full ADA Title II or WCAG compliance**. Manual inspection by assistive technology users remains mandatory.
2. **Authorized Screening Statuses**:
   Every finding must be labeled with exactly one of four statuses:
   - `Pass`: Heuristic rule satisfied.
   - `Issue`: Concrete barrier detected requiring remediation.
   - `Needs Human Review`: Elements detected (e.g. images) whose accessibility requires human evaluation.
   - `Could Not Evaluate`: Parser exception or encrypted stream prevented evaluation.
3. **Mandatory Remediation Guidance**:
   Every finding that is not a `Pass` must provide actionable, plain-English remediation instructions to guide the document author.

---

## 2. Check Specifications

### Check 1: Document Title (`check_title`)
- **WCAG Success Criterion**: [WCAG 2.4.2 Page Titled (Level A)](https://www.w3.org/WAI/WCAG21/Understanding/page-titled.html)
- **PDF Technique**: [PDF18: Specifying the document title using the Title entry in the document information dictionary](https://www.w3.org/WAI/WCAG21/Techniques/pdf/PDF18)
- **Implementation**: Evaluates `doc.metadata.get("title")` and `reader.metadata.title`.
- **Status Classification**:
  - `Pass`: Title metadata exists, is a non-empty string, and contains more than whitespace.
  - `Issue`: Title metadata is missing, `None`, or empty.
- **Evaluation Boundaries**:
  - Validates presence of document metadata title string.
  - Does *not* evaluate whether the title is descriptively accurate or meaningful.
  - Does *not* verify whether the PDF viewer is configured to display the document title in its title bar (`/ViewerPreferences << /DisplayDocTitle true >>`).

### Check 2: Document Language (`check_language`)
- **WCAG Success Criterion**: [WCAG 3.1.1 Language of Page (Level A)](https://www.w3.org/WAI/WCAG21/Understanding/language-of-page.html)
- **PDF Technique**: [PDF16: Setting the default language using the /Lang entry in the document catalog](https://www.w3.org/WAI/WCAG21/Techniques/pdf/PDF16)
- **Implementation**: Inspects `reader.root_object.get("/Lang")`.
- **Status Classification**:
  - `Pass`: `/Lang` entry exists in the document catalog dictionary and contains a non-empty string.
  - `Issue`: `/Lang` entry is missing or empty.
- **Evaluation Boundaries**:
  - Confirms declaration of default document language.
  - Does *not* validate BCP 47 language subtag syntax (RFC 5646).
  - Does *not* detect passages or phrases written in a secondary language (`/Lang` attribute on structure elements).

### Check 3: Document Structure Tree (`check_structure`)
- **WCAG Success Criterion**: [WCAG 1.3.1 Info and Relationships (Level A)](https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html)
- **PDF Technique**: [PDF7: Using the PDF table of contents to provide navigational aids / Tagged PDF](https://www.w3.org/WAI/WCAG21/Techniques/pdf/PDF7)
- **Implementation**: Inspects `reader.root_object.get("/StructTreeRoot")`.
- **Status Classification**:
  - `Pass`: `/StructTreeRoot` dictionary exists in the catalog.
  - `Issue`: `/StructTreeRoot` is absent (document is untagged).
- **Evaluation Boundaries**:
  - Proves the document contains a Tagged PDF root dictionary.
  - Does *not* verify semantic correctness of tags (e.g. `<H1>` through `<H6>`, `<Table>`, `<L>`).
  - Does *not* verify logical reading order or proper nesting of structural elements.

### Check 4: Page Text Layer (`check_page_text`)
- **WCAG Success Criterion**: [WCAG 1.4.5 Images of Text (Level AA)](https://www.w3.org/WAI/WCAG21/Understanding/images-of-text.html)
- **Implementation**: Evaluates `len(page.get_text().strip())` per page using PyMuPDF.
- **Status Classification**:
  - `Pass`: Extractable text layer contains 1 or more non-whitespace characters.
  - `Issue`: Page contains 0 extractable text characters (indicates scanned bitmap, pure raster graphic, or outlined glyphs).
- **Evaluation Boundaries**:
  - Verifies presence of digitally selectable and searchable text stream.
  - Does *not* guarantee reading order, character encoding fidelity, or screen-reader usability.
  - Does *not* perform OCR on scanned pages.

### Check 5: Embedded Image Resources (`check_page_images`)
- **WCAG Success Criterion**: [WCAG 1.1.1 Non-text Content (Level A)](https://www.w3.org/WAI/WCAG21/Understanding/non-text-content.html)
- **PDF Technique**: [PDF1: Applying text alternatives to images using the Alt entry](https://www.w3.org/WAI/WCAG21/Techniques/pdf/PDF1)
- **Implementation**: Calls `page.get_images(full=True)` per page using PyMuPDF.
- **Status Classification**:
  - `Pass`: Page contains 0 image resources.
  - `Needs Human Review`: Page contains 1 or more embedded image resources.
- **Evaluation Boundaries**:
  - Detects raster image XObjects referenced in the page resource dictionary.
  - Does *not* evaluate whether image structure tags contain `/Alt` alternative text.
  - Does *not* evaluate whether images are marked as decorative artifacts (`/Artifact`).
  - Does *not* detect visual diagrams rendered via vector path drawing operations.

---

## 3. Remediation Guidance Catalog

| Rule ID | Finding Status | Condition | Standard Remediation Text |
|---|---|---|---|
| `TITLE_001` | `Issue` | Document Title missing or empty | Set the document title in PDF document properties (e.g., File > Properties in Adobe Acrobat or via document authoring software before export). |
| `LANG_001` | `Issue` | Default language undeclared | Set the default document language in the PDF catalog properties (e.g., File > Properties > Advanced > Reading Options > Language in Acrobat). |
| `STRUCT_001` | `Issue` | Structure tree missing | Enable PDF tagging in your export settings (e.g., 'Save as Tagged PDF' in Microsoft Word or InDesign) or use Adobe Acrobat Autotag tool. |
| `TEXT_001` | `Issue` | Page lacks digital text layer | Run Optical Character Recognition (OCR) on this scanned page to generate a selectable text layer for assistive technology. |
| `IMG_001` | `Needs Human Review` | Image resources discovered | Review images on this page to ensure meaningful images have descriptive alternative text (/Alt) and decorative images are marked as artifacts. |
| `*` | `Could Not Evaluate` | Parsing exception / encryption | Ensure the PDF file is unencrypted, valid, and not password protected, then retry screening. |
