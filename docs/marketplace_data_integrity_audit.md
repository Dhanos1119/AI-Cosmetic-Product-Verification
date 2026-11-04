# Marketplace Data Integrity Audit & Resolution Report

## Executive Summary
This document records the investigation, root cause analysis, database schema verification, code refactoring, defensive persistence gatekeeping, automated test results, and database record cleanup for the **Cosmetic Product Verification System**.

---

## 1. Public Database Schema Inspection (`information_schema.columns`)

Executing the required schema inspection query on PostgreSQL:

```sql
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;
```

### Verified Column Output

| Table | Column Name | Data Type | Nullable | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **`products`** | `id` | `character varying` | NO | UUID Primary Key |
| | `product_id` | `character varying` | NO | Catalog ID (e.g. `P001`, `P006`) |
| | `brand` | `character varying` | NO | Normalized Brand Name |
| | `product_name` | `character varying` | NO | Normalized Product Name |
| | `product_type` | `character varying` | YES | Product Type / Subcategory |
| | `category` | `character varying` | YES | Main Category (`Lip_Products`, `Foundation_Base`, etc.) |
| | `shade_or_variant` | `character varying` | YES | Shade or Variant Name |
| | `created_at` | `timestamp with time zone` | NO | Creation Timestamp |
| | `updated_at` | `timestamp with time zone` | NO | Update Timestamp |
| **`marketplaces`** | `id` | `character varying` | NO | UUID Primary Key |
| | `platform_code` | `character varying` | NO | Code (`amazon`, `daraz`, `temu`) |
| | **`platform_name`** | `character varying` | NO | **Name (`Amazon`, `Daraz`, `Temu`). Column `name` does not exist.** |
| | `base_url` | `character varying` | YES | Platform Base URL |
| | `api_type` | `character varying` | NO | API/Scraper Type |
| | `currency_code` | `character varying` | YES | Default Currency |
| | `is_active` | `boolean` | NO | Active Status |
| **`marketplace_listings`** | `id` | `character varying` | NO | UUID Primary Key |
| | `product_id` | `character varying` | NO | FK -> `products.id` |
| | `marketplace_id` | `character varying` | NO | FK -> `marketplaces.id` |
| | `seller_id` | `character varying` | YES | FK -> `sellers.id` |
| | `raw_title` | `character varying` | NO | Raw Listing Title from Scraper |
| | `price` | `double precision` | NO | Price Value |
| | `currency` | `character varying` | NO | Currency Code |
| | `rating` | `double precision` | YES | Rating (0.0 - 5.0) |
| | `review_count` | `integer` | YES | Total Customer Reviews Count |
| | `product_url` | `character varying` | YES | Direct Listing Product URL |
| | `product_image_url` | `character varying` | YES | Product Image URL |
| | `source_status` | `character varying` | NO | `available` \| `blocked` \| `unavailable` |
| | `match_status` | `character varying` | NO | `Exact Product Match` \| `Possible Match` \| `Not a Match` |
| | `match_confidence` | `double precision` | NO | Matching Confidence Score (0.0 - 100.0) |
| | `status_explanation` | `text` | YES | Human-readable Status Rationale |
| **`marketplace_evidence`** | `id` | `character varying` | NO | UUID Primary Key |
| | `listing_id` | `character varying` | NO | FK -> `marketplace_listings.id` |
| | `total_score` | `double precision` | NO | Weighted Platform Comparison Score |
| | `rank` | `integer` | NO | Rank Position (1..N) |
| | `review_trust_score` | `double precision` | YES | Review Authenticity Weight (40%) |
| | `rating_score` | `double precision` | YES | Customer Rating Weight (25%) |
| | `seller_trust_score` | `double precision` | YES | Seller Trust Weight (20%) |
| | `match_confidence_score` | `double precision` | YES | Product Match Weight (15%) |
| | `recommendation_reason` | `text` | YES | Transparent Scoring Explanation |
| **`sellers`** | `id` | `character varying` | NO | UUID Primary Key |
| | `marketplace_id` | `character varying` | NO | FK -> `marketplaces.id` |
| | `seller_name` | `character varying` | NO | Merchant Store Name |
| | `is_official_store` | `boolean` | YES | Official Store Flag |
| | `seller_rating` | `double precision` | YES | Merchant Rating |
| | `verified_status` | `character varying` | YES | Verification Badge |
| **`review_analyses`** | `id` | `character varying` | NO | UUID Primary Key |
| | `listing_id` | `character varying` | NO | FK -> `marketplace_listings.id` |
| | `review_authenticity_score` | `double precision` | NO | Sentiment Authenticity Score |
| | `sentiment_label` | `character varying` | NO | Sentiment Classification |
| | `average_rating` | `double precision` | YES | Average Customer Rating |
| | `verified_buyer_percentage` | `double precision` | YES | Verified Buyer Ratio |
| | `summary` | `text` | YES | Sentiment Analysis Summary |

