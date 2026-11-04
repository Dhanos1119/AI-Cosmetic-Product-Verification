# Marketplace Integration Fix Report

**Date:** 2026-10-18  
**Scope:** End-to-end audit and remediation of Amazon, Daraz, and Temu marketplace integrations  
**Result:** All identified issues resolved. 84 tests pass (29 new, 55 existing), 0 failures.

---

## Executive Summary

A UI-visible end-to-end audit exposed a chain of issues in the marketplace scraping pipeline that caused:

- Every Amazon result card to emit *"Listing product URL 'None' is missing or invalid"*
- No verified product listings being persisted
- Daraz and Temu reporting misleading status labels
- Fabricated (hardcoded) rating and review-count values persisting in Daraz and Temu
- URL validation accepting look-alike domains (subdomain-confusion attack vector)

All six root causes were identified, traced through the full stack, and fixed without bypassing any anti-bot protections or inventing listing data.

---

## 1. Root-Cause Analysis

### 1.1 Amazon — "URL 'None' is missing or invalid" flood

**Observed symptom:** Every Amazon card in the UI reported  
`"Listing product URL 'None' is missing or invalid."` despite the scraper reporting `source_status = AVAILABLE`.

**Traced path:**
```
amazon_scraper.py -> marketplace_search.py -> url_validator.py
                                           -> persistence_service.py
                                           -> /api/analyze (JSON response)
                                           -> VerificationResult.tsx
```

**Root cause (primary):** Amazon's live search pages are served through Akamai's bot-management layer. When the scraper's `requests.get()` succeeded with HTTP 200, the page was actually an Akamai **bm-verify interstitial**, not search results. The old scraper:

1. Received HTTP 200 — so no blocked-status branch fired.
2. Parsed the interstitial — found zero `div[data-component-type="s-search-result"]` cards.
3. Returned `RawMarketplaceItem(source_status="unavailable", link=None)`.
4. `marketplace_search.py` called `validate_marketplace_url(None, "Amazon")` -> `INVALID_URL`.
5. The frontend rendered one error row per product query.

**Root cause (secondary):** The `h2 a[href]` CSS selector matched the legacy Amazon card markup. Current Amazon HTML wraps `<h2>` *inside* the anchor: `<a href="..."><h2><span>title</span></h2></a>`. The selector returned `None` for every card, so `link` was always `None`.

### 1.2 Daraz — Incorrect blocked vs NOT_RETRIEVABLE distinction

**Root cause:** Daraz's CDN-level JavaScript (Alibaba Baxia SDK: `window.baxiaCommon.init(...)`) is present on **every** Daraz page. A heuristic matching the substring `"baxia"` treated this as a CAPTCHA/block page, causing every Daraz response to report `blocked` / `MARKETPLACE_BLOCKED`. The correct state is `unavailable` / `NOT_RETRIEVABLE`.

**Additional issue:** Daraz card parsing assigned hardcoded `rating_val = 4.5` and `review_count_val = 12`.

### 1.3 Temu — verify substring false-positive

**Root cause:** The old block-detection heuristic checked `if "verify" in resp.text.lower()`. Normal Temu JavaScript pages include config keys such as `"verifyAuthToken"`. This caused every Temu HTTP 200 response to trigger `blocked` / `MARKETPLACE_BLOCKED`.

**Additional issue:** Temu cards were assigned hardcoded `rating_val = 4.2` and `review_count_val = 8`.

### 1.4 URL Validator — Subdomain look-alike bypass

**Root cause:** Domain validation used `str.endswith(allowed_domain)` on the full URL string. This accepted `https://www.amazon.com.evil.example/dp/B001FAKE` because the string ends with `"amazon.com"` as a substring.

### 1.5 Persistence gate — INVALID_URL listings reaching the DB layer

**Root cause:** `is_valid_listing_for_persistence()` checked `listing_status` but `None` product URL could still pass if `match_confidence` was above threshold. The URL check was not enforced as an unconditional gate before the confidence check.

