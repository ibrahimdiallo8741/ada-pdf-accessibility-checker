from typing import Any

from core.models import Finding


def check_title(metadata: dict[str, Any], finding_id: str = "F001") -> Finding:
    title = (metadata.get("title") or "").strip()
    if title:
        return Finding(
            finding_id=finding_id,
            input_location="Document Metadata",
            issue_description=f"Document title found: '{title}'.",
            WCAG_criterion="2.4.2 Page Titled (Level A)",
            analysis_method="Deterministic",
            status="Pass",
            remediation_guidance=None,
            additional_details=f"Title: {title}",
        )
    return Finding(
        finding_id=finding_id,
        input_location="Document Metadata",
        issue_description="No document title found in metadata.",
        WCAG_criterion="2.4.2 Page Titled (Level A)",
        analysis_method="Deterministic",
        status="Issue",
        remediation_guidance="Specify a descriptive document title in the PDF information dictionary.",
        additional_details="Title metadata is empty or absent.",
    )


def check_language(language_code: str | None, finding_id: str = "F002") -> Finding:
    lang = (language_code or "").strip()
    if lang:
        return Finding(
            finding_id=finding_id,
            input_location="Document Catalog",
            issue_description=f"Default document language declared: '{lang}'.",
            WCAG_criterion="3.1.1 Language of Page (Level A)",
            analysis_method="Deterministic",
            status="Pass",
            remediation_guidance=None,
            additional_details=f"Language code: {lang}",
        )
    return Finding(
        finding_id=finding_id,
        input_location="Document Catalog",
        issue_description="No default document language specified in catalog.",
        WCAG_criterion="3.1.1 Language of Page (Level A)",
        analysis_method="Deterministic",
        status="Issue",
        remediation_guidance="Set the default document language using the /Lang entry in the PDF catalog.",
        additional_details="Document catalog /Lang entry is missing.",
    )


def check_structure(root_object: Any, finding_id: str = "F003") -> Finding:
    has_struct = False
    try:
        if root_object and "/StructTreeRoot" in root_object:
            has_struct = True
    except (TypeError, KeyError, AttributeError):
        has_struct = False

    if has_struct:
        return Finding(
            finding_id=finding_id,
            input_location="Document Catalog /Root",
            issue_description="PDF structure tree found (/StructTreeRoot present). Tag presence confirmed.",
            WCAG_criterion="1.3.1 Info and Relationships (Level A)",
            analysis_method="Deterministic",
            status="Needs Human Review",
            remediation_guidance="Verify that tag semantics (<h1>, <p>, <table>) and reading order match visual layout.",
            additional_details="Structural root exists; tag quality requires human verification.",
        )
    return Finding(
        finding_id=finding_id,
        input_location="Document Catalog /Root",
        issue_description="No PDF structure tree found (/StructTreeRoot missing). Document is untagged.",
        WCAG_criterion="1.3.1 Info and Relationships (Level A)",
        analysis_method="Deterministic",
        status="Issue",
        remediation_guidance="Add structural tags to the PDF to ensure accessibility for screen readers.",
        additional_details="Assistive technology cannot determine reading order or semantics without tags.",
    )


def check_page_text(page_number: int, text: str, finding_id: str) -> Finding:
    cleaned = (text or "").strip()
    if cleaned:
        return Finding(
            finding_id=finding_id,
            input_location=f"Page {page_number}",
            issue_description=f"Page {page_number} contains extractable text.",
            WCAG_criterion="1.4.5 Images of Text (Level AA)",
            analysis_method="Deterministic",
            status="Pass",
            remediation_guidance=None,
            additional_details=f"Extracted {len(cleaned)} characters.",
        )
    return Finding(
        finding_id=finding_id,
        input_location=f"Page {page_number}",
        issue_description=f"Page {page_number} contains no extractable text.",
        WCAG_criterion="1.4.5 Images of Text (Level AA)",
        analysis_method="Deterministic",
        status="Needs Human Review",
        remediation_guidance="Apply Optical Character Recognition (OCR) if page is a scanned document.",
        additional_details="Page lacks a digital text stream; assistive tech cannot read text.",
    )


