# Marketplace Scraping Audit & Implementation Status Report

**Date:** 2026-10-18  
**Project:** AI-Based Cosmetic Product Verification  
**Scope:** Amazon, Daraz, and Temu marketplace adapters, structured data (JSON-LD) extraction, headless browser (Playwright) evaluation, user product URL scraping, data integrity guardrails, and test verification.  
**Status:** Audit complete. Implementations, safeguards, and 131 automated tests verified.

---

## Executive Summary

| Platform / Component | Status | Permitted Extraction Method | Findings & Safeguards |
|---|---|---|---|
| **Amazon (Search Scraper)** | ❌ Blocked | None without API credentials | Returns HTTP 503 (Akamai Bot Manager WAF). Request headers/User-Agents do not bypass this; mapped to `MARKETPLACE_BLOCKED`. |
| **Amazon (Official API)** | ⏳ Permitted | Amazon PA-API 5.0 (Creators API) | Requires Amazon Associates approval + 10 qualifying sales / 30 days. Provides verified product titles, prices, images, and ASINs. |
| **Daraz (Search Scraper)** | ⚠️ Not Retrievable | None via plain server HTML | Returns a client-rendered SPA shell (`<div id="root"></div>`) without product cards in server HTML. Mapped cleanly to `NOT_RETRIEVABLE`. |
| **Daraz (Direct Product URL)** | ✅ Implemented | Embedded state + Public Review API | Extracts real price (e.g. Rs. 5,490), currency (LKR), brand, and title from embedded state (`pdpTrackingData` / `__moduleData__`), and ratings/reviews from the public PDP review endpoint without anti-bot bypass. |
| **Daraz (Official API)** | ⏳ Permitted | Daraz Open Platform (Alibaba Open API) | Developer registration & API credentials required. |
| **Temu (Search Scraper)** | ⚠️ Not Retrievable | None via plain server HTML | Client-side dynamic application requiring obfuscated device session tokens (`_x_sessn`). Returns empty shell; mapped to `NOT_RETRIEVABLE`. |
| **Temu (Official API)** | ⏳ Permitted | Temu Affiliate / Partner Open API | Developer application required. |
| **Structured Data (JSON-LD)** | ✅ Implemented | schema.org Product metadata | Extracts title, brand, price, currency, aggregate rating, review count, and actual customer reviews from `<script type="application/ld+json">`. |
| **HTML Selectors Fallback** | ✅ Implemented | Robust multi-selector parsing | Prioritizes JSON-LD, falls back to platform-tailored and OpenGraph HTML selectors. Extracts only fields actually present. |
| **User-Submitted Product URLs** | ✅ Implemented | `scrape_user_product_url()` | Validates hostname, verifies redirect safety (anti-SSRF), extracts real metadata, and returns accurate operational statuses. |
| **Integrity & Ranking Safeguards** | ✅ Implemented | Data completeness gating | Ranking scores are **suppressed** (`total_score=0.0, rank=99`) when live ratings/reviews are unavailable. Zero fake data persisted. |
| **Review Sentiment vs Authenticity**| ✅ Preserved | Strict concern separation | Sentiment analysis (rating-derived baseline) is separated from review authenticity (`NOT_VALIDATED`). Packaging similarity is never equated to product genuineness. |

---

## 1. Platform-by-Platform Audit & Capabilities Matrix

### 1.1 Amazon
* **Automated HTML Scraping Reality:**  
  Amazon protects `/s?k=` and product detail endpoints using Akamai Bot Manager and AWS WAF. HTTP requests from standard clients return **HTTP 503 Service Unavailable** (or interstitial challenge bodies containing `api-services-support@amazon.com` or CAPTCHA). This occurs identically on malformed and clean queries because the transport layer (TLS fingerprint, lack of browser JS/session cookies) is flagged prior to query execution.
* **Legally & Technically Permitted Approach:**  
  1. **Amazon Product Advertising API (PA-API 5.0):**  
     Provides signed REST calls returning canonical titles, brands, prices, images, ratings, and ASINs. Requires an active Amazon Associates account.
  2. **User-Provided Product URL:**  
     Users can paste an authentic product link (`https://www.amazon.com/dp/B0046VIZ9A`). The app validates domain format and structure safely.
