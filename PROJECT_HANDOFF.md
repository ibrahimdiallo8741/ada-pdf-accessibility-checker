# Project Handoff — ADA PDF Accessibility Checker

**Prepared:** October 16, 2026  
**Audience:** Incoming AI agents, student teammates, and future contributors  
**Repository:** https://github.com/ibrahimdiallo8741/ada-pdf-accessibility-checker  
**Last confirmed push:** `b4cde35` on `main`

## 1. Purpose and course context
This is a group course project about making government-funded or public-sector digital information more accessible to people with disabilities. The broader subject is ADA Title II digital accessibility and WCAG 2.1 Level AA. The team initially considered checking both websites and PDFs, then deliberately narrowed this prototype to **PDF documents only**.

The team's goal is to create a simple program that helps identify PDF accessibility issues so a human reviewer can decide what needs attention. The professor has allowed AI-generated programming assistance provided students understand the overall program logic and can explain it. The immediate goal after completing the working code is to prepare the **Phase 3 project document**.

**Scope caution:** The project is not a complete legal compliance audit, automatic remediation tool, or validated screen-reader simulator. The existing code performs metadata/structure/text/image-resource checks, not a real screen-reader playback test.

## 2. Development history (chronological)
1. Created private GitHub repository `ada-pdf-accessibility-checker`, initially containing `.gitignore` and `README.md`.
2. Installed Git for Windows and configured it to work with Visual Studio Code.
3. Cloned the repository into a local Windows folder under `OneDrive\Documents\ada-pdf-accessibility-checker`.
4. Set up Python and a `.venv` virtual environment. Windows PowerShell initially blocked activation of `Activate.ps1`; switching to Command Prompt and running `.venv\Scripts\activate.bat` worked.
5. Installed and verified PyMuPDF (`import pymupdf`). Later installed `pypdf` for structure-tree detection.
6. Created `pdf_checker.py` and incrementally added PDF opening, page count, extractable-text detection, document title, language, and structure-tree checks.
7. Tested a text-based PDF and a PDF with no extractable text, confirming different findings.
8. Configured Git author identity, committed the scanner, and shared the repository with teammates.
9. Expanded the script to detect page image resources and save a JSON accessibility screening report.
10. Successfully ran the expanded script against `problemset6.pdf`, then committed and pushed the working version (`b4cde35`).

A separate Streamlit/web interface was proposed during discussion but was **not demonstrated as integrated into the current repository**. This handoff concerns the confirmed command-line scanner.

## 3. Current user-visible behavior
Launch the script:

```bat
python pdf_checker.py
```

It asks for the path to a PDF. It then prints the page count and findings for:

| Check | What it actually verifies | What it does not verify |
|---|---|---|
| Document title | Nonempty title metadata | Whether title is appropriate or displayed correctly |
| Document language | A declared document language | Accuracy of language or language changes within content |
| PDF structure tree | Presence of `/StructTreeRoot` | Quality of tags, reading order, tables, headings |
| Extractable text | Whether PyMuPDF extracts nonblank text on each page | Usable screen-reader order or meaningful content |
| Image resources | Number of image resources PyMuPDF lists per page | Presence/quality of alt text or all visual objects |

The scanner writes a JSON file named `<PDF-name>_accessibility_report.json` **in the same folder as the scanned PDF**. Its main keys are `file`, `pages`, `checks`, and `warnings`. Individual checks have `check`, `status`, and `details`.

## 4. Confirmed example run
The updated scanner analyzed `problemset6.pdf`:

- Opened successfully; **2 pages**.
- Title metadata: `Microsoft Word - Assignment-6`.
- Document language: **not specified**.
- PDF structure tree: **not found**.
- Page 1: **no extractable text**, **no embedded image resources detected**.
- Page 2: **no extractable text**, **1 image resource found**, requiring manual alt-text review.
- Summary: **7 checks performed**, **5 items needing review**.
- JSON report created successfully: `problemset6_accessibility_report.json`.

