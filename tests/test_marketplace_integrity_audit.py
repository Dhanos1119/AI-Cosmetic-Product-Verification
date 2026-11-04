"""
Focused Test Suite for Marketplace Data Integrity, Unrelated Product Rejection,
Placeholder Persistence Prevention, and Schema Correctness.
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

BASE_DIR = Path(__file__).parent.parent.resolve()
SITE_PACKAGES_DIR = BASE_DIR / "ai-service" / "venv" / "Lib" / "site-packages"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BASE_DIR / "ai-service") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "ai-service"))
if SITE_PACKAGES_DIR.exists() and str(SITE_PACKAGES_DIR) not in sys.path:
    sys.path.insert(0, str(SITE_PACKAGES_DIR))

from database.connection import Base
from database.models import Product, Marketplace, MarketplaceListing, MarketplaceEvidence
from database.persistence_service import (
    get_or_create_product,
    get_or_create_marketplace,
    persist_analysis_results,
    is_valid_listing_for_persistence
)
from app.schemas.marketplace import (
    ProductIdentity,
    MarketplaceListing as MarketplaceListingSchema,
    PlatformComparisonScore,
    ScoreBreakdown
)
from app.services.scraping.product_matcher import match_product
from app.services.scraping.marketplace_search import generate_search_queries


@pytest.fixture
def db_session():
    """Provides an isolated test database session for each test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name

    test_db_url = f"sqlite:///{tmp_path}"
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    yield session

    session.close()
    engine.dispose()
    if os.path.exists(tmp_path):
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def test_1_valid_cosmetic_listing_persisted(db_session):
    """Test 1: Valid cosmetic marketplace listing is persisted."""
    identity_dict = {
        "brand": "Colourpop",
        "product_name": "Lippie Pencil",
        "product_type": "Lip_Products",
        "category": "Lip_Products",
        "product_id": "P001"
    }

    valid_listing = {
        "platform": "Amazon",
        "product_name": "Colourpop Lippie Pencil - BFF / Warm Nude",
        "brand": "Colourpop",
        "product_type": "Lip_Products",
        "price": 7.00,
        "currency": "USD",
        "rating": 4.8,
        "review_count": 210,
        "seller_name": "Colourpop Official Store",
        "product_url": "https://www.amazon.com/dp/B08XYZ9999",
        "source_status": "available",
        "match_status": "Exact Product Match",
        "match_confidence": 95.0
    }

    result_data = {
        "product_identity": identity_dict,
        "platform_comparison": [
            {
                "platform": "Amazon",
                "total_score": 92.0,
                "rank": 1,
                "score_breakdown": {"review_trust_score": 95.0, "rating_score": 96.0, "seller_trust_score": 95.0, "match_confidence_score": 95.0},
                "recommendation_reason": "Strong evidence",
                "listing": valid_listing
            }
        ]
    }

    res = persist_analysis_results(db_session, result_data)
    assert res.get("db_persisted") is True

    persisted = db_session.query(MarketplaceListing).all()
    assert len(persisted) == 1
    assert persisted[0].raw_title == "Colourpop Lippie Pencil - BFF / Warm Nude"
    assert persisted[0].match_status == "Exact Product Match"


def test_2_unrelated_listing_rejection():
    """Test 2: Unrelated non-cosmetic listing rejection."""
    identity = ProductIdentity(
        brand="Maybelline",
        product_name="Fit Me Foundation",
        product_type="Foundation_Base",
        category="Foundation_Base",
        product_id="P001"
    )

    unrelated_titles = [
        "Bluetooth Headset, Single-Ear Wireless Earpiece",
        "Men's Casual Cotton T-Shirt",
        "USB C Charging Cable 6ft Fast Charging",
        "Wireless Gaming Mouse RGB Light"
    ]

    for title in unrelated_titles:
        match_status, conf = match_product(title, identity)
        assert match_status == "Not a Match", f"Title '{title}' should be rejected"
        assert conf == 0.0, f"Confidence for '{title}' should be 0.0"

        schema = MarketplaceListingSchema(
            platform="Amazon",
            product_name=title,
            brand="Maybelline",
            product_type="Foundation_Base",
            source_status="available",
            match_status=match_status,
            match_confidence=conf
        )
        assert is_valid_listing_for_persistence(schema) is False


