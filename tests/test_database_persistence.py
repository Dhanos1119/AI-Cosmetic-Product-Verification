"""
Unit Test Suite for Phase 1 Database Architecture, Persistence & Alembic Migrations
Tests 10 required database requirements in an isolated test database environment.
"""

import os
import sys
import tempfile
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from alembic.config import Config
from alembic import command

# Add root project path to sys.path
BASE_DIR = Path(__file__).parent.parent.resolve()
SITE_PACKAGES_DIR = BASE_DIR / "ai-service" / "venv" / "Lib" / "site-packages"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
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


def create_test_db_session(tmp_db_path):
    """Helper to initialize isolated SQLite test database and session maker."""
    test_db_url = f"sqlite:///{tmp_db_path}"
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, TestingSessionLocal


def test_1_database_connection():
    """Test 1: Database Connection"""
    print("[TEST 1] Testing Database Connection...")
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name
    engine = None
    try:
        engine, TestingSessionLocal = create_test_db_session(tmp_path)
        session = TestingSessionLocal()
        result = session.execute(text("SELECT 1")).scalar()
        assert result == 1, "Database connection test query failed"
        session.close()
        print("  PASS! Database connection established successfully.")
    finally:
        if engine:
            engine.dispose()
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def test_2_product_insertion_and_retrieval():
    """Test 2: Product Insertion and Retrieval"""
    print("[TEST 2] Testing Product Insertion and Retrieval...")
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name
    engine = None
    try:
        engine, TestingSessionLocal = create_test_db_session(tmp_path)
        session = TestingSessionLocal()

        prod = Product(
            product_id="P001",
            brand="Colourpop",
            product_name="Lippie Pencil",
            product_type="Lippie Pencil",
            category="Lip_Products",
            shade_or_variant="BFF / Warm Nude"
        )
        session.add(prod)
        session.commit()

        retrieved = session.query(Product).filter_by(product_id="P001").first()
        assert retrieved is not None, "Inserted product was not retrieved"
        assert retrieved.brand == "Colourpop"
        assert retrieved.product_name == "Lippie Pencil"
        assert retrieved.category == "Lip_Products"
        assert retrieved.shade_or_variant == "BFF / Warm Nude"
        session.close()
        print("  PASS! Product inserted and retrieved cleanly.")
    finally:
        if engine:
            engine.dispose()
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def test_3_marketplace_insertion_and_retrieval():
    """Test 3: Marketplace Insertion and Retrieval"""
    print("[TEST 3] Testing Marketplace Insertion and Retrieval...")
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name
    engine = None
    try:
        engine, TestingSessionLocal = create_test_db_session(tmp_path)
        session = TestingSessionLocal()

        mkt = Marketplace(
            platform_code="amazon",
            platform_name="Amazon",
            base_url="https://www.amazon.com",
            api_type="http_scraper",
            currency_code="USD"
        )
        session.add(mkt)
        session.commit()

        retrieved = session.query(Marketplace).filter_by(platform_code="amazon").first()
        assert retrieved is not None
        assert retrieved.platform_name == "Amazon"
        assert retrieved.base_url == "https://www.amazon.com"
        session.close()
        print("  PASS! Marketplace inserted and retrieved cleanly.")
    finally:
        if engine:
            engine.dispose()
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def test_4_seller_relationship():
    """Test 4: Seller Relationship"""
    print("[TEST 4] Testing Seller Relationship...")
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name
    engine = None
    try:
        engine, TestingSessionLocal = create_test_db_session(tmp_path)
        session = TestingSessionLocal()

        mkt = Marketplace(
            platform_code="daraz",
            platform_name="Daraz",
            base_url="https://www.daraz.lk",
            api_type="http_scraper"
        )
        session.add(mkt)
        session.commit()

        seller = Seller(
            marketplace_id=mkt.id,
            seller_name="Daraz Mall Official Store",
            is_official_store=True,
            seller_rating=4.9,
            verified_status="verified_official"
        )
        session.add(seller)
        session.commit()

        retrieved_mkt = session.query(Marketplace).filter_by(platform_code="daraz").first()
        assert len(retrieved_mkt.sellers) == 1
        assert retrieved_mkt.sellers[0].seller_name == "Daraz Mall Official Store"
        assert retrieved_mkt.sellers[0].is_official_store is True
        session.close()
        print("  PASS! Seller relationship navigation verified.")
    finally:
        if engine:
            engine.dispose()
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def test_5_marketplace_listing_relationship():
    """Test 5: Marketplace Listing Relationship"""
    print("[TEST 5] Testing Marketplace Listing Relationship...")
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name
    engine = None
    try:
        engine, TestingSessionLocal = create_test_db_session(tmp_path)
        session = TestingSessionLocal()

        prod = Product(
            product_id="P030",
            brand="Annabelle",
            product_name="Biggy Bronzer Haute Gold",
            product_type="Bronzer",
            category="Other_Makeup"
        )
        mkt = Marketplace(
            platform_code="temu",
            platform_name="Temu",
            base_url="https://www.temu.com",
            api_type="http_scraper"
        )
        session.add_all([prod, mkt])
        session.commit()

        seller = Seller(
            marketplace_id=mkt.id,
            seller_name="Temu Beauty Direct",
            is_official_store=False
        )
        session.add(seller)
        session.commit()

        listing = MarketplaceListing(
            product_id=prod.id,
            marketplace_id=mkt.id,
            seller_id=seller.id,
            raw_title="Annabelle Biggy Bronzer Haute Gold Compact",
            price=14.99,
            currency="USD",
            rating=4.8,
            review_count=150,
            product_url="https://www.temu.com/p/annabelle-bronzer-12345",
            source_status="available",
            match_status="Exact Product Match",
            match_confidence=96.5
        )
        session.add(listing)
        session.commit()

        retrieved_listing = session.query(MarketplaceListing).filter_by(raw_title="Annabelle Biggy Bronzer Haute Gold Compact").first()
        assert retrieved_listing is not None
        assert retrieved_listing.product.product_id == "P030"
        assert retrieved_listing.marketplace.platform_code == "temu"
        assert retrieved_listing.seller.seller_name == "Temu Beauty Direct"
        session.close()
        print("  PASS! Marketplace listing relationships verified across Product, Marketplace, and Seller.")
    finally:
        if engine:
            engine.dispose()
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def test_6_customer_review_relationship():
    """Test 6: Customer Review Relationship"""
    print("[TEST 6] Testing Customer Review Relationship...")
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name
    engine = None
    try:
        engine, TestingSessionLocal = create_test_db_session(tmp_path)
        session = TestingSessionLocal()

        prod = Product(product_id="P010", brand="Glossier", product_name="Stretch Concealer", product_type="Concealer", category="Foundation_Base")
        mkt = Marketplace(platform_code="amazon", platform_name="Amazon", base_url="https://www.amazon.com", api_type="http_scraper")
        session.add_all([prod, mkt])
        session.commit()

        listing = MarketplaceListing(
            product_id=prod.id,
            marketplace_id=mkt.id,
            raw_title="Glossier Stretch Concealer Medium",
            product_url="https://www.amazon.com/dp/B001234567"
        )
        session.add(listing)
        session.commit()

        rev1 = CustomerReview(listing_id=listing.id, author="Jane D.", rating=5.0, comment_text="Authentic texture, love it!", is_verified_purchase=True)
        rev2 = CustomerReview(listing_id=listing.id, author="Sarah M.", rating=4.0, comment_text="Good coverage.", is_verified_purchase=True)
        session.add_all([rev1, rev2])
        session.commit()

        retrieved_listing = session.query(MarketplaceListing).filter_by(id=listing.id).first()
        assert len(retrieved_listing.reviews) == 2
        authors = [r.author for r in retrieved_listing.reviews]
        assert "Jane D." in authors
        assert "Sarah M." in authors
        session.close()
        print("  PASS! Customer review relationship navigation verified.")
    finally:
        if engine:
            engine.dispose()
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def test_7_duplicate_listing_prevention():
    """Test 7: Duplicate Listing Prevention"""
    print("[TEST 7] Testing Duplicate Listing Prevention...")
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name
    engine = None
    try:
        engine, TestingSessionLocal = create_test_db_session(tmp_path)
        session = TestingSessionLocal()

        prod = Product(product_id="P005", brand="Marienatie", product_name="Lipstick", product_type="Lipstick", category="Lip_Products")
        mkt = Marketplace(platform_code="daraz", platform_name="Daraz", base_url="https://www.daraz.lk", api_type="http_scraper")
        session.add_all([prod, mkt])
        session.commit()

        listing1 = MarketplaceListing(
            product_id=prod.id,
            marketplace_id=mkt.id,
            raw_title="Marienatie Matte Lipstick Red",
            product_url="https://www.daraz.lk/products/marienatie-lipstick-1"
        )
        session.add(listing1)
        session.commit()

        listing2 = MarketplaceListing(
            product_id=prod.id,
            marketplace_id=mkt.id,
            raw_title="Marienatie Matte Lipstick Red Duplicate",
            product_url="https://www.daraz.lk/products/marienatie-lipstick-1"
        )
        session.add(listing2)

        caught = False
        try:
            session.commit()
        except IntegrityError:
            caught = True
            session.rollback()

        assert caught, "Duplicate listing failed to trigger UniqueConstraint IntegrityError"
        session.close()
        print("  PASS! Duplicate listing prevention triggered UniqueConstraint successfully.")
    finally:
        if engine:
            engine.dispose()
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def test_8_required_field_validation():
    """Test 8: Required Field Validation"""
    print("[TEST 8] Testing Required Field Validation...")
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name
    engine = None
    try:
        engine, TestingSessionLocal = create_test_db_session(tmp_path)
        session = TestingSessionLocal()

        invalid_prod = Product(
            product_id="P999",
            brand=None,
            product_name="No Brand Product",
            product_type="Lipstick",
            category="Lip_Products"
        )
        session.add(invalid_prod)

        caught = False
        try:
            session.commit()
        except IntegrityError:
            caught = True
            session.rollback()

        assert caught, "Missing required field failed to trigger IntegrityError"
        session.close()
        print("  PASS! Required field validation enforced non-nullable constraints.")
    finally:
        if engine:
            engine.dispose()
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def test_9_missing_optional_fields():
    """Test 9: Missing Optional Fields Handling"""
    print("[TEST 9] Testing Missing Optional Fields Handling...")
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name
    engine = None
    try:
        engine, TestingSessionLocal = create_test_db_session(tmp_path)
        session = TestingSessionLocal()

        prod = Product(product_id="P015", brand="Lotus Cosmetics USA", product_name="Mascara", product_type="Mascara", category="Eye_Products")
        mkt = Marketplace(platform_code="temu", platform_name="Temu", base_url="https://www.temu.com", api_type="http_scraper")
        session.add_all([prod, mkt])
        session.commit()

        listing = MarketplaceListing(
            product_id=prod.id,
            marketplace_id=mkt.id,
            seller_id=None,
            raw_title="Lotus Volumizing Mascara Black",
            product_url=None,
            status_explanation=None
        )
        session.add(listing)
        session.commit()

        retrieved = session.query(MarketplaceListing).filter_by(raw_title="Lotus Volumizing Mascara Black").first()
        assert retrieved is not None
        assert retrieved.seller_id is None
        assert retrieved.price == 0.0
        assert retrieved.currency == "USD"
        assert retrieved.rating == 0.0
        assert retrieved.match_status == "Not a Match"
        assert retrieved.source_status == "available"
        session.close()
        print("  PASS! Missing optional fields cleanly assigned default fallback values.")
    finally:
        if engine:
            engine.dispose()
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def test_10_migration_upgrade_and_downgrade():
    """Test 10: Alembic Migration Upgrade and Downgrade"""
    print("[TEST 10] Testing Alembic Migration Upgrade and Downgrade...")
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        alembic_cfg = Config(str(BASE_DIR / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(BASE_DIR / "database" / "alembic"))
        alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{tmp_path}")

        # Run Alembic Upgrade to HEAD
        command.upgrade(alembic_cfg, "head")

        # Verify tables created
        test_engine = create_engine(f"sqlite:///{tmp_path}")
        with test_engine.connect() as conn:
            tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';")).scalars().all()
            assert "products" in tables
            assert "marketplaces" in tables
            assert "marketplace_listings" in tables
        test_engine.dispose()

        # Run Alembic Downgrade to BASE
        command.downgrade(alembic_cfg, "base")

        # Verify tables removed
        test_engine2 = create_engine(f"sqlite:///{tmp_path}")
        with test_engine2.connect() as conn:
            tables_after = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';")).scalars().all()
            assert "products" not in tables_after
            assert "marketplace_listings" not in tables_after
        test_engine2.dispose()

        # Re-upgrade to HEAD to restore clean state
        command.upgrade(alembic_cfg, "head")
        print("  PASS! Alembic migration upgrade and downgrade executed reversibly.")
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def run_all_database_tests():
    print("=" * 80)
    print("RUNNING PHASE 1 DATABASE PERSISTENCE & MIGRATION TEST SUITE")
    print("=" * 80)
    test_1_database_connection()
    test_2_product_insertion_and_retrieval()
    test_3_marketplace_insertion_and_retrieval()
    test_4_seller_relationship()
    test_5_marketplace_listing_relationship()
    test_6_customer_review_relationship()
    test_7_duplicate_listing_prevention()
    test_8_required_field_validation()
    test_9_missing_optional_fields()
    test_10_migration_upgrade_and_downgrade()
    print("=" * 80)
    print("ALL 10 DATABASE TESTS PASSED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_database_tests()
