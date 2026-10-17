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