### 1.6 Duplicate Amazon cards

**Root cause:** Same ASIN can appear in multiple Amazon search-result positions. Without capturing `data-asin` as `listing_id`, `upsert_marketplace_listing()` had no stable key to de-duplicate on and created new rows per scrape run.

---

## 2. Changes Made

### 2.1 amazon_scraper.py

| Change | Detail |
|--------|--------|
| Akamai bm-verify detection | Added `"bm-verify="` to BOT_CHALLENGE_MARKERS; checked before card iteration |
| extract_amazon_card_link() | New helper supporting legacy (h2 > a) and modern (a > h2 > span) markup |
| ASIN capture | data-asin extracted as listing_id for de-duplication |
| Seller removal | Selector captured unrelated text (Sponsored, etc.); seller is now always None |

### 2.2 daraz_scraper.py

| Change | Detail |
|--------|--------|
| Baxia false-positive removed | DARAZ_CHALLENGE_MARKERS now only matches explicit punish/slider CAPTCHA markers |
| SPA shell -> NOT_RETRIEVABLE | Empty #root container -> source_status="unavailable" / NOT_RETRIEVABLE |
| Hardcoded ratings removed | rating_val=0.0, review_count_val=0 (unknown) |
| NameError fixed | img_url referenced before assignment in one code path |

### 2.3 temu_scraper.py

| Change | Detail |
|--------|--------|
| verify substring heuristic replaced | Only "captcha" triggers a block |
| Client-rendered page -> NOT_RETRIEVABLE | No .product-item cards -> unavailable / NOT_RETRIEVABLE |
| Hardcoded ratings removed | rating_val=0.0, review_count_val=0 (unknown) |

### 2.4 url_validator.py

| Change | Detail |
|--------|--------|
| Strict hostname matching | Parses hostname via urllib.parse; checks host == allowed OR host.endswith("." + allowed) |

### 2.5 schemas.py

Added `listing_id` and `status_code` fields to `RawMarketplaceItem`.

### 2.6 persistence_service.py

- `is_valid_listing_for_persistence()`: product_url=None or listing_status="INVALID_URL" blocks persistence unconditionally
- `upsert_marketplace_listing()`: product_url used as upsert key; second write updates the existing row

---

## 3. Status Label Semantics (Post-Fix)

| source_status | status_code | Meaning |
|---------------|-------------|---------|
| available | (none) | Listing extracted with valid URL; eligible for persistence gate |
| unavailable | NOT_RETRIEVABLE | Service responded; JS-rendered shell — no listings extractable without JS |
| unavailable | NO_MATCH_FOUND | Service responded; no parseable product cards found |
| blocked | MARKETPLACE_BLOCKED | Anti-bot challenge page or blocking HTTP status (403/429/503). Not bypassed. |
| blocked | SCRAPER_ERROR | Network-level exception |

NOT_RETRIEVABLE is not the same as MARKETPLACE_BLOCKED. The former means the service is reachable and returns a valid page; the latter means the request was actively blocked.

---

## 4. What Was NOT Changed

In compliance with the stated constraints, the following were not modified:

- authenticity_status remains NOT_VALIDATED
- No listing URLs, prices, ratings, review counts, or sellers were fabricated or hardcoded
- Anti-bot protections were not bypassed or worked around
- No database records were deleted or reset
- Unrelated features (sentiment analysis, CLIP, review analysis) were untouched

---

## 5. Test Results

### 5.1 New tests — tests/test_marketplace_scraper_fixes.py

29 new tests added. All pass:

