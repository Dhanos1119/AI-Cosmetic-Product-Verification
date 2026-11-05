"""
Marketplace Search Orchestrator Module
Generates marketplace-specific queries, orchestrates parallel scraper calls,
applies multi-factor product matching, and aggregates final marketplace listing results.
Integrates configurable demonstration mode with strict separation of LIVE, DEMO, and UNAVAILABLE data.
"""

from concurrent.futures import ThreadPoolExecutor, wait
from datetime import datetime, timezone
from urllib.parse import quote_plus
from typing import List, Optional, Dict, Any

from app.schemas.marketplace import ProductIdentity, MarketplaceListing, MarketplaceReview
from app.services.scraping.schemas import SearchQueryBundle, RawMarketplaceItem
from app.services.scraping.product_matcher import match_product
from app.services.scraping.amazon_scraper import scrape_amazon_products
from app.services.scraping.daraz_scraper import scrape_daraz_products
from app.services.scraping.temu_scraper import scrape_temu_products
from app.services.scraping.url_validator import validate_marketplace_url
from app.services.scraping.url_scraper import scrape_user_product_url
from app.services.demo_service import (
    is_demo_mode_active,
    get_marketplace_timeout,
    get_simulated_marketplace_listing,
)

INVALID_SEARCH_TOKENS = {
    "no text detected", "unidentified product", "unknown brand", "cosmetic brand",
    "cosmetic product", "unidentified brand", "lip_products", "eye_products",
    "foundation_base", "skin_care", "other_makeup", "makeup"
}

import re

# OCR artefacts that commonly appear on cosmetic packaging but are never valid
# product search terms. These are stripped from the query before it is sent
# to any marketplace scraper.
_OCR_NOISE_TOKENS = frozenset({
    "normaltooly", "normaltooily", "normaltooilysk", "oilysk",
    "skintone", "skintype", "nw", "nc",
    "net", "wt", "new", "limited", "edition",
})


def _normalize_query(text: str) -> str:
    """
    Sanitises raw OCR-derived text into a clean marketplace search query:
    1. Removes lone punctuation fragments that OCR produces when line-splitting label text.
    2. Removes known OCR noise tokens that are never valid search terms.
    3. Replaces remaining special characters with a space.
    4. Collapses multiple whitespace runs.
    5. Strips leading / trailing non-alphanumeric characters.
    """
    if not text:
        return ""
    cleaned = re.sub(r'(?<![\w])([+\-*/\\|^~!?.,:;\'"`#@$%]{1,3})(?![\w])', ' ', text)
    cleaned = re.sub(r'[^\w\s]', ' ', cleaned)
    tokens = [t for t in cleaned.split() if t.lower() not in _OCR_NOISE_TOKENS]
    cleaned = ' '.join(tokens)
    cleaned = re.sub(r'\s{2,}', ' ', cleaned).strip()
    return cleaned


def generate_search_queries(product_identity: ProductIdentity) -> Optional[SearchQueryBundle]:
    """
    Generates normalised marketplace-specific search queries.
    Format: "[brand] [product_name]"
    """
    brand_raw = (product_identity.brand or "").strip()
    name_raw = (product_identity.product_name or "").strip()

    brand = brand_raw if brand_raw.lower() not in INVALID_SEARCH_TOKENS else ""
    name = name_raw if name_raw.lower() not in INVALID_SEARCH_TOKENS else ""

    brand_clean = _normalize_query(brand)
    name_clean = _normalize_query(name)

    base_q = f"{brand_clean} {name_clean}".strip()

    if not base_q or len(base_q) < 3 or base_q.lower() in INVALID_SEARCH_TOKENS:
        return None

    return SearchQueryBundle(
        base_query=base_q,
        amazon_query=f"{base_q}",
        daraz_query=f"{base_q}",
        temu_query=f"{base_q}",
        brand=brand_clean or "Cosmetic Brand",
        product_name=name_clean or "Cosmetic Product"
    )


