"""Phase 5 Acceptance and Regression Tests (Milestones 6, 7, and 8).

Validates:
- Milestone 6: Deep Semantic Structure Tree Traversal (WCAG 1.3.1, 1.1.1)
- Milestone 7: Visual & Contrast Analysis (WCAG 1.4.3, 1.4.11)
- Milestone 8: Contextual AI Heuristic Advisory Engine (WCAG 1.3.3, 2.4.2, 1.4.1)
"""

import io
from typing import Any

import pypdf
from pypdf.generic import (
    ArrayObject,
    DictionaryObject,
    NameObject,
    NumberObject,
    TextStringObject,
)

from core.checker import screen_pdf


def make_struct_test_pdf(struct_elements: list[dict[str, Any]], role_map: dict[str, str] | None = None) -> bytes:
    """Builds an in-memory PDF with synthetic /StructTreeRoot structural elements."""
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=200, height=200)

    def serialize_elem(elem: dict[str, Any]) -> Any:
        d = DictionaryObject()
        d[NameObject("/Type")] = NameObject("/StructElem")
        for k, v in elem.items():
            if isinstance(v, str):
                if v.startswith("/"):
                    d[NameObject(k)] = NameObject(v)
                else:
                    d[NameObject(k)] = TextStringObject(v)
            elif isinstance(v, list):
                child_refs = [serialize_elem(child) for child in v]
                d[NameObject(k)] = ArrayObject(child_refs)
            elif isinstance(v, (int, float)):
                d[NameObject(k)] = NumberObject(v)
        return writer._add_object(d)

    k_refs = [serialize_elem(elem) for elem in struct_elements]
    st_root = DictionaryObject()
    st_root[NameObject("/Type")] = NameObject("/StructTreeRoot")
    st_root[NameObject("/K")] = ArrayObject(k_refs)

    if role_map:
        rm = DictionaryObject()
        for rk, rv in role_map.items():
            rm[NameObject(rk)] = NameObject(rv)
        st_root[NameObject("/RoleMap")] = rm

    st_ref = writer._add_object(st_root)
    writer._root_object[NameObject("/StructTreeRoot")] = st_ref

    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


# ==============================================================================
# Milestone 6: Structure Tree Traversal Tests
# ==============================================================================

def test_m6_heading_hierarchy_skipped_levels() -> tuple[bool, str]:
    """Asserts that non-sequential heading hierarchy (<H1> -> <H3>) flags an Issue."""
    pdf_bytes = make_struct_test_pdf([
        {"/S": "/H1", "/T": "Chapter 1"},
        {"/S": "/H3", "/T": "Subsection 1.1"},  # Skips H2
    ])
    res = screen_pdf(pdf_bytes, filename="skipped_heading.pdf")
    h_finding = next((f for f in res.findings if "Heading" in f.issue_description), None)

    if not h_finding:
        return False, "Expected heading hierarchy finding, but none was returned."
    if h_finding.status != "Issue":
        return False, f"Expected status 'Issue', got '{h_finding.status}'."
    if "<H1> to <H3>" not in h_finding.issue_description:
        return False, f"Expected '<H1> to <H3>' in description: {h_finding.issue_description}"
    if not h_finding.remediation_guidance:
        return False, "Missing remediation guidance on heading hierarchy issue."
    return True, f"Detected skipped heading level: {h_finding.issue_description}"


def test_m6_heading_hierarchy_sequential() -> tuple[bool, str]:
    """Asserts that sequential heading hierarchy (<H1> -> <H2> -> <H3>) passes."""
    pdf_bytes = make_struct_test_pdf([
        {"/S": "/H1", "/T": "Title"},
        {"/S": "/H2", "/T": "Section"},
        {"/S": "/H3", "/T": "Subsection"},
    ])
    res = screen_pdf(pdf_bytes, filename="sequential_heading.pdf")
    h_finding = next((f for f in res.findings if "Heading" in f.issue_description), None)

    if not h_finding:
        return False, "Expected heading hierarchy finding, but none was returned."
    if h_finding.status != "Pass":
        return False, f"Expected status 'Pass', got '{h_finding.status}'."
    return True, f"Sequential heading hierarchy passed: {h_finding.issue_description}"


