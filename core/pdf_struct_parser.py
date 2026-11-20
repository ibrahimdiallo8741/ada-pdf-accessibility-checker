"""Deep Semantic Structure Tree Traversal Engine (Milestone 6).

Recursively traverses PDF /StructTreeRoot hierarchies (/K structural elements),
resolving custom element types via /RoleMap to evaluate:
1. Heading Nesting Hierarchy (WCAG 1.3.1 / PDF9)
2. Data Table Structural Integrity (WCAG 1.3.1 / PDF6)
3. List Structural Consistency (WCAG 1.3.1 / PDF21)
4. Figure Alternative Text Quality (WCAG 1.1.1 / PDF1)
"""

from typing import Any

from core.models import Finding


def _deref(obj: Any) -> Any:
    """Dereferences indirect PDF objects safely."""
    if obj is None:
        return None
    if hasattr(obj, "get_object"):
        try:
            return obj.get_object()
        except Exception:
            return obj
    return obj


def _clean_tag(tag: Any) -> str:
    """Normalizes PDF structure tag names to uppercase strings without leading slash."""
    if tag is None:
        return ""
    s = str(tag).strip()
    if s.startswith("/"):
        s = s[1:]
    return s.upper()


def _decode_text(val: Any) -> str:
    """Decodes PDF text objects to clean strings."""
    if val is None:
        return ""
    if isinstance(val, bytes):
        try:
            return val.decode("utf-8").strip()
        except UnicodeDecodeError:
            return val.decode("latin-1", errors="replace").strip()
    return str(val).strip()


def build_role_map(struct_root: Any) -> dict[str, str]:
    """Extracts and normalizes the /RoleMap dictionary from /StructTreeRoot."""
    role_map: dict[str, str] = {}
    if not struct_root or not hasattr(struct_root, "get"):
        return role_map

    raw_map = _deref(struct_root.get("/RoleMap"))
    if raw_map and hasattr(raw_map, "items"):
        for k, v in raw_map.items():
            clean_k = _clean_tag(k)
            clean_v = _clean_tag(v)
            if clean_k and clean_v:
                role_map[clean_k] = clean_v
    return role_map


def resolve_role(tag: str, role_map: dict[str, str]) -> str:
    """Resolves custom structure types to standard PDF structure types via RoleMap."""
    current = tag
    visited = set()
    while current in role_map and current not in visited:
        visited.add(current)
        current = role_map[current]
    return current


def _extract_kids(elem: Any) -> list[Any]:
    """Extracts child structure elements from an element's /K entry."""
    k_entry = _deref(elem.get("/K"))
    if k_entry is None:
        return []
    if isinstance(k_entry, list):
        return [_deref(item) for item in k_entry]
    return [_deref(k_entry)]


def _inspect_table(table_elem: Any, role_map: dict[str, str]) -> dict[str, Any]:
    """Inspects a /Table element for structural integrity (rows, TH, TD)."""
    rows_count = 0
    th_count = 0
    td_count = 0

    stack = _extract_kids(table_elem)
    visited_ids = set()

    while stack:
        current = stack.pop()
        if not current or not hasattr(current, "get"):
            continue

        curr_id = id(current)
        if curr_id in visited_ids:
            continue
        visited_ids.add(curr_id)

        role = resolve_role(_clean_tag(current.get("/S")), role_map)

        if role == "TR":
            rows_count += 1
            # Push children of row
            for child in _extract_kids(current):
                stack.append(child)
        elif role == "TH":
            th_count += 1
        elif role == "TD":
            td_count += 1
        elif role in ("THEAD", "TBODY", "TFOOT", "SECT", "PART", "DIV"):
            for child in _extract_kids(current):
                stack.append(child)

    return {
        "rows_count": rows_count,
        "th_count": th_count,
        "td_count": td_count,
    }


def _inspect_list(list_elem: Any, role_map: dict[str, str]) -> dict[str, Any]:
    """Inspects an /L element for structural consistency (LI items with Lbl and LBody)."""
    items_count = 0
    malformed_count = 0
    malformed_reasons: list[str] = []

    kids = _extract_kids(list_elem)
    for idx, child in enumerate(kids, start=1):
        if not child or not hasattr(child, "get"):
            continue

        role = resolve_role(_clean_tag(child.get("/S")), role_map)
        if role == "LI":
            items_count += 1
            li_kids = _extract_kids(child)
            li_roles = [
                resolve_role(_clean_tag(k.get("/S")), role_map)
                for k in li_kids
                if k and hasattr(k, "get")
            ]

            has_lbl = "LBL" in li_roles
            has_body = "LBODY" in li_roles

            if not has_lbl or not has_body:
                malformed_count += 1
                missing = []
                if not has_lbl:
                    missing.append("<Lbl>")
                if not has_body:
                    missing.append("<LBody>")
                malformed_reasons.append(f"Item {idx} missing {' and '.join(missing)}")

    return {
        "items_count": items_count,
        "malformed_count": malformed_count,
        "reasons": malformed_reasons,
    }