def search_all_marketplaces(
    product_identity: ProductIdentity,
    user_product_url: Optional[str] = None,
    demo_key: Optional[str] = None,
) -> List[MarketplaceListing]:
    """
    Orchestrates independent concurrent marketplace requests with configurable timeout (8-12s).
    Enforces independent error handling so one marketplace failure never blocks the others.
    Assigns strict retrieval statuses:
      - LIVE: Actual verified scraped results.
      - DEMO: Configured simulated demo catalog data when live data is unavailable.
      - UNAVAILABLE: When no live or demo data is available.
    For Amazon in demonstration mode: always UNAVAILABLE with working search link.
    """
    queries = generate_search_queries(product_identity)
    has_user_url = bool(user_product_url and isinstance(user_product_url, str) and user_product_url.strip())
    demo_active = is_demo_mode_active() and bool(demo_key)

    if not queries and not has_user_url and not demo_active:
        return []

    search_q = queries.base_query if queries else (product_identity.product_name or "Cosmetic Product")

    now_iso = datetime.now(timezone.utc).isoformat()
    timeout_sec = get_marketplace_timeout()
    demo_active = is_demo_mode_active() and bool(demo_key)

    search_urls = {
        "Amazon": f"https://www.amazon.com/s?k={quote_plus(search_q)}",
        "Daraz LK": f"https://www.daraz.lk/catalog/?q={quote_plus(search_q)}",
        "Temu": f"https://www.temu.com/search_result.html?search_key={quote_plus(search_q)}"
    }

    platform_raw_items: Dict[str, List[RawMarketplaceItem]] = {
        "Amazon": [],
        "Daraz LK": [],
        "Temu": [],
    }

    user_url_item: Optional[RawMarketplaceItem] = None
    has_user_url = bool(user_product_url and isinstance(user_product_url, str) and user_product_url.strip())
    if has_user_url:
        try:
            user_url_item = scrape_user_product_url(user_product_url.strip())
        except Exception as exc:
            user_url_item = RawMarketplaceItem(
                platform="Marketplace",
                raw_title="User URL Extraction Failed",
                source_status="unavailable",
                status_code="SCRAPER_ERROR",
                explanation=f"Error scraping user-submitted URL: {str(exc)}",
                link=user_product_url
            )

    # Concurrently execute live scrapers across all platforms independently
    should_scrape_amazon = True
    should_scrape_daraz = True
    should_scrape_temu = True

    tasks = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        if should_scrape_amazon:
            tasks[executor.submit(scrape_amazon_products, search_q)] = "Amazon"
        if should_scrape_daraz:
            tasks[executor.submit(scrape_daraz_products, search_q)] = "Daraz LK"
        if should_scrape_temu:
            tasks[executor.submit(scrape_temu_products, search_q)] = "Temu"

        if tasks:
            done, not_done = wait(tasks.keys(), timeout=timeout_sec)

            for future in done:
                plat = tasks[future]
                try:
                    items = future.result()
                    if items:
                        platform_raw_items[plat] = items
                except Exception as exc:
                    print(f"[MARKETPLACE NOTICE] {plat} scraper failed independently: {exc}")
                    platform_raw_items[plat] = [RawMarketplaceItem(
                        platform=plat,
                        raw_title=f"{plat} Scraper Error",
                        source_status="unavailable",
                        status_code="SCRAPER_ERROR",
                        explanation=f"{plat} scraper failed independently: {str(exc)}"
                    )]

            for future in not_done:
                plat = tasks[future]
                future.cancel()
                print(f"[MARKETPLACE NOTICE] {plat} scraper timed out after {timeout_sec}s.")
                platform_raw_items[plat] = [RawMarketplaceItem(
                    platform=plat,
                    raw_title=f"{plat} Timeout",
                    source_status="unavailable",
                    status_code="SCRAPER_ERROR",
                    explanation=f"{plat} scraper timed out after {timeout_sec}s."
                )]

    final_listings: List[MarketplaceListing] = []

    # Process each core marketplace independently with strictly real data
    for platform_name in ["Amazon", "Daraz LK", "Temu"]:
        raw_items = platform_raw_items.get(platform_name, [])
        valid_raw = [r for r in raw_items if r.source_status == "available" and r.raw_title]
        has_scraper_error = any(r.status_code == "SCRAPER_ERROR" for r in raw_items)

        matching_raw = None
        if valid_raw:
            # Check multi-factor product match & URL validity
            for r in valid_raw:
                match_status, confidence = match_product(
                    listing_title=r.raw_title,
                    target_identity=product_identity,
                    seller_name=r.seller
                )
                is_valid_url, _ = validate_marketplace_url(r.link, platform_name)
                if is_valid_url and confidence >= 40.0:
                    matching_raw = (r, match_status, confidence)
                    break

        if matching_raw:
            best_raw, match_status, confidence = matching_raw
            final_listings.append(_build_live_listing(
                best_raw, platform_name, product_identity, search_q, search_urls[platform_name], now_iso,
                match_status=match_status, match_confidence=confidence
            ))
        elif demo_active:
            # Demo mode active: load configured demonstration listing (Amazon / Daraz DEMO, Temu UNAVAILABLE)
            sim_listing = get_simulated_marketplace_listing(demo_key, platform_name, search_q)
            if sim_listing:
                final_listings.append(sim_listing)
            else:
                final_listings.append(_build_unavailable_listing(
                    platform_name, product_identity, search_q, search_urls[platform_name], now_iso,
                    status_explanation=f"Live marketplace data unavailable."
                ))
        elif has_scraper_error and not valid_raw:
            err_item = next(r for r in raw_items if r.status_code == "SCRAPER_ERROR")
            final_listings.append(_build_unavailable_listing(
                platform_name, product_identity, search_q, search_urls[platform_name], now_iso,
                status_explanation=err_item.explanation or f"{platform_name} request failed.",
                is_failed=True
            ))
        else:
            # Marketplace returned no product data, anti-bot challenge, or client-rendered HTML
            final_listings.append(_build_unavailable_listing(
                platform_name, product_identity, search_q, search_urls[platform_name], now_iso,
                status_explanation="Live marketplace data unavailable."
            ))

    # If user provided a custom URL, prepend or append it
    if user_url_item:
        if user_url_item.source_status == "available":
            user_listing = _build_live_listing(
                user_url_item, user_url_item.platform or "Submitted URL", product_identity, search_q, user_url_item.link or search_q, now_iso
            )
        else:
            user_listing = MarketplaceListing(
                platform=user_url_item.platform or "Submitted URL",
                product_name=user_url_item.raw_title,
                brand=product_identity.brand or "Cosmetic Brand",
                product_type=product_identity.product_type or "Cosmetics",
                price=0.0,
                currency=user_url_item.currency or "USD",
                rating=0.0,
                rating_count=0,
                review_count=0,
                seller_name=user_url_item.seller,
                product_url=user_url_item.link,
                reviews=[],
                source_status="unavailable",
                match_status="Not a Match",
                match_confidence=0.0,
                status_explanation=user_url_item.explanation or "Unable to extract metadata from submitted URL.",
                search_query=search_q,
                listing_status="UNAVAILABLE",
                passed_match_threshold=False,
                retrieval_status="Data Unavailable",
                data_source="User Submitted URL",
                retrieval_timestamp=now_iso,
                search_url=user_url_item.link,
            )
        final_listings.append(user_listing)

    return final_listings


