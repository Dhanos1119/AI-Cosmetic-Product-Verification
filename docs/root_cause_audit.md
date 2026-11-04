# Live System Root Cause Audit & Technical Investigation Report

**Audit Date:** 2026-10-31  
**Project:** AI-Based Cosmetic Product Verification and Marketplace Review Analysis System  
**Auditor:** Antigravity AI  
**Scope:** Live workflow investigation from image upload through FastAPI, OCR, CLIP matching, database persistence, marketplace scraping, review extraction, and sentiment analysis.  
**Constraint Enforced:** Strict audit mode — zero application code changes made prior to user review.

---

## Executive Summary

A comprehensive forensic trace across the Next.js frontend (port 3000), Express gateway (port 5000), FastAPI AI service (port 8001), PostgreSQL database, and external marketplace endpoints was conducted. Three critical issues reported by the user were reproduced with empirical logs:

1. **Maybelline Fit Me foundation misidentification:** The 1-NN reference bank and catalog contain **only 30 products (P001–P030)**; Maybelline Fit Me is **completely absent from the dataset and reference bank**. Concurrently, packaging OCR failed to detect the faint/stylized "Maybelline" text and misclassified the first cosmetic attribute token `"MATTE"` as the brand name (`brand_name: "Matte"`), while CLIP matched visually closest bottles (P011 Fenty, P001 Colourpop) with a tiny discrimination margin (0.53%), correctly triggering a category mismatch / low-confidence fallback.
2. **Amazon, Daraz, and Temu automatic searches returning no listings:** Plain HTTP GET scrapers cannot retrieve search-result cards from external marketplaces due to **genuine external anti-bot and client-side rendering restrictions**: Amazon returns HTTP 503 / Akamai bot verification; Daraz search (`/catalog/?q=...`) serves an empty React client shell (`<div id="root"></div>`); Temu serves a JavaScript-only shell requiring device-fingerprint tokens. Furthermore, because OCR detected brand `"Matte"` and product `"PORELESS NORMALTOOLY FOUNDATION 130"`, any automated query was malformed.
3. **Absence of real reviews and live sentiment analysis:** Review extraction is strictly gated on having real marketplace listings. When automated searches return blocked/unavailable status, `listing.reviews` is empty (`[]`). To preserve empirical integrity, sentiment analysis refuses to fabricate reviews and accurately returns `"Not available (no actual review text)"`. When a direct product URL *is* supplied, direct scraping works (extracting actual Daraz reviews and computing positive sentiment), but the frontend has **no post-verification URL input field in the results dashboard**, and Express **lacks a route to proxy the standalone `/api/marketplace/scrape-url` endpoint**.

---

## Part 1: Confirmed Root Causes & Empirical Evidence

### Issue 1: Maybelline Fit Me Foundation Misidentification