* **Extraction Capabilities When Page Is Accessible:**
  * Title: `#productTitle`, `h1#title`, schema.org `name`
  * Brand: `#bylineInfo`, schema.org `brand.name`
  * Price: `.a-price .a-offscreen`, `#priceblock_ourprice`, schema.org `offers.price`
  * Aggregate Rating: `#acrPopover span.a-icon-alt`, schema.org `aggregateRating.ratingValue`
  * Review Count: `#acrCustomerReviewText`, schema.org `aggregateRating.reviewCount`
  * Customer Reviews: `div[data-hook="review"]`, schema.org `review` array

### 1.2 Daraz
* **Automated HTML Scraping Reality:**  
  Daraz (Alibaba Group) renders product catalogs dynamically using client-side JavaScript. The initial search catalog response contains an empty shell container (`<div id="root"></div>`) with script bundles. Automated requests to search also trigger Alibaba SecOps verification (`x5secdata`, `/_____tmd_____/punish`, slider challenges).
* **Legally & Technically Permitted Approach:**  
  1. **Direct Product URL Scraper (`scrape_user_product_url`):**  
     On individual product pages (PDP), Daraz embeds tracking and product-state JSON within the server HTML (`pdpTrackingData` and `__moduleData__`). Furthermore, real customer ratings and written review comments are accessible via Daraz's public review endpoint (`https://my.daraz.<tld>/pdp/review/getReviewList?itemId=...`) without requiring authentication, cookies, or bypass techniques.
  2. **Daraz Open Platform:** Official API suite for catalog and order management.
* **Extraction Capabilities When Page Is Accessible:**
  * Title: `pdpTrackingData.pdt_name`, schema.org `name`, `.pdp-mod-product-badge-title`
  * Price: `pdpTrackingData.pdt_price` (e.g. `Rs. 5,490` -> `5490.0`), `__moduleData__.data.root.fields.tracking.pdt_price`
  * Currency: `pdpTrackingData.core.currencyCode` (`LKR` supported by locale/page evidence; never defaulted to USD)
  * Brand: `pdpTrackingData.brand_name` (e.g. `No Brand`)
  * Aggregate Rating: `model.ratings.average` (e.g. `5.0`)
  * Rating Count: `model.ratings.rateCount` (e.g. `1`)
  * Written Review Count: `model.ratings.reviewCount` (e.g. `1`, accurately distinguished from rating count)
  * Actual Customer Reviews: `model.items` array with `reviewContent`, `buyerName`, `reviewTime`, `gradeItems.PRODUCT_REVIEW`

### 1.3 Temu
* **Automated HTML Scraping Reality:**  
  Temu catalog search is a single-page application requiring encrypted client token signatures (`_x_sessn`, `anti_token`). Plain HTTP GET requests yield no product cards in server HTML (`status_code="NOT_RETRIEVABLE"`).
* **Legally & Technically Permitted Approach:**  
  Temu Affiliate / Open Platform API.
* **Extraction Capabilities When Page Is Accessible:**
  * Title: `.goods-title`, schema.org `name`
  * Price: `.goods-price`, schema.org `offers.price`
  * Seller: `.merchant-name`

---

## 2. Browser-Rendering (Playwright) Evaluation

In accordance with Task 4, a standard browser-rendering approach (e.g., Playwright) was evaluated strictly within legal, contractual, and technical boundaries:

| Dimension | Evaluation Finding |
|---|---|
| **Terms of Service Compliance** | **Amazon:** Section "License and Access" explicitly prohibits "any use of data mining, robots, or similar data gathering and extraction tools."<br>**Daraz & Temu:** Terms strictly prohibit automated access and scraping without written authorization. |
| **Anti-Bot & Access Restrictions** | Akamai Bot Manager and Alibaba SecOps inspect headless browser environments (CDP runtime detection, `navigator.webdriver`, canvas/WebGL fingerprinting, JA3/JA4 TLS signatures). Standard Playwright without bypass tactics is still intercepted and served CAPTCHA/slider challenges. |
| **No-Bypass Policy Adherence** | Project guidelines strictly state: *Do not bypass CAPTCHA, anti-bot protections, or access controls.* Attempting to evade or solve challenges with stealth plugins would directly violate access terms. |
| **Resource Overhead** | Running headless Chromium instances requires 150–300 MB RAM per worker, introduces binary dependencies, and inflates request latency by 2–5 seconds per call. |
| **Architectural Conclusion** | **Playwright should NOT be deployed for scraping Amazon, Daraz, or Temu search endpoints.** It increases cost and resource usage without overcoming the fundamental anti-bot access restrictions, and would breach platform terms. The compliant path is using supported product APIs and user-provided URLs. |

---

## 3. Implementation Details

