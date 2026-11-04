"""
Test Suite for Phases 2 through 6:
- Marketplace search & query normalization
- Direct URL scraping & metadata extraction
- Customer review collection & DB persistence
- Sentiment analysis on collected reviews
- Missing review text & unavailable marketplace handling
- Suspicious review risk indicators (explainable heuristic)
- Evidence-based authenticity assessment outcomes
- Complete image-upload-to-analysis workflow
"""

import pytest
from io import BytesIO
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.marketplace import ProductIdentity, MarketplaceListing, MarketplaceReview
from app.services.scraping.marketplace_search import _normalize_query, generate_search_queries, search_all_marketplaces
from app.services.scraping.url_validator import validate_marketplace_url
from app.services.scraping.url_scraper import scrape_user_product_url
from app.services.scraping.metadata_extractor import extract_product_metadata
from app.services.review_analysis_service import (
    analyze_product_reviews,
    evaluate_suspicious_review_risk,
    build_marketplace_sentiment,
)
from app.services.authenticity_service import predict_final_authenticity
from app.services.marketplace_comparison_service import compare_marketplace_platforms
from database.connection import SessionLocal
from database.models import Product, Marketplace, MarketplaceListing as DbListing, CustomerReview
from database.persistence_service import (
    get_or_create_product,
    get_or_create_marketplace,
    upsert_marketplace_listing,
    save_customer_reviews,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Marketplace Product Search & Query Normalization
# ---------------------------------------------------------------------------

def test_query_normalization_removes_ocr_noise():
    """Verify OCR punctuation fragments and cosmetic noise tokens are stripped."""
    raw_ocr = "CeraVe - + ! Moisturizing Lotion normaltooly edition net wt"
    cleaned = _normalize_query(raw_ocr)
    assert "CeraVe Moisturizing Lotion" in cleaned
    assert "+" not in cleaned
    assert "normaltooly" not in cleaned
    assert "edition" not in cleaned
    assert "wt" not in cleaned


def test_generate_search_queries_valid():
    """Generates structured search bundle for valid brand and product."""
    identity = ProductIdentity(
        brand="CeraVe",
        product_name="Daily Moisturizing Lotion",
        product_type="Skin Care",
        category="Skin Care"
    )
    bundle = generate_search_queries(identity)
    assert bundle is not None
    assert bundle.base_query == "CeraVe Daily Moisturizing Lotion"
    assert "CeraVe" in bundle.amazon_query
    assert "CeraVe" in bundle.daraz_query


def test_generate_search_queries_rejects_placeholder_tokens():
    """Rejects placeholder tokens like 'No text detected' or 'Unidentified product'."""
    identity = ProductIdentity(
        brand="No text detected",
        product_name="Unidentified product",
        product_type="Cosmetics",
        category="Cosmetics"
    )
    bundle = generate_search_queries(identity)
    assert bundle is None


def test_manually_supplied_product_url_scraping_and_validation():
    """Direct URL input is validated for domain alignment and redirect safety."""
    valid_url = "https://www.daraz.lk/products/cerave-daily-moisturizing-lotion-i123456789.html"
    is_valid, reason = validate_marketplace_url(valid_url, "Daraz")
    assert is_valid is True
    assert "valid" in reason.lower()

    invalid_url = "https://phishing-site.com/fake-product"
    is_valid_bad, reason_bad = validate_marketplace_url(invalid_url, "Daraz")
    assert is_valid_bad is False


# ---------------------------------------------------------------------------
# 2. Real Listing Metadata Extraction
# ---------------------------------------------------------------------------

def test_metadata_extractor_parses_json_ld_and_html():
    """Extracts actual title, price, currency, rating, and review count from HTML/JSON-LD."""
    sample_html = """
    <html>
      <head>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org/",
          "@type": "Product",
          "name": "CeraVe Daily Moisturizing Lotion 12 oz",
          "brand": {"@type": "Brand", "name": "CeraVe"},
          "offers": {
            "@type": "Offer",
            "price": "14.99",
            "priceCurrency": "USD"
          },
          "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": "4.7",
            "reviewCount": "1250"
          },
          "review": [
            {
              "@type": "Review",
              "author": {"@type": "Person", "name": "Jane D."},
              "reviewRating": {"@type": "Rating", "ratingValue": "5"},
              "reviewBody": "Excellent moisturizer for dry skin! Absorbs quickly."
            }
          ]
        }
        </script>
      </head>
      <body>
        <div id="productTitle">CeraVe Daily Moisturizing Lotion 12 oz</div>
      </body>
    </html>
    """
    meta = extract_product_metadata(sample_html, platform="Amazon", url="https://www.amazon.com/dp/B000123456")
    assert meta["status"] == "SUCCESS"
    assert "CeraVe" in meta["title"]
    assert meta["price_val"] == 14.99
    assert meta["currency"] == "USD"
    assert meta["rating_val"] == 4.7
    assert meta["review_count_val"] == 1250
    assert len(meta["reviews"]) == 1
    assert meta["reviews"][0].author == "Jane D."
    assert "moisturizer" in meta["reviews"][0].comment


# ---------------------------------------------------------------------------
# 3. Customer Review Collection & Database Persistence
# ---------------------------------------------------------------------------

def test_customer_review_database_persistence():
    """Verifies that collected reviews are atomically stored and de-duplicated in PostgreSQL."""
    db = SessionLocal()
    try:
        # Create product and marketplace
        identity = ProductIdentity(
            brand="TestBrand",
            product_name="TestMoisturizer",
            product_type="Skin Care",
            category="Skin Care"
        )
        prod = get_or_create_product(db, identity)
        mkt = get_or_create_marketplace(db, "amazon")

        test_url = "https://www.amazon.com/dp/B0TESTREV01"
        listing_schema = MarketplaceListing(
            platform="Amazon",
            product_name="TestBrand Moisturizer 8oz",
            brand="TestBrand",
            product_type="Skin Care",
            price=19.99,
            currency="USD",
            rating=4.6,
            review_count=2,
            product_url=test_url,
            source_status="available",
            match_status="Exact Product Match",
            match_confidence=90.0,
            listing_status="VERIFIED_LISTING",
            passed_match_threshold=True,
            reviews=[
                MarketplaceReview(
                    author="Buyer Alice",
                    rating=5.0,
                    comment="Great cream, helped my barrier immensely.",
                    date="2026-01-15",
                    verified_purchase=True
                ),
                MarketplaceReview(
                    author="Buyer Bob",
                    rating=4.0,
                    comment="Hydrating but slightly greasy in summer.",
                    date="2026-01-16",
                    verified_purchase=False
                )
            ]
        )

        listing_record = upsert_marketplace_listing(db, prod, mkt, None, listing_schema)
        db.commit()

        # Save reviews
        saved_reviews = save_customer_reviews(db, listing_record, listing_schema.reviews)
        db.commit()

        assert len(saved_reviews) == 2
        rev_texts = [r.comment_text for r in saved_reviews]
        assert "Great cream, helped my barrier immensely." in rev_texts
        assert any(r.is_verified_purchase for r in saved_reviews)

        # Re-save with 1 review to verify no stale duplicates remain
        updated_reviews = [
            MarketplaceReview(
                author="Buyer Alice",
                rating=5.0,
                comment="Updated review: Still loving this cream.",
                date="2026-02-01",
                verified_purchase=True
            )
        ]
        saved_again = save_customer_reviews(db, listing_record, updated_reviews)
        db.commit()

        persisted_in_db = db.query(CustomerReview).filter(CustomerReview.listing_id == listing_record.id).all()
        assert len(persisted_in_db) == 1
        assert "Updated review" in persisted_in_db[0].comment_text

    finally:
        db.rollback()
        db.close()


# ---------------------------------------------------------------------------
# 4. Sentiment Analysis Integration on Real Reviews
# ---------------------------------------------------------------------------

def test_sentiment_analysis_on_collected_reviews():
    """Analyzes real customer review text and outputs positive/negative/neutral labels with confidence."""
    collected = [
        {"text": "Absolutely fantastic product, my skin feels amazing and glowing!", "rating": 5.0},
        {"text": "Awful formula, made my skin red, itchy, and irritated. Do not buy.", "rating": 1.0},
        {"text": "It is an okay moisturizer, neither bad nor exceptional.", "rating": 3.0}
    ]
    sentiment_result = build_marketplace_sentiment(collected)
    assert sentiment_result["status"] == "completed"
    assert sentiment_result["analyzed_count"] == 3
    assert sentiment_result["counts"]["positive"] >= 1
    assert sentiment_result["counts"]["negative"] >= 1
    assert len(sentiment_result["analyzed_reviews"]) == 3
    for r in sentiment_result["analyzed_reviews"]:
        assert r["sentiment"] in ("positive", "negative", "neutral")
        assert 0.0 <= r["sentiment_confidence"] <= 1.0


def test_empty_review_text_handled_safely():
    """Handles missing or empty review text safely without fabricating sentiment or crashing."""
    res = build_marketplace_sentiment([])
    assert res["status"] == "NO_REVIEW_TEXT_AVAILABLE"
    assert res["analyzed_count"] == 0
    assert res["counts"]["positive"] == 0
    assert "No actual customer review text was collected" in res["explanation"]

    res_whitespace = build_marketplace_sentiment([{"text": "   "}, {"text": None}])
    assert res_whitespace["status"] == "NO_REVIEW_TEXT_AVAILABLE"
    assert res_whitespace["analyzed_count"] == 0


# ---------------------------------------------------------------------------
# 5. Suspicious-Review Risk Detection (Explainable Heuristic)
# ---------------------------------------------------------------------------

def test_suspicious_review_insufficient_data():
    """Returns INSUFFICIENT_DATA when review count is less than 3."""
    reviews = [
        {"text": "Good lotion.", "rating": 5.0, "author": "User A"}
    ]
    risk = evaluate_suspicious_review_risk(reviews)
    assert risk["status"] == "INSUFFICIENT_DATA"
    assert risk["risk_level"] == "INSUFFICIENT_DATA"
    assert risk["flag"] is False
    assert "Insufficient customer review data" in risk["explanation"]
    assert risk["is_validated_ml_detector"] is False


def test_suspicious_review_duplicate_text_detection():
    """Detects identical or near-duplicate review comment bodies."""
    reviews = [
        {"text": "This product completely transformed my sensitive dry skin overnight!", "rating": 5.0, "author": "Alice"},
        {"text": "This product completely transformed my sensitive dry skin overnight!", "rating": 5.0, "author": "Bob"},
        {"text": "Very hydrating daily face lotion for winter.", "rating": 4.0, "author": "Charlie"},
    ]
    risk = evaluate_suspicious_review_risk(reviews)
    assert risk["status"] == "EVALUATED"
    indicator_names = [ind["indicator"] for ind in risk["indicators_detected"]]
    assert "DUPLICATE_REVIEW_TEXT" in indicator_names
    assert risk["flag"] is True
    assert risk["risk_level"] in ("ELEVATED", "MODERATE")


def test_suspicious_review_rating_sentiment_conflict_detection():
    """Detects sharp conflict between 5-star rating and strongly negative text."""
    reviews = [
        {"text": "Terrible product, caused severe chemical burns, itchy rash, complete garbage.", "rating": 5.0, "sentiment": "negative", "sentiment_confidence": 0.92, "author": "Alice"},
        {"text": "Average product, nothing special.", "rating": 3.0, "sentiment": "neutral", "sentiment_confidence": 0.55, "author": "Bob"},
        {"text": "Good everyday moisturizer.", "rating": 4.0, "sentiment": "positive", "sentiment_confidence": 0.80, "author": "Charlie"}
    ]
    risk = evaluate_suspicious_review_risk(reviews)
    assert risk["status"] == "EVALUATED"
    indicator_names = [ind["indicator"] for ind in risk["indicators_detected"]]
    assert "RATING_SENTIMENT_MISMATCH" in indicator_names


# ---------------------------------------------------------------------------
# 6. Evidence-Based Product Authenticity Assessment
# ---------------------------------------------------------------------------

def test_authenticity_outcome_requires_manual_verification():
    """Packaging verified by OCR and 1-NN CLIP outputs REQUIRES_MANUAL_VERIFICATION."""
    ocr = {"confidence": 0.95, "brand_name": "CeraVe", "product_name": "Moisturizing Cream", "category": "Skin Care"}
    clip = {
        "confidence_level": "High",
        "similarity_percentage": 94.5,
        "matched_brand": "CeraVe",
        "matched_product_name": "Moisturizing Cream",
        "catalog_category_mismatch": False,
        "discrimination_margin": 6.5
    }
    review = {"authenticity_analysis_status": "NOT_VALIDATED", "review_authenticity_score": None}
    img = {"width": 800, "height": 800, "image_validation": "valid"}

    res = predict_final_authenticity(ocr, clip, review, img)
    assert res["assessment_outcome"] == "REQUIRES_MANUAL_VERIFICATION"
    assert "REQUIRES_MANUAL_VERIFICATION" in res["assessment_outcome"]
    assert len(res["verified_evidence"]) >= 2
    assert len(res["missing_information"]) >= 2
    assert "chemical composition" in " ".join(res["missing_information"]).lower()


def test_authenticity_outcome_inconsistent_information():
    """Detects category mismatch and flags INCONSISTENT_INFORMATION."""
    ocr = {"confidence": 0.90, "brand_name": "MAC", "product_name": "Studio Fix", "category": "Eye Products"}
    clip = {
        "confidence_level": "High",
        "similarity_percentage": 91.0,
        "matched_brand": "MAC",
        "matched_product_name": "Studio Fix",
        "matched_category": "Face Foundation",
        "catalog_category_mismatch": True,
        "discrimination_margin": 4.0
    }
    review = {"authenticity_analysis_status": "NOT_VALIDATED", "review_authenticity_score": None}
    img = {"width": 800, "height": 800, "image_validation": "valid"}

    res = predict_final_authenticity(ocr, clip, review, img)
    assert res["assessment_outcome"] == "INCONSISTENT_INFORMATION"
    assert len(res["inconsistencies"]) >= 1
    assert "Category conflict" in res["inconsistencies"][0]


def test_authenticity_outcome_insufficient_evidence():
    """When CLIP confidence is Low and margin is poor, outputs INSUFFICIENT_EVIDENCE."""
    ocr = {"confidence": 0.30, "brand_name": "", "product_name": "", "category": "Cosmetics"}
    clip = {
        "confidence_level": "Low",
        "similarity_percentage": 58.0,
        "matched_brand": "Unknown",
        "catalog_category_mismatch": False,
        "discrimination_margin": 0.5
    }
    review = {"authenticity_analysis_status": "NOT_VALIDATED", "review_authenticity_score": None}
    img = {"width": 800, "height": 800, "image_validation": "valid"}

    res = predict_final_authenticity(ocr, clip, review, img)
    assert res["assessment_outcome"] in ("INSUFFICIENT_EVIDENCE", "NOT_ASSESSED")


# ---------------------------------------------------------------------------
# 7. Unavailable Marketplaces Not Ranked as Real Recommendations
# ---------------------------------------------------------------------------

def test_blocked_marketplaces_not_ranked():
    """Blocked or unavailable platforms are assigned rank 99 and excluded from recommendations."""
    blocked_listing = MarketplaceListing(
        platform="Amazon",
        product_name="Amazon Access Blocked",
        brand="CeraVe",
        product_type="Skin Care",
        source_status="blocked",
        match_status="Not a Match",
        match_confidence=0.0,
        listing_status="MARKETPLACE_BLOCKED",
        passed_match_threshold=False
    )
    scores = compare_marketplace_platforms([blocked_listing])
    assert len(scores) == 1
    assert scores[0].rank == 99
    assert scores[0].total_score == 0.0
    assert "Not ranked" in scores[0].recommendation_reason


# ---------------------------------------------------------------------------
# 8. Complete Image Upload to Analysis Workflow
# ---------------------------------------------------------------------------

def test_complete_image_upload_workflow_end_to_end():
    """Tests POST /api/analyze endpoint with simulated image bytes and direct product URL."""
    # Create valid synthetic image in memory
    img = Image.new("RGB", (640, 640), color=(220, 180, 200))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/api/analyze",
        files={"file": ("test_cosmetic_bottle.jpg", buf, "image/jpeg")},
        data={"product_url": "https://www.daraz.lk/products/test-moisturizer-i99887766.html"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "ocr_result" in data
    assert "clip_result" in data
    assert "review_result" in data
    assert "authenticity_result" in data
    assert "marketplace_listings" in data

    # Verify authenticity result contains explicit evidence outcome
    auth = data["authenticity_result"]
    assert "assessment_outcome" in auth
    assert auth["assessment_outcome"] in (
        "NOT_ASSESSED", "INSUFFICIENT_EVIDENCE", "INCONSISTENT_INFORMATION", "REQUIRES_MANUAL_VERIFICATION"
    )
    assert "verified_evidence" in auth
    assert "missing_information" in auth

    # Verify review result has suspicious review risk
    rev = data["review_result"]
    assert rev["authenticity_analysis_status"] == "NOT_VALIDATED"
    assert "suspicious_review_risk" in rev
