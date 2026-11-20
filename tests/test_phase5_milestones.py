"""Phase 5 Acceptance and Regression Tests (Milestones 6, 7, and 8).

Validates:
- Milestone 6: Deep Semantic Structure Tree Traversal (WCAG 1.3.1, 1.1.1)
- Milestone 7: Visual & Contrast Analysis (WCAG 1.4.3, 1.4.11)
- Milestone 8: Contextual AI Heuristic Advisory Engine (WCAG 1.3.3, 2.4.2, 1.4.1)
"""

import io
from typing import Any

import pypdf
from pypdf.generic import ArrayObject, DictionaryObject, NameObject, TextStringObject

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
                d[NameObject(k)] = pypdf.generic.NumberObject(v)
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

