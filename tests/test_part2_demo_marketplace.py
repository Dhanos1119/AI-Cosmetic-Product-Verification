"""
Comprehensive Part 2 Test Suite: Demonstration Mode & Marketplace Integration
Tests all 10 required scenarios:
  1. 1.png – Foundation demo
  2. 2.png – Lipstick demo (unconfirmed identity without sufficient evidence; actual product when evidence exists)
  3. 3.png – Non-cosmetic rejection ("Non-cosmetic image detected.", no marketplace results)
  4. Unmapped cosmetic image (normal AI predictions, no forced demo identity)
  5. Amazon unavailable ("Live marketplace data unavailable.", working search link, no fake data)
  6. Daraz unavailable (UNAVAILABLE status when live fails and demo mode is disabled)
  7. Temu unavailable (UNAVAILABLE status when live fails and demo mode is disabled)
  8. Independent marketplace failures (one scraper failure never blocks the others)
  9. LIVE / DEMO / UNAVAILABLE labels & data source separation
  10. Responsive marketplace cards structure & metadata completeness
"""

import sys
import io
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image

BASE_DIR = Path(__file__).parent.parent.resolve()
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BASE_DIR / "ai-service") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "ai-service"))

from app.schemas.marketplace import ProductIdentity
from app.services.demo_service import (
    is_demo_mode_active,
    evaluate_demo_scenario,
    get_simulated_marketplace_listing,
    get_marketplace_timeout,
)
from app.services.scraping.marketplace_search import (
    search_all_marketplaces,
    generate_search_queries,
)
from app.services.scraping.schemas import RawMarketplaceItem
from app.services.product_service import analyze_product_authenticity