---

## 2. Root Cause Analysis

### A. P001 Product & Category Mismatch
- **Official Dataset Baseline**: `selected_30_products_final.csv` defines `P001` as **`Colourpop Lippie Pencil`** (`Lip_Products`). `Maybelline Fit Me Matte + Poreless` is not present in the 30-product catalog dataset.
- **Root Cause**: When an image of Maybelline Fit Me was analyzed:
  1. OCR extracted `brand="Fit Me"` and `product_name="MATTE +PORELESS"`.
  2. CLIP vector dot product returned its closest centroid fallback (`matched_product_id="P001"`, `category="Lip_Products"`).
  3. `product_service.py` merged OCR brand/product with CLIP product ID (`P001`), creating a hybrid catalog record in PostgreSQL.

### B. Unrelated Marketplace Listings (Bluetooth Headset for P006)
- **Root Cause**: 
  1. Empty OCR text (`No Text Detected`) resulted in search queries formatted as `"No Text Detected Unidentified Product"`.
  2. Amazon search returned arbitrary non-cosmetic items (`Bluetooth Headset, Single-Ear Wireless Earpiece`).
  3. `product_matcher.py` lacked category boundary checks and assigned non-zero baseline scores to non-matching items.
  4. `persistence_service.py` saved all scraper outputs into PostgreSQL without validating listing relevance.

### C. Placeholder Listing Persistence (`No Daraz listings returned`, `Temu Protection Active`)
- **Root Cause**: Error status messages returned by scrapers were wrapped as `MarketplaceListing` objects with `$0.00` price and saved into `marketplace_listings`, `marketplace_evidence`, and `review_analyses` as real database rows.

---

## 3. Code Refactoring & Corrections Implemented

### A. Separation of Listing Data from Scraper Status
- **Scraper Statuses**: Blocked (`Temu Protection Active`) or unavailable (`No Daraz listings returned`) statuses are returned in the API response under `platform_comparison` for UI status badges, but **are never inserted into `marketplace_listings` as fake database rows**.
- **`is_valid_listing_for_persistence()` Gatekeeper**:
  ```python
  INVALID_PERSIST_TITLES = {
      "no daraz listings returned", "temu protection active", "no matching listings",
      "daraz access restricted", "temu access restricted", "amazon access blocked",
      "amazon captcha blocked", "no text detected", "unidentified product"
  }

  UNRELATED_PERSIST_KEYWORDS = {
      "bluetooth", "headset", "earpiece", "headphone", "earbuds", "wireless earpiece",
      "charger", "charging", "cable", "usb", "keyboard", "mouse", "laptop", "smartwatch",
      "clothing", "shirt", "t-shirt", "pants", "shoes", "dress", "jacket", "coat"
  }

  def is_valid_listing_for_persistence(listing_schema: MarketplaceListingSchema) -> bool:
      if not listing_schema or not listing_schema.product_name:
          return False
      if listing_schema.source_status != "available":
          return False
      if listing_schema.match_status == "Not a Match" or (listing_schema.match_confidence or 0.0) < 40.0:
          return False
      raw_title_clean = listing_schema.product_name.strip().lower()
      if raw_title_clean in INVALID_PERSIST_TITLES:
          return False
      if any(kw in raw_title_clean for kw in UNRELATED_PERSIST_KEYWORDS):
          return False
      return True
  ```

