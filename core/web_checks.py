import re
from typing import Any

from core.contrast_analyzer import compute_contrast_ratio
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


def check_web_tables(tables: list[dict[str, Any]], finding_id: str = "W007") -> Finding:
    """WCAG 1.3.1 Info and Relationships (Level A): Evaluates data table header markup (<th>)."""
    if not tables:
        return Finding(
            finding_id=finding_id,
            input_location="HTML <body> <table>",
            issue_description="No data table (<table>) elements detected.",
            WCAG_criterion="1.3.1 Info and Relationships (Level A)",
            analysis_method="Deterministic",
            status="Pass",
            remediation_guidance=None,
            additional_details="0 tables present.",
        )

    unheadered = [t for t in tables if not t.get("has_th", False)]
    if unheadered:
        return Finding(
            finding_id=finding_id,
            input_location="HTML <body> <table>",
            issue_description=f"{len(unheadered)} of {len(tables)} table(s) lack <th> header cell elements.",
            WCAG_criterion="1.3.1 Info and Relationships (Level A)",
            analysis_method="Deterministic",
            status="Issue",
            remediation_guidance="Structure data tables using <th> elements with proper 'scope' attributes to identify row or column headers.",
            additional_details=f"{len(unheadered)} table(s) have data cells (<td>) without associated header cells (<th>).",
        )

    return Finding(
        finding_id=finding_id,
        input_location="HTML <body> <table>",
        issue_description=f"All {len(tables)} data table(s) contain proper <th> header cell elements.",
        WCAG_criterion="1.3.1 Info and Relationships (Level A)",
        analysis_method="Deterministic",
        status="Pass",
        remediation_guidance=None,
        additional_details=f"{len(tables)} table(s) evaluated with header markup.",
    )


def check_web_lists(lists: list[dict[str, Any]], finding_id: str = "W008") -> Finding:
    """WCAG 1.3.1 Info and Relationships (Level A): Evaluates list structural consistency (<ul>/<ol> and <li>)."""
    if not lists:
        return Finding(
            finding_id=finding_id,
            input_location="HTML <body> <ol>/<ul>",
            issue_description="No list (<ol> or <ul>) elements detected.",
            WCAG_criterion="1.3.1 Info and Relationships (Level A)",
            analysis_method="Deterministic",
            status="Pass",
            remediation_guidance=None,
            additional_details="0 lists present.",
        )

    empty_or_malformed = [l for l in lists if l.get("li_count", 0) == 0]
    if empty_or_malformed:
        return Finding(
            finding_id=finding_id,
            input_location="HTML <body> <ol>/<ul>",
            issue_description=f"{len(empty_or_malformed)} of {len(lists)} list element(s) contain no <li> list items.",
            WCAG_criterion="1.3.1 Info and Relationships (Level A)",
            analysis_method="Deterministic",
            status="Issue",
            remediation_guidance="Ensure all <ol> and <ul> list containers properly encapsulate items within <li> elements.",
            additional_details=f"{len(empty_or_malformed)} empty or malformed list container(s).",
        )

    total_items = sum(l.get("li_count", 0) for l in lists)
    return Finding(
        finding_id=finding_id,
        input_location="HTML <body> <ol>/<ul>",
        issue_description=f"All {len(lists)} list element(s) are properly structured with {total_items} <li> item(s).",
        WCAG_criterion="1.3.1 Info and Relationships (Level A)",
        analysis_method="Deterministic",
        status="Pass",
        remediation_guidance=None,
        additional_details=f"{len(lists)} valid list container(s).",
    )