def test_m6_table_structural_integrity() -> tuple[bool, str]:
    """Asserts that table lacking <TH> flags an Issue and table with <TH> passes."""
    pdf_bytes = make_struct_test_pdf([
        # Table 1: Untagged headers (only TD)
        {
            "/S": "/Table",
            "/K": [
                {"/S": "/TR", "/K": [{"/S": "/TD", "/T": "Data 1"}, {"/S": "/TD", "/T": "Data 2"}]}
            ],
        },
        # Table 2: Proper headers (TH and TD)
        {
            "/S": "/Table",
            "/K": [
                {"/S": "/TR", "/K": [{"/S": "/TH", "/T": "Header"}, {"/S": "/TD", "/T": "Value"}]}
            ],
        },
    ])
    res = screen_pdf(pdf_bytes, filename="tables_struct.pdf")
    t1 = next((f for f in res.findings if f.input_location == "Document Structure Tree / Table 1"), None)
    t2 = next((f for f in res.findings if f.input_location == "Document Structure Tree / Table 2"), None)

    if not t1 or t1.status != "Issue":
        return False, f"Table 1 expected Issue for missing TH, got {t1}"
    if not t2 or t2.status != "Pass":
        return False, f"Table 2 expected Pass with TH, got {t2}"
    if not t1.remediation_guidance:
        return False, "Table 1 missing remediation guidance."
    return True, f"Table structure validated: Table 1 [{t1.status}], Table 2 [{t2.status}]"


def test_m6_list_consistency() -> tuple[bool, str]:
    """Asserts that malformed list items flag an Issue and valid items pass."""
    pdf_bytes = make_struct_test_pdf([
        # List 1: Malformed (LI missing Lbl)
        {
            "/S": "/L",
            "/K": [
                {"/S": "/LI", "/K": [{"/S": "/LBody", "/T": "Content without label"}]}
            ],
        },
        # List 2: Well-formed (LI with Lbl and LBody)
        {
            "/S": "/L",
            "/K": [
                {"/S": "/LI", "/K": [{"/S": "/Lbl", "/T": "1."}, {"/S": "/LBody", "/T": "Item text"}]}
            ],
        },
    ])
    res = screen_pdf(pdf_bytes, filename="lists_struct.pdf")
    l1 = next((f for f in res.findings if f.input_location == "Document Structure Tree / List 1"), None)
    l2 = next((f for f in res.findings if f.input_location == "Document Structure Tree / List 2"), None)

    if not l1 or l1.status != "Issue":
        return False, f"List 1 expected Issue for missing Lbl, got {l1}"
    if not l2 or l2.status != "Pass":
        return False, f"List 2 expected Pass for valid LI, got {l2}"
    return True, f"List consistency validated: List 1 [{l1.status}], List 2 [{l2.status}]"


def test_m6_figure_alt_text_evaluation() -> tuple[bool, str]:
    """Asserts that figure lacking /Alt flags an Issue and figure with /Alt requests Human Review."""
    pdf_bytes = make_struct_test_pdf([
        {"/S": "/Figure"},  # Missing Alt
        {"/S": "/Figure", "/Alt": "Quarterly revenue chart for 2026."},  # Has Alt
    ])
    res = screen_pdf(pdf_bytes, filename="figures_struct.pdf")
    f1 = next((f for f in res.findings if f.input_location == "Document Structure Tree / Figure 1"), None)
    f2 = next((f for f in res.findings if f.input_location == "Document Structure Tree / Figure 2"), None)

    if not f1 or f1.status != "Issue":
        return False, f"Figure 1 expected Issue for missing Alt, got {f1}"
    if not f2 or f2.status != "Needs Human Review":
        return False, f"Figure 2 expected Needs Human Review, got {f2}"
    if not f1.remediation_guidance or not f2.remediation_guidance:
        return False, "Remediation guidance missing on figure findings."
    return True, f"Figure alt text validated: Figure 1 [{f1.status}], Figure 2 [{f2.status}]"


# ==============================================================================
# Phase 5.2: PDF & Web Feature Parity Tests
# ==============================================================================

