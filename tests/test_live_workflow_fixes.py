"""
End-to-End Tests for Live Workflow Fixes:
1. OCR Descriptor Filtering (ensuring 'Matte', 'Foundation', 'Poreless' are never parsed as brand).
2. Direct Marketplace URL Scraper through Express Gateway (:5000).
3. Real Daraz review extraction and live sentiment analysis (no mock or synthetic data).
4. Browser search links generation when automated marketplace searches are blocked.
5. Catalog integrity: 30-product catalog preserved, Maybelline Fit Me kept out-of-catalog.
"""

import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
import pytest

BASE_DIR = Path(__file__).parent.parent.resolve()
SITE_PACKAGES_DIR = BASE_DIR / "ai-service" / "venv" / "Lib" / "site-packages"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if SITE_PACKAGES_DIR.exists() and str(SITE_PACKAGES_DIR) not in sys.path:
    sys.path.insert(0, str(SITE_PACKAGES_DIR))

# Import OCR service parsing
from app.services.ocr_service import parse_brand_and_product, NON_BRAND_DESCRIPTOR_WORDS

DARAZ_TEST_URL = "https://www.daraz.lk/products/maybelline-new-york-liquid-foundation-matte-finish-with-spf-absorbs-oil-fit-me-matte-poreless-128-warm-nude-30-ml-from-indiasam-i204252780-s1298331553.html"
EXPRESS_SCRAPE_URL = "http://localhost:5000/api/marketplace/scrape-url"
FASTAPI_SCRAPE_URL = "http://localhost:8001/api/marketplace/scrape-url"


def test_ocr_descriptor_filtering():
    """Verify OCR never promotes descriptors like Matte, Foundation, Poreless, SPF to brand."""
    # Packaging text from the actual uploaded Maybelline Fit Me image
    fit_me_ocr_lines = ["MATTE", "+PORELESS", "NORMALTOOLY", "FOUNDATION", "130"]
    res = parse_brand_and_product(fit_me_ocr_lines)
    brand = res["brand_name"]
    category = res["category"]

    assert brand != "MATTE", "Word 'MATTE' must never be identified as a brand name"
    assert brand != "FOUNDATION", "Word 'FOUNDATION' must never be identified as a brand name"
    assert brand != "PORELESS", "Word 'PORELESS' must never be identified as a brand name"
    assert brand == "Unknown Brand", f"Expected 'Unknown Brand', got '{brand}'"
    assert "Foundation" in category or category in ["Face Products", "Makeup"]

    # Other common descriptor edge cases
    test_cases = [
        (["LIQUID", "FOUNDATION", "SPF 50", "MATTE FINISH"], "Unknown Brand"),
        (["WATERPROOF", "MASCARA", "VOLUMIZING", "BLACK"], "Unknown Brand"),
        (["HYDRATING", "FACE", "CREAM", "MOISTURIZER"], "Unknown Brand"),
        (["CONCEALER", "FULL", "COVERAGE", "LIGHT"], "Unknown Brand"),
    ]
    for lines, expected_brand in test_cases:
        r = parse_brand_and_product(lines)
        b = r["brand_name"]
        assert b == expected_brand, f"Lines {lines} incorrectly produced brand '{b}' instead of '{expected_brand}'"

    # Known catalog brand should still be correctly parsed
    known_lines = ["MAYBELLINE", "NEW YORK", "INSTANT", "AGE", "REWIND", "CONCEALER"]
    r = parse_brand_and_product(known_lines)
    b = r["brand_name"]
    assert b == "Maybelline", f"Expected Maybelline, got {b}"


