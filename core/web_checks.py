from typing import Any

from core.models import Finding


def check_web_title(title_text: str | None, finding_id: str = "W001") -> Finding:
    """WCAG 2.4.2 Page Titled (Level A): Evaluates presence of <title> in <head>."""
    title = (title_text or "").strip()
    if title:
        return Finding(
            finding_id=finding_id,
            input_location="HTML <head>/<title>",
            issue_description=f"Webpage title found: '{title}'.",
            WCAG_criterion="2.4.2 Page Titled (Level A)",
            analysis_method="Deterministic",
            status="Pass",
            remediation_guidance=None,
            additional_details=f"Title: {title}",
        )
    return Finding(
        finding_id=finding_id,
        input_location="HTML <head>",
        issue_description="No webpage title found or title is empty.",
        WCAG_criterion="2.4.2 Page Titled (Level A)",
        analysis_method="Deterministic",
        status="Issue",
        remediation_guidance="Add a descriptive <title> element inside the <head> section of the HTML document.",
        additional_details="<title> element is missing or contains only whitespace.",
    )


def check_web_language(html_lang: str | None, finding_id: str = "W002") -> Finding:
    """WCAG 3.1.1 Language of Page (Level A): Evaluates 'lang' attribute on <html>."""
    lang = (html_lang or "").strip()
    if lang:
        return Finding(
            finding_id=finding_id,
            input_location="HTML <html>",
            issue_description=f"Webpage primary natural language declared: '{lang}'.",
            WCAG_criterion="3.1.1 Language of Page (Level A)",
            analysis_method="Deterministic",
            status="Pass",
            remediation_guidance=None,
            additional_details=f"Language code: {lang}",
        )
    return Finding(
        finding_id=finding_id,
        input_location="HTML <html>",
        issue_description="No language attribute declared on <html> root element.",
        WCAG_criterion="3.1.1 Language of Page (Level A)",
        analysis_method="Deterministic",
        status="Issue",
        remediation_guidance="Specify the primary natural language using the 'lang' attribute on the <html> root element (e.g. <html lang=\"en\">).",
        additional_details="Missing or empty 'lang' attribute on <html>.",
    )


def check_web_images(images: list[dict[str, Any]], finding_id: str = "W003") -> Finding:
    """WCAG 1.1.1 Non-text Content (Level A): Evaluates 'alt' attributes on <img> elements."""
    if not images:
        return Finding(
            finding_id=finding_id,
            input_location="HTML <body>",
            issue_description="No embedded image (<img>) elements detected on webpage.",
            WCAG_criterion="1.1.1 Non-text Content (Level A)",
            analysis_method="Deterministic",
            status="Pass",
            remediation_guidance=None,
            additional_details="0 images present.",
        )

    missing_alt = [img for img in images if not img.get("has_alt", False)]
    if missing_alt:
        return Finding(
            finding_id=finding_id,
            input_location="HTML <body> <img>",
            issue_description=f"{len(missing_alt)} of {len(images)} image element(s) lack an 'alt' attribute.",
            WCAG_criterion="1.1.1 Non-text Content (Level A)",
            analysis_method="Deterministic",
            status="Issue",
            remediation_guidance="Ensure every <img> element contains an alt attribute. Provide concise descriptions for informative images and alt=\"\" for decorative images.",
            additional_details=f"Missing alt on images: {[img.get('src', 'unknown') for img in missing_alt[:5]]}",
        )

    return Finding(
        finding_id=finding_id,
        input_location="HTML <body> <img>",
        issue_description=f"All {len(images)} image element(s) contain an 'alt' attribute. Contextual quality requires review.",
        WCAG_criterion="1.1.1 Non-text Content (Level A)",
        analysis_method="Deterministic",
        status="Needs Human Review",
        remediation_guidance="Review image descriptions to confirm alternative text accurately conveys the image's function or intent.",
        additional_details=f"Discovered {len(images)} image(s) with 'alt' attributes present.",
    )