def test_3_empty_search_result_not_persisted(db_session):
    """Test 3: Empty search result ('No matching listings') is not persisted as a fake listing."""
    schema = MarketplaceListingSchema(
        platform="Amazon",
        product_name="No matching listings found",
        brand="Maybelline",
        product_type="Foundation_Base",
        price=0.0,
        currency="USD",
        rating=0.0,
        review_count=0,
        source_status="unavailable",
        match_status="Not a Match",
        match_confidence=0.0
    )
    assert is_valid_listing_for_persistence(schema) is False


def test_4_marketplace_blocked_status_not_persisted(db_session):
    """Test 4: Marketplace blocked status ('Temu Protection Active') is not stored as a product listing."""
    schema = MarketplaceListingSchema(
        platform="Temu",
        product_name="Temu Protection Active",
        brand="Maybelline",
        product_type="Foundation_Base",
        price=0.0,
        currency="USD",
        rating=0.0,
        review_count=0,
        source_status="blocked",
        match_status="Not a Match",
        match_confidence=0.0
    )
    assert is_valid_listing_for_persistence(schema) is False


def test_5_invalid_or_missing_url_handled_safely(db_session):
    """Test 5: Invalid or missing listing URL is safely rejected without creating fake marketplace URLs."""
    identity = ProductIdentity(brand="Colourpop", product_name="Lippie Pencil", product_type="Lip_Products", category="Lip_Products")
    prod = get_or_create_product(db_session, identity)
    mkt = get_or_create_marketplace(db_session, "Amazon")

    schema = MarketplaceListingSchema(
        platform="Amazon",
        product_name="Colourpop Lippie Pencil - BFF",
        brand="Colourpop",
        product_type="Lip_Products",
        price=6.00,
        currency="USD",
        product_url=None,  # Missing URL
        source_status="available",
        match_status="Exact Product Match",
        match_confidence=85.0
    )

    # 1. Gatekeeper must reject missing URL
    assert is_valid_listing_for_persistence(schema) is False

    # 2. Direct upsert attempt must raise ValueError instead of generating fake URL
    from database.persistence_service import upsert_marketplace_listing
    with pytest.raises(ValueError) as exc_info:
        upsert_marketplace_listing(db_session, prod, mkt, None, schema)
    assert "invalid product URL" in str(exc_info.value)


def test_6_brand_name_mismatch_detected():
    """Test 6: Product brand/name mismatch is detected."""
    identity = ProductIdentity(brand="Maybelline", product_name="Fit Me Foundation", product_type="Foundation_Base", category="Foundation_Base")
    match_status, conf = match_product("L'Oreal Paris Infallible Foundation", identity)

    assert match_status in ["Not a Match", "Possible Match"]
    assert conf < 80.0, "Mismatching brand must not receive Exact Product Match"


def test_7_no_fabricated_data_inserted(db_session):
    """Test 7: No fabricated price, rating, seller, or review data is inserted for unavailable platforms."""
    result_data = {
        "product_identity": {
            "brand": "Unidentified Brand",
            "product_name": "Unidentified Product",
            "product_type": "Cosmetic Product",
            "category": "Cosmetic Product",
            "product_id": None
        },
        "platform_comparison": [
            {
                "platform": "Daraz",
                "total_score": 0.0,
                "rank": 99,
                "score_breakdown": {"review_trust_score": 0.0, "rating_score": 0.0, "seller_trust_score": 0.0, "match_confidence_score": 0.0},
                "recommendation_reason": "Data unavailable",
                "listing": {
                    "platform": "Daraz",
                    "product_name": "No Daraz listings returned",
                    "brand": "Unidentified Brand",
                    "product_type": "Cosmetic Product",
                    "price": 0.0,
                    "currency": "USD",
                    "rating": 0.0,
                    "review_count": 0,
                    "source_status": "unavailable",
                    "match_status": "Not a Match",
                    "match_confidence": 0.0
                }
            }
        ]
    }

    res = persist_analysis_results(db_session, result_data)
    assert res.get("db_persisted") is True
    assert db_session.query(MarketplaceListing).count() == 0, "No placeholder listings should be saved in DB"


