"""
Phase 6 Automated Test Suite for Marketplace Product Matching,
Evidence Quality, Brand Mismatch Penalty, Operational Status Isolation, and URL Safety.
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path
from sqlalchemy import create_engine
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
from database.models import Product, Marketplace, MarketplaceListing
from database.persistence_service import (
    get_or_create_product,
    get_or_create_marketplace,
    upsert_marketplace_listing,
    is_valid_listing_for_persistence,
    persist_analysis_results
)
from app.schemas.marketplace import ProductIdentity, MarketplaceListing as MarketplaceListingSchema
from app.services.scraping.product_matcher import match_product
from app.services.scraping.url_validator import validate_marketplace_url


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


def test_1_exact_product_match():
    """Test 1: Exact product match alignment."""
    identity = ProductIdentity(
        brand="Maybelline",
        product_name="Fit Me Matte + Poreless",
        product_type="Foundation_Base",
        category="Foundation_Base",
        product_id="P001"
    )
    title = "Maybelline Fit Me Matte + Poreless Liquid Foundation - 120 Classic Ivory"
    status, conf = match_product(title, identity)

    assert status == "Exact Product Match"
    assert conf >= 80.0


def test_2_partial_product_name_match():
    """Test 2: Partial product-name match alignment."""
    identity = ProductIdentity(
        brand="Maybelline",
        product_name="Fit Me Matte + Poreless Liquid Foundation",
        product_type="Foundation_Base",
        category="Foundation_Base",
        product_id="P001"
    )
    title = "Maybelline Fit Me Matte Foundation"
    status, conf = match_product(title, identity)

    assert status in ["Possible Match", "Exact Product Match"]
    assert conf >= 50.0


def test_3_unrelated_product_rejection():
    """Test 3: Unrelated non-cosmetic product rejection."""
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
        "USB C Charging Cable 6ft Fast Charger",
        "Wireless RGB Gaming Mouse"
    ]
    for title in unrelated_titles:
        status, conf = match_product(title, identity)
        assert status == "Not a Match"
        assert conf == 0.0

        schema = MarketplaceListingSchema(
            platform="Amazon",
            product_name=title,
            brand="Maybelline",
            product_type="Foundation_Base",
            product_url="https://www.amazon.com/dp/B000TEST111",
            source_status="available",
            match_status=status,
            match_confidence=conf
        )
        assert is_valid_listing_for_persistence(schema) is False


def test_4_brand_mismatch_rejection():
    """Test 4: Brand mismatch rejection."""
    identity = ProductIdentity(
        brand="Maybelline",
        product_name="Fit Me Foundation",
        product_type="Foundation_Base",
        category="Foundation_Base",
        product_id="P001"
    )
    title = "L'Oreal Paris Infallible 24H Fresh Wear Foundation"
    status, conf = match_product(title, identity)

    assert status == "Not a Match"
    assert conf <= 40.0, f"Confidence for brand mismatch should be <= 40.0, got {conf}"


def test_5_missing_product_url_rejection():
    """Test 5: Missing product URL listing is rejected from persistence."""
    schema = MarketplaceListingSchema(
        platform="Amazon",
        product_name="Maybelline Fit Me Foundation",
        brand="Maybelline",
        product_type="Foundation_Base",
        product_url=None,  # Missing URL
        source_status="available",
        match_status="Exact Product Match",
        match_confidence=90.0
    )
    assert is_valid_listing_for_persistence(schema) is False


def test_6_invalid_url_rejection():
    """Test 6: Invalid domain or placeholder URL listing is rejected."""
    placeholder_schema = MarketplaceListingSchema(
        platform="Amazon",
        product_name="Maybelline Fit Me Foundation",
        brand="Maybelline",
        product_type="Foundation_Base",
        product_url="https://www.amazon.com/item/P001",  # Placeholder URL
        source_status="available",
        match_status="Exact Product Match",
        match_confidence=90.0
    )
    assert is_valid_listing_for_persistence(placeholder_schema) is False

    wrong_domain_schema = MarketplaceListingSchema(
        platform="Amazon",
        product_name="Maybelline Fit Me Foundation",
        brand="Maybelline",
        product_type="Foundation_Base",
        product_url="https://www.ebay.com/itm/123456",  # Mismatched domain
        source_status="available",
        match_status="Exact Product Match",
        match_confidence=90.0
    )
    assert is_valid_listing_for_persistence(wrong_domain_schema) is False


def test_7_marketplace_unavailable_response_not_persisted(db_session):
    """Test 7: Marketplace blocked or unavailable response is not saved as a genuine listing."""
    result_data = {
        "product_identity": {
            "brand": "Maybelline",
            "product_name": "Fit Me",
            "product_type": "Foundation_Base",
            "category": "Foundation_Base",
            "product_id": "P001"
        },
        "platform_comparison": [
            {
                "platform": "Temu",
                "total_score": 0.0,
                "rank": 99,
                "score_breakdown": {"review_trust_score": 0.0, "rating_score": 0.0, "seller_trust_score": 0.0, "match_confidence_score": 0.0},
                "recommendation_reason": "Data unavailable: Anti-bot active",
                "listing": {
                    "platform": "Temu",
                    "product_name": "Temu Protection Active",
                    "brand": "Maybelline",
                    "product_type": "Foundation_Base",
                    "price": 0.0,
                    "currency": "USD",
                    "rating": 0.0,
                    "review_count": 0,
                    "source_status": "blocked",
                    "match_status": "Not a Match",
                    "match_confidence": 0.0,
                    "listing_status": "MARKETPLACE_BLOCKED"
                }
            }
        ]
    }
    res = persist_analysis_results(db_session, result_data)
    assert res.get("db_persisted") is True
    assert db_session.query(MarketplaceListing).count() == 0


def test_8_duplicate_listing_handling(db_session):
    """Test 8: Idempotent upsert updates existing row without creating duplicate listings."""
    identity = ProductIdentity(brand="Maybelline", product_name="Fit Me Foundation", product_type="Foundation_Base", category="Foundation_Base", product_id="P001")
    prod = get_or_create_product(db_session, identity)
    mkt = get_or_create_marketplace(db_session, "Amazon")

    schema1 = MarketplaceListingSchema(
        platform="Amazon",
        product_name="Maybelline Fit Me - Run 1",
        brand="Maybelline",
        product_type="Foundation_Base",
        price=7.99,
        product_url="https://www.amazon.com/dp/B0046VIZ9A",
        source_status="available",
        match_status="Exact Product Match",
        match_confidence=90.0,
        listing_status="VERIFIED_LISTING",
        passed_match_threshold=True
    )
    upsert_marketplace_listing(db_session, prod, mkt, None, schema1)
    db_session.commit()

    assert db_session.query(MarketplaceListing).count() == 1

    schema2 = MarketplaceListingSchema(
        platform="Amazon",
        product_name="Maybelline Fit Me - Run 2",
        brand="Maybelline",
        product_type="Foundation_Base",
        price=8.99,
        product_url="https://www.amazon.com/dp/B0046VIZ9A",
        source_status="available",
        match_status="Exact Product Match",
        match_confidence=92.0,
        listing_status="VERIFIED_LISTING",
        passed_match_threshold=True
    )
    upsert_marketplace_listing(db_session, prod, mkt, None, schema2)
    db_session.commit()

    listings = db_session.query(MarketplaceListing).all()
    assert len(listings) == 1
    assert listings[0].raw_title == "Maybelline Fit Me - Run 2"
    assert listings[0].price == 8.99