def check_web_headings(headings: list[tuple[int, str]], finding_id: str = "W004") -> Finding:
    """WCAG 1.3.1 Info and Relationships (Level A): Evaluates heading hierarchy (<h1>-<h6>)."""
    if not headings:
        return Finding(
            finding_id=finding_id,
            input_location="HTML <body>",
            issue_description="No heading elements (<h1>–<h6>) detected on webpage.",
            WCAG_criterion="1.3.1 Info and Relationships (Level A)",
            analysis_method="Deterministic",
            status="Issue",
            remediation_guidance="Structure page content with hierarchical heading elements (<h1>–<h6>) to convey document organization to assistive technologies.",
            additional_details="Webpage lacks structural headings.",
        )

    levels = [lvl for lvl, _ in headings]
    has_h1 = 1 in levels

    if not has_h1:
        return Finding(
            finding_id=finding_id,
            input_location="HTML <body>",
            issue_description="Webpage lacks a top-level <h1> heading.",
            WCAG_criterion="1.3.1 Info and Relationships (Level A)",
            analysis_method="Deterministic",
            status="Issue",
            remediation_guidance="Include at least one top-level <h1> heading identifying the overall page topic.",
            additional_details=f"Present heading levels: {sorted(set(levels))}",
        )

    # Check for skipped heading levels
    skipped: list[str] = []
    prev_lvl = levels[0]
    for lvl in levels[1:]:
        if lvl > prev_lvl + 1:
            skipped.append(f"<h{prev_lvl}> followed by <h{lvl}>")
        prev_lvl = lvl

    if skipped:
        return Finding(
            finding_id=finding_id,
            input_location="HTML <body>",
            issue_description=f"Heading levels skip intermediate ranks: {', '.join(skipped[:3])}.",
            WCAG_criterion="1.3.1 Info and Relationships (Level A)",
            analysis_method="Deterministic",
            status="Issue",
            remediation_guidance="Nest heading levels sequentially without skipping levels (e.g., place <h2> before <h3>).",
            additional_details=f"Skipped instances: {skipped}",
        )

    return Finding(
        finding_id=finding_id,
        input_location="HTML <body>",
        issue_description=f"Document contains hierarchical heading structure with {len(headings)} heading(s) and valid <h1>.",
        WCAG_criterion="1.3.1 Info and Relationships (Level A)",
        analysis_method="Deterministic",
        status="Pass",
        remediation_guidance=None,
        additional_details=f"Heading sequence: {[f'h{l}' for l in levels[:10]]}",
    )


def check_web_form_labels(controls: list[dict[str, Any]], finding_id: str = "W005") -> Finding:
    """WCAG 1.3.1 & 4.1.2 (Level A): Evaluates accessible labels on form controls."""
    if not controls:
        return Finding(
            finding_id=finding_id,
            input_location="HTML <form>",
            issue_description="No interactive form input controls detected.",
            WCAG_criterion="1.3.1 Info and Relationships (Level A)",
            analysis_method="Deterministic",
            status="Pass",
            remediation_guidance=None,
            additional_details="0 input/select/textarea controls.",
        )

    unlabeled = [c for c in controls if not c.get("has_label", False)]
    if unlabeled:
        return Finding(
            finding_id=finding_id,
            input_location="HTML <form>",
            issue_description=f"{len(unlabeled)} of {len(controls)} form control(s) lack accessible programmatic labels.",
            WCAG_criterion="1.3.1 Info and Relationships (Level A)",
            analysis_method="Deterministic",
            status="Issue",
            remediation_guidance="Provide programmatic labels for all form controls using <label for=\"id\">, aria-label, or aria-labelledby.",
            additional_details=f"Unlabeled controls: {[c.get('name') or c.get('id') or c.get('tag') for c in unlabeled[:5]]}",
        )

    return Finding(
        finding_id=finding_id,
        input_location="HTML <form>",
        issue_description=f"All {len(controls)} form control(s) have associated programmatic labels or ARIA descriptions.",
        WCAG_criterion="1.3.1 Info and Relationships (Level A)",
        analysis_method="Deterministic",
        status="Pass",
        remediation_guidance=None,
        additional_details=f"{len(controls)} labeled control(s).",
    )


def check_web_bypass_blocks(
    has_skip_link: bool, has_main_landmark: bool, finding_id: str = "W006"
) -> Finding:
    """WCAG 2.4.1 Bypass Blocks (Level A): Evaluates skip links and <main> landmark."""
    if has_skip_link or has_main_landmark:
        mechanisms = []
        if has_skip_link:
            mechanisms.append("skip navigation link")
        if has_main_landmark:
            mechanisms.append("<main> landmark")
        return Finding(
            finding_id=finding_id,
            input_location="HTML <body>",
            issue_description=f"Bypass mechanism detected ({' and '.join(mechanisms)}) for skipping repetitive navigation.",
            WCAG_criterion="2.4.1 Bypass Blocks (Level A)",
            analysis_method="Deterministic",
            status="Pass",
            remediation_guidance=None,
            additional_details=f"Mechanisms: {', '.join(mechanisms)}",
        )

    return Finding(
        finding_id=finding_id,
        input_location="HTML <body>",
        issue_description="No skip navigation link or <main> landmark region detected.",
        WCAG_criterion="2.4.1 Bypass Blocks (Level A)",
        analysis_method="Deterministic",
        status="Needs Human Review",
        remediation_guidance="Provide a skip-to-content link at the beginning of the body or declare a semantic <main> landmark region.",
        additional_details="Repetitive navigation cannot be easily bypassed by keyboard and screen-reader users.",
    )