def test_p52_web_table_integrity() -> tuple[bool, str]:
    """Asserts HTML tables lacking <th> flag an Issue, and tables with <th> pass."""
    from core.web_checker import screen_html

    # Inaccessible table: only <td>
    bad_html = """<!DOCTYPE html><html lang="en"><head><title>T</title></head><body>
    <main><table><tr><td>Data 1</td><td>Data 2</td></tr></table></main></body></html>"""
    bad_res = screen_html(bad_html, url="https://example.com/bad_table")
    bad_tbl_f = next((f for f in bad_res.findings if "table" in f.issue_description.lower()), None)
    if not bad_tbl_f or bad_tbl_f.status != "Issue":
        return False, f"Expected Issue for table lacking <th>, got: {bad_tbl_f}"

    # Accessible table: has <th>
    good_html = """<!DOCTYPE html><html lang="en"><head><title>T</title></head><body>
    <main><table><tr><th scope="col">Header</th></tr><tr><td>Data</td></tr></table></main></body></html>"""
    good_res = screen_html(good_html, url="https://example.com/good_table")
    good_tbl_f = next((f for f in good_res.findings if "table" in f.issue_description.lower()), None)
    if not good_tbl_f or good_tbl_f.status != "Pass":
        return False, f"Expected Pass for table with <th>, got: {good_tbl_f}"

    return True, f"Web table integrity validated: Bad table [{bad_tbl_f.status}], Good table [{good_tbl_f.status}]"


def test_p52_web_list_consistency() -> tuple[bool, str]:
    """Asserts HTML lists lacking <li> items flag an Issue, and lists with <li> pass."""
    from core.web_checker import screen_html

    # Empty/malformed list
    bad_html = """<!DOCTYPE html><html lang="en"><head><title>L</title></head><body>
    <main><ul></ul></main></body></html>"""
    bad_res = screen_html(bad_html, url="https://example.com/bad_list")
    bad_lst_f = next((f for f in bad_res.findings if "list" in f.issue_description.lower()), None)
    if not bad_lst_f or bad_lst_f.status != "Issue":
        return False, f"Expected Issue for empty list, got: {bad_lst_f}"

    # Valid list
    good_html = """<!DOCTYPE html><html lang="en"><head><title>L</title></head><body>
    <main><ul><li>Item 1</li><li>Item 2</li></ul></main></body></html>"""
    good_res = screen_html(good_html, url="https://example.com/good_list")
    good_lst_f = next((f for f in good_res.findings if "list" in f.issue_description.lower()), None)
    if not good_lst_f or good_lst_f.status != "Pass":
        return False, f"Expected Pass for valid list, got: {good_lst_f}"

    return True, f"Web list consistency validated: Bad list [{bad_lst_f.status}], Good list [{good_lst_f.status}]"


def test_p52_pdf_multipage_outlines() -> tuple[bool, str]:
    """Asserts multi-page PDF (> 3 pages) lacking /Outlines flags Needs Human Review, with /Outlines passes."""
    import io

    import pypdf

    # 1. 4-page PDF without outlines
    w1 = pypdf.PdfWriter()
    for _ in range(4):
        w1.add_blank_page(width=100, height=100)
    buf1 = io.BytesIO()
    w1.write(buf1)
    res1 = screen_pdf(buf1.getvalue(), filename="no_outlines.pdf")
    out_f1 = next((f for f in res1.findings if "outline" in f.issue_description.lower()), None)
    if not out_f1 or out_f1.status != "Needs Human Review":
        return False, f"Expected Needs Human Review for multi-page PDF lacking outlines, got: {out_f1}"

    # 2. 4-page PDF with outlines
    w2 = pypdf.PdfWriter()
    for _ in range(4):
        w2.add_blank_page(width=100, height=100)
    outlines = DictionaryObject()
    outlines[NameObject("/Type")] = NameObject("/Outlines")
    outlines[NameObject("/Count")] = NumberObject(1)
    w2._root_object[NameObject("/Outlines")] = w2._add_object(outlines)
    buf2 = io.BytesIO()
    w2.write(buf2)
    res2 = screen_pdf(buf2.getvalue(), filename="with_outlines.pdf")
    out_f2 = next((f for f in res2.findings if "outline" in f.issue_description.lower()), None)
    if not out_f2 or out_f2.status != "Pass":
        return False, f"Expected Pass for multi-page PDF with outlines, got: {out_f2}"

    return True, f"PDF outlines validated: Missing outlines [{out_f1.status}], Present outlines [{out_f2.status}]"