| # | Test | Result |
|---|------|--------|
| 1 | test_amazon_link_legacy_markup | PASS |
| 2 | test_amazon_link_modern_anchor_wraps_h2 | PASS |
| 3 | test_amazon_link_none_when_no_href | PASS |
| 4 | test_amazon_link_no_javascript_href | PASS |
| 5 | test_amazon_bm_verify_interstitial_reported_as_blocked | PASS |
| 6 | test_amazon_http_503_reported_as_blocked | PASS |
| 7 | test_amazon_200_empty_page_reported_as_unavailable | PASS |
| 8 | test_amazon_valid_cards_yield_valid_links_and_no_fabricated_sellers | PASS |
| 9 | test_amazon_asin_captured_as_listing_id | PASS |
| 10 | test_daraz_client_shell_reported_as_not_retrievable | PASS |
| 11 | test_daraz_captcha_punish_page_reported_as_blocked | PASS |
| 12 | test_daraz_no_hardcoded_ratings | PASS |
| 13 | test_daraz_baxia_sdk_alone_does_not_trigger_block | PASS |
| 14 | test_temu_verify_substring_no_longer_triggers_false_positive_block | PASS |
| 15 | test_temu_captcha_keyword_triggers_blocked | PASS |
| 16 | test_temu_client_rendered_page_reported_as_unavailable | PASS |
| 17 | test_temu_no_hardcoded_ratings | PASS |
| 18 | test_url_validator_rejects_lookalike_domain | PASS |
| 19 | test_url_validator_accepts_amazon_subdomain | PASS |
| 20 | test_url_validator_accepts_daraz_subdomain | PASS |
| 21 | test_url_validator_rejects_none_url | PASS |
| 22 | test_url_validator_rejects_placeholder_patterns | PASS |
| 23 | test_persistence_rejects_invalid_url_listing | PASS |
| 24 | test_persistence_rejects_none_url_even_with_high_match | PASS |
| 25 | test_persistence_accepts_valid_url_listing | PASS |
| 26 | test_duplicate_asin_upserted_not_duplicated | PASS |
| 27 | test_amazon_status_labels_are_mutually_exclusive | PASS |
| 28 | test_daraz_status_labels_mutually_exclusive | PASS |
| 29 | test_temu_status_labels_mutually_exclusive | PASS |

### 5.2 Existing regression suite — 55 tests, 0 regressions

| Test file | Tests | Result |
|-----------|-------|--------|
| test_marketplace_url_validation.py | 10 | All pass |
| test_marketplace_persistence.py | 8 | All pass |
| test_marketplace_integrity_audit.py | 10 | All pass |
| test_phase6_matching_evidence_quality.py | 8 | All pass |
| test_database_persistence.py | 10 | All pass |
| test_review_analysis.py | 9 | All pass |

**Total: 84 tests, 0 failures, 0 regressions.**

---

## 6. Remaining Known Limitations

The following cannot be resolved without violating platform terms of service or bypassing authentication:

| Marketplace | Constraint | Status reported |
|-------------|------------|----------------|
| Amazon | Akamai bot-management blocks raw requests on most IPs | MARKETPLACE_BLOCKED |
| Daraz | Full catalog is JavaScript-rendered (React SPA) | NOT_RETRIEVABLE |
| Temu | Requires app-token authentication and JS execution | NOT_RETRIEVABLE |

These statuses are now accurately reported in the API response and frontend UI. No false AVAILABLE status is emitted when real listings cannot be retrieved.

---

## 7. Files Modified

| File | Nature of change |
|------|-----------------|
| ai-service/app/services/scraping/schemas.py | Added listing_id, status_code fields to RawMarketplaceItem |
| ai-service/app/services/scraping/amazon_scraper.py | bm-verify detection, modern-markup link extraction, ASIN capture, seller removal |
| ai-service/app/services/scraping/daraz_scraper.py | Baxia false-positive removed, NOT_RETRIEVABLE status, hardcoded ratings removed, NameError fixed |
| ai-service/app/services/scraping/temu_scraper.py | verify false-positive replaced, hardcoded ratings removed |
| ai-service/app/services/scraping/url_validator.py | Strict hostname matching |
| tests/test_marketplace_scraper_fixes.py | 29 new tests |
