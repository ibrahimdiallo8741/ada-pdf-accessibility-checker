"""Visual & Contrast Analysis Engine (Milestone 7).

Evaluates visual accessibility heuristics strictly in memory without writing
any raster image to disk:
1. Text Contrast Ratio (WCAG 1.4.3 / Level AA: 4.5:1 normal, 3:1 large text)
2. Graphical Object & Vector Path Contrast (WCAG 1.4.11 / Level AA: 3:1)
"""

from typing import Any

import pymupdf

from core.models import Finding


def srgb_to_relative_luminance(r: float, g: float, b: float) -> float:
    """Calculates relative luminance (L) according to WCAG 2.1 specifications.
    
    Channels r, g, b should be normalized in [0.0, 1.0].
    """
    def channel_linear(c: float) -> float:
        c = max(0.0, min(1.0, c))
        if c <= 0.04045:
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4

    r_lin = channel_linear(r)
    g_lin = channel_linear(g)
    b_lin = channel_linear(b)
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def compute_contrast_ratio(
    color1: tuple[float, float, float],
    color2: tuple[float, float, float],
) -> float:
    """Computes the WCAG 2.1 contrast ratio between two sRGB colors (1.0:1 to 21.0:1)."""
    l1 = srgb_to_relative_luminance(*color1)
    l2 = srgb_to_relative_luminance(*color2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return round((lighter + 0.05) / (darker + 0.05), 2)


def int_color_to_rgb(color_int: int | None) -> tuple[float, float, float]:
    """Converts a 24-bit sRGB integer (0xRRGGBB) to normalized (r, g, b) in [0.0, 1.0]."""
    if color_int is None or not isinstance(color_int, int):
        return (0.0, 0.0, 0.0)
    r = ((color_int >> 16) & 0xFF) / 255.0
    g = ((color_int >> 8) & 0xFF) / 255.0
    b = (color_int & 0xFF) / 255.0
    return (r, g, b)


def _normalize_drawing_color(raw_color: Any) -> tuple[float, float, float] | None:
    """Converts a drawing stroke or fill color to normalized sRGB tuple (r, g, b)."""
    if not raw_color:
        return None
    if isinstance(raw_color, (list, tuple)):
        if len(raw_color) == 1:
            val = float(raw_color[0])
            return (val, val, val)
        if len(raw_color) >= 3:
            return (float(raw_color[0]), float(raw_color[1]), float(raw_color[2]))
    if isinstance(raw_color, (int, float)):
        val = float(raw_color)
        return (val, val, val)
    return None


def find_background_color_for_bbox(
    bbox: tuple[float, float, float, float],
    drawings: list[dict[str, Any]],
    default_bg: tuple[float, float, float] = (1.0, 1.0, 1.0),
) -> tuple[float, float, float]:
    """Finds the background color behind a text span bbox by inspecting enclosing vector drawings."""
    if not drawings:
        return default_bg

    bx0, by0, bx1, by1 = bbox
    span_center_x = (bx0 + bx1) / 2.0
    span_center_y = (by0 + by1) / 2.0

    # Inspect drawings from topmost to bottommost
    for d in reversed(drawings):
        rect = d.get("rect")
        if not rect:
            continue
        # Check if span center point is within the drawing rect
        if rect.x0 <= span_center_x <= rect.x1 and rect.y0 <= span_center_y <= rect.y1:
            fill_color = _normalize_drawing_color(d.get("fill"))
            if fill_color is not None:
                return fill_color

    return default_bg


def analyze_page_contrast(
    page: pymupdf.Page,
    page_number: int,
    finding_id: str = "F001",
) -> Finding:
    """Evaluates text contrast across all text spans on a PDF page in memory."""
    tdict = page.get_text("dict")
    raw_drawings = page.get_drawings()
    drawings = [d for d in raw_drawings if d.get("fill") is not None and d.get("rect")]

    tested_spans = 0
    failing_spans: list[dict[str, Any]] = []
    min_ratio = 21.0

    for b in tdict.get("blocks", []):
        if "lines" not in b:
            continue
        for line in b.get("lines", []):
            for span in line.get("spans", []):
                text = (span.get("text") or "").strip()
                if not text:
                    continue

                size = float(span.get("size", 12.0))
                flags = int(span.get("flags", 0))
                font_name = str(span.get("font", "")).lower()
                is_bold = bool((flags & 2) or ("bold" in font_name))
                is_large = (size >= 18.0) or (size >= 14.0 and is_bold)
                req_ratio = 3.0 if is_large else 4.5

                fg_color = int_color_to_rgb(span.get("color"))
                bbox = span.get("bbox", (0, 0, 0, 0))
                bg_color = find_background_color_for_bbox(bbox, drawings)

                ratio = compute_contrast_ratio(fg_color, bg_color)
                tested_spans += 1
                if ratio < min_ratio:
                    min_ratio = ratio

                if ratio < req_ratio:
                    failing_spans.append({
                        "text": text[:30],
                        "ratio": ratio,
                        "required": req_ratio,
                        "is_large": is_large,
                    })

    if tested_spans == 0:
        return Finding(
            finding_id=finding_id,
            input_location=f"Page {page_number}",
            issue_description=f"Page {page_number} contains no text elements for contrast evaluation.",
            WCAG_criterion="1.4.3 Contrast (Minimum) (Level AA)",
            analysis_method="Deterministic",
            status="Pass",
            remediation_guidance=None,
            additional_details="No text spans detected on page.",
        )

    if failing_spans:
        worst_span = min(failing_spans, key=lambda s: s["ratio"])
        return Finding(
            finding_id=finding_id,
            input_location=f"Page {page_number}",
            issue_description=(
                f"Page {page_number} has {len(failing_spans)} text span(s) failing WCAG AA contrast "
                f"(lowest: {worst_span['ratio']:.1f}:1 on '{worst_span['text']}', required: {worst_span['required']}:1)."
            ),
            WCAG_criterion="1.4.3 Contrast (Minimum) (Level AA)",
            analysis_method="Deterministic",
            status="Issue",
            remediation_guidance=(
                "Increase luminance contrast between text and its background to meet the minimum "
                "4.5:1 ratio (3:1 for large text)."
            ),
            additional_details=(
                f"Tested {tested_spans} text span(s). {len(failing_spans)} span(s) fell below "
                f"WCAG 1.4.3 thresholds. Lowest ratio: {worst_span['ratio']:.1f}:1."
            ),
        )

    return Finding(
        finding_id=finding_id,
        input_location=f"Page {page_number}",
        issue_description=(
            f"Page {page_number} text contrast satisfies WCAG AA requirements "
            f"(tested {tested_spans} text span(s); minimum ratio: {min_ratio:.1f}:1)."
        ),
        WCAG_criterion="1.4.3 Contrast (Minimum) (Level AA)",
        analysis_method="Deterministic",
        status="Pass",
        remediation_guidance=None,
        additional_details=f"All {tested_spans} text span(s) meet or exceed required contrast ratios.",
    )


def analyze_graphical_contrast(
    page: pymupdf.Page,
    page_number: int,
    finding_id: str = "F001",
) -> Finding | None:
    """Evaluates vector path and graphical boundary contrast (WCAG 1.4.11 / Level AA: 3:1)."""
    drawings = page.get_drawings()
    if not drawings:
        return None

    low_contrast_count = 0
    total_evaluated = 0

    for d in drawings:
        rect = d.get("rect")
        if not rect:
            continue

        color = _normalize_drawing_color(d.get("color"))
        fill = _normalize_drawing_color(d.get("fill"))

        if color is not None:
            total_evaluated += 1
            ratio = compute_contrast_ratio(color, (1.0, 1.0, 1.0))
            if ratio < 3.0:
                low_contrast_count += 1
        elif fill is not None:
            total_evaluated += 1
            ratio = compute_contrast_ratio(fill, (1.0, 1.0, 1.0))
            if ratio < 3.0:
                low_contrast_count += 1

    if total_evaluated == 0:
        return None

    if low_contrast_count > 0:
        return Finding(
            finding_id=finding_id,
            input_location=f"Page {page_number}",
            issue_description=(
                f"Page {page_number} contains {low_contrast_count} graphical/vector element(s) "
                "with contrast ratio below 3:1 against the background."
            ),
            WCAG_criterion="1.4.11 Non-text Contrast (Level AA)",
            analysis_method="Deterministic",
            status="Needs Human Review",
            remediation_guidance=(
                "Ensure important graphical elements, icons, and UI boundaries have at least 3:1 "
                "contrast against adjacent colors."
            ),
            additional_details=(
                f"Evaluated {total_evaluated} vector path(s). {low_contrast_count} element(s) "
                "have low luminance contrast. Verify if these are informative or decorative."
            ),
        )

    return Finding(
        finding_id=finding_id,
        input_location=f"Page {page_number}",
        issue_description=f"Page {page_number} graphical objects satisfy WCAG AA non-text contrast (3:1 minimum).",
        WCAG_criterion="1.4.11 Non-text Contrast (Level AA)",
        analysis_method="Deterministic",
        status="Pass",
        remediation_guidance=None,
        additional_details=f"Evaluated {total_evaluated} vector path(s).",
    )
