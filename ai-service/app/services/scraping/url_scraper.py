"""
User-Submitted Product URL Scraper Module
Validates hostnames, verifies redirect safety, and extracts product data from accessible pages.
Adheres strictly to anti-bot terms: never bypasses CAPTCHA, access controls, or challenge pages.
"""

import re
import logging
import requests
from urllib.parse import urlparse
from typing import Optional, Tuple, List
from app.services.scraping.schemas import RawMarketplaceItem
from app.schemas.marketplace import MarketplaceReview
from app.services.scraping.url_validator import validate_marketplace_url, VALID_DOMAINS
from app.services.scraping.metadata_extractor import extract_product_metadata

logger = logging.getLogger("ai_service.url_scraper")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Known anti-bot / challenge markers across platforms
CHALLENGE_MARKERS = {
    "amazon": (
        "api-services-support@amazon.com",
        "Type the characters you see in this image",
        "bm-verify=",
        "/_sec/verify?provider=interstitial",
    ),
    "daraz": (
        "x5secdata",
        "/_____tmd_____/punish",
        "punish?x5secdata",
        "nocaptcha"
    ),
    "temu": (
        "captcha",
    )
}


def detect_platform_from_url(url: str) -> Optional[str]:
    """Detects marketplace platform name from hostname."""
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        for plat, domains in VALID_DOMAINS.items():
            if any(host == d or host.endswith("." + d) for d in domains):
                return plat.capitalize()
    except Exception:
        pass
    return None


def is_safe_redirect(initial_url: str, final_url: str, platform: str) -> Tuple[bool, str]:
    """
    Validates that any HTTP redirects remain strictly within the authorized marketplace domain.
    Rejects redirects to untrusted external hostnames (preventing SSRF and phishing).
    """
    try:
        init_parsed = urlparse(initial_url)
        final_parsed = urlparse(final_url)

        init_host = (init_parsed.hostname or "").lower()
        final_host = (final_parsed.hostname or "").lower()

        if not final_host:
            return False, "Redirect target missing valid hostname"

        plat_key = platform.lower().strip()
        allowed_domains = VALID_DOMAINS.get(plat_key, [])

        # Final host must be an exact match or subdomain of allowed domains
        is_allowed = any(final_host == d or final_host.endswith("." + d) for d in allowed_domains)
        if not is_allowed:
            return False, f"Redirect target domain '{final_host}' is not an authorized domain for {platform}"

        return True, "Safe redirect"
    except Exception as exc:
        return False, f"Redirect validation error: {str(exc)}"