def _create_test_image_bytes(color=(210, 160, 130), size=(200, 200)) -> bytes:
    """Generates an in-memory valid RGB JPEG image."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# --------------------------------------------------------------------------
# Scenario 1: 1.png – Foundation Demo
# --------------------------------------------------------------------------
def test_scenario_1_foundation_demo():
    """Scenario 1: 1.png evaluates to Foundation demo identity when validated as cosmetic face makeup."""
    demo_eval = evaluate_demo_scenario(
        filename="1.png",
        detected_category="Foundation",
        is_cosmetic=True,
    )
    assert demo_eval is not None
    assert demo_eval["demo_key"] == "1.png"
    assert demo_eval["is_rejected"] is False
    assert demo_eval["category"] == "Foundation"
    assert demo_eval["brand"] == "Maybelline"
    assert demo_eval["product_name"] == "Maybelline Fit Me Matte + Poreless Foundation"
    assert demo_eval["is_confirmed"] is True
    assert demo_eval["identity_status"] == "Confirmed Product Identity"


def test_scenario_1_foundation_content_validation_rejects_unrelated_image():
    """Scenario 1: Content validation prevents forcing Maybelline identity onto non-cosmetic or unrelated image."""
    # When an image named 1.png is actually non-cosmetic
    demo_eval_non_cosmetic = evaluate_demo_scenario(
        filename="1.png",
        detected_category="Non-cosmetic / uncertain",
        is_cosmetic=False,
    )
    assert demo_eval_non_cosmetic is None, "Should not force foundation demo identity onto non-cosmetic object"


# --------------------------------------------------------------------------
# Scenario 2: 2.png – Lipstick Demo
# --------------------------------------------------------------------------
def test_scenario_2_lipstick_demo_unconfirmed_without_sufficient_evidence():
    """Scenario 2: 2.png shows category Lipstick and marks exact identity as unconfirmed without evidence."""
    demo_eval = evaluate_demo_scenario(
        filename="2.png",
        detected_category="Lipstick",
        is_cosmetic=True,
        ocr_brand=None,
        ocr_product=None,
        clip_result={"similarity_percentage": 68.0, "discrimination_margin": 0.05},
    )
    assert demo_eval is not None
    assert demo_eval["demo_key"] == "2.png"
    assert demo_eval["is_rejected"] is False
    assert demo_eval["category"] == "Lipstick"
    assert demo_eval["product_name"] == "Lipstick"
    assert demo_eval["is_confirmed"] is False
    assert demo_eval["identity_status"] == "Unconfirmed Product Identity"


def test_scenario_2_lipstick_demo_identifies_actual_product_with_evidence():
    """Scenario 2: 2.png identifies actual product when sufficient evidence exists (OCR brand/product)."""
    demo_eval = evaluate_demo_scenario(
        filename="2.png",
        detected_category="Lipstick",
        is_cosmetic=True,
        ocr_brand="MAC",
        ocr_product="Ruby Woo Matte Lipstick",
        clip_result={"matched_brand": "MAC", "matched_product_name": "Ruby Woo Matte Lipstick", "similarity_percentage": 88.0, "discrimination_margin": 0.20},
    )
    assert demo_eval is not None
    assert demo_eval["category"] == "Lipstick"
    assert demo_eval["brand"] == "MAC"
    assert demo_eval["product_name"] == "Ruby Woo Matte Lipstick"
    assert demo_eval["is_confirmed"] is True
    assert demo_eval["identity_status"] == "Confirmed Product Identity"


# --------------------------------------------------------------------------
# Scenario 3: 3.png – Non-Cosmetic Rejection
# --------------------------------------------------------------------------
def test_scenario_3_non_cosmetic_rejection():
    """Scenario 3: 3.png rejects non-cosmetic input with explicit message and no marketplace results."""
    demo_eval = evaluate_demo_scenario(
        filename="3.png",
        detected_category="Non-cosmetic / uncertain",
        is_cosmetic=False,
    )
    assert demo_eval is not None
    assert demo_eval["demo_key"] == "3.png"
    assert demo_eval["is_rejected"] is True
    assert demo_eval["rejection_message"] == "Non-cosmetic image detected."


def test_scenario_3_end_to_end_non_cosmetic_produces_no_marketplace_or_reviews():
    """Scenario 3: End-to-end analysis of 3.png produces empty marketplace listings, reviews, and recommendations."""
    img_bytes = _create_test_image_bytes()
    res = analyze_product_authenticity(
        file_bytes=img_bytes,
        ocr_result={"brand_name": "", "product_name": "", "raw_text": [], "confidence": 0.0},
        image_info={"filename": "3.png"},
    )
    assert res["status"] == "rejected_non_cosmetic"
    assert res["message"] == "Non-cosmetic image detected."
    assert res["marketplace_listings"] == []
    assert res["platform_comparison"] == []
    assert res["review_result"] is None


# --------------------------------------------------------------------------
# Scenario 4: Unmapped Cosmetic Image
# --------------------------------------------------------------------------
def test_scenario_4_unmapped_cosmetic_image():
    """Scenario 4: Normal cosmetic image without demo mapping does NOT trigger demonstration overrides."""
    demo_eval = evaluate_demo_scenario(
        filename="camera_capture_normal.jpg",
        detected_category="Foundation",
        is_cosmetic=True,
    )
    assert demo_eval is None, "Unmapped images should not match demo scenarios"


# --------------------------------------------------------------------------
# Scenario 5: Amazon Demo Configuration & Unavailable Handling
# --------------------------------------------------------------------------
def test_scenario_5_amazon_demo_configuration():
    """Scenario 5: Amazon returns configured DEMO price, rating and product link for demo, and UNAVAILABLE when demo is disabled."""
    ident = ProductIdentity(
        brand="Maybelline",
        product_name="Maybelline Fit Me Matte + Poreless Foundation",
        product_type="Liquid Foundation",
        category="Foundation",
    )
    with patch("app.services.scraping.marketplace_search.scrape_amazon_products", return_value=[]), \
         patch("app.services.scraping.marketplace_search.scrape_daraz_products", return_value=[]), \
         patch("app.services.scraping.marketplace_search.scrape_temu_products", return_value=[]):
        # In demo mode for 1.png: Amazon loads configured demonstration product info
        listings_demo = search_all_marketplaces(ident, demo_key="1.png")
        amazon_item = next((l for l in listings_demo if l.platform == "Amazon"), None)
        assert amazon_item is not None
        assert amazon_item.retrieval_status == "DEMO"
        assert amazon_item.price == 2988.10
        assert amazon_item.currency == "LKR"
        assert amazon_item.rating == 4.5
        assert amazon_item.product_url is not None
        assert "B00FF7MJ70" in amazon_item.product_url
        assert amazon_item.data_source in ("Demo / Reference Data", "Simulated Demo Catalog")

        # When demo mode is disabled (demo_key=None), Amazon returns Data Unavailable with search URL
        listings_unmapped = search_all_marketplaces(ident, demo_key=None)
        amazon_unavail = next((l for l in listings_unmapped if l.platform == "Amazon"), None)
        assert amazon_unavail is not None
        assert amazon_unavail.retrieval_status in ("Data Unavailable", "UNAVAILABLE")
        assert amazon_unavail.price == 0.0
        assert amazon_unavail.search_url is not None
        assert "amazon.com/s?k=" in amazon_unavail.search_url


# --------------------------------------------------------------------------
# Scenario 6 & 7: Daraz and Temu Unavailable
# --------------------------------------------------------------------------
def test_scenario_6_7_daraz_and_temu_unavailable_when_demo_disabled():
    """Scenarios 6 & 7: When live scraper returns no items, display Data Unavailable."""
    ident = ProductIdentity(
        brand="Rare Beauty",
        product_name="Soft Pinch Liquid Blush",
        product_type="Blush",
        category="Blush",
    )
    # Simulate scrapers returning empty results and demo_key is None
    with patch("app.services.scraping.marketplace_search.scrape_amazon_products", return_value=[]), \
         patch("app.services.scraping.marketplace_search.scrape_daraz_products", return_value=[]), \
         patch("app.services.scraping.marketplace_search.scrape_temu_products", return_value=[]):
        listings = search_all_marketplaces(ident, demo_key=None)

        daraz_item = next((l for l in listings if "daraz" in l.platform.lower()), None)
        temu_item = next((l for l in listings if "temu" in l.platform.lower()), None)

        assert daraz_item is not None
        assert daraz_item.retrieval_status in ("Data Unavailable", "UNAVAILABLE")
        assert daraz_item.price == 0.0
        assert "daraz.lk" in daraz_item.search_url

        assert temu_item is not None
        assert temu_item.retrieval_status in ("Data Unavailable", "UNAVAILABLE")
        assert temu_item.price == 0.0
        assert "temu.com" in temu_item.search_url


# --------------------------------------------------------------------------
# Scenario 8: Independent Marketplace Failures
# --------------------------------------------------------------------------
def test_scenario_8_independent_marketplace_failures():
    """Scenario 8: A failure in one marketplace scraper does not crash or block the other scrapers."""
    ident = ProductIdentity(
        brand="Fenty Beauty",
        product_name="Gloss Bomb Universal Lip Luminizer",
        product_type="Lip gloss",
        category="Lip gloss",
    )

    # Daraz raises an unhandled exception, Amazon returns empty, Temu succeeds with a live item
    mock_temu_item = RawMarketplaceItem(
        platform="Temu",
        raw_title="Fenty Beauty Gloss Bomb Universal Lip Luminizer Fenty Glow",
        price_val=22.0,
        currency="USD",
        rating_val=4.8,
        rating_count_val=150,
        seller="Fenty Authorized Direct",
        link="https://www.temu.com/goods.html?goods_id=999888",
        source_status="available"
    )

    with patch("app.services.scraping.marketplace_search.scrape_daraz_products", side_effect=RuntimeError("Daraz connection failed")), \
         patch("app.services.scraping.marketplace_search.scrape_temu_products", return_value=[mock_temu_item]), \
         patch("app.services.scraping.marketplace_search.scrape_amazon_products", return_value=[]):

        listings = search_all_marketplaces(ident, demo_key=None)

        assert len(listings) >= 3
        temu_res = next((l for l in listings if "temu" in l.platform.lower()), None)
        daraz_res = next((l for l in listings if "daraz" in l.platform.lower()), None)
        amazon_res = next((l for l in listings if "amazon" in l.platform.lower()), None)

        # Temu should have succeeded with Live Data
        assert temu_res is not None
        assert temu_res.retrieval_status in ("Live Data", "LIVE")
        assert temu_res.price == 22.0
        assert temu_res.data_source == "Live Scraper"

        # Daraz should have handled its error gracefully and reported Retrieval Failed / Data Unavailable
        assert daraz_res is not None
        assert daraz_res.retrieval_status in ("Retrieval Failed", "Data Unavailable", "UNAVAILABLE")

        # Amazon should be Data Unavailable
        assert amazon_res is not None
        assert amazon_res.retrieval_status in ("Data Unavailable", "UNAVAILABLE")


# --------------------------------------------------------------------------
# Scenario 9: 1.png Accuracy & Production Statuses
# --------------------------------------------------------------------------
def test_scenario_9_live_demo_unavailable_labels():
    """Scenario 9: Validates Amazon & Daraz DEMO data, and strictly checks that Temu returns UNAVAILABLE due to CAPTCHA."""
    ident = ProductIdentity(
        brand="Maybelline",
        product_name="Maybelline Fit Me Matte + Poreless Foundation",
        product_type="Liquid Foundation",
        category="Foundation",
    )

    with patch("app.services.scraping.marketplace_search.scrape_amazon_products", return_value=[]), \
         patch("app.services.scraping.marketplace_search.scrape_daraz_products", return_value=[]), \
         patch("app.services.scraping.marketplace_search.scrape_temu_products", return_value=[]):
        listings = search_all_marketplaces(ident, demo_key="1.png")

        amazon_res = next((l for l in listings if l.platform == "Amazon"), None)
        daraz_res = next((l for l in listings if "daraz" in l.platform.lower()), None)
        temu_res = next((l for l in listings if "temu" in l.platform.lower()), None)

        # Amazon returns configured DEMO data
        assert amazon_res.retrieval_status == "DEMO"
        assert amazon_res.price == 2988.10
        assert amazon_res.currency == "LKR"
        assert amazon_res.rating == 4.5
        assert amazon_res.data_source in ("Demo / Reference Data", "Simulated Demo Catalog")

        # Daraz returns configured DEMO data
        assert daraz_res.retrieval_status == "DEMO"
        assert daraz_res.price == 3990.00
        assert daraz_res.currency == "LKR"
        assert daraz_res.rating == 5.0
        assert daraz_res.review_count == 1
        assert daraz_res.data_source in ("Demo / Reference Data", "Simulated Demo Catalog")

        # Temu strictly returns UNAVAILABLE due to CAPTCHA limitation (never fake listing)
        assert temu_res.retrieval_status in ("Data Unavailable", "UNAVAILABLE")
        assert temu_res.retrieval_status != "DEMO"
        assert temu_res.price == 0.0
        assert temu_res.rating == 0.0
        assert temu_res.data_source == "Direct Search"


# --------------------------------------------------------------------------
# Scenario 10: Responsive Marketplace Cards Data Integrity
# --------------------------------------------------------------------------
def test_scenario_10_marketplace_cards_data_integrity():
    """Scenario 10: Validates completeness of all metadata fields needed for responsive UI cards."""
    ident = ProductIdentity(
        brand="Maybelline",
        product_name="Maybelline Fit Me Matte + Poreless Foundation",
        product_type="Liquid Foundation",
        category="Foundation",
    )
    with patch("app.services.scraping.marketplace_search.scrape_amazon_products", return_value=[]), \
         patch("app.services.scraping.marketplace_search.scrape_daraz_products", return_value=[]), \
         patch("app.services.scraping.marketplace_search.scrape_temu_products", return_value=[]):
        listings = search_all_marketplaces(ident, demo_key="1.png")

        for listing in listings:
            # Every card must have platform, product_name, retrieval_status, and search_url
            assert listing.platform in ("Amazon", "Daraz LK", "Temu")
            assert listing.product_name
            assert listing.retrieval_status in ("Live Data", "Data Unavailable", "Retrieval Failed", "LIVE", "DEMO", "UNAVAILABLE")
            assert listing.search_url and listing.search_url.startswith("http")
            assert listing.retrieval_timestamp is not None
            assert listing.data_source in ("Live Scraper", "Direct Search", "Demo / Reference Data", "Simulated Demo Catalog")


if __name__ == "__main__":
    print("Running Part 2 automated tests...")
    test_scenario_1_foundation_demo()
    test_scenario_1_foundation_content_validation_rejects_unrelated_image()
    test_scenario_2_lipstick_demo_unconfirmed_without_sufficient_evidence()
    test_scenario_2_lipstick_demo_identifies_actual_product_with_evidence()
    test_scenario_3_non_cosmetic_rejection()
    test_scenario_3_end_to_end_non_cosmetic_produces_no_marketplace_or_reviews()
    test_scenario_4_unmapped_cosmetic_image()
    test_scenario_5_amazon_demo_configuration()
    test_scenario_6_7_daraz_and_temu_unavailable_when_demo_disabled()
    test_scenario_8_independent_marketplace_failures()
    test_scenario_9_live_demo_unavailable_labels()
    test_scenario_10_marketplace_cards_data_integrity()
    print("ALL 10 SCENARIOS PASSED SUCCESSFULLY!")
    test_scenario_8_independent_marketplace_failures()
    test_scenario_9_live_demo_unavailable_labels()
    test_scenario_10_marketplace_cards_data_integrity()
    print("ALL 10 SCENARIOS PASSED SUCCESSFULLY!")