NAMED_CSS_COLORS: dict[str, tuple[float, float, float]] = {
    "black": (0.0, 0.0, 0.0),
    "white": (1.0, 1.0, 1.0),
    "red": (1.0, 0.0, 0.0),
    "green": (0.0, 0.502, 0.0),
    "blue": (0.0, 0.0, 1.0),
    "yellow": (1.0, 1.0, 0.0),
    "gray": (0.502, 0.502, 0.502),
    "grey": (0.502, 0.502, 0.502),
    "silver": (0.753, 0.753, 0.753),
    "navy": (0.0, 0.0, 0.502),
    "teal": (0.0, 0.502, 0.502),
    "purple": (0.502, 0.0, 0.502),
    "maroon": (0.502, 0.0, 0.0),
    "olive": (0.502, 0.502, 0.0),
    "lime": (0.0, 1.0, 0.0),
    "aqua": (0.0, 1.0, 1.0),
    "cyan": (0.0, 1.0, 1.0),
    "fuchsia": (1.0, 0.0, 1.0),
    "magenta": (1.0, 0.0, 1.0),
    "orange": (1.0, 0.647, 0.0),
    "darkgray": (0.663, 0.663, 0.663),
    "darkgrey": (0.663, 0.663, 0.663),
    "lightgray": (0.827, 0.827, 0.827),
    "lightgrey": (0.827, 0.827, 0.827),
}


def parse_css_color(raw_val: str) -> tuple[float, float, float] | None:
    """Parses a CSS color string (hex, rgb/rgba, or named color) into normalized (r, g, b)."""
    raw = raw_val.strip().lower()
    if not raw or raw in ("transparent", "inherit", "initial", "unset", "none"):
        return None
    if raw in NAMED_CSS_COLORS:
        return NAMED_CSS_COLORS[raw]

    # Hex color: #rgb, #rgba, #rrggbb, #rrggbbaa
    if raw.startswith("#"):
        hex_val = raw[1:]
        if len(hex_val) == 3:
            hex_val = "".join(c * 2 for c in hex_val)
        elif len(hex_val) == 4:
            hex_val = "".join(c * 2 for c in hex_val[:3])
        elif len(hex_val) >= 6:
            hex_val = hex_val[:6]
        else:
            return None
        try:
            r = int(hex_val[0:2], 16) / 255.0
            g = int(hex_val[2:4], 16) / 255.0
            b = int(hex_val[4:6], 16) / 255.0
            return (r, g, b)
        except ValueError:
            return None

    # rgb(...) / rgba(...)
    m = re.match(r"^rgba?\s*\(\s*(\d+%?)\s*,\s*(\d+%?)\s*,\s*(\d+%?)", raw)
    if m:
        def parse_comp(c: str) -> float:
            if c.endswith("%"):
                return max(0.0, min(1.0, float(c[:-1]) / 100.0))
            return max(0.0, min(1.0, float(c) / 255.0))
        try:
            return (parse_comp(m.group(1)), parse_comp(m.group(2)), parse_comp(m.group(3)))
        except ValueError:
            return None

    return None


def parse_inline_styles(style_str: str) -> dict[str, str]:
    """Splits an inline style attribute into a normalized dictionary of property -> value."""
    props: dict[str, str] = {}
    for part in style_str.split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            props[k.strip().lower()] = v.strip().lower()
    return props


