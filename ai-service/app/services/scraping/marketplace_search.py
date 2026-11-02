"""
Marketplace Search Orchestrator Module
Generates marketplace-specific queries, orchestrates parallel scraper calls,
applies multi-factor product matching, and aggregates final marketplace listing results.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional
from app.schemas.marketplace import ProductIdentity, MarketplaceListing, MarketplaceReview
from app.services.scraping.schemas import SearchQueryBundle, RawMarketplaceItem
from app.services.scraping.product_matcher import match_product
from app.services.scraping.amazon_scraper import scrape_amazon_products
from app.services.scraping.daraz_scraper import scrape_daraz_products
from app.services.scraping.temu_scraper import scrape_temu_products
from app.services.scraping.url_validator import validate_marketplace_url
from app.services.scraping.url_scraper import scrape_user_product_url

INVALID_SEARCH_TOKENS = {
    "no text detected", "unidentified product", "unknown brand", "cosmetic brand",
    "cosmetic product", "unidentified brand", "lip_products", "eye_products",
    "foundation_base", "skin_care", "other_makeup", "makeup"
}

import re

# OCR artefacts that commonly appear on cosmetic packaging but are never valid
# product search terms.  These are stripped from the query before it is sent
# to any marketplace scraper.
_OCR_NOISE_TOKENS = frozenset({
    "normaltooly", "normaltooily", "normaltooilysk", "oilysk",
    "skintone", "skintype", "nw", "nc",
    "net", "wt", "new", "limited", "edition",
})


def _normalize_query(text: str) -> str:
    """
    Sanitises raw OCR-derived text into a clean marketplace search query:
    1. Removes lone punctuation fragments (standalone -, +, !, etc.) that OCR
       produces when line-splitting cosmetic label text.
    2. Removes known OCR noise tokens that are never valid search terms.
    3. Replaces remaining special characters with a space.
    4. Collapses multiple whitespace runs.
    5. Strips leading / trailing non-alphanumeric characters.
    """
    if not text:
        return ""
    # Remove lone punctuation tokens (not surrounded by word characters)
    cleaned = re.sub(r'(?<![\w])([+\-*/\\|^~!?.,:;\'"`#@$%]{1,3})(?![\w])', ' ', text)
    # Replace remaining special characters with spaces
    cleaned = re.sub(r'[^\w\s]', ' ', cleaned)
    # Remove OCR noise tokens (whole-word match)
    tokens = [t for t in cleaned.split() if t.lower() not in _OCR_NOISE_TOKENS]
    cleaned = ' '.join(tokens)
    # Final collapse and strip
    cleaned = re.sub(r'\s{2,}', ' ', cleaned).strip()
    return cleaned


def generate_search_queries(product_identity: ProductIdentity) -> SearchQueryBundle:
    """
    Generates normalised marketplace-specific search queries.
    Format: "[brand] [product_name]"
    The brand and product_name are cleaned of OCR artefacts (punctuation fragments,
    noise tokens) before they are combined into the base query.
    """
    brand_raw = (product_identity.brand or "").strip()
    name_raw = (product_identity.product_name or "").strip()

    brand = brand_raw if brand_raw.lower() not in INVALID_SEARCH_TOKENS else ""
    name = name_raw if name_raw.lower() not in INVALID_SEARCH_TOKENS else ""

    # Normalise both components to remove OCR punctuation artefacts and noise tokens
    brand_clean = _normalize_query(brand)
    name_clean = _normalize_query(name)

    base_q = f"{brand_clean} {name_clean}".strip()

    # Reject empty queries or queries containing only generic placeholder tokens
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

def search_all_marketplaces(product_identity: ProductIdentity, user_product_url: Optional[str] = None) -> List[MarketplaceListing]:
    """
    Orchestrates marketplace scraping and multi-factor product matching.
    Supports automated queries across platforms and optionally scrapes a user-submitted product URL.
    """
    queries = generate_search_queries(product_identity)
    has_user_url = bool(user_product_url and isinstance(user_product_url, str) and user_product_url.strip())
    if (not queries or not queries.base_query) and not has_user_url:
        return []

    # If no automated query could be generated from OCR, synthesize a minimal bundle for the user URL
    if not queries or not queries.base_query:
        queries = SearchQueryBundle(
            base_query=user_product_url.strip() if has_user_url else "",
            amazon_query="",
            daraz_query="",
            temu_query="",
            brand=product_identity.brand or "Cosmetic Brand",
            product_name=product_identity.product_name or "Cosmetic Product"
        )

    all_raw_items: List[RawMarketplaceItem] = []

    # If user provided a direct product URL, scrape it using safe validation and redirect handling
    if has_user_url:
        try:
            url_item = scrape_user_product_url(user_product_url.strip())
            all_raw_items.append(url_item)
        except Exception as exc:
            all_raw_items.append(RawMarketplaceItem(
                platform="Marketplace",
                raw_title="User URL Extraction Failed",
                source_status="unavailable",
                status_code="SCRAPER_ERROR",
                explanation=f"Error scraping user-submitted URL: {str(exc)}",
                link=user_product_url
            ))

    # Run platform scrapers concurrently in background threads IF a valid automated search query exists
    has_valid_platform_query = bool(queries.amazon_query or queries.daraz_query or queries.temu_query)
    if has_valid_platform_query:
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_scraper = {
                executor.submit(scrape_amazon_products, queries.amazon_query or queries.base_query): "Amazon",
                executor.submit(scrape_daraz_products, queries.daraz_query or queries.base_query): "Daraz",
                executor.submit(scrape_temu_products, queries.temu_query or queries.base_query): "Temu"
            }

            for future in as_completed(future_to_scraper):
                platform_name = future_to_scraper[future]
                try:
                    items = future.result()
                    all_raw_items.extend(items)
                except Exception as exc:
                    all_raw_items.append(RawMarketplaceItem(
                        platform=platform_name,
                        raw_title=f"{platform_name} Query Failed",
                        source_status="blocked",
                        explanation=f"Scraper thread exception: {str(exc)}"
                    ))

    # Process each raw item into normalized MarketplaceListing with Product Matching
    final_listings: List[MarketplaceListing] = []

    for raw in all_raw_items:
        if raw.source_status != "available":
            status_code = raw.status_code or ("MARKETPLACE_BLOCKED" if raw.source_status == "blocked" else "UNAVAILABLE")
            # Pass through blocked/unavailable status cleanly without fake data
            final_listings.append(MarketplaceListing(
                platform=raw.platform,
                product_name=raw.raw_title,
                brand=product_identity.brand,
                product_type=product_identity.product_type,
                price=0.0,
                currency=raw.currency,
                rating=0.0,
                rating_count=0,
                review_count=0,
                seller_name=None,
                product_url=raw.link,
                product_image_url=raw.image_link,
                reviews=[],
                source_status=raw.source_status,
                match_status="Not a Match",
                match_confidence=0.0,
                status_explanation=raw.explanation,
                search_query=queries.base_query,
                listing_status=status_code,
                passed_match_threshold=False
            ))
        else:
            # Execute Product Matching algorithm
            match_status, confidence = match_product(
                listing_title=raw.raw_title,
                target_identity=product_identity,
                seller_name=raw.seller
            )

            # Validate Product URL format and platform domain alignment
            is_valid_url, url_reason = validate_marketplace_url(raw.link, raw.platform)

            passed_threshold = match_status in ["Exact Product Match", "Possible Match"] and confidence >= 50.0 and is_valid_url
            
            if not is_valid_url:
                listing_status_code = "INVALID_URL"
                explanation = f"Listing product URL '{raw.link}' is missing or invalid for platform {raw.platform}: {url_reason}"
            elif raw.status_code == "PARTIAL_DATA":
                listing_status_code = "PARTIAL_DATA"
                explanation = raw.explanation or ("Listing matched but contains only partial product metadata (rating or reviews unavailable)." if passed_threshold else f"Listing title '{raw.raw_title}' rejected as product/category mismatch or low match confidence ({confidence}%).")
            else:
                listing_status_code = "VERIFIED_LISTING" if passed_threshold else "REJECTED_LOW_MATCH_CONFIDENCE"
                explanation = raw.explanation if passed_threshold else f"Listing title '{raw.raw_title}' rejected as product/category mismatch or low match confidence ({confidence}%)."

            # Only actual customer review text extracted from structured page data or permitted markup
            # is preserved; synthetic placeholder reviews remain strictly DISABLED.
            sample_reviews: List[MarketplaceReview] = []
            if raw.reviews:
                for rv in raw.reviews:
                    if isinstance(rv, MarketplaceReview):
                        sample_reviews.append(rv)
                    elif isinstance(rv, dict) and rv.get("comment"):
                        sample_reviews.append(MarketplaceReview(**rv))

            final_listings.append(MarketplaceListing(
                platform=raw.platform,
                product_name=raw.raw_title,
                brand=product_identity.brand,
                product_type=product_identity.product_type,
                shade_or_variant=product_identity.shade_or_variant,
                price=raw.price_val if passed_threshold else 0.0,
                currency=raw.currency,
                rating=raw.rating_val if passed_threshold else 0.0,
                rating_count=raw.rating_count_val if passed_threshold else 0,
                review_count=raw.review_count_val if passed_threshold else 0,
                seller_name=raw.seller if passed_threshold else None,
                product_url=raw.link,
                product_image_url=raw.image_link if passed_threshold else None,
                reviews=sample_reviews,
                source_status="available",
                match_status=match_status,
                match_confidence=confidence,
                status_explanation=explanation,
                search_query=queries.base_query,
                listing_status=listing_status_code,
                passed_match_threshold=passed_threshold
            ))

    return final_listings