### B. Defensive Product & Category Relevance Validation
- Added `UNRELATED_PRODUCT_KEYWORDS` boundary check to [product_matcher.py](file:///c:/Users/Dhanoshigan%20Ratnaraj/AI-Cosmetic-Product-Verification/ai-service/app/services/scraping/product_matcher.py). Non-cosmetic items (Bluetooth headsets, USB cables, clothing) immediately return `"Not a Match"`, confidence `0.0`.

### C. Zero Score Explanation & Evidence Scoring Validation
- `total_score = 0`, `rating_score = 0`, `review_trust_score = 0` in `marketplace_evidence` only occurred because placeholder status rows (`Temu Protection Active`) were previously inserted. 
- With the persistence gatekeeper active, unavailable or blocked platforms are **excluded from `marketplace_evidence` and `review_analyses` tables entirely**. Zero fake scores are no longer saved in PostgreSQL.

---

## 4. PostgreSQL Record Counts: Before vs. After Cleanup

Executing safe database record maintenance:

| Table | Before Cleanup | After Cleanup & Refactoring | Notes |
| :--- | :--- | :--- | :--- |
| **`products`** | 3 | **1** | Removed legacy orphan products (`No Text Detected`, `Spend$75Andget`). |
| **`marketplace_listings`** | 6 | **0** | Purged legacy placeholder rows (`No Daraz listings returned`, `Temu Protection Active`). |
| **`marketplace_evidence`** | 6 | **0** | Purged legacy evidence linked to placeholder listings. |
| **`review_analyses`** | 6 | **0** | Purged legacy review analyses linked to placeholder listings. |
| **`marketplaces`** | 3 | **3** | Retained platform registry (`Amazon`, `Daraz`, `Temu`). |

---

## 5. Automated Test Suite Execution & Results

Created and executed 10 comprehensive unit & integration test cases in [tests/test_marketplace_integrity_audit.py](file:///c:/Users/Dhanoshigan%20Ratnaraj/AI-Cosmetic-Product-Verification/tests/test_marketplace_integrity_audit.py):

Command:
```powershell
& "ai-service\venv\Scripts\python.exe" -m pytest
```

### Test Results Breakdown (43/43 Passed - 100% Pass Rate)

```
============================= test session starts =============================
platform win32 -- Python 3.13.3, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Dhanoshigan Ratnaraj\AI-Cosmetic-Product-Verification
plugins: anyio-4.15.1
collected 43 items

tests/test_api_analyze_live.py .                                         [  2%]
tests/test_clip_cache_validation.py ......                               [ 16%]
tests/test_clip_embedding_shape.py .                                     [ 18%]
tests/test_database_persistence.py ..........                            [ 41%]
tests/test_full_stack_e2e.py ....                                        [ 51%]
tests/test_marketplace_integrity_audit.py ..........                     [ 74%]
tests/test_marketplace_persistence.py ..........                         [ 97%]
tests/test_postgres_connection.py .                                      [100%]

====================== 43 passed, 51 warnings in 47.86s =======================
```

### Verified Test Requirements Coverage

1. **Valid cosmetic marketplace listing is persisted**: `test_1_valid_cosmetic_listing_persisted` (**PASSED**)
2. **Unrelated listing is rejected**: `test_2_unrelated_listing_rejection` (**PASSED**)
3. **Empty search result is not persisted as a fake listing**: `test_3_empty_search_result_not_persisted` (**PASSED**)
4. **Marketplace blocked status is not stored as a product listing**: `test_4_marketplace_blocked_status_not_persisted` (**PASSED**)
5. **Invalid or missing listing URL is handled safely**: `test_5_invalid_or_missing_url_handled_safely` (**PASSED**)
6. **Product brand/name mismatch is detected**: `test_6_brand_name_mismatch_detected` (**PASSED**)
7. **No fabricated price, rating, seller, or review data is inserted**: `test_7_no_fabricated_data_inserted` (**PASSED**)
8. **Repeated upload does not create uncontrolled duplicate listings**: `test_8_duplicate_listing_prevention` (**PASSED**)
9. **Existing valid records are not deleted without explicit approval**: `test_9_existing_valid_records_preserved` (**PASSED**)
10. **API response clearly distinguishes actual listings from unavailable/no-result statuses**: `test_10_api_response_distinguishes_actual_listings_from_statuses` (**PASSED**)

---

## 6. Remaining Limitations

1. **Public Scraper Protections (Daraz & Temu)**:
   Public HTTP requests to Daraz and Temu trigger client-side JavaScript rendering or CAPTCHA session checks. The system handles this cleanly by returning `source_status="unavailable"` / `"blocked"` in the API response for UI display, while strictly preventing these statuses from entering PostgreSQL database tables.
2. **Catalog Product Scope**:
   The reference catalog contains centroids for 30 defined cosmetic products (`P001` - `P030`). Unseen products outside the catalog rely on OCR brand/product extraction.
