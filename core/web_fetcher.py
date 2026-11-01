import ipaddress
import socket
from urllib.parse import urlsplit

import httpx

MAX_BODY_SIZE = 10 * 1024 * 1024  # 10 MB limit


class InvalidURLError(ValueError):
    """Raised when URL syntax or scheme is invalid."""
    pass


class SSRFError(ValueError):
    """Raised when URL resolves to private, loopback, or metadata addresses."""
    pass


class PageInaccessibleError(Exception):
    """Raised when target page cannot be reached, times out, or returns non-HTML."""
    pass


def validate_and_sanitize_url(url: str) -> str:
    """Validates URL format, scheme, and enforces SSRF restrictions against private networks."""
    cleaned = (url or "").strip()
    if not cleaned:
        raise InvalidURLError("URL must not be empty.")

    try:
        parts = urlsplit(cleaned)
    except Exception as exc:
        raise InvalidURLError(f"Malformed URL: {exc}")

    if parts.scheme.lower() not in ("http", "https"):
        raise InvalidURLError(f"Unsupported scheme '{parts.scheme}'. Only HTTP and HTTPS are permitted.")

    hostname = parts.hostname
    if not hostname:
        raise InvalidURLError("URL lacks a valid hostname.")

    # Check for localhost / loopback aliases directly
    if hostname.lower() in ("localhost", "ip6-localhost", "ip6-loopback"):
        raise SSRFError(f"Access to localhost ('{hostname}') is prohibited.")

    # Resolve hostname to verify destination IP addresses
    try:
        addr_info = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise PageInaccessibleError(f"DNS resolution failed for host '{hostname}': {exc}")

    for family, socktype, proto, canonname, sockaddr in addr_info:
        ip_str = sockaddr[0]
        try:
            ip_obj = ipaddress.ip_address(ip_str)
        except ValueError:
            continue

        if (
            ip_obj.is_loopback
            or ip_obj.is_private
            or ip_obj.is_link_local
            or ip_obj.is_multicast
            or ip_obj.is_reserved
            or str(ip_obj) == "169.254.169.254"
        ):
            raise SSRFError(f"Target host '{hostname}' resolves to restricted IP range ({ip_str}).")

    return cleaned


async def fetch_webpage_html(url: str) -> str:
    """Streams and fetches HTML from target URL in memory with strict timeouts and size limits."""
    sanitized_url = validate_and_sanitize_url(url)

    try:
        async with httpx.AsyncClient(
            timeout=10.0,
            follow_redirects=True,
            verify=False,
            headers={"User-Agent": "ADAAccessibilityChecker/1.0 (+https://adacheck.deltadizzy.org)"},
        ) as client:
            response = await client.get(sanitized_url)

            # Check status code
            if response.status_code >= 400:
                raise PageInaccessibleError(
                    f"Target server returned error HTTP {response.status_code} ({response.reason_phrase})."
                )

            # Content-type check
            content_type = response.headers.get("content-type", "").lower()
            if "application/pdf" in content_type:
                raise PageInaccessibleError(
                    "Target URL returned a PDF document. Please use the PDF screening endpoint /api/scans/pdf."
                )
            if not any(t in content_type for t in ("text/html", "application/xhtml+xml", "text/plain")):
                raise PageInaccessibleError(
                    f"Unsupported content type '{content_type}'. Web screening requires an HTML document."
                )

            # Enforce body size limit in memory
            body_bytes = response.content
            if len(body_bytes) > MAX_BODY_SIZE:
                raise PageInaccessibleError(
                    f"Webpage payload size ({len(body_bytes)} bytes) exceeds 10 MB limit."
                )

            return response.text

    except (InvalidURLError, SSRFError):
        raise
    except PageInaccessibleError:
        raise
    except httpx.TimeoutException as exc:
        raise PageInaccessibleError(f"Connection to target timed out after 10 seconds: {exc}")
    except httpx.RequestError as exc:
        raise PageInaccessibleError(f"Network error communicating with target: {exc}")
    except Exception as exc:
        raise PageInaccessibleError(f"Unexpected error retrieving webpage: {exc}")