### 3.1 Metadata Extractor (`app/services/scraping/metadata_extractor.py`)
* Extracts schema.org `Product`, `IndividualProduct`, and `@graph` JSON-LD structures.
* Safely parses numeric prices (handling currency prefixes such as `Rs.`, `$`, `LKR`), ratings, and review counts.
* Extracts real customer review text (author, rating, comment text, date) when present in page markup.
* Evaluates data completeness into clear status codes:
  * `SUCCESS`: Product title, price, and rating/reviews are retrieved.
  * `PARTIAL_DATA`: Product title is present, but ratings, reviews, or price are missing.
  * `UNAVAILABLE`: Page contained no usable product title or data in server HTML.

### 3.2 User-Submitted Product URL Scraper (`app/services/scraping/url_scraper.py`)
* **Host & Protocol Validation:** Validates that URLs use `http://` or `https://` and match known marketplace hostnames (`VALID_DOMAINS` in `url_validator.py`). Rejects internal placeholder patterns (`/item/P001`, `no_daraz`, etc.).
* **Safe Redirect Handling:** Inspects `response.history` to verify that any redirects remain strictly within the authorized marketplace domain, protecting against open-redirect and SSRF vulnerabilities.
* **Anti-Bot Challenge Detection:** Checks for HTTP 403/503/429 and challenge markers (`api-services-support@amazon.com`, `bm-verify=`, Daraz `punish`, Temu `captcha`) and returns `MARKETPLACE_BLOCKED` without attempting evasion.
* **Exposed Endpoints:**
  * AI Service: `POST /api/marketplace/scrape-url` accepting `{"url": "...", "platform": "..."}`
  * Express Gateway: `POST /api/upload` forwarding `product_url` form-data field to FastAPI `:8001/api/analyze`.

### 3.3 Marketplace Ranking Safeguard (`app/services/marketplace_comparison_service.py`)
* **Task 8 Compliance:** In `calculate_platform_score()`, if a listing is available and matched but lacks real rating and review data (`rating == 0.0` and `review_count == 0` and no reviews):
  * `total_score = 0.0`
  * `rank = 99`
  * `recommendation_reason = "Data unavailable: Live marketplace ratings and reviews are required to generate recommendation ranking scores but are unavailable."`
* Such listings are appended as unranked and are **never** presented as active recommendations.