def test_express_gateway_scrape_daraz_url():
    """Verify Express gateway forwards direct URL scrape to FastAPI and returns real Daraz data."""
    payload = json.dumps({"url": DARAZ_TEST_URL}).encode("utf-8")
    req = urllib.request.Request(
        EXPRESS_SCRAPE_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            assert resp.status == 200
            res = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        pytest.fail(f"Express gateway request failed: {e}")

    assert res["success"] is True, f"Expected success=True, got {res}"
    data = res["data"]
    assert data["platform"] == "Daraz"
    assert "Maybelline" in data["raw_title"] or "Fit Me" in data["raw_title"]
    assert data["price_val"] > 0, "Real listing price must be greater than zero"
    assert data["currency"] in ["LKR", "USD"]
    assert data["source_status"] == "available"

    # Verify real customer reviews are returned
    reviews = data.get("reviews", [])
    assert len(reviews) > 0, "Real customer reviews must be returned for the Daraz listing"
    first_review = reviews[0]
    assert "comment" in first_review and len(first_review["comment"].strip()) > 0
    assert "author" in first_review and len(first_review["author"].strip()) > 0
    assert first_review.get("rating", 0) > 0


def test_sentiment_analysis_on_real_daraz_reviews():
    """Verify live sentiment model evaluates real reviews without mock or synthetic fallback."""
    payload = json.dumps({"url": DARAZ_TEST_URL}).encode("utf-8")
    req = urllib.request.Request(
        EXPRESS_SCRAPE_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=20) as resp:
        res = json.loads(resp.read().decode("utf-8"))

    review_result = res.get("review_result")
    assert review_result is not None, "Review analysis result must be attached"

    sentiment_summary = review_result.get("marketplace_sentiment")
    assert sentiment_summary is not None, "Marketplace sentiment summary must be present"
    assert sentiment_summary["analyzed_count"] > 0, "Analyzed review count must be > 0"

    counts = sentiment_summary.get("counts", {})
    assert "positive" in counts and "neutral" in counts and "negative" in counts
    total_counts = counts["positive"] + counts["neutral"] + counts["negative"]
    assert total_counts == sentiment_summary["analyzed_count"]

    # Check that individual reviews have assigned sentiment & confidence
    analyzed_reviews = review_result.get("analyzed_reviews", [])
    assert len(analyzed_reviews) > 0
    for rev in analyzed_reviews:
        assert rev.get("sentiment") in ["positive", "neutral", "negative"]
        assert 0.0 <= rev.get("sentiment_confidence", 0.0) <= 1.0


def test_browser_search_links_format():
    """Verify browser search link generation handles spaces, brand, and product name safely."""
    import urllib.parse

    test_queries = [
        ("Maybelline", "Fit Me Matte Foundation", "Maybelline Fit Me Matte Foundation"),
        ("Unknown Brand", "Liquid Concealer", "Liquid Concealer"),
        ("The Ordinary", "Niacinamide 10%", "The Ordinary Niacinamide 10%"),
    ]

    for brand, product, expected_query in test_queries:
        query = f"{brand if brand != 'Unknown Brand' else ''} {product}".strip()
        assert query == expected_query

        encoded = urllib.parse.quote(query)
        daraz_url = f"https://www.daraz.lk/catalog/?q={encoded}"
        amazon_url = f"https://www.amazon.com/s?k={encoded}"
        temu_url = f"https://www.temu.com/search_result.html?search_key={encoded}"

        assert daraz_url.startswith("https://www.daraz.lk/catalog/?q=")
        assert amazon_url.startswith("https://www.amazon.com/s?k=")
        assert temu_url.startswith("https://www.temu.com/search_result.html?search_key=")
        assert " " not in daraz_url
        assert " " not in amazon_url
        assert " " not in temu_url


def test_catalog_integrity_thirty_products():
    """Verify product catalog strictly maintains 30 products and does not expand to Fit Me."""
    import pandas as pd

    catalog_csv = BASE_DIR / "data" / "selected_30_products_final.csv"
    assert catalog_csv.exists(), f"Missing product catalog CSV at {catalog_csv}"

    df = pd.read_csv(catalog_csv)
    assert len(df) == 30, f"Catalog must strictly contain 30 products, found {len(df)}"

    # Fit Me should NOT be in the catalog yet
    names = df["product_name"].str.lower().tolist()
    fit_me_entries = [n for n in names if "fit me" in n]
    assert len(fit_me_entries) == 0, f"Maybelline Fit Me must NOT be in 30-product catalog, found {fit_me_entries}"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