def check_page_images(page_number: int, image_count: int, finding_id: str) -> Finding:
    if image_count > 0:
        return Finding(
            finding_id=finding_id,
            input_location=f"Page {page_number}",
            issue_description=f"Page {page_number} contains {image_count} embedded image resource(s).",
            WCAG_criterion="1.1.1 Non-text Content (Level A)",
            analysis_method="Deterministic",
            status="Needs Human Review",
            remediation_guidance="Ensure meaningful images have alternative text (/Alt) and decorative images are tagged as artifacts.",
            additional_details=f"Found {image_count} image XObject(s).",
        )
    return Finding(
        finding_id=finding_id,
        input_location=f"Page {page_number}",
        issue_description=f"Page {page_number} contains no embedded image resources.",
        WCAG_criterion="1.1.1 Non-text Content (Level A)",
        analysis_method="Deterministic",
        status="Pass",
        remediation_guidance=None,
        additional_details="No image XObjects detected.",
    )


def check_pdf_outlines(root_object: Any, page_count: int, finding_id: str = "F004") -> Finding | None:
    """WCAG 2.4.1 Bypass Blocks (Level A): For multi-page PDFs (> 3 pages), checks for /Outlines bookmark tree."""
    if page_count <= 3:
        return None

    has_outlines = False
    try:
        if root_object and "/Outlines" in root_object:
            outlines_obj = root_object["/Outlines"]
            if hasattr(outlines_obj, "get_object"):
                outlines_obj = outlines_obj.get_object()
            if outlines_obj and ("/First" in outlines_obj or "/Count" in outlines_obj):
                has_outlines = True
    except Exception:
        has_outlines = False

    if has_outlines:
        return Finding(
            finding_id=finding_id,
            input_location="Document Catalog /Outlines",
            issue_description=f"Document contains navigational bookmark outlines ({page_count} pages).",
            WCAG_criterion="2.4.1 Bypass Blocks (Level A)",
            analysis_method="Deterministic",
            status="Pass",
            remediation_guidance=None,
            additional_details="Bookmark tree allows users to bypass repeated blocks and jump to sections.",
        )

    return Finding(
        finding_id=finding_id,
        input_location="Document Catalog /Outlines",
        issue_description=f"Multi-page document ({page_count} pages) lacks navigational bookmark outlines (/Outlines).",
        WCAG_criterion="2.4.1 Bypass Blocks (Level A)",
        analysis_method="Deterministic",
        status="Needs Human Review",
        remediation_guidance="Add bookmark outlines to multi-page documents so users can navigate directly to sections.",
        additional_details="Screen reader and keyboard users cannot easily bypass preceding pages without bookmarks.",
    )


def check_pdf_form_fields(root_object: Any, finding_id: str = "F005") -> list[Finding]:
    """WCAG 1.3.1 & 4.1.2: Evaluates accessible descriptions (/TU) on interactive form fields."""
    findings: list[Finding] = []
    if not root_object or "/AcroForm" not in root_object:
        return findings

    try:
        acro = root_object["/AcroForm"]
        if hasattr(acro, "get_object"):
            acro = acro.get_object()
        if not acro or "/Fields" not in acro:
            return findings

        fields = acro["/Fields"]
        if hasattr(fields, "get_object"):
            fields = fields.get_object()
        if not isinstance(fields, list) or not fields:
            return findings

        unlabeled = 0
        total = 0
        for f in fields:
            if hasattr(f, "get_object"):
                f = f.get_object()
            if not f or not hasattr(f, "get"):
                continue
            total += 1
            tu = f.get("/TU")
            if not tu or not str(tu).strip():
                unlabeled += 1

        if total == 0:
            return findings

        if unlabeled > 0:
            findings.append(Finding(
                finding_id=finding_id,
                input_location="Document Catalog /AcroForm",
                issue_description=f"{unlabeled} of {total} interactive form field(s) lack accessible descriptions (/TU attribute).",
                WCAG_criterion="1.3.1 Info and Relationships (Level A)",
                analysis_method="Deterministic",
                status="Issue",
                remediation_guidance="Provide a descriptive tooltip (/TU attribute) for all interactive form fields to serve as an accessible name.",
                additional_details="Assistive technologies read /TU as the field label for interactive inputs.",
            ))
        else:
            findings.append(Finding(
                finding_id=finding_id,
                input_location="Document Catalog /AcroForm",
                issue_description=f"All {total} interactive form field(s) have accessible descriptions (/TU).",
                WCAG_criterion="1.3.1 Info and Relationships (Level A)",
                analysis_method="Deterministic",
                status="Pass",
                remediation_guidance=None,
                additional_details=f"{total} form field(s) verified with /TU attributes.",
            ))
    except Exception:
        pass

    return findings

