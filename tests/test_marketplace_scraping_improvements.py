"""
Automated Test Suite: Marketplace Scraping Improvements & Safeguards
Covers:
  - Structured data (JSON-LD) extraction
  - Robust HTML selector fallback extraction
  - Client-rendered / JavaScript-only pages (UNAVAILABLE / NOT_RETRIEVABLE)
  - Missing fields handling (PARTIAL_DATA status)
  - Invalid URLs and unauthorized redirect attempts (INVALID_URL)
  - HTTP 503 anti-bot and CAPTCHA challenge detection (MARKETPLACE_BLOCKED)
  - Empty review collections preserved without fabrication
  - Ranking score suppression when required real data is unavailable (total_score=0.0, rank=99)
  - End-to-end user product URL scraping in search_all_marketplaces
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

BASE_DIR = Path(__file__).parent.parent.resolve()
SITE_PACKAGES_DIR = BASE_DIR / "ai-service" / "venv" / "Lib" / "site-packages"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BASE_DIR / "ai-service") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "ai-service"))
if SITE_PACKAGES_DIR.exists() and str(SITE_PACKAGES_DIR) not in sys.path:
    sys.path.insert(0, str(SITE_PACKAGES_DIR))

from app.services.scraping.metadata_extractor import (
    extract_product_metadata,
    extract_json_ld_products,
    extract_daraz_embedded_state,
    parse_price,
    parse_rating,
    parse_review_count,
)
from app.services.scraping.url_scraper import (
    scrape_user_product_url,
    fetch_daraz_reviews_and_ratings,
    is_safe_redirect,
    detect_platform_from_url,
)
from app.services.scraping.marketplace_search import (
    search_all_marketplaces,
)
from app.services.marketplace_comparison_service import (
    calculate_platform_score,
    compare_marketplace_platforms,
)
from app.schemas.marketplace import (
    ProductIdentity,
    MarketplaceListing as MarketplaceListingSchema,
    MarketplaceReview,
)
from app.services.scraping.schemas import RawMarketplaceItem


# ──────────────────────────────────────────────────────────────────────────────
# 1. Structured Data (JSON-LD) Extraction Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_json_ld_full_product_extraction():
    """Extracts title, brand, price, currency, rating, review_count, and actual reviews from JSON-LD."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "Maybelline Fit Me Matte + Poreless Foundation",
        "brand": {
          "@type": "Brand",
          "name": "Maybelline New York"
        },
        "offers": {
          "@type": "Offer",
          "price": "7.99",
          "priceCurrency": "USD",
          "seller": {
            "@type": "Organization",
            "name": "Amazon.com Services LLC"
          }
        },
        "aggregateRating": {
          "@type": "AggregateRating",
          "ratingValue": "4.5",
          "reviewCount": "12540"
        },
        "image": "https://m.media-amazon.com/images/I/fitme.jpg",
        "review": [
          {
            "@type": "Review",
            "author": {"@type": "Person", "name": "Sarah T."},
            "reviewRating": {"ratingValue": "5"},
            "reviewBody": "Best lightweight matte foundation for oily skin.",
            "datePublished": "2026-05-12"
          }
        ]
      }
      </script>
    </head>
    <body><h1>Product Page</h1></body>
    </html>
    """
    res = extract_product_metadata(html, platform="Amazon")
    assert res["status"] == "SUCCESS", f"Expected SUCCESS, got {res['status']}"
    assert res["title"] == "Maybelline Fit Me Matte + Poreless Foundation"
    assert res["brand"] == "Maybelline New York"
    assert res["price_val"] == 7.99
    assert res["currency"] == "USD"
    assert res["rating_val"] == 4.5
    assert res["review_count_val"] == 12540
    assert res["seller"] == "Amazon.com Services LLC"
    assert res["image_link"] == "https://m.media-amazon.com/images/I/fitme.jpg"
    assert len(res["reviews"]) == 1
    assert res["reviews"][0].author == "Sarah T."
    assert res["reviews"][0].rating == 5.0
    assert "lightweight matte" in res["reviews"][0].comment


def test_json_ld_graph_format_extraction():
    """Extracts Product entity when wrapped inside an @graph schema array."""
    html = """
    <html>
    <head>
      <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@graph": [
          {"@type": "WebSite", "name": "BeautyStore"},
          {
            "@type": "Product",
            "name": "Colourpop Lippie Stix",
            "brand": "Colourpop",
            "offers": {"@type": "Offer", "price": "6.50", "priceCurrency": "USD"},
            "aggregateRating": {"@type": "AggregateRating", "ratingValue": 4.8, "ratingCount": 350}
          }
        ]
      }
      </script>
    </head>
    </html>
    """
    res = extract_product_metadata(html)
    assert res["status"] == "SUCCESS"
    assert res["title"] == "Colourpop Lippie Stix"
    assert res["brand"] == "Colourpop"
    assert res["price_val"] == 6.50
    assert res["rating_val"] == 4.8
    assert res["review_count_val"] == 350


# ──────────────────────────────────────────────────────────────────────────────
# 2. Robust HTML Selectors Fallback Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_html_accessible_product_page_extraction():
    """Extracts product data using robust HTML selectors when JSON-LD is absent."""
    html = """
    <html>
    <body>
      <h1 id="productTitle">L'Oreal True Match Liquid Foundation</h1>
      <a id="bylineInfo">Brand: L'Oreal Paris</a>
      <span class="a-price"><span class="a-offscreen">$11.49</span></span>
      <div id="acrPopover"><span class="a-icon-alt">4.4 out of 5 stars</span></div>
      <span id="acrCustomerReviewText">8,920 ratings</span>
      <img id="landingImage" src="https://images.example.com/loreal.jpg" />
      <div data-hook="review">
        <span class="a-profile-name">Emily K.</span>
        <span class="review-rating"><span class="a-icon-alt">4.0 out of 5 stars</span></span>
        <span class="review-text-content"><span>Blends very naturally into skin.</span></span>
      </div>
    </body>
    </html>
    """
    res = extract_product_metadata(html, platform="Amazon")
    assert res["status"] == "SUCCESS"
    assert "L'Oreal True Match" in res["title"]
    assert "L'Oreal Paris" in res["brand"]
    assert res["price_val"] == 11.49
    assert res["rating_val"] == 4.4
    assert res["review_count_val"] == 8920
    assert len(res["reviews"]) == 1
    assert res["reviews"][0].author == "Emily K."
    assert "Blends very naturally" in res["reviews"][0].comment


# ──────────────────────────────────────────────────────────────────────────────
# 3. Missing Fields & PARTIAL_DATA Status Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_missing_fields_partial_data_status():
    """When only title and price are present without ratings/reviews, status is PARTIAL_DATA."""
    html = """
    <html>
    <body>
      <h1 class="pdp-mod-product-badge-title">Daraz Verified Lipstick</h1>
      <span class="pdp-price">Rs. 1,250</span>
      <!-- No rating stars, no review count, no customer reviews -->
    </body>
    </html>
    """
    res = extract_product_metadata(html, platform="Daraz")
    assert res["status"] == "PARTIAL_DATA", f"Expected PARTIAL_DATA, got {res['status']}"
    assert res["title"] == "Daraz Verified Lipstick"
    assert res["price_val"] == 1250.0
    assert res["rating_val"] == 0.0
    assert res["review_count_val"] == 0
    assert res["reviews"] == []
    assert "missing" in res["explanation"].lower()


# ──────────────────────────────────────────────────────────────────────────────
# 4. Client-Rendered / JavaScript-Only Shell Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_javascript_only_empty_shell():
    """An empty SPA shell (#root container with no product elements) returns UNAVAILABLE."""
    html = """
    <!DOCTYPE html>
    <html>
    <head><title>Marketplace Shell</title></head>
    <body>
      <div id="root"></div>
      <script src="/app.bundle.js"></script>
    </body>
    </html>
    """
    res = extract_product_metadata(html, platform="Daraz")
    assert res["status"] == "UNAVAILABLE"
    assert res["title"] is None
    assert "no readable product title" in res["explanation"].lower()


# ──────────────────────────────────────────────────────────────────────────────
# 5. Invalid URLs & Safe Redirects Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_invalid_urls_rejected():
    """Invalid URLs, missing protocol, or placeholder patterns are rejected without network requests."""
    invalid_cases = [
        ("https://www.amazon.com/item/P001", "Amazon"),
        ("https://www.ebay.com/itm/12345", "Amazon"),
        ("not-a-valid-url", "Daraz"),
        ("", "Temu"),
        (None, "Amazon")
    ]
    for url, plat in invalid_cases:
        item = scrape_user_product_url(url, expected_platform=plat)
        assert item.source_status == "unavailable"
        assert item.status_code == "INVALID_URL"
        assert "rejected" in item.explanation.lower() or "missing" in item.explanation.lower()


def test_safe_redirect_validation():
    """Redirects within platform domain are allowed; redirects to external domains are rejected."""
    # Internal redirect (same platform domain)
    safe, _ = is_safe_redirect(
        "https://amazon.com/dp/B0046VIZ9A",
        "https://www.amazon.com/Maybelline-Foundation/dp/B0046VIZ9A",
        "Amazon"
    )
    assert safe is True

    # Malicious redirect jumping out to untrusted domain
    unsafe, reason = is_safe_redirect(
        "https://www.amazon.com/redirect",
        "https://www.attacker-site.com/fake-product",
        "Amazon"
    )
    assert unsafe is False
    assert "not an authorized domain" in reason.lower()


# ──────────────────────────────────────────────────────────────────────────────
# 6. HTTP 503 Anti-Bot & CAPTCHA Detection Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_http_503_anti_bot_response():
    """HTTP 503 response is mapped to source_status='blocked' and MARKETPLACE_BLOCKED."""
    mock_resp = MagicMock()
    mock_resp.status_code = 503
    mock_resp.history = []

    with patch("app.services.scraping.url_scraper.requests.Session.get", return_value=mock_resp):
        item = scrape_user_product_url("https://www.amazon.com/dp/B0046VIZ9A")

    assert item.source_status == "blocked"
    assert item.status_code == "MARKETPLACE_BLOCKED"
    assert "503" in item.explanation


def test_captcha_and_challenge_markers_detection():
    """When anti-bot challenge markers appear in HTML, returns MARKETPLACE_BLOCKED cleanly."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.history = []
    mock_resp.url = "https://www.amazon.com/dp/B0046VIZ9A"
    mock_resp.text = "<html><body>To discuss automated access to Amazon data please contact api-services-support@amazon.com</body></html>"

    with patch("app.services.scraping.url_scraper.requests.Session.get", return_value=mock_resp):
        item = scrape_user_product_url("https://www.amazon.com/dp/B0046VIZ9A")

    assert item.source_status == "blocked"
    assert item.status_code == "MARKETPLACE_BLOCKED"
    assert "challenge" in item.explanation.lower() or "not bypassed" in item.explanation.lower()


# ──────────────────────────────────────────────────────────────────────────────
# 7. Ranking Score Suppression When Real Data Is Unavailable (Task 8)
# ──────────────────────────────────────────────────────────────────────────────

def test_ranking_scores_suppressed_when_real_data_unavailable():
    """
    Task 8: Do not generate marketplace ranking scores when the required real data is unavailable.
    A listing with rating=0.0 and review_count=0 must receive total_score=0.0 and rank=99.
    """
    listing_without_ratings = MarketplaceListingSchema(
        platform="Daraz",
        product_name="Maybelline Foundation",
        brand="Maybelline",
        product_type="Foundation_Base",
        price=1500.0,
        currency="LKR",
        rating=0.0,
        review_count=0,
        reviews=[],
        source_status="available",
        match_status="Exact Product Match",
        match_confidence=85.0,
        listing_status="PARTIAL_DATA",
        passed_match_threshold=True,
        product_url="https://www.daraz.lk/products/maybelline-foundation.html"
    )

    score_obj = calculate_platform_score(listing_without_ratings)
    assert score_obj.total_score == 0.0, f"Expected 0.0, got {score_obj.total_score}"
    assert score_obj.rank == 99, f"Expected rank 99, got {score_obj.rank}"
    assert "Data unavailable" in score_obj.recommendation_reason

    # In platform comparison, it must be appended as unranked (rank 99), not a recommendation
    scores = compare_marketplace_platforms([listing_without_ratings])
    assert scores[0].rank == 99
    assert scores[0].total_score == 0.0


def test_ranking_scores_calculated_when_real_data_is_available():
    """When authentic rating and review count are available, ranking score is calculated."""
    listing_with_ratings = MarketplaceListingSchema(
        platform="Amazon",
        product_name="Maybelline Fit Me Matte",
        brand="Maybelline",
        product_type="Foundation_Base",
        price=7.99,
        currency="USD",
        rating=4.5,
        review_count=1200,
        seller_name="Official Maybelline Store",
        reviews=[],
        source_status="available",
        match_status="Exact Product Match",
        match_confidence=90.0,
        listing_status="VERIFIED_LISTING",
        passed_match_threshold=True,
        product_url="https://www.amazon.com/dp/B0046VIZ9A"
    )

    score_obj = calculate_platform_score(listing_with_ratings)
    assert score_obj.total_score > 70.0, f"Expected high total score, got {score_obj.total_score}"
    assert score_obj.rank == 1


# ──────────────────────────────────────────────────────────────────────────────
# 8. User-Submitted Product URL Integration in search_all_marketplaces
# ──────────────────────────────────────────────────────────────────────────────

def test_user_product_url_integration_in_search_all_marketplaces():
    """search_all_marketplaces scrapes user_product_url and includes it in listings."""
    identity = ProductIdentity(
        brand="Maybelline",
        product_name="Fit Me Matte Poreless",
        product_type="Foundation_Base",
        category="Foundation_Base"
    )

    mock_url_item = RawMarketplaceItem(
        platform="Amazon",
        raw_title="Maybelline Fit Me Matte Poreless Foundation",
        brand="Maybelline",
        price_val=7.99,
        price_str="$7.99",
        currency="USD",
        rating_val=4.5,
        review_count_val=2500,
        seller="Amazon Services",
        link="https://www.amazon.com/dp/B0046VIZ9A",
        source_status="available",
        status_code="SUCCESS"
    )

    with (
        patch("app.services.scraping.marketplace_search.scrape_user_product_url", return_value=mock_url_item),
        patch("app.services.scraping.marketplace_search.scrape_amazon_products", return_value=[]),
        patch("app.services.scraping.marketplace_search.scrape_daraz_products", return_value=[]),
        patch("app.services.scraping.marketplace_search.scrape_temu_products", return_value=[]),
    ):
        listings = search_all_marketplaces(identity, user_product_url="https://www.amazon.com/dp/B0046VIZ9A")

    assert len(listings) >= 1
    user_listing = next(l for l in listings if l.product_url == "https://www.amazon.com/dp/B0046VIZ9A")
    assert user_listing.listing_status == "VERIFIED_LISTING"
    assert user_listing.passed_match_threshold is True
    assert user_listing.price == 7.99
    assert user_listing.rating == 4.5


# ──────────────────────────────────────────────────────────────────────────────
# 9. Daraz Embedded State Extraction & PDP Review Integration Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_daraz_embedded_state_pdp_tracking_data():
    """Extracts price, currency, brand, item_id, and title from pdpTrackingData script."""
    html = """
    <html>
    <head>
      <script>
        var pdpTrackingData = "{\\"pdt_price\\":\\"Rs. 5,490\\",\\"brand_name\\":\\"No Brand\\",\\"pdt_name\\":\\"Maybelline Fit Me Matte Foundation\\",\\"core\\":{\\"currencyCode\\":\\"LKR\\",\\"country\\":\\"LK\\"},\\"pdt_sku\\":204252780}";
      </script>
    </head>
    <body><h1>Maybelline Fit Me Matte Foundation</h1></body>
    </html>
    """
    state = extract_daraz_embedded_state(html)
    assert state["price_val"] == 5490.0
    assert state["price_str"] == "Rs. 5,490"
    assert state["currency"] == "LKR"
    assert state["brand"] == "No Brand"
    assert state["item_id"] == "204252780"
    assert state["title"] == "Maybelline Fit Me Matte Foundation"


def test_daraz_embedded_state_module_data_fallback():
    """Extracts tracking state from __moduleData__ when pdpTrackingData is not present."""
    html = """
    <html>
    <head>
      <script>
        var __moduleData__ = {"data":{"root":{"fields":{"tracking":{"pdt_price":"Rs. 3,250","core":{"currencyCode":"LKR"},"brand_name":"Maybelline","pdt_sku":"10029384_LK"}}}},"extra":{}};
      </script>
    </head>
    <body><h1>Maybelline Lipstick</h1></body>
    </html>
    """
    state = extract_daraz_embedded_state(html)
    assert state["price_val"] == 3250.0
    assert state["currency"] == "LKR"
    assert state["brand"] == "Maybelline"
    assert state["item_id"] == "10029384"


def test_daraz_distinguish_rating_count_from_written_review_count():
    """
    Verifies that rating count (total star ratings) and written-review count (text comments)
    are correctly distinguished and not assumed to be identical.
    """
    mock_review_response = {
        "success": True,
        "model": {
            "ratings": {
                "average": 4.8,
                "rateCount": 150,      # 150 total ratings
                "reviewCount": 12      # 12 written reviews
            },
            "items": [
                {
                    "buyerName": "dilani_k",
                    "reviewTime": "12 Jan 2026",
                    "reviewContent": "Excellent shade match for warm undertone",
                    "gradeItems": {"PRODUCT_REVIEW": 5},
                    "reviewStatus": "approved"
                }
            ]
        }
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_review_response

    with patch("requests.get", return_value=mock_resp):
        avg_r, rate_c, rev_c, reviews = fetch_daraz_reviews_and_ratings(
            item_id="204252780",
            product_url="https://www.daraz.lk/products/maybelline-foundation-i204252780.html"
        )

    assert avg_r == 4.8
    assert rate_c == 150          # Rating count
    assert rev_c == 12            # Written review count
    assert rate_c != rev_c        # Distinct values preserved
    assert len(reviews) == 1
    assert reviews[0].author == "dilani_k"
    assert reviews[0].comment == "Excellent shade match for warm undertone"
    assert reviews[0].rating == 5.0
    assert reviews[0].verified_purchase is True


def test_currency_lkr_only_when_evidence_supported():
    """
    Currency must be kept as LKR only when supported by the page's currency or locale evidence.
    Unknown currencies must NOT be silently defaulted to USD.
    """
    # 1. Daraz LK evidence -> LKR
    html_lk = """
    <html>
      <script>var pdpTrackingData = "{\\"pdt_price\\":\\"Rs. 5,000\\",\\"core\\":{\\"currencyCode\\":\\"LKR\\"}}";</script>
    </html>
    """
    meta_lk = extract_product_metadata(html_lk, platform="Daraz", url="https://www.daraz.lk/products/item-i123.html")
    assert meta_lk["currency"] == "LKR"

    # 2. Generic HTML with unknown platform and no currency tag -> None (not USD)
    html_unknown = """
    <html>
      <head><title>Some Generic Product</title></head>
      <body><span class="price">50.00</span></body>
    </html>
    """
    meta_unknown = extract_product_metadata(html_unknown, platform="CustomStore")
    assert meta_unknown["currency"] is None, f"Expected None for unknown currency, got {meta_unknown['currency']}"


def test_daraz_empty_missing_data_returns_partial_or_unavailable():
    """
    If product data or reviews cannot be retrieved, returns PARTIAL_DATA or UNAVAILABLE
    and clearly identifies missing fields.
    """
    # Case A: Title present, but price and reviews missing -> PARTIAL_DATA
    html_title_only = """
    <html>
      <head><title>Maybelline Foundation Only Title</title></head>
      <body><h1 class="pdp-mod-product-badge-title">Maybelline Foundation Only Title</h1></body>
    </html>
    """
    meta = extract_product_metadata(html_title_only, platform="Daraz", url="https://www.daraz.lk/products/item-i999.html")
    assert meta["status"] == "PARTIAL_DATA"
    assert "missing: price, rating, reviews" in meta["explanation"].lower()
    assert meta["price_val"] == 0.0
    assert meta["rating_val"] == 0.0
    assert len(meta["reviews"]) == 0

    # Case B: Completely empty HTML -> UNAVAILABLE
    meta_empty = extract_product_metadata("", platform="Daraz")
    assert meta_empty["status"] == "UNAVAILABLE"
    assert "Empty HTML content" in meta_empty["explanation"]


def test_scrape_user_product_url_daraz_end_to_end_mock():
    """
    Simulates end-to-end user URL scraping on Daraz product page:
    verifies price=5490.0, currency=LKR, rating=5.0, rating_count=1, review_count=1, review comment.
    """
    pdp_html = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>Maybelline New York Liquid Foundation, Matte Finish - Daraz.lk</title>
      <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "Maybelline New York Liquid Foundation, Matte Finish, With SPF, Absorbs Oil, Fit Me Matte + Poreless, 128 Warm Nude, 30 ml FROM INDIA(SAM)",
        "brand": {"@type": "Brand", "name": "No Brand"},
        "image": "https://static-01.daraz.lk/p/sample.jpg"
      }
      </script>
      <script>
        var pdpTrackingData = "{\\"pdt_price\\":\\"Rs. 5,490\\",\\"brand_name\\":\\"No Brand\\",\\"pdt_name\\":\\"Maybelline New York Liquid Foundation, Matte Finish, With SPF, Absorbs Oil, Fit Me Matte + Poreless, 128 Warm Nude, 30 ml FROM INDIA(SAM)\\",\\"core\\":{\\"currencyCode\\":\\"LKR\\",\\"country\\":\\"LK\\"},\\"pdt_sku\\":204252780}";
      </script>
    </head>
    <body><h1>Maybelline New York Liquid Foundation</h1></body>
    </html>
    """

    mock_review_json = {
        "success": True,
        "model": {
            "ratings": {"average": 5.0, "rateCount": 1, "reviewCount": 1},
            "items": [
                {
                    "buyerName": "nadheesha1990",
                    "reviewTime": "14 Nov 2025",
                    "reviewContent": "nice shade \\nMatt finish  ",
                    "gradeItems": {"PRODUCT_REVIEW": 5},
                    "reviewStatus": "approved"
                }
            ]
        }
    }

    mock_pdp_resp = MagicMock()
    mock_pdp_resp.status_code = 200
    mock_pdp_resp.text = pdp_html
    mock_pdp_resp.url = "https://www.daraz.lk/products/maybelline-i204252780-s1298331553.html"
    mock_pdp_resp.history = []

    mock_rev_resp = MagicMock()
    mock_rev_resp.status_code = 200
    mock_rev_resp.json.return_value = mock_review_json

    def mock_get(url, *args, **kwargs):
        if "review/getReviewList" in url:
            return mock_rev_resp
        return mock_pdp_resp

    with patch("requests.Session.get", side_effect=mock_get), patch("requests.get", side_effect=mock_get):
        item = scrape_user_product_url(
            "https://www.daraz.lk/products/maybelline-i204252780-s1298331553.html",
            expected_platform="Daraz"
        )

    assert item.status_code == "SUCCESS"
    assert item.platform == "Daraz"
    assert item.brand == "No Brand"
    assert item.price_val == 5490.0
    assert item.price_str == "Rs. 5,490"
    assert item.currency == "LKR"
    assert item.rating_val == 5.0
    assert item.rating_count_val == 1
    assert item.review_count_val == 1
    assert len(item.reviews) == 1
    assert item.reviews[0].author == "nadheesha1990"
    assert "nice shade" in item.reviews[0].comment
    assert item.reviews[0].rating == 5.0