def check_web_contrast(
    styled_elements: list[dict[str, Any]],
    finding_id: str = "W009",
) -> Finding:
    """WCAG 1.4.3 Contrast (Minimum) (Level AA): Evaluates inline CSS text-to-background contrast."""
    if not styled_elements:
        return Finding(
            finding_id=finding_id,
            input_location="HTML <body> style",
            issue_description="No inline color styles detected. Visual contrast depends on external stylesheets or browser defaults.",
            WCAG_criterion="1.4.3 Contrast (Minimum) (Level AA)",
            analysis_method="Deterministic",
            status="Needs Human Review",
            remediation_guidance="Inspect external CSS stylesheets using a contrast evaluation tool to ensure text-to-background contrast ratios satisfy WCAG AA (4.5:1 normal text, 3:1 large text).",
            additional_details="0 elements with inline color styles present.",
        )

    # 1. Determine baseline document background from body/html if declared
    default_bg = (1.0, 1.0, 1.0)
    for elem in styled_elements:
        if elem.get("tag") in ("body", "html"):
            st = parse_inline_styles(elem.get("style", ""))
            bg_raw = st.get("background-color") or st.get("background")
            if bg_raw:
                parsed_bg = parse_css_color(bg_raw)
                if parsed_bg is not None:
                    default_bg = parsed_bg
            break

    # 2. Evaluate contrast on styled text elements
    evaluated_count = 0
    failing_elements: list[str] = []
    min_observed_ratio = 21.0

    for elem in styled_elements:
        tag = elem.get("tag", "element")
        if tag in ("body", "html"):
            continue

        st = parse_inline_styles(elem.get("style", ""))
        fg_raw = st.get("color")
        bg_raw = st.get("background-color") or st.get("background")

        if not fg_raw and not bg_raw:
            continue

        fg_color = parse_css_color(fg_raw) if fg_raw else None
        bg_color = parse_css_color(bg_raw) if bg_raw else default_bg

        # If only background is defined, assume standard dark text (0, 0, 0)
        if fg_color is None:
            fg_color = (0.0, 0.0, 0.0)

        ratio = compute_contrast_ratio(fg_color, bg_color)
        evaluated_count += 1
        if ratio < min_observed_ratio:
            min_observed_ratio = ratio

        # Determine threshold: 3.0:1 for large text (h1, h2, or explicit font size >= 18pt / 24px)
        is_large_text = tag in ("h1", "h2")
        font_size_raw = st.get("font-size", "")
        if "px" in font_size_raw:
            try:
                px_val = float(re.findall(r"[\d.]+", font_size_raw)[0])
                if px_val >= 24.0 or (px_val >= 18.5 and "bold" in st.get("font-weight", "")):
                    is_large_text = True
            except Exception:
                pass
        elif "pt" in font_size_raw:
            try:
                pt_val = float(re.findall(r"[\d.]+", font_size_raw)[0])
                if pt_val >= 18.0 or (pt_val >= 14.0 and "bold" in st.get("font-weight", "")):
                    is_large_text = True
            except Exception:
                pass

        required_ratio = 3.0 if is_large_text else 4.5
        if ratio < required_ratio:
            failing_elements.append(
                f"<{tag}> element with style '{elem.get('style', '')}' has contrast ratio {ratio}:1 (required: {required_ratio}:1)"
            )

    if evaluated_count == 0:
        return Finding(
            finding_id=finding_id,
            input_location="HTML <body> style",
            issue_description="Inline styles present but contain no text or background color declarations. Visual contrast requires external CSS inspection.",
            WCAG_criterion="1.4.3 Contrast (Minimum) (Level AA)",
            analysis_method="Deterministic",
            status="Needs Human Review",
            remediation_guidance="Inspect external CSS stylesheets using a contrast evaluation tool to ensure text-to-background contrast ratios satisfy WCAG AA (4.5:1 normal text, 3:1 large text).",
            additional_details=f"Evaluated {len(styled_elements)} styled element(s) with no color properties.",
        )

    if failing_elements:
        return Finding(
            finding_id=finding_id,
            input_location="HTML <body> style",
            issue_description=f"{len(failing_elements)} of {evaluated_count} element(s) with inline styles fail WCAG AA contrast ratio requirements.",
            WCAG_criterion="1.4.3 Contrast (Minimum) (Level AA)",
            analysis_method="Deterministic",
            status="Issue",
            remediation_guidance="Increase the contrast between foreground text and background colors to achieve at least 4.5:1 for standard text and 3:1 for large text.",
            additional_details="; ".join(failing_elements[:3]),
        )

    return Finding(
        finding_id=finding_id,
        input_location="HTML <body> style",
        issue_description=f"All {evaluated_count} element(s) with inline color styles satisfy WCAG AA contrast requirements (minimum observed ratio: {min_observed_ratio}:1).",
        WCAG_criterion="1.4.3 Contrast (Minimum) (Level AA)",
        analysis_method="Deterministic",
        status="Pass",
        remediation_guidance=None,
        additional_details=f"Evaluated {evaluated_count} styled element(s); minimum ratio {min_observed_ratio}:1.",
    )


