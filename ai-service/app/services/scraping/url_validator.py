"""
Marketplace URL Validation Module
Validates URL format, marketplace domain alignment, and detects internal placeholder patterns.
"""

from urllib.parse import urlparse
from typing import Optional, Tuple

VALID_DOMAINS = {
    "amazon": ["amazon.com", "amazon.in", "amazon.co.uk", "amazon.ca", "amazon.de", "amazon.fr", "amazon.co.jp", "amazon.es", "amazon.it"],
    "daraz": ["daraz.lk", "daraz.pk", "daraz.com.bd", "daraz.np", "daraz.com"],
    "temu": ["temu.com"]
}

FORBIDDEN_URL_PATTERNS = [
    "/item/p00", "/item/prod", "/item/p0", "/item/p1", "no_daraz", "temu_protection",
    "no_matching", "invalid_url", "placeholder", "undefined", "null"
]

def validate_marketplace_url(url: Optional[str], platform: Optional[str] = None) -> Tuple[bool, str]:
    """
    Validates a marketplace product URL.
    Checks HTTP/HTTPS protocol, forbidden placeholder patterns, and domain compatibility.
    Returns (is_valid, reason).
    """
    if not url or not isinstance(url, str):
        return False, "URL is empty or missing"

    url_clean = url.strip()
    if not url_clean:
        return False, "URL is empty string"

    url_lower = url_clean.lower()

    # 1. Protocol check
    if not url_lower.startswith("http://") and not url_lower.startswith("https://"):
        return False, "URL must start with http:// or https://"

    # 2. Forbidden placeholder patterns check
    for pattern in FORBIDDEN_URL_PATTERNS:
        if pattern in url_lower:
            return False, f"URL contains invalid placeholder pattern '{pattern}'"

    # 3. Domain parsing & validation
    try:
        parsed = urlparse(url_clean)
        netloc = parsed.netloc.lower()
        if not netloc:
            return False, "URL missing domain hostname"
        host = (parsed.hostname or "").lower()
        if not host:
            return False, "URL missing domain hostname"

        if platform:
            plat_clean = platform.strip().lower()
            known_domains = VALID_DOMAINS.get(plat_clean)
            if known_domains:
                # Exact host or true subdomain only (rejects look-alikes such as amazon.com.evil.example)
                domain_matched = any(host == d or host.endswith("." + d) for d in known_domains)
            else:
                domain_matched = plat_clean in host
            if not domain_matched:
                return False, f"URL domain '{netloc}' does not match expected platform '{platform}'"

    except Exception as exc:
        return False, f"URL parsing error: {str(exc)}"

    return True, "Valid URL"
