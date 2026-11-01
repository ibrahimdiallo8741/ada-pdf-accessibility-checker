from core.web_checker import screen_html
from core.web_fetcher import (
    InvalidURLError,
    SSRFError,
    validate_and_sanitize_url,
)

ACCESSIBLE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Accessible Government Portal</title>
</head>
<body>
  <a href="#main-content">Skip to main content</a>
  <header>
    <h1>City Services and Programs</h1>
  </header>
  <main id="main-content">
    <h2>Public Works Information</h2>
    <p>Welcome to our municipal accessibility portal.</p>
    <img src="/assets/city_hall.jpg" alt="Photograph of City Hall building entrance with accessibility ramp">
    <form action="/search" method="get">
      <label for="query">Search Services:</label>
      <input type="text" id="query" name="q">
      <button type="submit">Search</button>
    </form>
  </main>
</body>
</html>
"""

INACCESSIBLE_HTML = """<!DOCTYPE html>
<html>
<head>
  <!-- Missing <title> -->
</head>
<body>
  <!-- Missing <h1>, starts directly with <h3> -->
  <h3>Upcoming Events</h3>
  <!-- Missing alt attribute -->
  <img src="/banner.png">
  <!-- Unlabeled form input -->
  <form>
    <input type="email" name="subscribe">
  </form>
  <!-- Lacks <main> and skip link -->
</body>
</html>
"""


def test_web_accessible_fixture() -> tuple[bool, str]:
    """Evaluates fully accessible synthetic HTML fixture against all 6 WCAG web rules."""
    res = screen_html(ACCESSIBLE_HTML, url="https://example.gov")
    if res.summary.checks != 6:
        return False, f"Expected 6 checks, got {res.summary.checks}"
    if res.summary.issues != 0:
        return False, f"Expected 0 issues on accessible HTML, got {res.summary.issues}"
    if res.summary.passed < 5:
        return False, f"Expected at least 5 passes, got {res.summary.passed}"

    # Verify findings contain Title, Lang, Image, Headings, Form, Bypass
    criteria = {f.WCAG_criterion for f in res.findings}
    expected = {
        "2.4.2 Page Titled (Level A)",
        "3.1.1 Language of Page (Level A)",
        "1.1.1 Non-text Content (Level A)",
        "1.3.1 Info and Relationships (Level A)",
        "2.4.1 Bypass Blocks (Level A)",
    }
    if not expected.issubset(criteria):
        return False, f"Missing expected WCAG criteria in findings: {expected - criteria}"

    return True, f"Accessible HTML evaluated cleanly: checks={res.summary.checks}, passed={res.summary.passed}, review={res.summary.human_review}"


def test_web_inaccessible_fixture() -> tuple[bool, str]:
    """Asserts that inaccessible HTML fixture triggers Issues across title, lang, alt, headings, and labels."""
    res = screen_html(INACCESSIBLE_HTML, url="https://inaccessible.example.gov")

    title_f = next((f for f in res.findings if "2.4.2" in f.WCAG_criterion), None)
    lang_f = next((f for f in res.findings if "3.1.1" in f.WCAG_criterion), None)
    img_f = next((f for f in res.findings if "1.1.1" in f.WCAG_criterion), None)
    head_f = next((f for f in res.findings if "1.3.1" in f.WCAG_criterion and "heading" in f.issue_description.lower()), None)
    form_f = next((f for f in res.findings if "form" in f.issue_description.lower()), None)
    skip_f = next((f for f in res.findings if "2.4.1" in f.WCAG_criterion), None)

    checks_valid = (
        title_f is not None and title_f.status == "Issue"
        and lang_f is not None and lang_f.status == "Issue"
        and img_f is not None and img_f.status == "Issue"
        and head_f is not None and head_f.status == "Issue"
        and form_f is not None and form_f.status == "Issue"
        and skip_f is not None and skip_f.status == "Needs Human Review"
    )

    if not checks_valid:
        return False, f"Inaccessible fixture findings mismatch: title={getattr(title_f, 'status', None)}, lang={getattr(lang_f, 'status', None)}, img={getattr(img_f, 'status', None)}, head={getattr(head_f, 'status', None)}, form={getattr(form_f, 'status', None)}, skip={getattr(skip_f, 'status', None)}"

    # All non-passing findings must contain remediation guidance
    non_passing = [f for f in res.findings if f.status in ("Issue", "Needs Human Review")]
    if not all(bool(f.remediation_guidance and f.remediation_guidance.strip()) for f in non_passing):
        return False, "Not all non-passing web findings include actionable remediation guidance."

    return True, f"Inaccessible HTML detected expected defects: issues={res.summary.issues}, review={res.summary.human_review}"


def test_web_ssrf_and_invalid_schemes() -> tuple[bool, str]:
    """Asserts that SSRF targets (loopback, link-local, private subnets) and malformed schemes are rejected."""
    # 1. Invalid schemes
    for bad_url in ("ftp://example.gov", "file:///etc/passwd", "javascript:alert(1)", "not-a-url"):
        try:
            validate_and_sanitize_url(bad_url)
            return False, f"Expected InvalidURLError for '{bad_url}', but none was raised."
        except InvalidURLError:
            pass

    # 2. SSRF loopback & private subnets
    for ssrf_url in (
        "http://127.0.0.1:8080/admin",
        "http://localhost:8000",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.1/internal",
        "http://192.168.1.1/router",
    ):
        try:
            validate_and_sanitize_url(ssrf_url)
            return False, f"Expected SSRFError for '{ssrf_url}', but none was raised."
        except SSRFError:
            pass

    return True, "SSRF and URL scheme validation rejected all forbidden and malformed targets."


def test_web_empty_html_resilience() -> tuple[bool, str]:
    """Asserts that 0-byte or malformed unclosed HTML tags do not crash the parser."""
    res_empty = screen_html("", url="https://empty.example.gov")
    if res_empty.summary.checks != 6:
        return False, f"Empty HTML expected 6 checks, got {res_empty.summary.checks}"

    res_broken = screen_html("<div><p><span>Unclosed elements <h1>Only opening tag", url="https://broken.example.gov")
    if res_broken.summary.checks != 6:
        return False, f"Broken unclosed HTML expected 6 checks, got {res_broken.summary.checks}"

    return True, "HTML screening engine operates resiliently on empty or unclosed tags."

