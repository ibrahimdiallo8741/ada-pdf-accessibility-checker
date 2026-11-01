import uuid
from html.parser import HTMLParser
from typing import Any

from core.models import Finding, ScanResult, ScanSummary
from core.web_checks import (
    check_web_bypass_blocks,
    check_web_form_labels,
    check_web_headings,
    check_web_images,
    check_web_language,
    check_web_title,
)


class WebDOMExtractor(HTMLParser):
    """Streaming, zero-disk in-memory HTML parser extracting accessibility landmarks and elements."""

    def __init__(self) -> None:
        super().__init__()
        self.html_lang: str | None = None
        self.title_text: str | None = None
        self._in_title: bool = False
        self._current_title_chunks: list[str] = []

        self.images: list[dict[str, Any]] = []
        self.headings: list[tuple[int, str]] = []
        self._in_heading: int = 0
        self._current_heading_chunks: list[str] = []

        # Form controls & labels
        self.controls: list[dict[str, Any]] = []
        self._labels_for: set[str] = set()
        self._in_label: bool = False

        # Bypass blocks
        self.has_skip_link: bool = False
        self.has_main_landmark: bool = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = {k.lower(): (v or "") for k, v in attrs}
        tag_lower = tag.lower()

        if tag_lower == "html":
            self.html_lang = attr_dict.get("lang")

        elif tag_lower == "title":
            self._in_title = True
            self._current_title_chunks = []

        elif tag_lower in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._in_heading = int(tag_lower[1])
            self._current_heading_chunks = []

        elif tag_lower == "img":
            has_alt = "alt" in attr_dict
            self.images.append({
                "src": attr_dict.get("src", ""),
                "alt": attr_dict.get("alt", ""),
                "has_alt": has_alt,
            })

        elif tag_lower == "label":
            self._in_label = True
            target_for = attr_dict.get("for")
            if target_for:
                self._labels_for.add(target_for.strip())

        elif tag_lower in ("input", "select", "textarea"):
            control_type = attr_dict.get("type", "").lower()
            # Ignore hidden inputs and submit/button inputs that have intrinsic labels
            if control_type not in ("hidden", "submit", "button", "reset", "image"):
                cid = attr_dict.get("id", "").strip()
                has_aria = bool(attr_dict.get("aria-label") or attr_dict.get("aria-labelledby"))
                self.controls.append({
                    "tag": tag_lower,
                    "type": control_type,
                    "id": cid,
                    "name": attr_dict.get("name", "").strip(),
                    "has_aria": has_aria,
                    "in_label": self._in_label,
                })

        elif tag_lower == "main" or attr_dict.get("role") == "main":
            self.has_main_landmark = True

        elif tag_lower == "a":
            href = attr_dict.get("href", "").strip().lower()
            if href.startswith("#") and len(href) > 1:
                # Potential skip link
                self.has_skip_link = True

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if tag_lower == "title":
            self._in_title = False
            self.title_text = "".join(self._current_title_chunks).strip()

        elif tag_lower in ("h1", "h2", "h3", "h4", "h5", "h6"):
            text = "".join(self._current_heading_chunks).strip()
            if self._in_heading > 0:
                self.headings.append((self._in_heading, text))
            self._in_heading = 0

        elif tag_lower == "label":
            self._in_label = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._current_title_chunks.append(data)
        if self._in_heading > 0:
            self._current_heading_chunks.append(data)

    def finalize(self) -> None:
        """Post-process relationships such as explicit label 'for' associations."""
        for c in self.controls:
            c_id = c.get("id")
            c["has_label"] = (
                c.get("in_label", False)
                or c.get("has_aria", False)
                or (bool(c_id) and c_id in self._labels_for)
            )


def screen_html(
    html_content: str,
    url: str,
    scan_id: str | None = None,
) -> ScanResult:
    """Performs deterministic accessibility screening on raw HTML content in memory."""
    if scan_id is None:
        scan_id = f"W-{uuid.uuid4().hex[:8].upper()}"

    extractor = WebDOMExtractor()
    try:
        extractor.feed(html_content or "")
        extractor.finalize()
    except Exception as exc:
        finding = Finding(
            finding_id="W001",
            input_location="HTML Document",
            issue_description=f"HTML parsing failure: {exc}",
            WCAG_criterion="General Accessibility",
            analysis_method="Deterministic",
            status="Could Not Evaluate",
            remediation_guidance="Ensure target webpage delivers valid, well-formed HTML syntax.",
        )
        return ScanResult(
            scan_id=scan_id,
            file_or_url=url,
            pages=1,
            summary=ScanSummary(checks=1, passed=0, issues=0, human_review=0, could_not_evaluate=1),
            findings=[finding],
        )

    findings: list[Finding] = []
    f_counter = 1

    # 1. Page Title Check (WCAG 2.4.2)
    findings.append(check_web_title(extractor.title_text, finding_id=f"W{f_counter:03d}"))
    f_counter += 1

    # 2. Page Language Check (WCAG 3.1.1)
    findings.append(check_web_language(extractor.html_lang, finding_id=f"W{f_counter:03d}"))
    f_counter += 1

    # 3. Image Alt Attributes (WCAG 1.1.1)
    findings.append(check_web_images(extractor.images, finding_id=f"W{f_counter:03d}"))
    f_counter += 1

    # 4. Heading Structure (WCAG 1.3.1)
    findings.append(check_web_headings(extractor.headings, finding_id=f"W{f_counter:03d}"))
    f_counter += 1

    # 5. Form Control Labels (WCAG 1.3.1 & 4.1.2)
    findings.append(check_web_form_labels(extractor.controls, finding_id=f"W{f_counter:03d}"))
    f_counter += 1

    # 6. Bypass Blocks (WCAG 2.4.1)
    findings.append(
        check_web_bypass_blocks(
            has_skip_link=extractor.has_skip_link,
            has_main_landmark=extractor.has_main_landmark,
            finding_id=f"W{f_counter:03d}",
        )
    )

    summary = ScanSummary(
        checks=len(findings),
        passed=sum(1 for f in findings if f.status == "Pass"),
        issues=sum(1 for f in findings if f.status == "Issue"),
        human_review=sum(1 for f in findings if f.status == "Needs Human Review"),
        could_not_evaluate=sum(1 for f in findings if f.status == "Could Not Evaluate"),
    )

    return ScanResult(
        scan_id=scan_id,
        file_or_url=url,
        pages=1,
        summary=summary,
        findings=findings,
    )

