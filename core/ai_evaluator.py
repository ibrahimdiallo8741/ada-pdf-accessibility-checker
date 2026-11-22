"""Contextual AI Heuristic Advisory Engine (Milestone 8).

Assesses qualitative accessibility criteria using contextual heuristics and
Google AI Studio REST APIs (gemini-3.5-flash-lite) with 100% resilient local fallback:
1. Sensory Characteristics Detection (WCAG 1.3.3 / Level A)
2. Document Title Descriptiveness (WCAG 2.4.2 / Level A & 2.4.6)
3. Color-Only Information Reliance (WCAG 1.4.1 / Level A)

Strict Invariant: All AI findings are advisory (analysis_method="AI", status="Needs Human Review").
AI never provides a hard pass or certifies compliance.
"""

import json
import os
import re
from pathlib import Path
from typing import Any

import httpx

from core.models import Finding


def _load_env_file() -> None:
    """Loads environment variables from local .env file in the project root if present."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        try:
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("\"'")
                    if k and k not in os.environ:
                        os.environ[k] = v
        except Exception:
            pass


_load_env_file()

SENSORY_PATTERNS = [
    re.compile(
        r"\b(?:click|press|select|tap|refer to|see)\s+(?:the\s+)?(?:green|red|blue|yellow|orange|purple)?\s*"
        r"(?:button|icon|box|link|diagram|arrow)?\s*(?:above|below|on the right|on the left|at the top|at the bottom)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:click|press|select|tap)\s+(?:the\s+)?(?:green|red|blue|yellow|orange|purple)\s+(?:button|link|icon|box)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:the|see)\s+(?:round|square|triangular|hexagonal|circular)\s+(?:button|icon|shape|symbol|diagram)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:in the right column|in the left panel|in the upper right|in the lower left)\b",
        re.IGNORECASE,
    ),
]

COLOR_ONLY_PATTERNS = [
    re.compile(
        r"\b(?:items?|fields?|rows?|cells?)\s+(?:in|marked in|highlighted in)\s+(?:red|green|blue|yellow)\s+"
        r"(?:are|indicates?|means?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:see|refer to)\s+(?:red|green|blue|yellow)\s+for\s+(?:errors?|status|pass|fail|completed?)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\brequired\s+fields?\s+are\s+(?:in\s+)?red\b", re.IGNORECASE),
]

UNINFORMATIVE_TITLE_PATTERNS = [
    re.compile(
        r"^(?:untitled(?:\s+document)?|document\s*\d*|microsoft word\s*-\s*document\d*|scan\s*\d*|"
        r"new document|pdf document|presentation\d*|temp|draft|report)$",
        re.IGNORECASE,
    ),
]


def _local_heuristic_analyzer(
    title: str,
    content_items: list[tuple[str, str]],
) -> list[dict[str, Any]]:
    """Evaluates qualitative accessibility barriers using local deterministic regex heuristics."""
    candidates: list[dict[str, Any]] = []

    # 1. Uninformative title evaluation
    clean_title = (title or "").strip()
    if clean_title:
        for p in UNINFORMATIVE_TITLE_PATTERNS:
            if p.match(clean_title):
                candidates.append({
                    "location": "Document Metadata",
                    "criterion": "2.4.2 Page Titled (Level A)",
                    "description": (
                        f"Document title '{clean_title}' appears generic, uninformative, "
                        "or a default software placeholder."
                    ),
                    "remediation": (
                        "Provide a descriptive, informative document title that clearly "
                        "identifies the document's subject or purpose."
                    ),
                    "details": f"Matched generic title pattern: '{p.pattern}'",
                })
                break

    # 2. Sensory characteristics and color-only reliance evaluation per section/page
    for location, text in content_items:
        if not text:
            continue

        # Sensory cues
        for p in SENSORY_PATTERNS:
            m = p.search(text)
            if m:
                snippet = m.group(0)
                candidates.append({
                    "location": location,
                    "criterion": "1.3.3 Sensory Characteristics (Level A)",
                    "description": (
                        f"Potential sensory instruction detected: '{snippet}' relies on spatial, "
                        "shape, or visual cues alone."
                    ),
                    "remediation": (
                        "Provide secondary textual identifiers (e.g. labeled button names or section titles) "
                        "alongside visual or positional cues."
                    ),
                    "details": f"Context: '{text[max(0, m.start() - 20):min(len(text), m.end() + 20)]}'",
                })
                break

        # Color-only cues
        for p in COLOR_ONLY_PATTERNS:
            m = p.search(text)
            if m:
                snippet = m.group(0)
                candidates.append({
                    "location": location,
                    "criterion": "1.4.1 Use of Color (Level A)",
                    "description": (
                        f"Potential color-only information conveyance detected: '{snippet}'."
                    ),
                    "remediation": (
                        "Ensure information conveyed by color is also available through text, symbols, "
                        "or additional formatting."
                    ),
                    "details": f"Context: '{text[max(0, m.start() - 20):min(len(text), m.end() + 20)]}'",
                })
                break

    return candidates


def query_gemini_rest(
    title: str,
    content_items: list[tuple[str, str]],
    api_key: str,
    model: str = "gemini-3.5-flash-lite",
    timeout_seconds: float = 8.0,
) -> list[dict[str, Any]] | None:
    """Invokes Google AI Studio Gemini API via direct REST transport.
    
    Returns structured candidate findings or None on timeout/failure.
    """
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    system_prompt = (
        "You are an accessibility auditor evaluating a document for WCAG 2.1 compliance. "
        "Review the text for: 1) WCAG 1.3.3 Sensory Characteristics (instructions relying on color/shape/location), "
        "2) WCAG 2.4.2 Title descriptiveness (flagging generic/default titles), "
        "3) WCAG 1.4.1 Use of Color (information communicated only by color). "
        "Return a JSON object: {\"findings\": [{\"location\": str, \"criterion\": str, \"description\": str, \"remediation\": str, \"details\": str}]}. "
        "If no accessibility barriers are detected, return {\"findings\": []}."
    )
    sample_text = "\n".join(f"[{loc}]: {txt[:200]}" for loc, txt in content_items[:5])
    user_content = f"Title: {title}\nSample Content:\n{sample_text[:2000]}"

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": system_prompt + "\n\n" + user_content}
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.1,
        }
    }

    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            resp = client.post(endpoint, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text_out = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text_out)
                findings = parsed.get("findings")
                if isinstance(findings, list):
                    return findings
    except Exception:
        # Graceful fallback on any network, timeout, or parsing error
        return None
    return None


def evaluate_ai_heuristics(
    title: str,
    content_items: list[tuple[str, str]],
    start_counter: int = 1,
) -> tuple[list[Finding], int]:
    """Coordinates advisory AI accessibility heuristic evaluation with 100% resilient fallback."""
    findings: list[Finding] = []
    counter = start_counter

    # Ensure .env is refreshed
    _load_env_file()
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()

    candidate_items: list[dict[str, Any]] | None = None

    if api_key:
        candidate_items = query_gemini_rest(
            title=title,
            content_items=content_items,
            api_key=api_key,
            model=model,
        )

    if candidate_items is None:
        candidate_items = _local_heuristic_analyzer(title, content_items)

    for item in candidate_items:
        findings.append(Finding(
            finding_id=f"F{counter:03d}",
            input_location=item.get("location", "Document Content"),
            issue_description=item.get("description", "Potential accessibility barrier detected."),
            WCAG_criterion=item.get("criterion", "General Accessibility"),
            analysis_method="AI",
            status="Needs Human Review",
            remediation_guidance=item.get("remediation", "Review content to ensure multi-modal accessibility."),
            additional_details=item.get("details", f"Evaluated via {model} heuristic model."),
        ))
        counter += 1

    return findings, counter