def test_p52_pdf_form_fields() -> tuple[bool, str]:
    """Asserts PDF form fields lacking /TU tooltip flag an Issue, and fields with /TU pass."""
    import io

    import pypdf

    # 1. AcroForm with unlabeled field (missing /TU)
    w1 = pypdf.PdfWriter()
    w1.add_blank_page(width=100, height=100)
    f_bad = DictionaryObject()
    f_bad[NameObject("/FT")] = NameObject("/Tx")
    f_bad[NameObject("/T")] = TextStringObject("username")
    # Missing /TU
    f_bad_ref = w1._add_object(f_bad)

    acro1 = DictionaryObject()
    acro1[NameObject("/Fields")] = ArrayObject([f_bad_ref])
    w1._root_object[NameObject("/AcroForm")] = w1._add_object(acro1)
    buf1 = io.BytesIO()
    w1.write(buf1)
    res1 = screen_pdf(buf1.getvalue(), filename="bad_form.pdf")
    form_f1 = next((f for f in res1.findings if "form field" in f.issue_description.lower()), None)
    if not form_f1 or form_f1.status != "Issue":
        return False, f"Expected Issue for form field lacking /TU, got: {form_f1}"

    # 2. AcroForm with labeled field (has /TU)
    w2 = pypdf.PdfWriter()
    w2.add_blank_page(width=100, height=100)
    f_good = DictionaryObject()
    f_good[NameObject("/FT")] = NameObject("/Tx")
    f_good[NameObject("/T")] = TextStringObject("username")
    f_good[NameObject("/TU")] = TextStringObject("Enter your user name")
    f_good_ref = w2._add_object(f_good)

    acro2 = DictionaryObject()
    acro2[NameObject("/Fields")] = ArrayObject([f_good_ref])
    w2._root_object[NameObject("/AcroForm")] = w2._add_object(acro2)
    buf2 = io.BytesIO()
    w2.write(buf2)
    res2 = screen_pdf(buf2.getvalue(), filename="good_form.pdf")
    form_f2 = next((f for f in res2.findings if "form field" in f.issue_description.lower()), None)
    if not form_f2 or form_f2.status != "Pass":
        return False, f"Expected Pass for form field with /TU, got: {form_f2}"

    return True, f"PDF form fields validated: Missing /TU [{form_f1.status}], With /TU [{form_f2.status}]"


# ==============================================================================
# Milestone 7: Visual & Contrast Analysis Tests
# ==============================================================================

def test_m7_contrast_math_unit_tests() -> tuple[bool, str]:
    """Asserts that relative luminance and contrast ratio calculations match WCAG formulas."""
    from core.contrast_analyzer import (
        compute_contrast_ratio,
        srgb_to_relative_luminance,
    )

    # Relative luminance tests
    lum_black = srgb_to_relative_luminance(0.0, 0.0, 0.0)
    lum_white = srgb_to_relative_luminance(1.0, 1.0, 1.0)
    if abs(lum_black - 0.0) > 1e-4:
        return False, f"Expected black luminance 0.0, got {lum_black}"
    if abs(lum_white - 1.0) > 1e-4:
        return False, f"Expected white luminance 1.0, got {lum_white}"

    # Contrast ratio tests
    ratio_max = compute_contrast_ratio((0.0, 0.0, 0.0), (1.0, 1.0, 1.0))
    ratio_min = compute_contrast_ratio((1.0, 1.0, 1.0), (1.0, 1.0, 1.0))
    if ratio_max != 21.0:
        return False, f"Expected 21.0:1 contrast, got {ratio_max}"
    if ratio_min != 1.0:
        return False, f"Expected 1.0:1 contrast, got {ratio_min}"

    # #767676 on white should satisfy 4.5:1
    grey_c = 0x76 / 255.0
    ratio_grey = compute_contrast_ratio((grey_c, grey_c, grey_c), (1.0, 1.0, 1.0))
    if ratio_grey < 4.5:
        return False, f"Expected #767676 on white to be >= 4.5, got {ratio_grey}"

    return True, f"Contrast formulas verified: Max={ratio_max}:1, Min={ratio_min}:1, #767676={ratio_grey}:1"