### 3.4 Review Sentiment & Authenticity Independence
* [`review_analysis_service.py`](file:///c:/Users/Dhanoshigan%20Ratnaraj/AI-Cosmetic-Product-Verification/ai-service/app/services/review_analysis_service.py) preserves strict separation between sentiment and authenticity:
  * **Sentiment Analysis:** Predicts positive, neutral, or negative sentiment for actual review text using a trained model.
  * **Review Authenticity:** Remains `NOT_VALIDATED` because no independently labeled real-world review authenticity dataset exists.
  * **Packaging Similarity:** Visual similarity (CLIP) and OCR confidence measure packaging appearance, never physical product genuineness.

---

## 4. Automated Test Results

The test suite covers all required edge cases, error conditions, and status codes.

```
============================== test session starts ==============================
tests\test_marketplace_scraping_improvements.py ............             [  9%]
tests\test_ocr_query_normalisation.py .................................... [ 36%]
tests\test_marketplace_scraper_fixes.py .............................    [ 58%]
tests\test_marketplace_url_validation.py ........                        [ 64%]
tests\test_phase6_matching_evidence_quality.py ........                  [ 70%]
tests\test_marketplace_integrity_audit.py ..........                     [ 78%]
tests\test_marketplace_persistence.py ..........                         [ 86%]
tests\test_critical_manual_test_findings.py ..................           [100%]

============================ 131 passed in 28.93s =============================
```

### Coverage Highlights in `test_marketplace_scraping_improvements.py`
1. `test_json_ld_full_product_extraction`: Parses complete Product, Offer, AggregateRating, and Customer Reviews from JSON-LD (`SUCCESS`).
2. `test_json_ld_graph_format_extraction`: Extracts Product entity inside `@graph` schema arrays.
3. `test_html_accessible_product_page_extraction`: Fallback HTML selector extraction when JSON-LD is absent.
4. `test_missing_fields_partial_data_status`: Validates `PARTIAL_DATA` status when ratings/reviews are missing.
5. `test_javascript_only_empty_shell`: Validates `UNAVAILABLE` status on unrendered SPA containers.
6. `test_invalid_urls_rejected`: Validates rejection of placeholder URLs and mismatched domains (`INVALID_URL`).
7. `test_safe_redirect_validation`: Confirms internal redirects are accepted while external domain hops are rejected.
8. `test_http_503_anti_bot_response`: Confirms HTTP 503 is cleanly mapped to `MARKETPLACE_BLOCKED`.
9. `test_captcha_and_challenge_markers_detection`: Confirms bot challenge markers are detected and not bypassed.
10. `test_ranking_scores_suppressed_when_real_data_unavailable`: Validates `total_score=0.0` and `rank=99` when ratings/reviews are unavailable.
11. `test_ranking_scores_calculated_when_real_data_is_available`: Validates normal platform scoring when authentic rating/reviews exist.
12. `test_user_product_url_integration_in_search_all_marketplaces`: End-to-end integration test verifying user URLs are scraped and matched in `search_all_marketplaces`.

---

## 5. Step-by-Step Manual Verification Guide

### Step 1: Run Automated Verification Suite
Open PowerShell in the project root:
```powershell
$env:PYTHONPATH="ai-service;database;."
.\ai-service\venv\Scripts\pytest.exe tests/test_marketplace_scraping_improvements.py -v
```
**Expected Result:** 12 passed in < 1s.

### Step 2: Test User-Submitted URL Endpoint Directly
With the FastAPI AI service running on port 8001:

#### Case A: Test a valid Daraz product URL (Maybelline Fit Me Foundation)
```powershell
Invoke-RestMethod -Uri "http://localhost:8001/api/marketplace/scrape-url" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"url": "https://www.daraz.lk/products/maybelline-new-york-liquid-foundation-matte-finish-with-spf-absorbs-oil-fit-me-matte-poreless-128-warm-nude-30-ml-from-indiasam-i204252780-s1298331553.html"}' | ConvertTo-Json -Depth 5
```
**Expected Result:**
```json
{
  "success": true,
  "data": {
    "platform": "Daraz",
    "raw_title": "Maybelline New York Liquid Foundation, Matte Finish, With SPF, Absorbs Oil, Fit Me Matte + Poreless, 128 Warm Nude, 30 ml FROM INDIA(SAM)",
    "brand": "No Brand",
    "price_str": "Rs. 5,490",
    "price_val": 5490.0,
    "currency": "LKR",
    "rating_val": 5.0,
    "rating_count_val": 1,
    "review_count_val": 1,
    "status_code": "SUCCESS",
    "reviews": [
      {
        "author": "nadheesha1990",
        "rating": 5.0,
        "comment": "nice shade \nMatt finish  ",
        "date": "14 Nov 2025",
        "verified_purchase": true
      }
    ]
  }
}
```

#### Case B: Test an Amazon product URL (Akamai 503 protection detected)
```powershell
Invoke-RestMethod -Uri "http://localhost:8001/api/marketplace/scrape-url" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"url": "https://www.amazon.com/dp/B0046VIZ9A", "platform": "Amazon"}'
```
**Expected Result:**
```json
{
  "success": true,
  "data": {
    "platform": "Amazon",
    "raw_title": "Amazon Access Blocked",
    "source_status": "blocked",
    "status_code": "MARKETPLACE_BLOCKED",
    "explanation": "Amazon returned HTTP 503 anti-bot protection. Live product data is unavailable.",
    "link": "https://www.amazon.com/dp/B0046VIZ9A"
  }
}
```

### Step 3: Test Invalid URL Rejection
```powershell
Invoke-RestMethod -Uri "http://localhost:8001/api/marketplace/scrape-url" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"url": "https://www.amazon.com/item/P001", "platform": "Amazon"}'
```
**Expected Result:**
```json
{
  "success": true,
  "data": {
    "platform": "Amazon",
    "raw_title": "Invalid Product URL",
    "source_status": "unavailable",
    "status_code": "INVALID_URL",
    "explanation": "Product URL rejected: URL contains invalid placeholder pattern '/item/p0'"
  }
}
```

### Step 4: Verify Database Persistence Guard
Check PostgreSQL database records to confirm no placeholder or blocked listings are saved:
```powershell
.\ai-service\venv\Scripts\python.exe -c "from database.connection import engine; from sqlalchemy import text; 
with engine.connect() as conn:
    res = conn.execute(text('SELECT platform_code, raw_title, listing_status, source_status FROM marketplace_listings;')).fetchall();
    print('Total Listings in DB:', len(res));
    for r in res: print(r)"
```
**Expected Result:** Only valid, verified listings with real URLs and evidence are stored; zero `MARKETPLACE_BLOCKED` or placeholder listings exist in the database.
