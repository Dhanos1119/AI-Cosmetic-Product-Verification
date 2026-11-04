"""
Database Persistence Service Module for AI Cosmetic Product Verification.
Handles atomic transactional persistence of multi-modal analysis, marketplace listings,
review sentiment analysis, and platform comparison evidence.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.models import (
    Product,
    Marketplace,
    Seller,
    MarketplaceListing,
    CustomerReview,
    ReviewAnalysis,
    MarketplaceEvidence,
)
from app.schemas.marketplace import (
    ProductIdentity as ProductIdentitySchema,
    MarketplaceListing as MarketplaceListingSchema,
    PlatformComparisonScore as PlatformComparisonScoreSchema,
    MarketplaceReview as MarketplaceReviewSchema,
)
from app.services.scraping.url_validator import validate_marketplace_url

logger = logging.getLogger("database.persistence")


def get_or_create_product(db: Session, identity: ProductIdentitySchema) -> Product:
    """Retrieves or creates a catalog Product record based on product_id or brand/name/variant."""
    # 1. Try matching by product_id if present
    if identity.product_id:
        existing = db.query(Product).filter(Product.product_id == identity.product_id).first()
        if existing:
            return existing

    # 2. Try matching by unique constraint: (brand, product_name, shade_or_variant)
    existing = db.query(Product).filter(
        Product.brand == identity.brand,
        Product.product_name == identity.product_name,
        Product.shade_or_variant == identity.shade_or_variant,
    ).first()
    if existing:
        return existing

    # 3. Try matching by synthesized product_id if brand and name align
    base_prod_id = identity.product_id or f"PROD_{identity.brand[:3].upper()}_{identity.product_name[:3].upper()}"
    existing_by_pid = db.query(Product).filter(Product.product_id == base_prod_id).first()
    if existing_by_pid:
        brand_matches = (existing_by_pid.brand or "").strip().lower() == (identity.brand or "").strip().lower()
        if brand_matches:
            ex_name = (existing_by_pid.product_name or "").strip().lower()
            id_name = (identity.product_name or "").strip().lower()
            if ex_name == id_name or ex_name in id_name or id_name in ex_name:
                return existing_by_pid

    # 4. Create new product record, guaranteeing unique product_id to avoid constraint violations
    prod_id_val = base_prod_id
    if db.query(Product).filter(Product.product_id == prod_id_val).first():
        counter = 1
        while db.query(Product).filter(Product.product_id == f"{base_prod_id}_{counter}").first():
            counter += 1
        prod_id_val = f"{base_prod_id}_{counter}"

    new_product = Product(
        product_id=prod_id_val,
        brand=identity.brand,
        product_name=identity.product_name,
        product_type=identity.product_type,
        category=identity.category,
        shade_or_variant=identity.shade_or_variant,
    )
    db.add(new_product)
    db.flush()
    return new_product


def get_or_create_marketplace(db: Session, platform_name: str) -> Marketplace:
    """Retrieves or creates a Marketplace platform registry record by platform code/name."""
    code = platform_name.lower().strip()
    existing = db.query(Marketplace).filter(Marketplace.platform_code == code).first()
    if existing:
        return existing

    base_urls = {
        "amazon": "https://www.amazon.com",
        "daraz": "https://www.daraz.lk",
        "temu": "https://www.temu.com",
    }
    new_mkt = Marketplace(
        platform_code=code,
        platform_name=platform_name.capitalize(),
        base_url=base_urls.get(code, f"https://www.{code}.com"),
        api_type="http_scraper",
        currency_code="USD",
        is_active=True,
    )
    db.add(new_mkt)
    db.flush()
    return new_mkt


def get_or_create_seller(db: Session, marketplace_id: str, seller_name: Optional[str]) -> Optional[Seller]:
    """Retrieves or creates a Seller merchant record."""
    if not seller_name or seller_name.strip() == "":
        return None

    s_name = seller_name.strip()
    existing = db.query(Seller).filter(
        Seller.marketplace_id == marketplace_id,
        Seller.seller_name == s_name,
    ).first()
    if existing:
        return existing

    is_official = any(kw in s_name.lower() for kw in ["official", "verified", "mall", "direct"])
    new_seller = Seller(
        marketplace_id=marketplace_id,
        seller_name=s_name,
        is_official_store=is_official,
        seller_rating=4.5 if is_official else 4.0,
        verified_status="verified_official" if is_official else "unverified",
    )
    db.add(new_seller)
    db.flush()
    return new_seller


def upsert_marketplace_listing(
    db: Session,
    product: Product,
    marketplace: Marketplace,
    seller: Optional[Seller],
    listing_schema: MarketplaceListingSchema,
) -> MarketplaceListing:
    """Upserts a marketplace product listing using unique (marketplace_id, product_url) constraint."""
    url = (listing_schema.product_url or "").strip()
    is_valid_url, url_reason = validate_marketplace_url(url, marketplace.platform_name)
    if not is_valid_url:
        raise ValueError(f"Cannot upsert listing with invalid product URL '{url}': {url_reason}")

    existing = db.query(MarketplaceListing).filter(
        MarketplaceListing.marketplace_id == marketplace.id,
        MarketplaceListing.product_url == url,
    ).first()

    if existing:
        existing.raw_title = listing_schema.product_name
        existing.price = listing_schema.price or 0.0
        existing.currency = listing_schema.currency or "USD"
        existing.rating = listing_schema.rating or 0.0
        existing.review_count = listing_schema.review_count or 0
        existing.product_image_url = listing_schema.product_image_url
        existing.source_status = listing_schema.source_status
        existing.match_status = listing_schema.match_status
        existing.match_confidence = listing_schema.match_confidence
        existing.status_explanation = listing_schema.status_explanation
        existing.search_query = listing_schema.search_query
        existing.listing_status = listing_schema.listing_status or "VERIFIED_LISTING"
        existing.passed_match_threshold = listing_schema.passed_match_threshold
        existing.last_scraped_at = datetime.now(timezone.utc)
        if seller:
            existing.seller_id = seller.id
        db.flush()
        return existing

    new_listing = MarketplaceListing(
        product_id=product.id,
        marketplace_id=marketplace.id,
        seller_id=seller.id if seller else None,
        raw_title=listing_schema.product_name,
        price=listing_schema.price or 0.0,
        currency=listing_schema.currency or "USD",
        rating=listing_schema.rating or 0.0,
        review_count=listing_schema.review_count or 0,
        product_url=url,
        product_image_url=listing_schema.product_image_url,
        source_status=listing_schema.source_status,
        match_status=listing_schema.match_status,
        match_confidence=listing_schema.match_confidence,
        status_explanation=listing_schema.status_explanation,
        search_query=listing_schema.search_query,
        listing_status=listing_schema.listing_status or "VERIFIED_LISTING",
        passed_match_threshold=listing_schema.passed_match_threshold,
    )
    db.add(new_listing)
    db.flush()
    return new_listing


def save_customer_reviews(
    db: Session,
    listing: MarketplaceListing,
    reviews: List[MarketplaceReviewSchema],
) -> List[CustomerReview]:
    """Saves customer reviews for a given listing."""
    # Delete existing reviews to prevent stale duplicates on update
    db.query(CustomerReview).filter(CustomerReview.listing_id == listing.id).delete()
    db.flush()

    saved = []
    for r in reviews:
        rev = CustomerReview(
            listing_id=listing.id,
            author=r.author or "Anonymous",
            rating=r.rating or 0.0,
            comment_text=r.comment,
            review_date=r.date,
            is_verified_purchase=r.verified_purchase or False,
        )
        db.add(rev)
        saved.append(rev)
    db.flush()
    return saved


def upsert_review_analysis(
    db: Session,
    listing: MarketplaceListing,
    review_res: Dict[str, Any],
) -> ReviewAnalysis:
    """Upserts review authenticity and sentiment analysis for a listing."""
    existing = db.query(ReviewAnalysis).filter(ReviewAnalysis.listing_id == listing.id).first()

    auth_score = float(review_res.get("review_authenticity_score") or 0.0)
    avg_rating = float(review_res.get("average_rating") or 0.0)
    verified_pct = float(review_res.get("verified_buyer_percentage") or 0.0)

    if existing:
        existing.review_authenticity_score = auth_score
        existing.sentiment_label = review_res.get("sentiment_label", "Neutral")
        existing.average_rating = avg_rating
        existing.verified_buyer_percentage = verified_pct
        existing.authenticity_status = review_res.get("authenticity_status", "Unverified")
        existing.suspicious_review_flag = bool(review_res.get("suspicious_review_flag", False))
        existing.summary = review_res.get("summary", "")
        existing.analyzed_at = datetime.now(timezone.utc)
        db.flush()
        return existing

    new_analysis = ReviewAnalysis(
        listing_id=listing.id,
        review_authenticity_score=auth_score,
        sentiment_label=review_res.get("sentiment_label", "Neutral"),
        average_rating=avg_rating,
        verified_buyer_percentage=verified_pct,
        authenticity_status=review_res.get("authenticity_status", "Unverified"),
        suspicious_review_flag=bool(review_res.get("suspicious_review_flag", False)),
        summary=review_res.get("summary", ""),
    )
    db.add(new_analysis)
    db.flush()
    return new_analysis


def upsert_marketplace_evidence(
    db: Session,
    listing: MarketplaceListing,
    comp_score: PlatformComparisonScoreSchema,
) -> MarketplaceEvidence:
    """Upserts marketplace platform comparison evidence score for a listing."""
    existing = db.query(MarketplaceEvidence).filter(MarketplaceEvidence.listing_id == listing.id).first()
    bd = comp_score.score_breakdown

    if existing:
        existing.total_score = comp_score.total_score
        existing.rank = comp_score.rank
        existing.review_trust_score = bd.review_trust_score
        existing.rating_score = bd.rating_score
        existing.seller_trust_score = bd.seller_trust_score
        existing.match_confidence_score = bd.match_confidence_score
        existing.recommendation_reason = comp_score.recommendation_reason
        existing.evaluated_at = datetime.now(timezone.utc)
        db.flush()
        return existing

    new_evidence = MarketplaceEvidence(
        listing_id=listing.id,
        total_score=comp_score.total_score,
        rank=comp_score.rank,
        review_trust_score=bd.review_trust_score,
        rating_score=bd.rating_score,
        seller_trust_score=bd.seller_trust_score,
        match_confidence_score=bd.match_confidence_score,
        recommendation_reason=comp_score.recommendation_reason,
    )
    db.add(new_evidence)
    db.flush()
    return new_evidence


INVALID_PERSIST_TITLES = {
    "no daraz listings returned", "temu protection active", "no matching listings",
    "daraz access restricted", "temu access restricted", "amazon access blocked",
    "amazon captcha blocked", "no text detected", "unidentified product", "no matching daraz listings",
    "no matching temu listings", "no direct amazon listings returned", "daraz product",
    "temu cosmetic listing", "daraz query failed", "temu query failed", "amazon query failed",
    "no matching listings found"
}

UNRELATED_PERSIST_KEYWORDS = {
    "bluetooth", "headset", "earpiece", "headphone", "earbuds", "wireless earpiece",
    "charger", "usb cable", "keyboard", "mouse", "laptop", "smartwatch", "clothing",
    "shirt", "pants", "shoes", "dress", "jacket", "coat", "car", "auto", "tool"
}

def is_valid_listing_for_persistence(listing_schema: MarketplaceListingSchema) -> bool:
    """
    Defensive validation rule before inserting marketplace listing into database:
    1. Must be available (not blocked/unavailable/failed)
    2. Must be a valid match (not 'Not a Match' or confidence < 50%)
    3. Must not be a placeholder title or scraper error string
    4. Must not contain non-cosmetic unrelated keywords (electronics, clothing, etc.)
    5. Must have a valid HTTP/HTTPS product_url (not placeholder or status text)
    """
    if not listing_schema or not listing_schema.product_name:
        return False

    if listing_schema.source_status != "available":
        return False

    if listing_schema.match_status == "Not a Match" or (listing_schema.match_confidence or 0.0) < 50.0:
        return False

    is_valid_match = listing_schema.match_status in ["Exact Product Match", "Possible Match"] and (listing_schema.match_confidence or 0.0) >= 50.0
    if not is_valid_match and listing_schema.passed_match_threshold is False:
        return False

    # Listing status check: reject explicitly invalid listing statuses
    status = (listing_schema.listing_status or "").upper()
    if status in ["BLOCKED", "NO_MATCH", "REJECTED_UNRELATED", "REJECTED_LOW_MATCH_CONFIDENCE", "ERROR"]:
        return False
    if status == "UNAVAILABLE" and listing_schema.source_status != "available":
        return False

    raw_title_clean = listing_schema.product_name.strip().lower()
    if raw_title_clean in INVALID_PERSIST_TITLES:
        return False

    title_words = set(raw_title_clean.split())
    if title_words.intersection(UNRELATED_PERSIST_KEYWORDS):
        return False

    # Validate source URL format, platform domain, and absence of internal placeholder patterns
    is_valid_url, _ = validate_marketplace_url(listing_schema.product_url, listing_schema.platform)
    if not is_valid_url:
        return False

    return True


def persist_analysis_results(db: Session, result_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Persists complete analysis pipeline output into PostgreSQL cleanly within an atomic transaction.
    Only valid products and real, relevant marketplace listings are persisted.
    Placeholder, blocked, unavailable, or unrelated listings are excluded from database tables.
    If database persistence fails, rolls back and logs the error safely.
    """
    identity_dict = result_data.get("product_identity")
    if not identity_dict:
        logger.warning("No product_identity provided in result_data; skipping persistence.")
        return result_data

    try:
        identity = ProductIdentitySchema(**identity_dict)
        product_db = get_or_create_product(db, identity)

        platform_comp_list = result_data.get("platform_comparison", [])
        review_res = result_data.get("review_result", {})

        valid_listings_persisted = 0

        for comp_item in platform_comp_list:
            comp_score = PlatformComparisonScoreSchema(**comp_item)
            listing_schema = comp_score.listing

            # Filter out placeholder, blocked, unavailable, or non-matching marketplace items
            if not is_valid_listing_for_persistence(listing_schema):
                logger.info(f"Skipped persistence for non-valid/placeholder listing: '{listing_schema.product_name}' (status: {listing_schema.source_status}, match: {listing_schema.match_status})")
                continue

            marketplace_db = get_or_create_marketplace(db, comp_score.platform)
            seller_db = get_or_create_seller(db, marketplace_db.id, listing_schema.seller_name)
            listing_db = upsert_marketplace_listing(db, product_db, marketplace_db, seller_db, listing_schema)

            if listing_schema.reviews:
                save_customer_reviews(db, listing_db, listing_schema.reviews)

            if review_res and review_res.get("authenticity_analysis_status") != "NOT_VALIDATED" \
                    and review_res.get("review_authenticity_score") is not None:
                upsert_review_analysis(db, listing_db, review_res)

            upsert_marketplace_evidence(db, listing_db, comp_score)
            valid_listings_persisted += 1

        db.commit()
        logger.info(f"Successfully persisted analysis results for product '{product_db.product_name}' (ID: {product_db.product_id}, Valid Listings Persisted: {valid_listings_persisted})")
        result_data["db_persisted"] = True
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(f"PostgreSQL persistence transaction failed, rolled back cleanly: {str(exc)}")
        result_data["db_persisted"] = False
        result_data["db_error"] = str(exc)
    except Exception as exc:
        db.rollback()
        logger.error(f"Unexpected error during DB persistence, rolled back cleanly: {str(exc)}")
        result_data["db_persisted"] = False
        result_data["db_error"] = str(exc)

    return result_data