def test_m7_text_contrast_passing_and_failing() -> tuple[bool, str]:
    """Asserts that high-contrast text passes and low-contrast text is flagged as an Issue."""
    import pymupdf

    # 1. Failing document (light grey on white)
    doc_fail = pymupdf.open()
    p_fail = doc_fail.new_page(width=300, height=200)
    p_fail.insert_text((50, 50), "Faint light grey text", fontsize=12, color=(0.85, 0.85, 0.85))
    res_fail = screen_pdf(doc_fail.tobytes(), filename="contrast_fail.pdf")

    c_fail = next((f for f in res_fail.findings if f.WCAG_criterion.startswith("1.4.3")), None)
    if not c_fail or c_fail.status != "Issue":
        return False, f"Expected Issue for low contrast text, got {c_fail}"
    if not c_fail.remediation_guidance:
        return False, "Missing remediation guidance on failing contrast finding."

    # 2. Passing document (black text on white)
    doc_pass = pymupdf.open()
    p_pass = doc_pass.new_page(width=300, height=200)
    p_pass.insert_text((50, 50), "Solid black text", fontsize=12, color=(0.0, 0.0, 0.0))
    res_pass = screen_pdf(doc_pass.tobytes(), filename="contrast_pass.pdf")

    c_pass = next((f for f in res_pass.findings if f.WCAG_criterion.startswith("1.4.3")), None)
    if not c_pass or c_pass.status != "Pass":
        return False, f"Expected Pass for high contrast text, got {c_pass}"

    return True, f"Text contrast validated: Low-contrast [{c_fail.status}], High-contrast [{c_pass.status}]"


def test_m7_background_drawing_detection() -> tuple[bool, str]:
    """Asserts that background vector fill is detected when calculating contrast."""
    import pymupdf

    doc = pymupdf.open()
    page = doc.new_page(width=300, height=200)

    # Dark navy background fill
    shape = page.new_shape()
    shape.draw_rect(pymupdf.Rect(20, 20, 280, 180))
    shape.finish(fill=(0.05, 0.1, 0.3))
    shape.commit()

    # White text inside dark rectangle (should have high contrast against navy background)
    page.insert_text((50, 50), "White text on dark navy", fontsize=14, color=(1.0, 1.0, 1.0))
    res = screen_pdf(doc.tobytes(), filename="navy_bg.pdf")

    c_finding = next((f for f in res.findings if f.WCAG_criterion.startswith("1.4.3")), None)
    if not c_finding or c_finding.status != "Pass":
        return False, f"Expected Pass with background fill detection, got {c_finding}"

    return True, f"Background fill contrast passed: {c_finding.issue_description}"


# ==============================================================================
# Milestone 8: Contextual AI Advisory Heuristics Tests
# ==============================================================================

def test_m8_sensory_characteristics_detection() -> tuple[bool, str]:
    """Asserts that sensory instructions (WCAG 1.3.3) trigger advisory AI findings."""
    import pymupdf

    doc = pymupdf.open()
    page = doc.new_page(width=300, height=200)
    page.insert_text((50, 50), "Please click the green button above to submit.", fontsize=12, color=(0, 0, 0))
    res = screen_pdf(doc.tobytes(), filename="sensory_doc.pdf")

    s_finding = next((f for f in res.findings if "1.3.3" in f.WCAG_criterion), None)
    if not s_finding:
        return False, "Expected sensory characteristics finding (WCAG 1.3.3), but none was found."
    if s_finding.analysis_method != "AI":
        return False, f"Expected analysis_method='AI', got '{s_finding.analysis_method}'."
    if s_finding.status != "Needs Human Review":
        return False, f"Expected status='Needs Human Review', got '{s_finding.status}'."
    if not s_finding.remediation_guidance:
        return False, "Missing remediation guidance on sensory characteristics finding."

    return True, f"Sensory cue detected: {s_finding.issue_description}"


def test_m8_uninformative_title_detection() -> tuple[bool, str]:
    """Asserts that default/generic titles (WCAG 2.4.2/2.4.6) trigger advisory AI findings."""
    import pymupdf

    doc = pymupdf.open()
    doc.set_metadata({"title": "Untitled Document"})
    page = doc.new_page(width=300, height=200)
    page.insert_text((50, 50), "Generic title document content.", fontsize=12, color=(0, 0, 0))
    res = screen_pdf(doc.tobytes(), filename="untitled.pdf")

    t_finding = next((f for f in res.findings if "2.4.2" in f.WCAG_criterion and f.analysis_method == "AI"), None)
    if not t_finding:
        return False, "Expected AI uninformative title advisory finding (WCAG 2.4.2), got None."
    if t_finding.status != "Needs Human Review":
        return False, f"Expected status='Needs Human Review', got '{t_finding.status}'."

    return True, f"Uninformative title flagged: {t_finding.issue_description}"


