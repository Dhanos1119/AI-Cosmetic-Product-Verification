"""
Phase 2 Unit & Integration Test Suite for Marketplace Persistence, Transaction Rollback,
and API Integration Compatibility.
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
from database.models import (
    Product,
    Marketplace,
    Seller,
    MarketplaceListing,
    CustomerReview,
    ReviewAnalysis,
    MarketplaceEvidence,
)
from database.persistence_service import (
    get_or_create_product,
    get_or_create_marketplace,
    get_or_create_seller,
    upsert_marketplace_listing,
    save_customer_reviews,
    upsert_review_analysis,
    upsert_marketplace_evidence,
    persist_analysis_results,
)
from app.schemas.marketplace import (
    ProductIdentity,
    MarketplaceListing as MarketplaceListingSchema,
    MarketplaceReview,
    PlatformComparisonScore,
    ScoreBreakdown,
)
from app.services.product_service import analyze_product_authenticity


@pytest.fixture
def db_session():
    """Provides an isolated SQLite test database session for each test."""
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


def test_1_product_persistence(db_session):
    """Test 1: Product persistence via ProductIdentity schema."""
    identity = ProductIdentity(
        brand="Colourpop",
        product_name="Lippie Pencil",
        product_type="Lippie Pencil",
        category="Lip_Products",
        product_id="P001",
        shade_or_variant="BFF"
    )
    prod = get_or_create_product(db_session, identity)
    db_session.commit()

    assert prod.id is not None
    assert prod.product_id == "P001"
    assert prod.brand == "Colourpop"

    # Verify idempotency
    prod_again = get_or_create_product(db_session, identity)
    assert prod_again.id == prod.id


def test_2_marketplace_persistence(db_session):
    """Test 2: Marketplace platform persistence."""
    mkt = get_or_create_marketplace(db_session, "amazon")
    db_session.commit()

    assert mkt.platform_code == "amazon"
    assert mkt.platform_name == "Amazon"
    assert mkt.base_url == "https://www.amazon.com"

    # Verify idempotency
    mkt_again = get_or_create_marketplace(db_session, "amazon")
    assert mkt_again.id == mkt.id


def test_3_listing_persistence(db_session):
    """Test 3: Marketplace listing persistence and relationships."""
    identity = ProductIdentity(brand="Glossier", product_name="Stretch Concealer", product_type="Concealer", category="Base", product_id="P010")
    prod = get_or_create_product(db_session, identity)
    mkt = get_or_create_marketplace(db_session, "daraz")
    seller = get_or_create_seller(db_session, mkt.id, "Daraz Mall Official Store")

    listing_schema = MarketplaceListingSchema(
        platform="daraz",
        product_name="Glossier Stretch Concealer Shade G9",
        brand="Glossier",
        product_type="Concealer",
        price=22.0,
        currency="USD",
        rating=4.7,
        review_count=85,
        seller_name="Daraz Mall Official Store",
        product_url="https://www.daraz.lk/products/glossier-concealer-123",
        source_status="available",
        match_status="Exact Product Match",
        match_confidence=95.0
    )

    listing = upsert_marketplace_listing(db_session, prod, mkt, seller, listing_schema)
    db_session.commit()

    assert listing.id is not None
    assert listing.price == 22.0
    assert listing.seller.seller_name == "Daraz Mall Official Store"
    assert listing.product.brand == "Glossier"


def test_4_review_persistence(db_session):
    """Test 4: Customer review persistence and analysis binding."""
    identity = ProductIdentity(brand="Annabelle", product_name="Bronzer", product_type="Bronzer", category="Face", product_id="P030")
    prod = get_or_create_product(db_session, identity)
    mkt = get_or_create_marketplace(db_session, "temu")
    listing_schema = MarketplaceListingSchema(platform="temu", product_name="Annabelle Bronzer", brand="Annabelle", product_type="Bronzer", product_url="https://www.temu.com/goods-annabelle-bronzer.html")
    listing = upsert_marketplace_listing(db_session, prod, mkt, None, listing_schema)

    reviews = [
        MarketplaceReview(author="Alice", rating=5.0, comment="Great bronzer!", verified_purchase=True),
        MarketplaceReview(author="Bob", rating=4.0, comment="Nice shade.", verified_purchase=True),
    ]
    save_customer_reviews(db_session, listing, reviews)

    review_res = {
        "review_authenticity_score": 92.5,
        "sentiment_label": "Positive",
        "average_rating": 4.5,
        "verified_buyer_percentage": 100.0,
        "authenticity_status": "High Authenticity",
        "suspicious_review_flag": False,
        "summary": "Positive feedback with verified buyers."
    }
    upsert_review_analysis(db_session, listing, review_res)
    db_session.commit()

    retrieved_reviews = db_session.query(CustomerReview).filter_by(listing_id=listing.id).all()
    assert len(retrieved_reviews) == 2
    analysis = db_session.query(ReviewAnalysis).filter_by(listing_id=listing.id).first()
    assert analysis.review_authenticity_score == 92.5


def test_5_duplicate_listing_handling(db_session):
    """Test 5: Duplicate listing updating (upsert idempotency)."""
    identity = ProductIdentity(brand="Marienatie", product_name="Lipstick", product_type="Lipstick", category="Lip", product_id="P005")
    prod = get_or_create_product(db_session, identity)
    mkt = get_or_create_marketplace(db_session, "amazon")

    listing_schema1 = MarketplaceListingSchema(
        platform="amazon",
        product_name="Marienatie Lipstick Original",
        brand="Marienatie",
        product_type="Lipstick",
        price=12.99,
        product_url="https://www.amazon.com/dp/B000TEST123"
    )
    listing1 = upsert_marketplace_listing(db_session, prod, mkt, None, listing_schema1)
    db_session.commit()

    # Second call with updated price
    listing_schema2 = MarketplaceListingSchema(
        platform="amazon",
        product_name="Marienatie Lipstick Original Updated",
        brand="Marienatie",
        product_type="Lipstick",
        price=14.99,
        product_url="https://www.amazon.com/dp/B000TEST123"
    )
    listing2 = upsert_marketplace_listing(db_session, prod, mkt, None, listing_schema2)
    db_session.commit()

    assert listing1.id == listing2.id
    assert listing2.price == 14.99
    assert listing2.raw_title == "Marienatie Lipstick Original Updated"


def test_6_missing_optional_fields(db_session):
    """Test 6: Missing optional marketplace fields default assignment."""
    identity = ProductIdentity(brand="Lotus", product_name="Mascara", product_type="Mascara", category="Eye", product_id="P015")
    prod = get_or_create_product(db_session, identity)
    mkt = get_or_create_marketplace(db_session, "temu")

    minimal_schema = MarketplaceListingSchema(
        platform="temu",
        product_name="Lotus Mascara",
        brand="Lotus",
        product_type="Mascara",
        product_url="https://www.temu.com/goods-lotus-mascara.html"
    )
    listing = upsert_marketplace_listing(db_session, prod, mkt, None, minimal_schema)
    db_session.commit()

    assert listing.seller_id is None
    assert listing.price == 0.0
    assert listing.rating == 0.0
    assert listing.review_count == 0
    assert listing.source_status == "available"


def test_7_transaction_rollback(db_session):
    """Test 7: Transaction rollback on failure."""
    db_session.add(Product(product_id="VALID_P1", brand="ValidBrand", product_name="ValidProduct", product_type="Type", category="Cat"))
    db_session.commit()

    try:
        # Invalid insertion missing non-nullable brand
        db_session.add(Product(product_id="INVALID_P2", brand=None, product_name="NoBrand", product_type="Type", category="Cat"))
        db_session.commit()
    except Exception:
        db_session.rollback()

    valid_prod = db_session.query(Product).filter_by(product_id="VALID_P1").first()
    invalid_prod = db_session.query(Product).filter_by(product_id="INVALID_P2").first()
    assert valid_prod is not None
    assert invalid_prod is None


def test_8_blocked_unavailable_marketplace_handling(db_session):
    """Test 8: Persisting restricted or blocked marketplace listings."""
    identity = ProductIdentity(brand="Fenty", product_name="Gloss", product_type="Lip Gloss", category="Lip", product_id="P020")
    prod = get_or_create_product(db_session, identity)
    mkt = get_or_create_marketplace(db_session, "amazon")

    blocked_schema = MarketplaceListingSchema(
        platform="amazon",
        product_name="Fenty Gloss Bomb",
        brand="Fenty",
        product_type="Lip Gloss",
        product_url="https://www.amazon.com/dp/B000FENTY01",
        source_status="blocked",
        match_status="Not a Match",
        match_confidence=0.0,
        status_explanation="Marketplace access restricted by anti-bot controls."
    )
    listing = upsert_marketplace_listing(db_session, prod, mkt, None, blocked_schema)

    score_schema = PlatformComparisonScore(
        platform="amazon",
        total_score=0.0,
        rank=99,
        score_breakdown=ScoreBreakdown(review_trust_score=0.0, rating_score=0.0, seller_trust_score=0.0, match_confidence_score=0.0),
        recommendation_reason="Data unavailable: Marketplace access restricted",
        listing=blocked_schema
    )
    evidence = upsert_marketplace_evidence(db_session, listing, score_schema)
    db_session.commit()

    assert listing.source_status == "blocked"
    assert evidence.total_score == 0.0
    assert evidence.rank == 99


def test_9_api_response_compatibility():
    """Test 9: Existing API response schema compatibility."""
    dummy_bytes = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xFF\xDB\x00C\x00" + b"\x00" * 500
    res = analyze_product_authenticity(
        file_bytes=dummy_bytes,
        ocr_result={"status": "extracted", "brand_name": "Colourpop", "product_name": "Lippie Pencil", "category": "Lip_Products"},
        image_info={"filename": "test.jpg", "image_validation": "valid", "width": 500, "height": 500, "format": "JPEG", "size": 600}
    )

    assert "product_identity" in res
    assert "marketplace_listings" in res
    assert "platform_comparison" in res
    assert "clip_similarity" in res
    assert "review_authenticity" in res


def test_10_persistence_through_analysis_flow(db_session):
    """Test 10: Complete persistence through analyze_product_authenticity flow."""
    from unittest.mock import patch
    from app.schemas.marketplace import MarketplaceListing as MarketplaceListingSchema

    mock_listing = MarketplaceListingSchema(
        platform="Amazon",
        product_name="Colourpop Lippie Pencil - BFF",
        brand="Colourpop",
        product_type="Lip_Products",
        price=7.00,
        currency="USD",
        rating=4.8,
        review_count=120,
        seller_name="Colourpop Official",
        product_url="https://www.amazon.com/dp/B08XYZ1234",
        source_status="available",
        match_status="Exact Product Match",
        match_confidence=95.0,
        listing_status="VERIFIED_LISTING",
        passed_match_threshold=True
    )

    dummy_bytes = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xFF\xDB\x00C\x00" + b"\x00" * 500

    with patch("app.services.product_service.search_all_marketplaces", return_value=[mock_listing]):
        res = analyze_product_authenticity(
            file_bytes=dummy_bytes,
            ocr_result={"status": "extracted", "brand_name": "Colourpop", "product_name": "Lippie Pencil", "category": "Lip_Products", "confidence": 0.95},
            image_info={"filename": "test.jpg", "image_validation": "valid", "width": 500, "height": 500, "format": "JPEG", "size": 600},
            db=db_session
        )

    assert res.get("db_persisted") is True
    saved_prod = db_session.query(Product).filter(Product.brand == "Colourpop").first()
    assert saved_prod is not None
    listings = db_session.query(MarketplaceListing).filter_by(product_id=saved_prod.id).all()
    assert len(listings) >= 1
    assert listings[0].raw_title == "Colourpop Lippie Pencil - BFF"