def _build_live_listing(
    raw: RawMarketplaceItem,
    platform: str,
    product_identity: ProductIdentity,
    search_query: str,
    fallback_search_url: str,
    retrieval_timestamp: str,
    match_status: Optional[str] = None,
    match_confidence: Optional[float] = None,
) -> MarketplaceListing:
    """Constructs a verified Live Data MarketplaceListing from actual scraped data."""
    if match_status is None or match_confidence is None:
        match_status, match_confidence = match_product(
            listing_title=raw.raw_title,
            target_identity=product_identity,
            seller_name=raw.seller
        )
    is_valid_url, _ = validate_marketplace_url(raw.link, platform)
    passed_threshold = is_valid_url and match_confidence >= 40.0

    sample_reviews: List[MarketplaceReview] = []
    if raw.reviews:
        for rv in raw.reviews:
            if isinstance(rv, MarketplaceReview):
                sample_reviews.append(rv)
            elif isinstance(rv, dict) and rv.get("comment"):
                sample_reviews.append(MarketplaceReview(**rv))

    curr = raw.currency
    if not curr:
        curr = "LKR" if "daraz" in platform.lower() else "USD"

    return MarketplaceListing(
        platform=platform,
        product_name=raw.raw_title,
        brand=product_identity.brand or "Cosmetic Brand",
        product_type=product_identity.product_type or "Cosmetics",
        shade_or_variant=product_identity.shade_or_variant,
        price=raw.price_val if raw.price_val and raw.price_val > 0 else 0.0,
        currency=curr,
        rating=raw.rating_val if raw.rating_val and raw.rating_val > 0 else 0.0,
        rating_count=raw.rating_count_val or 0,
        review_count=raw.review_count_val or len(sample_reviews),
        seller_name=raw.seller,
        product_url=raw.link or fallback_search_url,
        product_image_url=raw.image_link,
        reviews=sample_reviews,
        source_status="available",
        match_status=match_status,
        match_confidence=match_confidence,
        status_explanation=f"Live verified listing retrieved from {platform}.",
        search_query=search_query,
        listing_status="VERIFIED_LISTING" if passed_threshold else "PARTIAL_DATA",
        passed_match_threshold=passed_threshold,
        retrieval_status="Live Data",
        data_source="Live Scraper",
        retrieval_timestamp=retrieval_timestamp,
        search_url=fallback_search_url,
    )


def _build_unavailable_listing(
    platform: str,
    product_identity: ProductIdentity,
    search_query: str,
    search_url: str,
    retrieval_timestamp: str,
    status_explanation: str = "Live marketplace data unavailable.",
    is_failed: bool = False,
) -> MarketplaceListing:
    """Constructs a clean Data Unavailable or Retrieval Failed MarketplaceListing with search link and zero fake data."""
    return MarketplaceListing(
        platform=platform,
        product_name=f"{platform} Search: {search_query}",
        brand=product_identity.brand or "Cosmetic Brand",
        product_type=product_identity.product_type or "Cosmetics",
        price=0.0,
        currency="LKR" if "daraz" in platform.lower() else "USD",
        rating=0.0,
        rating_count=0,
        review_count=0,
        seller_name=None,
        product_url=search_url,
        product_image_url=None,
        reviews=[],
        source_status="unavailable",
        match_status="Not a Match",
        match_confidence=0.0,
        status_explanation=status_explanation,
        search_query=search_query,
        listing_status="SCRAPER_ERROR" if is_failed else "UNAVAILABLE",
        passed_match_threshold=False,
        retrieval_status="Retrieval Failed" if is_failed else "Data Unavailable",
        data_source="Direct Search",
        retrieval_timestamp=retrieval_timestamp,
        search_url=search_url,
    )