def fetch_daraz_reviews_and_ratings(
    item_id: str,
    product_url: str,
    timeout: int = 6
) -> Tuple[float, int, int, List[MarketplaceReview]]:
    """
    Fetches real ratings breakdown and customer reviews from Daraz's public review endpoint.
    Distinguishes rating count (total number of star ratings) from written review count (comments).
    Extracts actual review comments without using anti-bot bypass techniques or sessions.
    Returns: (rating_val, rating_count, written_review_count, reviews_list)
    """
    try:
        parsed = urlparse(product_url)
        domain = (parsed.hostname or "www.daraz.lk").lower()
        base_domain = domain.replace("www.", "")
        review_host = f"my.{base_domain}"
        review_url = f"https://{review_host}/pdp/review/getReviewList?itemId={item_id}&pageSize=10&filter=0&sort=0&pageNo=1"

        headers = {
            "User-Agent": HEADERS["User-Agent"],
            "Accept": "application/json, text/plain, */*",
            "Referer": product_url
        }
        resp = requests.get(review_url, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            model = data.get("model", {})
            ratings = model.get("ratings", {})

            avg_rating = float(ratings.get("average", 0.0) or 0.0)
            rate_count = int(ratings.get("rateCount", 0) or 0)
            rev_count = int(ratings.get("reviewCount", 0) or 0)

            reviews_list: List[MarketplaceReview] = []
            for item in model.get("items", []):
                content = (item.get("reviewContent") or "").strip()
                if not content:
                    continue
                author = item.get("buyerName") or "Anonymous"
                r_time = item.get("reviewTime")
                # Product rating from gradeItems or buyerRating
                grade = item.get("gradeItems", {}).get("PRODUCT_REVIEW")
                if grade is None:
                    grade = item.get("buyerRating")
                try:
                    r_val = float(grade) if grade is not None else avg_rating
                except (ValueError, TypeError):
                    r_val = avg_rating

                is_verified = (item.get("reviewStatus") == "approved")

                reviews_list.append(MarketplaceReview(
                    author=author,
                    rating=r_val,
                    comment=content,
                    date=str(r_time) if r_time else None,
                    verified_purchase=is_verified
                ))

            return avg_rating, rate_count, rev_count, reviews_list
    except Exception as exc:
        logger.warning(f"Error fetching Daraz reviews for itemId {item_id}: {exc}")

    return 0.0, 0, 0, []


def scrape_user_product_url(url: str, expected_platform: Optional[str] = None, timeout: int = 8) -> RawMarketplaceItem:
    """
    Scrapes a user-submitted marketplace product URL.
    1. Validates the URL format and platform domain.
    2. Executes a standard HTTP GET with timeout.
    3. Validates redirect safety against unauthorized domains.
    4. Detects anti-bot blocks without attempting to bypass them.
    5. Extracts structured JSON-LD and robust HTML metadata.
    6. Returns clean RawMarketplaceItem with status (SUCCESS, PARTIAL_DATA, BLOCKED, UNAVAILABLE, or INVALID_URL).
    """
    detected_plat = detect_platform_from_url(url)
    platform = expected_platform or detected_plat or "Marketplace"

    # Step 1: Pre-flight URL validation
    is_valid, reason = validate_marketplace_url(url, platform)
    if not is_valid:
        return RawMarketplaceItem(
            platform=platform,
            raw_title="Invalid Product URL",
            source_status="unavailable",
            status_code="INVALID_URL",
            explanation=f"Product URL rejected: {reason}",
            link=url
        )

    # Step 2: Fetch URL with safe redirect handling
    try:
        session = requests.Session()
        resp = session.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)

        # Step 3: Check redirect safety
        if resp.history:
            safe, redirect_reason = is_safe_redirect(url, resp.url, platform)
            if not safe:
                return RawMarketplaceItem(
                    platform=platform,
                    raw_title="Unsafe Redirect Detected",
                    source_status="unavailable",
                    status_code="INVALID_URL",
                    explanation=f"URL redirected unsafely: {redirect_reason}",
                    link=url
                )

        # Step 4: Check HTTP status codes for anti-bot / rate limiting
        final_url = resp.url if isinstance(getattr(resp, 'url', None), str) and resp.url else url

        if resp.status_code in (403, 503, 429):
            return RawMarketplaceItem(
                platform=platform,
                raw_title=f"{platform} Access Blocked",
                source_status="blocked",
                status_code="MARKETPLACE_BLOCKED",
                explanation=f"{platform} returned HTTP {resp.status_code} anti-bot protection. Live product data is unavailable.",
                link=final_url
            )

        if resp.status_code != 200:
            return RawMarketplaceItem(
                platform=platform,
                raw_title=f"{platform} HTTP {resp.status_code}",
                source_status="unavailable",
                status_code="UNAVAILABLE",
                explanation=f"{platform} server returned non-200 HTTP status: {resp.status_code}.",
                link=final_url
            )

        # Step 5: Check explicit challenge / CAPTCHA markers
        plat_lower = platform.lower()
        markers = CHALLENGE_MARKERS.get(plat_lower, ())
        low_text = resp.text.lower() if isinstance(getattr(resp, 'text', None), str) else ""
        for marker in markers:
            if marker.lower() in low_text:
                return RawMarketplaceItem(
                    platform=platform,
                    raw_title=f"{platform} Challenge Active",
                    source_status="blocked",
                    status_code="MARKETPLACE_BLOCKED",
                    explanation=f"{platform} returned an anti-bot challenge / verification page (HTTP {resp.status_code}). Not bypassed.",
                    link=final_url
                )

        # Step 6: Extract metadata (JSON-LD + HTML selectors + embedded state)
        html_raw = resp.text if isinstance(getattr(resp, 'text', None), str) else ""
        meta = extract_product_metadata(html_raw, platform=platform, url=final_url)

        # Step 6b: Enrich Daraz products with public review & rating breakdown
        if platform.lower() == "daraz":
            item_id = meta.get("item_id")
            if not item_id:
                m_id = re.search(r'-i(\d+)', final_url)
                if m_id:
                    item_id = m_id.group(1)
            if item_id and (meta.get("rating_val", 0.0) == 0.0 or not meta.get("reviews")):
                avg_r, rate_c, rev_c, rev_items = fetch_daraz_reviews_and_ratings(item_id, final_url, timeout=timeout)
                if avg_r > 0.0 or rate_c > 0:
                    meta["rating_val"] = avg_r
                    meta["rating_count_val"] = rate_c
                    meta["review_count_val"] = rev_c
                if rev_items:
                    meta["reviews"] = rev_items

        if meta["status"] == "UNAVAILABLE":
            return RawMarketplaceItem(
                platform=platform,
                raw_title="No Product Data Retrieved",
                source_status="unavailable",
                status_code="UNAVAILABLE",
                explanation=meta["explanation"],
                link=final_url
            )

        # Re-assess completeness status after review enrichment
        has_price = (meta.get("price_val", 0.0) > 0.0)
        has_rating = (meta.get("rating_val", 0.0) > 0.0 or meta.get("rating_count_val", 0) > 0)
        has_reviews = bool(meta.get("reviews"))

        if has_price and (has_rating or has_reviews):
            final_status = "SUCCESS"
            final_explanation = "Extracted product title, price, and marketplace rating/review data."
        else:
            final_status = "PARTIAL_DATA"
            missing = []
            if not has_price:
                missing.append("price")
            if not has_rating:
                missing.append("rating")
            if not has_reviews:
                missing.append("reviews")
            final_explanation = f"Extracted product title '{meta.get('title')}' but missing: {', '.join(missing)}."

        # Step 7: Formulate RawMarketplaceItem
        return RawMarketplaceItem(
            platform=platform,
            raw_title=meta["title"],
            brand=meta.get("brand"),
            price_val=meta.get("price_val", 0.0),
            price_str=meta.get("price_str"),
            currency=meta.get("currency") or ("USD" if "amazon" in platform.lower() else None),
            rating_val=meta.get("rating_val", 0.0),
            rating_count_val=meta.get("rating_count_val", 0),
            review_count_val=meta.get("review_count_val", 0),
            seller=meta.get("seller"),
            link=final_url,
            image_link=meta.get("image_link"),
            source_status="available",
            status_code=final_status,
            explanation=final_explanation,
            reviews=meta.get("reviews", [])
        )

    except requests.exceptions.Timeout:
        return RawMarketplaceItem(
            platform=platform,
            raw_title=f"{platform} Request Timeout",
            source_status="unavailable",
            status_code="SCRAPER_ERROR",
            explanation=f"Timed out ({timeout}s) waiting for response from {platform}.",
            link=url
        )
    except requests.exceptions.RequestException as exc:
        return RawMarketplaceItem(
            platform=platform,
            raw_title=f"{platform} Connection Failed",
            source_status="blocked",
            status_code="SCRAPER_ERROR",
            explanation=f"Network error accessing {platform}: {str(exc)}",
            link=url
        )
    except Exception as exc:
        return RawMarketplaceItem(
            platform=platform,
            raw_title=f"{platform} Extraction Error",
            source_status="unavailable",
            status_code="SCRAPER_ERROR",
            explanation=f"Unexpected error processing page: {str(exc)}",
            link=url
        )