An earlier version was tested with `accessible_test.pdf`: 1 page, extractable text, language `en`, structure tree found, but no title metadata. Its filename does not establish actual accessibility.

These results demonstrate the code runs and flags differing document properties. They **do not prove** that any PDF complies with or violates ADA or WCAG.

## 5. Tools and environment
- Python 3.13.5 was observed during setup.
- Visual Studio Code on Windows.
- Git for Windows and GitHub collaboration.
- PyMuPDF (`pymupdf`) for opening PDFs, extracting text, reading metadata/language, and identifying image resources.
- `pypdf` for inspecting `/StructTreeRoot` in the PDF catalog.
- `json` and `pathlib` from the Python standard library for reports and file paths.
- Dependencies tracked in `requirements.txt` (read the current file for exact versions).

### Quick setup
```bat
git clone https://github.com/ibrahimdiallo8741/ada-pdf-accessibility-checker.git
cd ada-pdf-accessibility-checker
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python pdf_checker.py
```

The repository is private, so cloning requires authorized GitHub access. Enter an existing PDF path when prompted. On Windows, do not type quotation marks as part of the path unless the program strips them; the last shared version does strip surrounding double quotes.

## 6. How to explain the program in plain English
> The user gives the program a PDF file. Python opens it and checks whether basic accessibility-related information exists: a document title, language, structural tags, and selectable/extractable text. It also looks for image resources that may need descriptions. The program prints its findings and saves them as a JSON report. It flags things for human review rather than deciding whether the document legally passes or fails ADA requirements.

### Program flow
```text
User enters PDF path
         |
         v
Open PDF (PyMuPDF + pypdf)
         |
         v
Check title, language, structure tree
         |
         v
For each page: inspect extractable text and image resources
         |
         v
Collect FOUND / REVIEW / INFO findings
         |
         v
Print summary + save JSON report beside PDF
```

## 7. What is done versus not yet done

**Done and manually demonstrated:** repository setup, Python environment, PDF opening, page counting, title/language checks, structure-tree presence check, text extraction check, image-resource detection, JSON report generation, and push to GitHub.

**Not established as done:** an upload webpage, hosted deployment, direct screen-reader testing, actual alternative-text extraction/quality assessment, complete WCAG 2.1 AA checking, automatic fixes, full tagged-PDF semantic validation, automated test suite, or a final Phase 3 written submission.

## 8. Recommended immediate next step: Phase 3 documentation
Ask for and read the instructor's **actual Phase 3 prompt/rubric** and the team's earlier phase materials. Do not guess which deliverables are required. Use this handoff as implementation evidence, then draft only what the rubric calls for. A useful narrative may cover the problem, target users, narrowed PDF scope, architecture, implementation, test cases/results, limitations, collaboration, and next steps—**but these are suggestions, not verified rubric requirements**.

## 9. Guidance for future AI agents
- Read `AGENTS.md` first and inspect the actual repository before proposing edits.
- Preserve the existing working CLI behavior and report schema unless the team approves changes.
- Keep language student-friendly and make every code change explainable.
- Do not confuse finding a structure tree with validating the tags.
- Do not confuse counting image resources with checking alternative text.
- Avoid stating that the tool uses a screen reader; that was part of the original idea, not the demonstrated implementation.
- Do not claim a full ADA compliance result from the current checks.
- Prefer narrow changes with tests over rewriting the entire project.
- Do not upload private PDFs or credentials to GitHub.
- Collaborators should pull changes before editing and coordinate branches/merges.

## 10. Questions to resolve with the team
1. What are the exact Phase 3 submission requirements and deadline?
2. Does Phase 3 require a GUI, deployment, screenshots, code, a report, or a demonstration?
3. Which teammates own documentation, testing, and code review?
4. Should future work prioritize accessibility accuracy, user interface, or report presentation?

**Handoff integrity note:** This document summarizes the user's demonstrated development session and pasted code, screenshots, and terminal output. It is not a fresh source-code audit or a verification of the latest GitHub contents.
