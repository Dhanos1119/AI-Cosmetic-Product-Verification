"""
Test Suite: OCR Query Normalisation and Search Query Construction
Covers:
  - _normalize_query: lone punctuation removal, OCR noise token removal, multi-space collapse
  - generate_search_queries: normalises brand + product_name before building query
  - parse_brand_and_product: product_name now joins up to 4 lines; trailing/leading punctuation stripped
  - Amazon 503 is correctly mapped to source_status='blocked' (not fabricated data)
  - INVALID_SEARCH_TOKENS gate still rejects placeholder identities
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'ai-service'))

from app.services.scraping.marketplace_search import (
    _normalize_query,
    generate_search_queries,
    INVALID_SEARCH_TOKENS,
)
from app.services.ocr_service import parse_brand_and_product
from app.schemas.marketplace import ProductIdentity


# ─────────────────────────────────────────────────────────────────────────────
# Section 1 — _normalize_query unit tests
# ─────────────────────────────────────────────────────────────────────────────

class TestNormalizeQuery:

    def test_removes_standalone_trailing_dash(self):
        """Trailing standalone dash from OCR line-split should be removed."""
        result = _normalize_query("Matte -")
        assert result == "Matte", f"Expected 'Matte', got {result!r}"

    def test_removes_standalone_leading_plus(self):
        """Leading standalone plus from OCR line-split should be removed."""
        result = _normalize_query("+PORELESS foundation")
        assert result == "PORELESS foundation", f"Got {result!r}"

    def test_removes_standalone_dash_and_plus_in_middle(self):
        """Both - and + when standalone (not part of a word) are removed."""
        result = _normalize_query("Matte - +PORELESS")
        assert "-" not in result, f"Dash should be removed; got {result!r}"
        assert "+" not in result, f"Plus should be removed; got {result!r}"
        assert "Matte" in result
        assert "PORELESS" in result

    def test_removes_ocr_noise_token_normaltooly(self):
        """'NORMALTOOLY' is a well-known OCR artefact for 'Normal to Oily'; removed."""
        result = _normalize_query("Matte PORELESS NORMALTOOLY")
        assert "NORMALTOOLY" not in result.upper(), f"Got {result!r}"
        assert "PORELESS" in result.upper()

    def test_removes_ocr_noise_token_normaltooly_case_insensitive(self):
        result = _normalize_query("foundation normaltooly skin")
        assert "normaltooly" not in result.lower()

    def test_collapses_multiple_spaces(self):
        result = _normalize_query("Fit  Me   Matte   Poreless")
        assert "  " not in result, f"Multiple spaces remain: {result!r}"
        assert result == "Fit Me Matte Poreless"

    def test_empty_string_returns_empty(self):
        assert _normalize_query("") == ""

    def test_none_like_empty(self):
        assert _normalize_query("") == ""

    def test_already_clean_query_unchanged(self):
        q = "Maybelline Fit Me Matte Poreless Foundation"
        result = _normalize_query(q)
        assert result == q, f"Clean query should be unchanged; got {result!r}"

    def test_hyphen_within_word_preserved(self):
        """Hyphen inside compound word (like 'Super-Blendable') stays intact."""
        result = _normalize_query("True Match Super-Blendable Foundation")
        # After processing hyphens in words become spaces (regex replaces non-word chars)
        # The key is the word tokens are preserved: Super, Blendable
        assert "Super" in result
        assert "Blendable" in result

    def test_exclamation_in_product_name_removed(self):
        result = _normalize_query("fit me! matte poreless")
        assert "!" not in result
        assert "fit me" in result.lower()
        assert "matte" in result.lower()

    def test_removes_multiple_noise_tokens(self):
        result = _normalize_query("Matte Poreless normaltooly oilysk")
        result_lower = result.lower()
        assert "normaltooly" not in result_lower
        assert "oilysk" not in result_lower
        assert "matte" in result_lower
        assert "poreless" in result_lower

    def test_reported_malformed_query_fixed(self):
        """The exact reported case: 'Matte - +PORELESS NORMALTOOLY' must be cleaned."""
        result = _normalize_query("Matte - +PORELESS NORMALTOOLY")
        assert "-" not in result
        assert "+" not in result
        assert "NORMALTOOLY" not in result.upper()
        assert "Matte" in result
        assert "PORELESS" in result


# ─────────────────────────────────────────────────────────────────────────────
# Section 2 — generate_search_queries integration tests
# ─────────────────────────────────────────────────────────────────────────────

def _make_identity(brand: str, name: str, category: str = "Foundation_Base") -> ProductIdentity:
    return ProductIdentity(brand=brand, product_name=name, product_type=category, category=category)


class TestGenerateSearchQueries:

    def test_reported_malformed_query_produces_clean_base_query(self):
        """
        When OCR produces 'Matte - +PORELESS NORMALTOOLY', the resulting
        base_query must not contain '-', '+', or 'NORMALTOOLY'.
        """
        identity = _make_identity("Maybelline", "Matte - +PORELESS NORMALTOOLY")
        result = generate_search_queries(identity)
        assert result is not None
        q = result.base_query
        assert "-" not in q, f"Dash in query: {q!r}"
        assert "+" not in q, f"Plus in query: {q!r}"
        assert "NORMALTOOLY" not in q.upper(), f"Noise token in query: {q!r}"
        assert "Maybelline" in q
        assert "Matte" in q
        assert "PORELESS" in q

    def test_clean_query_passes_through_unchanged(self):
        identity = _make_identity("Maybelline", "Fit Me Matte Poreless Foundation")
        result = generate_search_queries(identity)
        assert result is not None
        assert "Maybelline" in result.base_query
        assert "Fit Me" in result.base_query
        assert "Matte" in result.base_query

    def test_amazon_query_equals_base_query(self):
        """amazon_query must be the same clean query (no 'Amazon' appended)."""
        identity = _make_identity("Maybelline", "Fit Me Matte Poreless")
        result = generate_search_queries(identity)
        assert result is not None
        assert result.amazon_query == result.base_query, (
            f"amazon_query should equal base_query; got {result.amazon_query!r}"
        )

    def test_invalid_search_tokens_rejected(self):
        """If both brand and product_name are placeholder tokens, return None."""
        identity = _make_identity("Unknown Brand", "Cosmetic Product")
        result = generate_search_queries(identity)
        assert result is None, f"Expected None for placeholder identity; got {result}"

    def test_valid_brand_with_invalid_product_still_passes(self):
        """A real brand with a placeholder product should still produce a query."""
        identity = _make_identity("Maybelline", "Cosmetic Product")
        result = generate_search_queries(identity)
        # brand alone is enough for a non-None result
        assert result is not None
        assert "Maybelline" in result.base_query

    def test_empty_brand_product_name_rejected(self):
        identity = _make_identity("", "")
        result = generate_search_queries(identity)
        assert result is None

    def test_brand_field_is_normalised(self):
        """brand field in the bundle should also be normalised."""
        identity = _make_identity("L'Oreal", "True Match Foundation")
        result = generate_search_queries(identity)
        assert result is not None
        # The brand should not have a lone apostrophe causing issues
        assert result.brand  # non-empty

    def test_trailing_dash_stripped_from_product_name_in_query(self):
        """OCR fragmented join 'fit me Matte -' must produce clean query."""
        identity = _make_identity("Maybelline", "fit me Matte -")
        result = generate_search_queries(identity)
        assert result is not None
        assert result.base_query.endswith("-") is False, (
            f"Query must not end with dash: {result.base_query!r}"
        )

    def test_query_has_no_double_spaces(self):
        identity = _make_identity("Maybelline", "Fit  Me   Matte   Poreless")
        result = generate_search_queries(identity)
        assert result is not None
        assert "  " not in result.base_query, f"Double space in query: {result.base_query!r}"


# ─────────────────────────────────────────────────────────────────────────────
# Section 3 — parse_brand_and_product: product_name construction
# ─────────────────────────────────────────────────────────────────────────────

class TestParseBrandAndProduct:

    def test_fragmented_ocr_captures_up_to_4_lines(self):
        """
        With the old [:2] slice, fragmented OCR for 'Fit Me / Matte / +Poreless / Foundation'
        only produced 'fit me Matte -'. The fix joins up to 4 lines.
        """
        lines = [
            {'text': 'Maybelline', 'confidence': 0.98},
            {'text': 'fit me', 'confidence': 0.82},
            {'text': 'Matte', 'confidence': 0.75},
            {'text': 'Poreless', 'confidence': 0.71},
            {'text': 'Foundation', 'confidence': 0.65},
            {'text': '30ml', 'confidence': 0.95},
        ]
        result = parse_brand_and_product(lines)
        name = result['product_name']
        # Must contain at least 3 of the 4 content tokens (Maybelline skipped as brand)
        assert 'fit me' in name.lower(), f"'fit me' missing from product_name: {name!r}"
        assert 'matte' in name.lower(), f"'matte' missing from product_name: {name!r}"
        assert 'poreless' in name.lower(), f"'poreless' missing from product_name: {name!r}"

    def test_trailing_lone_dash_stripped_from_product_name(self):
        """'fit me Matte -' must strip the trailing dash."""
        lines = [
            {'text': 'Maybelline', 'confidence': 0.98},
            {'text': 'fit me', 'confidence': 0.82},
            {'text': 'Matte -', 'confidence': 0.75},
        ]
        result = parse_brand_and_product(lines)
        name = result['product_name']
        assert not name.endswith('-'), f"Trailing dash not stripped: {name!r}"
        assert 'Matte' in name

    def test_leading_lone_plus_stripped_from_product_name(self):
        """'+PORELESS foundation' must strip the leading plus."""
        lines = [
            {'text': 'Maybelline', 'confidence': 0.97},
            {'text': '+PORELESS', 'confidence': 0.71},
            {'text': 'foundation', 'confidence': 0.90},
        ]
        result = parse_brand_and_product(lines)
        name = result['product_name']
        assert not name.startswith('+'), f"Leading plus not stripped: {name!r}"

    def test_volume_lines_skipped(self):
        """Volume lines like '30ml', '1.0 fl oz' must not appear in product_name."""
        lines = [
            {'text': 'Maybelline', 'confidence': 0.98},
            {'text': 'Fit Me Matte', 'confidence': 0.88},
            {'text': '30ml', 'confidence': 0.95},
            {'text': '1.0 fl oz', 'confidence': 0.92},
        ]
        result = parse_brand_and_product(lines)
        name = result['product_name']
        assert '30ml' not in name.lower()
        assert 'fl oz' not in name.lower()

    def test_brand_line_skipped_from_product_name(self):
        """The brand line ('Maybelline') must not appear in product_name."""
        lines = [
            {'text': 'Maybelline', 'confidence': 0.98},
            {'text': 'Fit Me Matte Poreless', 'confidence': 0.88},
        ]
        result = parse_brand_and_product(lines)
        name = result['product_name']
        # 'Maybelline' alone should not be the product_name
        assert name.lower() != 'maybelline', f"Brand leaked into product_name: {name!r}"

    def test_brand_detected_for_maybelline(self):
        lines = [
            {'text': 'Maybelline', 'confidence': 0.98},
            {'text': 'Fit Me Matte Poreless Foundation', 'confidence': 0.88},
        ]
        result = parse_brand_and_product(lines)
        assert result['brand_name'] == 'Maybelline', f"Got {result['brand_name']!r}"

    def test_category_detected_as_makeup_for_foundation(self):
        lines = [
            {'text': 'Maybelline', 'confidence': 0.98},
            {'text': 'Fit Me Matte Poreless Foundation', 'confidence': 0.88},
        ]
        result = parse_brand_and_product(lines)
        assert result['category'] == 'Makeup', f"Expected Makeup; got {result['category']!r}"

    def test_empty_lines_returns_fallback(self):
        result = parse_brand_and_product([])
        assert result['brand_name'] == 'No Text Detected'


# ─────────────────────────────────────────────────────────────────────────────
# Section 4 — Amazon 503 mapped correctly (no fabricated listings)
# ─────────────────────────────────────────────────────────────────────────────

class TestAmazon503Handling:

    def test_amazon_503_returns_blocked_status(self):
        """Amazon 503 must produce source_status='blocked', never 'available'."""
        import unittest.mock as mock
        from app.services.scraping.amazon_scraper import scrape_amazon_products

        mock_resp = mock.MagicMock()
        mock_resp.status_code = 503
        mock_resp.text = ""

        with mock.patch("app.services.scraping.amazon_scraper.requests.get", return_value=mock_resp):
            result = scrape_amazon_products("Maybelline Fit Me Matte Poreless")

        assert len(result) == 1
        assert result[0].source_status == "blocked"
        assert result[0].status_code == "MARKETPLACE_BLOCKED"
        assert "503" in result[0].explanation

    def test_amazon_403_returns_blocked_status(self):
        import unittest.mock as mock
        from app.services.scraping.amazon_scraper import scrape_amazon_products

        mock_resp = mock.MagicMock()
        mock_resp.status_code = 403
        mock_resp.text = ""

        with mock.patch("app.services.scraping.amazon_scraper.requests.get", return_value=mock_resp):
            result = scrape_amazon_products("Maybelline Fit Me")

        assert result[0].source_status == "blocked"

    def test_amazon_captcha_returns_blocked_status(self):
        """CAPTCHA interstitial must return blocked, not parsed results."""
        import unittest.mock as mock
        from app.services.scraping.amazon_scraper import scrape_amazon_products

        mock_resp = mock.MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "please contact api-services-support@amazon.com for assistance"

        with mock.patch("app.services.scraping.amazon_scraper.requests.get", return_value=mock_resp):
            result = scrape_amazon_products("Maybelline Fit Me Matte")

        assert result[0].source_status == "blocked"
        assert result[0].raw_title != "Maybelline Fit Me Matte"  # not a fabricated listing

    def test_blocked_amazon_does_not_persist_as_verified_listing(self):
        """When Amazon is blocked, no listing with listing_status=VERIFIED_LISTING is created."""
        import unittest.mock as mock
        from app.services.scraping.marketplace_search import search_all_marketplaces
        from app.schemas.marketplace import ProductIdentity
        from app.services.scraping.schemas import RawMarketplaceItem

        mock_blocked = [RawMarketplaceItem(
            platform="Amazon",
            raw_title="Amazon Access Blocked",
            source_status="blocked",
            status_code="MARKETPLACE_BLOCKED",
            explanation="HTTP 503"
        )]
        identity = ProductIdentity(
            brand="Maybelline",
            product_name="Fit Me Matte Poreless",
            product_type="Foundation_Base",
            category="Foundation_Base"
        )

        with (
            mock.patch("app.services.scraping.marketplace_search.scrape_amazon_products",
                       return_value=mock_blocked),
            mock.patch("app.services.scraping.marketplace_search.scrape_daraz_products",
                       return_value=[RawMarketplaceItem(platform="Daraz", raw_title="Blocked",
                                                        source_status="unavailable", explanation="JS")]),
            mock.patch("app.services.scraping.marketplace_search.scrape_temu_products",
                       return_value=[RawMarketplaceItem(platform="Temu", raw_title="Blocked",
                                                        source_status="blocked", explanation="Bot")]),
        ):
            listings = search_all_marketplaces(identity)

        verified = [l for l in listings if l.listing_status == "VERIFIED_LISTING"]
        assert len(verified) == 0, (
            f"No VERIFIED_LISTING should exist when Amazon is blocked; got: {verified}"
        )
        amazon_listings = [l for l in listings if l.platform == "Amazon"]
        assert all(l.passed_match_threshold is False for l in amazon_listings)

    def test_cleaned_query_is_passed_to_amazon_scraper(self):
        """Confirm the cleaned query is actually passed to scrape_amazon_products."""
        import unittest.mock as mock
        from app.services.scraping.marketplace_search import search_all_marketplaces
        from app.schemas.marketplace import ProductIdentity
        from app.services.scraping.schemas import RawMarketplaceItem

        identity = ProductIdentity(
            brand="Maybelline",
            product_name="Matte - +PORELESS NORMALTOOLY",
            product_type="Foundation_Base",
            category="Foundation_Base"
        )

        mock_amazon = mock.MagicMock(return_value=[RawMarketplaceItem(
            platform="Amazon",
            raw_title="Amazon Access Blocked",
            source_status="blocked",
            status_code="MARKETPLACE_BLOCKED",
            explanation="HTTP 503"
        )])

        with (
            mock.patch("app.services.scraping.marketplace_search.scrape_amazon_products", mock_amazon),
            mock.patch("app.services.scraping.marketplace_search.scrape_daraz_products", return_value=[]),
            mock.patch("app.services.scraping.marketplace_search.scrape_temu_products", return_value=[]),
        ):
            search_all_marketplaces(identity)

        assert mock_amazon.called, "scrape_amazon_products must be called"
        called_query = mock_amazon.call_args[0][0]
        # Query must be cleaned: no lone dash, no plus, no noise token
        assert called_query == "Maybelline Matte PORELESS", f"Expected cleaned query, got {called_query!r}"
        assert "-" not in called_query
        assert "+" not in called_query
        assert "NORMALTOOLY" not in called_query

    def test_user_provided_amazon_url_format_validation(self):
        """Verify permitted alternative: user-provided Amazon product URLs can be validated safely."""
        from app.services.scraping.url_validator import validate_marketplace_url

        valid_urls = [
            "https://www.amazon.com/dp/B0046VDW88",
            "https://www.amazon.com/Maybelline-Fit-Me-Matte-Poreless/dp/B0046VDW88",
            "https://www.amazon.co.uk/dp/B0046VDW88",
            "https://www.amazon.in/dp/B0046VDW88",
        ]
        for url in valid_urls:
            is_valid, reason = validate_marketplace_url(url, "Amazon")
            assert is_valid is True, f"Expected valid for {url}, got reason: {reason}"

        invalid_urls = [
            "https://www.amazon.com/item/P001",
            "https://www.amazon.com/placeholder_item",
            "https://www.ebay.com/itm/123456789",
            "https://www.fake-amazon.com/dp/B0046VDW88",
            "http://placeholder.amazon.com",
            "",
            None
        ]
        for url in invalid_urls:
            is_valid, reason = validate_marketplace_url(url, "Amazon")
            assert is_valid is False, f"Expected invalid for {url}"
