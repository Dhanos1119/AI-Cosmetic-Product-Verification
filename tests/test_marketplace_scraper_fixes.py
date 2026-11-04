"""
Test Suite: Marketplace Integration Fixes
Covers issues identified in the end-to-end UI audit:
  - Amazon "URL 'None' is missing or invalid" root cause
  - Akamai bm-verify interstitial detection
  - Fabricated Daraz/Temu rating/review_count removal
  - Temu false-positive 'verify' substring blocking
  - Daraz honest NOT_RETRIEVABLE vs MARKETPLACE_BLOCKED distinction
  - URL validator strict domain match (anti-lookalike)
  - Persistence gate rejects INVALID_URL listings
  - Duplicate ASIN listing upsert de-duplication
"""

import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).parent.parent.resolve()
SITE_PACKAGES_DIR = BASE_DIR / "ai-service" / "venv" / "Lib" / "site-packages"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BASE_DIR / "ai-service") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "ai-service"))
if SITE_PACKAGES_DIR.exists() and str(SITE_PACKAGES_DIR) not in sys.path:
    sys.path.insert(0, str(SITE_PACKAGES_DIR))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.services.scraping.amazon_scraper import (
    scrape_amazon_products,
    extract_amazon_card_link,
    BOT_CHALLENGE_MARKERS,
)
from app.services.scraping.daraz_scraper import scrape_daraz_products
from app.services.scraping.temu_scraper import scrape_temu_products
from app.services.scraping.url_validator import validate_marketplace_url
from database.connection import Base
from database.models import MarketplaceListing
from database.persistence_service import (
    is_valid_listing_for_persistence,
    get_or_create_product,
    get_or_create_marketplace,
    upsert_marketplace_listing,
)
from app.schemas.marketplace import (
    ProductIdentity,
    MarketplaceListing as MarketplaceListingSchema,
)


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def db_session():
    """Isolated SQLite test DB for each test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name

    engine = create_engine(f"sqlite:///{tmp_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()
    try:
        os.remove(tmp_path)
    except OSError:
        pass


def _mock_response(status_code: int, text: str):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    return resp


# ──────────────────────────────────────────────────────────────────────────────
# Section 1 – Amazon: link extraction helpers
# ──────────────────────────────────────────────────────────────────────────────

def test_amazon_link_legacy_markup():
    """h2 > a[href] markup – links must be extracted correctly."""
    card = BeautifulSoup(
        '<div><h2><a href="/dp/B001LEGACY?tag=x">Title</a></h2></div>',
        "html.parser"
    )
    link = extract_amazon_card_link(card)
    assert link == "https://www.amazon.com/dp/B001LEGACY?tag=x", link


def test_amazon_link_modern_anchor_wraps_h2():
    """Current Amazon markup: anchor wraps h2. Link must be extracted."""
    card = BeautifulSoup(
        '<div><a class="a-link-normal" href="/dp/B002MODERN?ref=x">'
        "<h2><span>Product Title</span></h2></a></div>",
        "html.parser"
    )
    link = extract_amazon_card_link(card)
    assert link is not None, "Link should have been found"
    assert "B002MODERN" in link, link


def test_amazon_link_none_when_no_href():
    """Card with no anchor at all must return None, not raise."""
    card = BeautifulSoup("<div><h2><span>Title Only</span></h2></div>", "html.parser")
    link = extract_amazon_card_link(card)
    assert link is None


def test_amazon_link_no_javascript_href():
    """Anchors with javascript: hrefs must be rejected."""
    card = BeautifulSoup(
        "<div><a href=\"javascript:void(0)\"><h2><span>Js Link</span></h2></a></div>",
        "html.parser"
    )
    link = extract_amazon_card_link(card)
    assert link is None


# ──────────────────────────────────────────────────────────────────────────────
# Section 2 – Amazon scraper: bot/interstitial detection
# ──────────────────────────────────────────────────────────────────────────────

def test_amazon_bm_verify_interstitial_reported_as_blocked():
    """Akamai bm-verify interstitial (HTTP 200) must be detected as blocked.
    Root cause: 200 + bm-verify page had no cards, fell to 'No matching listings found'
    (source_status='unavailable'), then every card iterated with link=None -> INVALID_URL flood.
    """
    bm_verify_html = (
        '<!DOCTYPE html><html><body>'
        '<meta http-equiv="refresh" content="5; URL=\'/s?bm-verify=AAQAAAAO\'" />'
        '</body></html>'
    )
    with patch("app.services.scraping.amazon_scraper.requests.get") as mock_get:
        mock_get.return_value = _mock_response(200, bm_verify_html)
        results = scrape_amazon_products("Maybelline Foundation")

    assert len(results) == 1
    r = results[0]
    assert r.source_status == "blocked", f"Expected blocked, got: {r.source_status}"
    assert r.status_code == "MARKETPLACE_BLOCKED"
    assert r.link is None  # no fabricated URL


def test_amazon_http_503_reported_as_blocked():
    """HTTP 503 anti-bot response must be reported as blocked."""
    with patch("app.services.scraping.amazon_scraper.requests.get") as mock_get:
        mock_get.return_value = _mock_response(503, "<html>Service Unavailable</html>")
        results = scrape_amazon_products("L'Oreal Mascara")

    assert results[0].source_status == "blocked"
    assert results[0].status_code == "MARKETPLACE_BLOCKED"


def test_amazon_200_empty_page_reported_as_unavailable():
    """HTTP 200 with no search-result cards (and no bm-verify) yields 'unavailable'."""
    clean_200 = "<html><body><div id='s-results-list-atf'></div></body></html>"
    with patch("app.services.scraping.amazon_scraper.requests.get") as mock_get:
        mock_get.return_value = _mock_response(200, clean_200)
        results = scrape_amazon_products("Nonexistent Product XYZ999")

    assert results[0].source_status == "unavailable"
    assert results[0].status_code == "NO_MATCH_FOUND"
    assert results[0].link is None


def test_amazon_valid_cards_yield_valid_links_and_no_fabricated_sellers():
    """Real search cards must produce non-None links; seller must always be None."""
    html_with_cards = """
    <html><body>
      <div data-component-type="s-search-result" data-asin="B001XXXX">
        <h2><a href="/dp/B001XXXX?tag=sr">
          <span>Maybelline Fit Me Foundation Matte</span>
        </a></h2>
        <span class="a-price"><span class="a-offscreen">$9.97</span></span>
        <span class="a-icon-alt">4.6 out of 5 stars</span>
        <img class="s-image" src="https://m.media-amazon.com/images/I/123.jpg" />
      </div>
      <div data-component-type="s-search-result" data-asin="B002YYYY">
        <a class="a-link-normal" href="/dp/B002YYYY">
          <h2><span class="a-text-normal">L'Oreal True Match Foundation</span></h2>
        </a>
        <span class="a-price"><span class="a-offscreen">$12.49</span></span>
      </div>
    </body></html>
    """
    with patch("app.services.scraping.amazon_scraper.requests.get") as mock_get:
        mock_get.return_value = _mock_response(200, html_with_cards)
        results = scrape_amazon_products("Foundation", max_results=5)

    assert len(results) == 2, f"Expected 2 items, got {len(results)}"
    for r in results:
        assert r.source_status == "available"
        assert r.link is not None, f"Link must not be None for: {r.raw_title}"
        assert r.link.startswith("https://www.amazon.com"), r.link
        assert r.seller is None, "Seller must not be set from search-result cards"


def test_amazon_asin_captured_as_listing_id():
    """data-asin attribute must be captured as listing_id for de-duplication."""
    html = """
    <html><body>
      <div data-component-type="s-search-result" data-asin="B00TESTASIN">
        <h2><a href="/dp/B00TESTASIN"><span>Test Product</span></a></h2>
      </div>
    </body></html>
    """
    with patch("app.services.scraping.amazon_scraper.requests.get") as mock_get:
        mock_get.return_value = _mock_response(200, html)
        results = scrape_amazon_products("Test Product")

    assert results[0].listing_id == "B00TESTASIN"


# ──────────────────────────────────────────────────────────────────────────────
# Section 3 – Daraz: honest status reporting
# ──────────────────────────────────────────────────────────────────────────────

def test_daraz_client_shell_reported_as_not_retrievable():
    """Empty #root container (SPA shell) must yield source_status='unavailable'
    with status_code='NOT_RETRIEVABLE', NOT 'blocked'."""
    spa_shell_html = """
    <html><body>
      <div id="root"></div>
      <script>window.baxiaCommon && window.baxiaCommon.init({});</script>
    </body></html>
    """
    with patch("app.services.scraping.daraz_scraper.requests.get") as mock_get:
        mock_get.return_value = _mock_response(200, spa_shell_html)
        results = scrape_daraz_products("Maybelline Foundation")

    r = results[0]
    assert r.source_status == "unavailable", f"Expected unavailable, got: {r.source_status}"
    assert r.status_code == "NOT_RETRIEVABLE", r.status_code
    assert "JavaScript" in r.explanation or "client-side" in r.explanation


def test_daraz_captcha_punish_page_reported_as_blocked():
    """Explicit slider/punish page must yield source_status='blocked'."""
    punish_html = """
    <html><body>
      <script src="/_____tmd_____/punish?x5secdata=abc"></script>
    </body></html>
    """
    with patch("app.services.scraping.daraz_scraper.requests.get") as mock_get:
        mock_get.return_value = _mock_response(200, punish_html)
        results = scrape_daraz_products("Maybelline Foundation")

    assert results[0].source_status == "blocked"
    assert results[0].status_code == "MARKETPLACE_BLOCKED"


def test_daraz_no_hardcoded_ratings():
    """When real cards are found, rating_val and review_count_val must NOT be 4.5 / 12."""
    cards_html = """
    <html><body>
      <div data-qa-locator="product-item">
        <a class="c165B3" href="//www.daraz.lk/products/maybelline.html">
          Maybelline Fit Me
        </a>
        <span class="c3g2v4">LKR 1,200</span>
      </div>
    </body></html>
    """
    with patch("app.services.scraping.daraz_scraper.requests.get") as mock_get:
        mock_get.return_value = _mock_response(200, cards_html)
        results = scrape_daraz_products("Maybelline")

    available = [r for r in results if r.source_status == "available"]
    for r in available:
        assert r.rating_val == 0.0, f"Fabricated rating detected: {r.rating_val}"
        assert r.review_count_val == 0, f"Fabricated review count: {r.review_count_val}"


def test_daraz_baxia_sdk_alone_does_not_trigger_block():
    """The baxia SDK init script appears on NORMAL Daraz pages; must NOT trigger BLOCKED."""
    baxia_only = """
    <html><body>
      <div id="root"></div>
      <script>window.baxiaCommon && window.baxiaCommon.init({appName:'daraz'});</script>
    </body></html>
    """
    with patch("app.services.scraping.daraz_scraper.requests.get") as mock_get:
        mock_get.return_value = _mock_response(200, baxia_only)
        results = scrape_daraz_products("L'Oreal Paris")

    r = results[0]
    assert r.source_status != "blocked", "baxia SDK alone must not trigger MARKETPLACE_BLOCKED"
    assert r.status_code in ("NOT_RETRIEVABLE", "NO_MATCH_FOUND")


# ──────────────────────────────────────────────────────────────────────────────
# Section 4 – Temu: honest status reporting
# ──────────────────────────────────────────────────────────────────────────────

def test_temu_verify_substring_no_longer_triggers_false_positive_block():
    """'verifyAuthToken' config key must NOT cause source_status='blocked'."""
    normal_temu_html = """
    <html><body>
      <script>
        window.__CONFIG__ = {"verifyAuthToken": "abc123", "pass_verify_back_url": "/home"};
      </script>
      <div id="root"><div class="search-content"></div></div>
    </body></html>
    """
    with patch("app.services.scraping.temu_scraper.requests.get") as mock_get:
        mock_get.return_value = _mock_response(200, normal_temu_html)
        results = scrape_temu_products("Maybelline")

    r = results[0]
    assert r.source_status != "blocked", (
        f"'verify' in config key must not trigger MARKETPLACE_BLOCKED; got {r.source_status}"
    )


def test_temu_captcha_keyword_triggers_blocked():
    """Explicit 'captcha' keyword in page -> source_status='blocked'."""
    captcha_html = (
        "<html><body><script>window.captcha = {enabled: true};</script></body></html>"
    )
    with patch("app.services.scraping.temu_scraper.requests.get") as mock_get:
        mock_get.return_value = _mock_response(200, captcha_html)
        results = scrape_temu_products("Maybelline")

    assert results[0].source_status == "blocked"
    assert results[0].status_code == "MARKETPLACE_BLOCKED"


def test_temu_client_rendered_page_reported_as_unavailable():
    """Standard Temu JS-rendered page (no .product-item cards, no captcha) -> unavailable."""
    js_page = """
    <html><body>
      <script>window.__PageContext__ = {"pagePath":"w/search_result"};</script>
      <div id="app"></div>
    </body></html>
    """
    with patch("app.services.scraping.temu_scraper.requests.get") as mock_get:
        mock_get.return_value = _mock_response(200, js_page)
        results = scrape_temu_products("Foundation")

    r = results[0]
    assert r.source_status == "unavailable", r.source_status
    assert r.status_code == "NOT_RETRIEVABLE", r.status_code


def test_temu_no_hardcoded_ratings():
    """If .product-item cards ARE present, rating_val / review_count_val must be 0.0 / 0."""
    html_with_items = """
    <html><body>
      <div class="product-item">
        <a href="/goods-123.html"><div class="title">Maybelline Mascara</div></a>
        <div class="price">$5.99</div>
      </div>
    </body></html>
    """
    with patch("app.services.scraping.temu_scraper.requests.get") as mock_get:
        mock_get.return_value = _mock_response(200, html_with_items)
        results = scrape_temu_products("Maybelline")

    available = [r for r in results if r.source_status == "available"]
    for r in available:
        assert r.rating_val == 0.0, f"Fabricated rating: {r.rating_val}"
        assert r.review_count_val == 0, f"Fabricated review count: {r.review_count_val}"


# ──────────────────────────────────────────────────────────────────────────────
# Section 5 – URL validator: strict domain matching
# ──────────────────────────────────────────────────────────────────────────────

def test_url_validator_rejects_lookalike_domain():
    """amazon.com.evil.example must NOT pass as an Amazon URL (old substring match accepted this)."""
    lookalike = "https://www.amazon.com.evil.example/dp/B001FAKE"
    is_valid, reason = validate_marketplace_url(lookalike, "Amazon")
    assert is_valid is False, f"Look-alike domain must be rejected; reason: {reason}"


def test_url_validator_accepts_amazon_subdomain():
    """www.amazon.com is a valid Amazon domain."""
    url = "https://www.amazon.com/dp/B0046VIZ9A"
    is_valid, _ = validate_marketplace_url(url, "Amazon")
    assert is_valid is True


def test_url_validator_accepts_daraz_subdomain():
    """www.daraz.lk is a valid Daraz domain."""
    url = "https://www.daraz.lk/products/maybelline-i100.html"
    is_valid, _ = validate_marketplace_url(url, "Daraz")
    assert is_valid is True


def test_url_validator_rejects_none_url():
    """None URL must be rejected without raising an exception."""
    is_valid, reason = validate_marketplace_url(None, "Amazon")
    assert is_valid is False
    assert "missing" in reason.lower() or "empty" in reason.lower()


def test_url_validator_rejects_placeholder_patterns():
    """Internal catalog placeholder patterns must be rejected."""
    placeholders = [
        "https://www.amazon.com/item/P001",
        "https://www.daraz.lk/item/PROD_COL",
        "https://www.temu.com/item/p0abc",
    ]
    for url in placeholders:
        is_valid, _ = validate_marketplace_url(url)
        assert is_valid is False, f"Placeholder URL must be rejected: {url}"


# ──────────────────────────────────────────────────────────────────────────────
# Section 6 – Persistence gate: INVALID_URL listings must never be stored
# ──────────────────────────────────────────────────────────────────────────────

def test_persistence_rejects_invalid_url_listing():
    """listing_status='INVALID_URL' must be rejected by is_valid_listing_for_persistence."""
    schema = MarketplaceListingSchema(
        platform="Amazon",
        product_name="Maybelline Fit Me Foundation",
        brand="Maybelline",
        product_type="Foundation_Base",
        product_url=None,
        source_status="available",
        match_status="Possible Match",
        match_confidence=65.0,
        listing_status="INVALID_URL",
        passed_match_threshold=False,
    )
    assert is_valid_listing_for_persistence(schema) is False


def test_persistence_rejects_none_url_even_with_high_match():
    """product_url=None must block persistence regardless of match confidence."""
    schema = MarketplaceListingSchema(
        platform="Amazon",
        product_name="Colourpop Lippie Pencil",
        brand="Colourpop",
        product_type="Lip_Products",
        product_url=None,
        source_status="available",
        match_status="Exact Product Match",
        match_confidence=92.0,
        listing_status="INVALID_URL",
        passed_match_threshold=False,
    )
    assert is_valid_listing_for_persistence(schema) is False


def test_persistence_accepts_valid_url_listing(db_session):
    """Valid listing with proper URL must be persisted exactly once."""
    identity = ProductIdentity(
        brand="Maybelline",
        product_name="Fit Me Foundation",
        product_type="Foundation_Base",
        category="Foundation_Base",
        product_id="PROD_TEST_PERSIST",
    )
    prod = get_or_create_product(db_session, identity)
    mkt = get_or_create_marketplace(db_session, "Amazon")

    schema = MarketplaceListingSchema(
        platform="Amazon",
        product_name="Maybelline Fit Me Matte",
        brand="Maybelline",
        product_type="Foundation_Base",
        price=9.97,
        currency="USD",
        product_url="https://www.amazon.com/dp/B00VALID001",
        source_status="available",
        match_status="Exact Product Match",
        match_confidence=88.0,
        listing_status="VERIFIED_LISTING",
        passed_match_threshold=True,
    )
    assert is_valid_listing_for_persistence(schema) is True
    upsert_marketplace_listing(db_session, prod, mkt, None, schema)
    db_session.commit()

    listings = db_session.query(MarketplaceListing).all()
    assert len(listings) == 1
    assert listings[0].product_url == "https://www.amazon.com/dp/B00VALID001"


def test_duplicate_asin_upserted_not_duplicated(db_session):
    """Two calls with the same product_url must produce exactly 1 DB row."""
    identity = ProductIdentity(
        brand="L'Oreal",
        product_name="True Match Foundation",
        product_type="Foundation_Base",
        category="Foundation_Base",
        product_id="PROD_LOreal_001",
    )
    prod = get_or_create_product(db_session, identity)
    mkt = get_or_create_marketplace(db_session, "Amazon")

    base = dict(
        platform="Amazon",
        brand="L'Oreal",
        product_type="Foundation_Base",
        currency="USD",
        source_status="available",
        match_status="Exact Product Match",
        match_confidence=85.0,
        listing_status="VERIFIED_LISTING",
        passed_match_threshold=True,
        product_url="https://www.amazon.com/dp/B00DUP0001",
    )

    s1 = MarketplaceListingSchema(product_name="L'Oreal True Match - first", price=11.99, **base)
    s2 = MarketplaceListingSchema(product_name="L'Oreal True Match - updated", price=10.49, **base)

    upsert_marketplace_listing(db_session, prod, mkt, None, s1)
    db_session.commit()
    upsert_marketplace_listing(db_session, prod, mkt, None, s2)
    db_session.commit()

    listings = db_session.query(MarketplaceListing).all()
    assert len(listings) == 1, f"Duplicate rows created: {len(listings)}"
    assert listings[0].raw_title == "L'Oreal True Match - updated"
    assert listings[0].price == 10.49


# ──────────────────────────────────────────────────────────────────────────────
# Section 7 – Scraper status label mutual-exclusivity
# ──────────────────────────────────────────────────────────────────────────────

def test_amazon_status_labels_are_mutually_exclusive():
    """503 -> blocked; clean 200 with no cards -> unavailable."""
    scenarios = [
        (503, "<html>Service Unavailable</html>",          "blocked"),
        (200, "<html><body><div id='root'></div></body></html>", "unavailable"),
    ]
    for code, body, expected in scenarios:
        with patch("app.services.scraping.amazon_scraper.requests.get") as mock_get:
            mock_get.return_value = _mock_response(code, body)
            results = scrape_amazon_products("L'Oreal")
        assert results[0].source_status == expected, (
            f"HTTP {code}: expected {expected}, got {results[0].source_status}"
        )


def test_daraz_status_labels_mutually_exclusive():
    """Daraz 403 -> blocked; SPA shell -> unavailable."""
    scenarios = [
        (403, "<html>Forbidden</html>",                  "blocked"),
        (200, "<html><body><div id='root'></div></body></html>", "unavailable"),
    ]
    for code, body, expected in scenarios:
        with patch("app.services.scraping.daraz_scraper.requests.get") as mock_get:
            mock_get.return_value = _mock_response(code, body)
            results = scrape_daraz_products("Maybelline")
        assert results[0].source_status == expected, (
            f"HTTP {code}: expected {expected}, got {results[0].source_status}"
        )


def test_temu_status_labels_mutually_exclusive():
    """Temu 503 -> blocked; clean JS page -> unavailable."""
    scenarios = [
        (503, "<html>Server Error</html>",              "blocked"),
        (200, "<html><body><script>init();</script></body></html>", "unavailable"),
    ]
    for code, body, expected in scenarios:
        with patch("app.services.scraping.temu_scraper.requests.get") as mock_get:
            mock_get.return_value = _mock_response(code, body)
            results = scrape_temu_products("Mascara")
        assert results[0].source_status == expected, (
            f"HTTP {code}: expected {expected}, got {results[0].source_status}"
        )