def test_8_duplicate_listing_prevention(db_session):
    """Test 8: Repeated upload does not create uncontrolled duplicate listings."""
    identity_dict = {
        "brand": "Maybelline",
        "product_name": "Fit Me Matte + Poreless",
        "product_type": "Foundation_Base",
        "category": "Foundation_Base",
        "product_id": "P001"
    }

    valid_listing = {
        "platform": "Amazon",
        "product_name": "Maybelline Fit Me Matte + Poreless Pressed Face Powder",
        "brand": "Maybelline",
        "product_type": "Foundation_Base",
        "price": 7.99,
        "currency": "USD",
        "rating": 4.6,
        "review_count": 150,
        "seller_name": "Amazon Verified Seller",
        "product_url": "https://www.amazon.com/dp/B0046VIZ9A",
        "source_status": "available",
        "match_status": "Exact Product Match",
        "match_confidence": 85.0
    }

    result_data = {
        "product_identity": identity_dict,
        "platform_comparison": [
            {
                "platform": "Amazon",
                "total_score": 88.5,
                "rank": 1,
                "score_breakdown": {"review_trust_score": 95.0, "rating_score": 92.0, "seller_trust_score": 95.0, "match_confidence_score": 85.0},
                "recommendation_reason": "Strong evidence",
                "listing": valid_listing
            }
        ]
    }

    persist_analysis_results(db_session, result_data)
    assert db_session.query(MarketplaceListing).count() == 1

    persist_analysis_results(db_session, result_data)
    assert db_session.query(MarketplaceListing).count() == 1, "Repeated runs must update cleanly without duplicate rows"


def test_9_existing_valid_records_preserved(db_session):
    """Test 9: Existing valid records are not deleted during persistence."""
    identity = ProductIdentity(brand="Colourpop", product_name="Lippie Pencil", product_type="Lip_Products", category="Lip_Products", product_id="P001")
    prod = get_or_create_product(db_session, identity)
    mkt = get_or_create_marketplace(db_session, "Amazon")

    from database.persistence_service import upsert_marketplace_listing
    schema1 = MarketplaceListingSchema(platform="Amazon", product_name="Listing 1", brand="Colourpop", product_type="Lip_Products", price=5.0, product_url="https://www.amazon.com/dp/111", source_status="available", match_status="Exact Product Match", match_confidence=90.0)
    upsert_marketplace_listing(db_session, prod, mkt, None, schema1)
    db_session.commit()

    assert db_session.query(MarketplaceListing).count() == 1

    # Persist another valid listing for different URL
    schema2 = MarketplaceListingSchema(platform="Amazon", product_name="Listing 2", brand="Colourpop", product_type="Lip_Products", price=6.0, product_url="https://www.amazon.com/dp/222", source_status="available", match_status="Exact Product Match", match_confidence=90.0)
    upsert_marketplace_listing(db_session, prod, mkt, None, schema2)
    db_session.commit()

    assert db_session.query(MarketplaceListing).count() == 2, "Existing valid listing must be preserved"


def test_10_api_response_distinguishes_actual_listings_from_statuses():
    """Test 10: API response clearly distinguishes actual listings from unavailable/no-result statuses."""
    from app.services.marketplace_comparison_service import calculate_platform_score

    available_listing = MarketplaceListingSchema(
        platform="Amazon", product_name="Maybelline Fit Me Powder", brand="Maybelline", product_type="Foundation_Base", price=7.99, rating=4.6, review_count=100, source_status="available", match_status="Exact Product Match", match_confidence=85.0, listing_status="VERIFIED_LISTING", passed_match_threshold=True
    )
    blocked_listing = MarketplaceListingSchema(
        platform="Temu", product_name="Temu Protection Active", brand="Maybelline", product_type="Foundation_Base", price=0.0, rating=0.0, review_count=0, source_status="blocked", match_status="Not a Match", match_confidence=0.0, status_explanation="Anti-bot verification required"
    )

    score_avail = calculate_platform_score(available_listing)
    score_blocked = calculate_platform_score(blocked_listing)

    assert score_avail.total_score > 0.0
    assert score_avail.listing.source_status == "available"

    assert score_blocked.total_score == 0.0
    assert score_blocked.listing.source_status == "blocked"
    assert "Data unavailable" in score_blocked.recommendation_reason