#### 1.1 Empirical Reproduction
- **Uploaded File:** `backend/uploads/fitme-1793389836878-568858284.png` (111,318 bytes, uploaded in the live application).
- **Execution Run:** Diagnosed via [scratch/diagnose_fit_me_live.py](file:///c:/Users/Dhanoshigan%20Ratnaraj/AI-Cosmetic-Product-Verification/scratch/diagnose_fit_me_live.py).

#### 1.2 Step-by-Step Pipeline Trace & Top 5 Candidates
1. **OCR Extraction ([ocr_service.py](file:///c:/Users/Dhanoshigan%20Ratnaraj/AI-Cosmetic-Product-Verification/ai-service/app/services/ocr_service.py#L165-L245)):**
   - Engine used: `RapidOCR ONNX Engine`
   - Raw detected text lines: `['MATTE', '+PORELESS', 'NORMALTOOLY', 'FOUNDATION', '130']`
   - Extracted brand: `"Matte"` *(Bug: `parse_brand_and_product` took the first non-filtered token since "Maybelline" was not detected)*
   - Extracted product name: `"PORELESS NORMALTOOLY FOUNDATION 130"`
   - Extracted category: `"Makeup"` (Confidence: `0.82`)
2. **CLIP 1-NN Reference Bank Matching ([clip_service.py](file:///c:/Users/Dhanoshigan%20Ratnaraj/AI-Cosmetic-Product-Verification/ai-service/app/services/clip_service.py#L352-L460)):**
   - Reference bank source: `models/clip_reference_bank/product_id_map.json` and `data/clip_reference_embeddings.npz` (1,340 vectors across 30 products).
   - Top 5 Nearest Neighbors:
     - **Rank 1:** `P011` — `fenty` | `MATCH STIX - Matte Skinstick` (`Foundation_Base`) -> Cosine Sim: `0.7193` (71.9%)
     - **Rank 2:** `P001` — `colourpop` | `Lippie Pencil` (`Lip_Products`) -> Cosine Sim: `0.7140` (71.4%)
     - **Rank 3:** `P009` — `rejuva minerals` | `Pressed Powder Foundation` (`Foundation_Base`) -> Cosine Sim: `0.7065` (70.7%)
     - **Rank 4:** `P008` — `w3llpeople` | `Realist Invisible Setting Powder` (`Foundation_Base`) -> Cosine Sim: `0.7009` (70.1%)
     - **Rank 5:** `P012` — `clinique` | `Even Better Compact Makeup Broad Spectrum SPF 15` (`Foundation_Base`) -> Cosine Sim: `0.6990` (69.9%)
3. **Discrimination Margin & Brand Boost:**
   - Rank-1 to Rank-2 margin: `0.7193 - 0.7140 = 0.0053` (**0.53%**).
   - System threshold: `_MIN_DISCRIMINATION_MARGIN = 0.02` (**2.00%**).
   - Discrimination check: **FAILED** (`poor_discrimination = True`).
   - Brand boost: `0.00` boost applied because detected brand `"Matte"` does not match catalog brands (`colourpop`, `fenty`, `deciem`, etc.).
4. **Category Mismatch Filtering:**
   - OCR category: `"Makeup"`
   - CLIP top-candidate category: `"Foundation_Base"`
   - Catalog category mismatch: `True` (`"makeup"` not in `"foundation_base"`).
5. **Final Output State:**
   - `match_status`: `"Low-Confidence / Catalog Mismatch"`
   - `confidence_level`: `"Low"`
   - `best_match`: `None`
   - In [product_service.py](file:///c:/Users/Dhanoshigan%20Ratnaraj/AI-Cosmetic-Product-Verification/ai-service/app/services/product_service.py#L65-L87), because `has_reliable_clip` is `False`, the system fell back to the raw OCR identity: `brand: "Matte"`, `product_name: "PORELESS NORMALTOOLY FOUNDATION 130"`, `product_id: None`.

#### 1.3 Confirmed Root Cause
- **Absence from Reference Bank:** The 30 products in `selected_30_products_final.csv` and `data/clip_reference_embeddings.npz` are strictly `P001` to `P030`. **Maybelline Fit Me foundation does not exist anywhere in the catalog or reference bank.** A 1-NN classifier cannot predict a class that is absent from its reference set.
- **OCR Fallback Heuristic Flaw:** In `ocr_service.py` (`parse_brand_and_product`), when packaging text does not match `KNOWN_BRANDS`, line 144 falls back to `clean_lines[0][0]`, promoting the cosmetic finish term `"MATTE"` to the brand name.

---

### Issue 2: Automatic Marketplace Searches Return No Listings

#### 2.1 Empirical Evidence from Scraper Execution
Tested directly using [scratch/test_marketplace_queries.py](file:///c:/Users/Dhanoshigan%20Ratnaraj/AI-Cosmetic-Product-Verification/scratch/test_marketplace_queries.py) with the query `"Maybelline Fit Me Foundation"`:
- **Amazon ([amazon_scraper.py](file:///c:/Users/Dhanoshigan%20Ratnaraj/AI-Cosmetic-Product-Verification/ai-service/app/services/scraping/amazon_scraper.py#L63-L70)):**
  - Result: `status=blocked`, `code=MARKETPLACE_BLOCKED`
  - Explanation: `Amazon returned HTTP 503 anti-bot protection. Real-time listing data unavailable.`
  - Amazon uses Akamai Bot Manager and automated IP rate-limiting that unconditionally challenges plain HTTP GET requests.
- **Daraz ([daraz_scraper.py](file:///c:/Users/Dhanoshigan%20Ratnaraj/AI-Cosmetic-Product-Verification/ai-service/app/services/scraping/daraz_scraper.py#L55-L60)):**
  - Result: `status=unavailable`, `code=NOT_RETRIEVABLE`
  - Explanation: `Daraz search endpoint responded (HTTP 200) but the page is a client-side JavaScript application shell (empty #root container) with no product cards in the server HTML.`
  - Daraz search results (`https://www.daraz.lk/catalog/?q=...`) are rendered client-side via React. BeautifulSoup receives only the empty shell `<div id="root"></div>`.
- **Temu ([temu_scraper.py](file:///c:/Users/Dhanoshigan%20Ratnaraj/AI-Cosmetic-Product-Verification/ai-service/app/services/scraping/temu_scraper.py#L52-L60)):**
  - Result: `status=unavailable`, `code=NOT_RETRIEVABLE`
  - Explanation: `Temu search endpoint responded (HTTP 200) with a client-rendered page containing no product data in the server HTML.`
  - Temu requires dynamic JavaScript execution and cryptographic device token verification (`verifyAuthToken`).

#### 2.2 Query Degradation Bug
- In `marketplace_search.py` (`generate_search_queries`), queries are generated as `f"{brand} {product_name}"`.
- Because OCR identified `brand = "Matte"` and `product_name = "PORELESS NORMALTOOLY FOUNDATION 130"`, the query generated was:
  `"Matte PORELESS FOUNDATION 130"`
- Even on platforms without anti-bot blocking, searching for `"Matte PORELESS FOUNDATION 130"` produces 0 relevant cosmetic results because the true brand `"Maybelline"` and product name `"Fit Me"` were omitted.

---

### Issue 3: Real Reviews Not Displayed & Sentiment Analysis Inaccessible

#### 3.1 Empirical Trace of Direct Marketplace URL Scraper
Tested using [scratch/test_upload_with_url.py](file:///c:/Users/Dhanoshigan%20Ratnaraj/AI-Cosmetic-Product-Verification/scratch/test_upload_with_url.py) by passing a valid Daraz product URL (`https://www.daraz.lk/products/maybelline-new-york-liquid-foundation...html`):
- **Direct Scraper Output:**
  - `status_code`: `200`
  - `listing_status`: `VERIFIED_LISTING` (`source_status: available`)
  - `price`: `5490 LKR`
  - `reviews_count`: `1`
  - Review collected: `author: "nadheesha1990"`, `rating: 5`, `comment: "nice shade \nMatt finish"`, `verified_purchase: true`
  - Sentiment model output: `sentiment_label: "Positive"`, `confidence: 0.8459`
  - Persisted to PostgreSQL: `CustomerReview ID: 0d574e98-cc76-4bdc-bf5a-9c84cd9a0b6a`
- **Conclusion:** The direct marketplace URL scraper (`scrape_user_product_url`) **works correctly and extracts real reviews and live sentiment**.

#### 3.2 Where Data is Disconnected in the Live Workflow
1. **Frontend Disconnect ([VerificationWorkspace.tsx](file:///c:/Users/Dhanoshigan%20Ratnaraj/AI-Cosmetic-Product-Verification/frontend/components/VerificationWorkspace.tsx#L148-L170) & [VerificationResult.tsx](file:///c:/Users/Dhanoshigan%20Ratnaraj/AI-Cosmetic-Product-Verification/frontend/components/VerificationResult.tsx#L659-L666)):**
   - The user interface only provides the `Direct Marketplace Product URL` input field on the **initial upload form**.
   - When users upload an image without entering a URL upfront (expecting automated search to find listings), the system completes analysis and renders `VerificationResult.tsx`.
   - In `VerificationResult.tsx` (Section 3), the UI states:
     > *"No Verified Product Listings Returned... You can supply an exact product link in the workspace above."*
   - **Crucial UI Defect:** There is **no input field or submit button** in `VerificationResult.tsx` allowing the user to paste a URL and trigger extraction! The workspace is hidden (`hasVerified === true`). The user's only recourse is "Reset Verification", which erases the uploaded image and analysis state.
2. **Missing Express Proxy Route ([backend/src/routes/uploadRoutes.js](file:///c:/Users/Dhanoshigan%20Ratnaraj/AI-Cosmetic-Product-Verification/backend/src/routes/uploadRoutes.js)):**
   - FastAPI implements `POST /api/marketplace/scrape-url` in [analysis.py](file:///c:/Users/Dhanoshigan%20Ratnaraj/AI-Cosmetic-Product-Verification/ai-service/app/routes/analysis.py#L159-L175).
   - Express gateway (`backend/src/`) contains **zero routes** mapping to `/api/marketplace/scrape-url`. A standalone URL extraction call from the frontend cannot reach the AI service through the gateway.
3. **Data Loss Chain When Automated Search Fails:**
   - Automated scrapers return `source_status: blocked` / `unavailable`.
   - `marketplace_listings` contains no items with `reviews`.
   - In `product_service.py` (lines 111–131), `real_reviews = []`.
   - `build_marketplace_sentiment` receives an empty list and returns `analyzed_count: 0`.
   - In `VerificationResult.tsx`:
     - Section 3 (`validListings` filter at lines 258–268) filters out blocked listings, resulting in `validListings.length === 0`.
     - Section 4 (`allCustomerReviews` at lines 282–285) receives `[]` and displays `Collected: 0 Real Review(s)`.
     - Section 5 displays `Sentiment: Not available (no actual review text)`.

---

## Part 2: Exact Files, Functions, and Line Numbers Responsible

| Component | File | Function / Location | Responsibility / Defect |
|---|---|---|---|
| **Catalog & Reference Bank** | `data/selected_30_products_final.csv`<br>`models/clip_reference_bank/product_id_map.json` | Catalog definitions | Maybelline Fit Me foundation is not present in the 30-product catalog. Only P001–P030 exist. |
| **OCR Brand Fallback** | `ai-service/app/services/ocr_service.py` | `parse_brand_and_product` (Lines 140–160) | Fallback logic assigns `clean_lines[0][0]` as `brand_name`, turning `"MATTE"` into a brand. Also `"Maybelline"` is in `KNOWN_BRANDS` but OCR failed to extract it from low-contrast packaging. |
| **Query Normalization** | `ai-service/app/services/scraping/marketplace_search.py` | `generate_search_queries` (Lines 60–91) | Generates queries using unvalidated OCR brand name, yielding `"Matte PORELESS FOUNDATION 130"`. |
| **Marketplace Scrapers** | `ai-service/app/services/scraping/amazon_scraper.py`<br>`daraz_scraper.py`<br>`temu_scraper.py` | `scrape_amazon_products`<br>`scrape_daraz_products`<br>`scrape_temu_products` | Genuine external limitations: Amazon HTTP 503 bot verification, Daraz client-rendered React `#root` shell, Temu dynamic client-side JavaScript. |
| **Direct URL Scraper Gateway** | `backend/src/routes/uploadRoutes.js`<br>`backend/src/controllers/uploadController.js` | Missing endpoint | Express gateway has no handler or proxy for `POST /api/marketplace/scrape-url`. |
| **Frontend URL Input & Flow** | `frontend/components/VerificationWorkspace.tsx`<br>`frontend/components/VerificationResult.tsx` | Lines 148–170 (`Workspace`)<br>Lines 659–666 (`Result`) | Direct URL input is only present before verification. After verification completes, `VerificationResult.tsx` prompts user to supply link but provides no input field or submission handler. |
| **Review & Sentiment Gate** | `ai-service/app/services/product_service.py`<br>`ai-service/app/services/review_analysis_service.py` | `analyze_product_authenticity` (L111–131)<br>`build_marketplace_sentiment` (L260–280) | Correctly refuses to fabricate review text or sentiment scores when automated search yields 0 items. |

---

## Part 3: Recommended Fixes in Priority Order

### Priority 1: Interactive Direct URL Scraper in Verification Results (Immediate Workflow Fix)
- **Problem Solved:** Connects the working direct URL scraper to the live frontend workflow so users can paste a Daraz or Amazon product link directly inside the results dashboard and fetch real listings, reviews, and sentiment analysis without resetting.
- **Implementation:**
  1. Add an inline "Fetch Real Product Reviews & Marketplace Data" form inside Section 3 of `frontend/components/VerificationResult.tsx` when `validListings.length === 0`.
  2. Add Express gateway route `POST /api/marketplace/scrape-url` in `backend/src/routes/uploadRoutes.js` and controller method in `backend/src/controllers/uploadController.js` that forwards to FastAPI `POST /api/marketplace/scrape-url`.
  3. When URL is submitted in the results view, fetch the listing, re-run sentiment analysis on collected reviews, update state, and display real reviews in Section 4 and sentiment in Section 5.

### Priority 2: Fix OCR Brand Fallback & Packaging Preprocessing
- **Problem Solved:** Prevents attribute terms like `"MATTE"` or `"SPF"` from becoming the product brand name; improves text extraction on glossy bottles.
- **Implementation:**
  1. In `ocr_service.py` (`parse_brand_and_product`): Add an attribute blacklist (`{"matte", "poreless", "foundation", "spf", "normal", "oily", "broad", "spectrum"}`) preventing cosmetic descriptors from being selected as fallback brands.
  2. If detected brand is not in `KNOWN_BRANDS` and first token is a cosmetic descriptor, mark `brand_name: "Unidentified Brand"`.
  3. Add adaptive contrast enhancement (CLAHE) in `preprocess_image_for_ocr` to boost detection of faint packaging branding text (e.g. Maybelline New York at top of bottle).

### Priority 3: Catalog & Reference Bank Alignment (Fit Me Foundation)
- **Problem Solved:** Allows Maybelline Fit Me foundation images to match its genuine reference embeddings rather than defaulting to Low-Confidence / Catalog Mismatch against P011 Fenty.
- **Implementation Options (User Decision Required):**
  - *Option A (Expand Catalog to include Maybelline Fit Me):* Add product `P031` (Maybelline Fit Me Matte + Poreless Foundation) to `selected_30_products_final.csv`, add 70% reference images to `data/image_model_dataset/Foundation_Base/P031_Maybelline_FitMe/`, and re-embed reference bank vectors into `clip_reference_embeddings.npz`.
  - *Option B (Maintain 30-Product Scope & Surface Explicit "Out-of-Catalog" Badge):* If the project scope is strictly limited to the 30 evaluation products, ensure the UI clearly explains: *"Maybelline Fit Me is not currently indexed in the 30-product reference catalog (P001–P030). System identified packaging features via OCR and relied on direct marketplace extraction."*

### Priority 4: External Scraper Fallback & Client-Side Rendering Guidance
- **Problem Solved:** Transparent user guidance when automated search hits Amazon 503, Daraz React shell, or Temu JS shell.
- **Implementation:**
  1. Retain honest `MARKETPLACE_BLOCKED` and `NOT_RETRIEVABLE` indicators without fabricating listings.
  2. Provide one-click search link buttons (e.g. `Search Amazon in browser`, `Search Daraz in browser`) pre-populated with the normalized query so the user can easily find the exact product link and paste it into the direct URL field.

---

## Part 4: Tests Required to Verify Each Fix

1. **Direct Marketplace URL Express Gateway Test:**
   - Test `POST /api/marketplace/scrape-url` on port 5000 with a valid Daraz URL.
   - Verify HTTP 200, parsed title, price, and at least 1 customer review returned.
2. **OCR Brand Fallback Blacklist Test:**
   - Test `parse_brand_and_product([{"text": "MATTE"}, {"text": "FOUNDATION 130"}])`.
   - Verify `brand_name` is NOT `"Matte"` (must return `"Unidentified Brand"` or `"Unknown Brand"`).
3. **End-to-End Image + Direct URL Verification Test:**
   - Upload `fitme-1793389836878-568858284.png` with `product_url`.
   - Verify `marketplace_listings` contains Daraz listing with `status_code == 'VERIFIED_LISTING'`.
   - Verify `review_result.analyzed_reviews` contains real review text.
   - Verify `review_result.sentiment_label` is `"Positive"`.
   - Verify PostgreSQL persistence of the `CustomerReview` record.
4. **Automated Search Degradation Safety Test:**
   - Verify that automated search failure across Amazon, Daraz, and Temu continues to report `source_status: blocked/unavailable` without raising unhandled 500 exceptions.
5. **Full Regression Test Suite:**
   - Run `pytest tests/` (all 193 tests must continue to pass).

---

## Status and Next Steps

The audit is complete. Application code has **not** been modified.
Please review these findings and confirm whether you would like to proceed with implementing Priority 1 (Interactive Direct URL Scraper & Express Proxy), Priority 2 (OCR Brand Fallback Fix), and/or Priority 3 (Catalog Alignment).