def test_m8_color_only_reliance_detection() -> tuple[bool, str]:
    """Asserts that color-only information conveyance (WCAG 1.4.1) triggers advisory AI findings."""
    import pymupdf

    doc = pymupdf.open()
    page = doc.new_page(width=300, height=200)
    page.insert_text((50, 50), "Notice: items in red are required fields.", fontsize=12, color=(0, 0, 0))
    res = screen_pdf(doc.tobytes(), filename="color_doc.pdf")

    c_finding = next((f for f in res.findings if "1.4.1" in f.WCAG_criterion), None)
    if not c_finding:
        return False, "Expected color-only dependency finding (WCAG 1.4.1), got None."
    if c_finding.analysis_method != "AI":
        return False, f"Expected analysis_method='AI', got '{c_finding.analysis_method}'."

    return True, f"Color-only reliance flagged: {c_finding.issue_description}"


def test_m8_offline_resilience_fallback() -> tuple[bool, str]:
    """Asserts that AI heuristic engine executes 100% reliably in pure offline mode without network."""
    import os

    from core.ai_evaluator import evaluate_ai_heuristics

    # Temporarily force API key empty to test deterministic local fallback
    old_key = os.environ.get("GEMINI_API_KEY")
    try:
        os.environ["GEMINI_API_KEY"] = ""
        findings, counter = evaluate_ai_heuristics(
            title="scan001",
            content_items=[("Section A", "Press the blue button on the right to continue.")],
            start_counter=10,
        )
        if len(findings) < 2:
            return False, f"Expected at least 2 fallback findings (title + sensory), got {len(findings)}"
        all_ai = all(f.analysis_method == "AI" and f.status == "Needs Human Review" for f in findings)
        if not all_ai:
            return False, f"Not all fallback findings have method='AI' and status='Needs Human Review': {findings}"
    finally:
        if old_key is not None:
            os.environ["GEMINI_API_KEY"] = old_key

    return True, f"Offline fallback verified: {len(findings)} advisory findings generated without network."


def test_p53_web_contrast_passing() -> tuple[bool, str]:
    """Asserts that web page with high-contrast inline styles passes WCAG 1.4.3."""
    from core.web_checker import screen_html

    html = """<!DOCTYPE html>
<html lang="en">
<head><title>Contrast Test</title></head>
<body>
  <main>
    <p style="color: #000000; background-color: #ffffff;">High contrast black text on white background.</p>
  </main>
</body>
</html>"""
    res = screen_html(html, url="https://contrast.example.gov")
    c_finding = next((f for f in res.findings if "1.4.3" in f.WCAG_criterion), None)
    if not c_finding:
        return False, "Expected WCAG 1.4.3 contrast finding, got None."
    if c_finding.status != "Pass":
        return False, f"Expected status 'Pass', got '{c_finding.status}'."
    return True, f"Web contrast passing validated: {c_finding.issue_description}"


def test_p53_web_contrast_failing() -> tuple[bool, str]:
    """Asserts that web page with low-contrast inline styles flags an Issue with remediation."""
    from core.web_checker import screen_html

    html = """<!DOCTYPE html>
<html lang="en">
<head><title>Low Contrast Test</title></head>
<body>
  <main>
    <p style="color: #cccccc; background-color: #ffffff;">Low contrast faint grey text on white.</p>
  </main>
</body>
</html>"""
    res = screen_html(html, url="https://lowcontrast.example.gov")
    c_finding = next((f for f in res.findings if "1.4.3" in f.WCAG_criterion), None)
    if not c_finding:
        return False, "Expected WCAG 1.4.3 contrast finding, got None."
    if c_finding.status != "Issue":
        return False, f"Expected status 'Issue', got '{c_finding.status}'."
    if not c_finding.remediation_guidance:
        return False, "Missing remediation guidance on failing web contrast finding."
    return True, f"Web contrast failing validated: {c_finding.issue_description}"




