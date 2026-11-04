"""
Focused Automated Test Suite for Marketplace URL Validation,
Domain Alignment, Internal Placeholder Rejection, and Data Integrity.
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
    is_valid_listing_for_persistence
)
from app.schemas.marketplace import ProductIdentity, MarketplaceListing as MarketplaceListingSchema
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


def test_1_valid_amazon_url():
    """Test 1: Valid Amazon URL is accepted."""
    url = "https://www.amazon.com/dp/B0046VIZ9A"
    is_valid, reason = validate_marketplace_url(url, "Amazon")
    assert is_valid is True, f"Valid Amazon URL failed: {reason}"


def test_2_valid_daraz_url():
    """Test 2: Valid Daraz URL is accepted."""
    url = "https://www.daraz.lk/products/maybelline-fit-me-foundation-i100200300.html"
    is_valid, reason = validate_marketplace_url(url, "Daraz")
    assert is_valid is True, f"Valid Daraz URL failed: {reason}"


def test_3_valid_temu_url():
    """Test 3: Valid Temu URL is accepted."""
    url = "https://www.temu.com/goods-123456789.html"
    is_valid, reason = validate_marketplace_url(url, "Temu")
    assert is_valid is True, f"Valid Temu URL failed: {reason}"


def test_4_placeholder_url_rejected():
    """Test 4: Placeholder URL containing /item/ pattern is rejected."""
    url = "https://www.amazon.com/item/P001"
    is_valid, reason = validate_marketplace_url(url, "Amazon")
    assert is_valid is False
    assert "placeholder pattern" in reason.lower()


def test_5_wrong_marketplace_domain_rejected():
    """Test 5: URL with domain not matching the platform is rejected."""
    url = "https://www.ebay.com/itm/123456789"
    is_valid, reason = validate_marketplace_url(url, "Amazon")
    assert is_valid is False
    assert "does not match expected platform" in reason


def test_6_empty_url_rejected():
    """Test 6: Empty or missing URL is rejected."""
    is_valid1, reason1 = validate_marketplace_url(None, "Amazon")
    assert is_valid1 is False

    is_valid2, reason2 = validate_marketplace_url("", "Amazon")
    assert is_valid2 is False


def test_7_internal_product_id_url_rejected():
    """Test 7: URL containing internal catalog product ID (e.g. /item/P001 or PROD_) is rejected."""
    urls = [
        "https://www.amazon.com/item/P001",
        "https://www.daraz.lk/item/PROD_COL_LIP",
        "https://www.temu.com/item/P006"
    ]
    for url in urls:
        is_valid, reason = validate_marketplace_url(url)
        assert is_valid is False


def test_8_duplicate_listing_detection(db_session):
    """Test 8: Duplicate listing with same (marketplace_id, product_url) is idempotently updated."""
    identity = ProductIdentity(brand="Maybelline", product_name="Fit Me Foundation", product_type="Foundation_Base", category="Foundation_Base", product_id="P001")
    prod = get_or_create_product(db_session, identity)
    mkt = get_or_create_marketplace(db_session, "Amazon")

    schema1 = MarketplaceListingSchema(
        platform="Amazon",
        product_name="Maybelline Fit Me - Original",
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

    # Re-upsert listing with identical URL
    schema2 = MarketplaceListingSchema(
        platform="Amazon",
        product_name="Maybelline Fit Me - Updated Title",
        brand="Maybelline",
        product_type="Foundation_Base",
        price=8.49,
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
    assert listings[0].raw_title == "Maybelline Fit Me - Updated Title"
    assert listings[0].price == 8.49