def parse_structure_tree(
    root_object: Any,
    start_counter: int = 1,
) -> tuple[list[Finding], int]:
    """Recursively walks the structure tree starting at /StructTreeRoot.
    
    Generates deterministic findings for:
    - Skipped heading levels (WCAG 1.3.1 / PDF9)
    - Untagged table headers (WCAG 1.3.1 / PDF6)
    - Broken list hierarchies (WCAG 1.3.1 / PDF21)
    - Missing figure alternative text (WCAG 1.1.1 / PDF1)
    """
    findings: list[Finding] = []
    counter = start_counter

    if not root_object or "/StructTreeRoot" not in root_object:
        return findings, counter

    struct_root = _deref(root_object["/StructTreeRoot"])
    if not struct_root or not hasattr(struct_root, "get"):
        return findings, counter

    role_map = build_role_map(struct_root)

    headings: list[dict[str, Any]] = []
    tables: list[dict[str, Any]] = []
    lists: list[dict[str, Any]] = []
    figures: list[dict[str, Any]] = []

    table_counter = 1
    list_counter = 1
    figure_counter = 1

    # Depth-First Search traversal to preserve reading order
    raw_kids = _extract_kids(struct_root)
    if not raw_kids:
        return findings, counter

    # Use stack with depth guard to prevent cyclic recursion
    stack: list[tuple[Any, int]] = [(k, 0) for k in reversed(raw_kids)]
    visited_ids: set[int] = set()

    while stack:
        current, depth = stack.pop()
        if not current or not hasattr(current, "get") or depth > 60:
            continue

        curr_id = id(current)
        if curr_id in visited_ids:
            continue
        visited_ids.add(curr_id)

        raw_tag = _clean_tag(current.get("/S"))
        role = resolve_role(raw_tag, role_map)

        # 1. Heading extraction
        if role in ("H1", "H2", "H3", "H4", "H5", "H6"):
            lvl = int(role[1])
            headings.append({
                "level": lvl,
                "tag": role,
                "title": _decode_text(current.get("/T")),
            })

        # 2. Table extraction
        elif role == "TABLE":
            tbl_info = _inspect_table(current, role_map)
            tbl_info["table_id"] = table_counter
            table_counter += 1
            tables.append(tbl_info)
            # Table inspected via sub-traversal; avoid re-pushing inner nodes to main heading stack

        # 3. List extraction
        elif role == "L":
            lst_info = _inspect_list(current, role_map)
            lst_info["list_id"] = list_counter
            list_counter += 1
            lists.append(lst_info)

        # 4. Figure extraction
        elif role == "FIGURE":
            alt = current.get("/Alt") or current.get("/ActualText")
            alt_text = _decode_text(alt)
            elem_type = _clean_tag(current.get("/Type"))
            is_artifact = (role == "ARTIFACT" or elem_type == "ARTIFACT")

            figures.append({
                "figure_id": figure_counter,
                "alt_text": alt_text,
                "is_artifact": is_artifact,
            })
            figure_counter += 1

        # Push children for nested structures (Sect, Part, Div, Document, Art, etc.)
        if role not in ("TABLE", "L"):
            kids = _extract_kids(current)
            for child in reversed(kids):
                stack.append((child, depth + 1))

    # =========================================================================
    # Evaluation 1: Heading Nesting Hierarchy (WCAG 1.3.1 / PDF9)
    # =========================================================================
    if headings:
        skipped_transitions: list[str] = []
        prev_level = 0

        for h in headings:
            curr_level = h["level"]
            if prev_level > 0 and curr_level > prev_level + 1:
                skipped_transitions.append(f"<H{prev_level}> to <H{curr_level}>")
            prev_level = curr_level

        if skipped_transitions:
            findings.append(Finding(
                finding_id=f"F{counter:03d}",
                input_location="Document Structure Tree",
                issue_description=(
                    f"Heading nesting hierarchy contains skipped levels ({len(skipped_transitions)} instance(s): "
                    f"{', '.join(skipped_transitions[:3])})."
                ),
                WCAG_criterion="1.3.1 Info and Relationships (Level A)",
                analysis_method="Deterministic",
                status="Issue",
                remediation_guidance="Nest heading tags sequentially without skipping levels (e.g. nest <H2> before <H3>).",
                additional_details=f"Evaluated {len(headings)} heading tags. Total skipped transitions: {len(skipped_transitions)}.",
            ))
            counter += 1
        else:
            findings.append(Finding(
                finding_id=f"F{counter:03d}",
                input_location="Document Structure Tree",
                issue_description=(
                    f"Heading nesting hierarchy is sequential ({len(headings)} heading tag(s) in proper order)."
                ),
                WCAG_criterion="1.3.1 Info and Relationships (Level A)",
                analysis_method="Deterministic",
                status="Pass",
                remediation_guidance=None,
                additional_details=f"Sequence: {' -> '.join(h['tag'] for h in headings[:8])}{'...' if len(headings) > 8 else ''}",
            ))
            counter += 1

    # =========================================================================
    # Evaluation 2: Data Table Structural Integrity (WCAG 1.3.1 / PDF6)
    # =========================================================================
    for tbl in tables:
        if tbl["th_count"] == 0:
            findings.append(Finding(
                finding_id=f"F{counter:03d}",
                input_location=f"Document Structure Tree / Table {tbl['table_id']}",
                issue_description=(
                    f"Table {tbl['table_id']} has {tbl['rows_count']} row(s) and {tbl['td_count']} data cell(s) "
                    "but lacks <TH> header cell tags."
                ),
                WCAG_criterion="1.3.1 Info and Relationships (Level A)",
                analysis_method="Deterministic",
                status="Issue",
                remediation_guidance="Tag table column or row headers using <TH> elements with proper Scope attributes.",
                additional_details="Screen readers require <TH> header cells to associate data cells with column/row headings.",
            ))
            counter += 1
        else:
            findings.append(Finding(
                finding_id=f"F{counter:03d}",
                input_location=f"Document Structure Tree / Table {tbl['table_id']}",
                issue_description=(
                    f"Table {tbl['table_id']} has valid structure with {tbl['th_count']} header (<TH>) "
                    f"and {tbl['td_count']} data (<TD>) cells."
                ),
                WCAG_criterion="1.3.1 Info and Relationships (Level A)",
                analysis_method="Deterministic",
                status="Pass",
                remediation_guidance=None,
                additional_details=f"Table contains {tbl['rows_count']} row(s) with properly tagged header cells.",
            ))
            counter += 1

    # =========================================================================
    # Evaluation 3: List Structural Consistency (WCAG 1.3.1 / PDF21)
    # =========================================================================
    for lst in lists:
        if lst["malformed_count"] > 0:
            findings.append(Finding(
                finding_id=f"F{counter:03d}",
                input_location=f"Document Structure Tree / List {lst['list_id']}",
                issue_description=(
                    f"List {lst['list_id']} contains {lst['malformed_count']} malformed item(s) "
                    f"({', '.join(lst['reasons'][:2])})."
                ),
                WCAG_criterion="1.3.1 Info and Relationships (Level A)",
                analysis_method="Deterministic",
                status="Issue",
                remediation_guidance="Structure lists with <L> containing <LI> elements that separate labels (<Lbl>) from content (<LBody>).",
                additional_details=f"Total items: {lst['items_count']}, malformed items: {lst['malformed_count']}.",
            ))
            counter += 1
        elif lst["items_count"] > 0:
            findings.append(Finding(
                finding_id=f"F{counter:03d}",
                input_location=f"Document Structure Tree / List {lst['list_id']}",
                issue_description=(
                    f"List {lst['list_id']} is properly structured with {lst['items_count']} valid item(s) "
                    "(<LI> containing <Lbl> and <LBody>)."
                ),
                WCAG_criterion="1.3.1 Info and Relationships (Level A)",
                analysis_method="Deterministic",
                status="Pass",
                remediation_guidance=None,
                additional_details=f"All {lst['items_count']} list items follow standard PDF list structure.",
            ))
            counter += 1

    # =========================================================================
    # Evaluation 4: Figure Alternative Text Quality (WCAG 1.1.1 / PDF1)
    # =========================================================================
    for fig in figures:
        if fig["is_artifact"]:
            continue

        if not fig["alt_text"]:
            findings.append(Finding(
                finding_id=f"F{counter:03d}",
                input_location=f"Document Structure Tree / Figure {fig['figure_id']}",
                issue_description=f"Figure {fig['figure_id']} in structure tree is missing alternative text (/Alt).",
                WCAG_criterion="1.1.1 Non-text Content (Level A)",
                analysis_method="Deterministic",
                status="Issue",
                remediation_guidance="Add descriptive alternative text (/Alt) to <Figure> elements or mark decorative elements as /Artifact.",
                additional_details="Structural <Figure> element lacks a non-empty /Alt or /ActualText attribute.",
            ))
            counter += 1
        else:
            findings.append(Finding(
                finding_id=f"F{counter:03d}",
                input_location=f"Document Structure Tree / Figure {fig['figure_id']}",
                issue_description=f"Figure {fig['figure_id']} contains alternative text: '{fig['alt_text'][:80]}'.",
                WCAG_criterion="1.1.1 Non-text Content (Level A)",
                analysis_method="Deterministic",
                status="Needs Human Review",
                remediation_guidance="Verify that the alternative text accurately describes the image purpose and context.",
                additional_details=f"Alternative text: {fig['alt_text']}",
            ))
            counter += 1

    return findings, counter
