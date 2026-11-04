# OCR-to-Marketplace Search Audit

**Date:** 2026-10-18
**Scope:** Trace OCR text extraction → query construction → Amazon scraper → result handling
**Status:** Audit complete. Fixes applied and verified. All tests pass.

---

## Executive Summary

| Step | Status | Finding |
|------|--------|---------|
| OCR text extraction | ✅ Working | EasyOCR / RapidOCR correctly extract text from packaging |
| product_name construction | ⚠️ Fixed | Was sliced to `[:2]` lines — truncated multi-line labels; trailing punctuation not stripped |
| Query normalisation | ⚠️ Fixed | No cleanup of lone punctuation (`-`, `+`) or OCR noise tokens before passing to scraper |
| Amazon search | ❌ Blocked | HTTP 503 (Akamai bot-management) on every request — both malformed and clean queries |
| Amazon 503 handling | ✅ Correct | Correctly mapped to `source_status="blocked"`, `listing_status="MARKETPLACE_BLOCKED"` |
| Listing fabrication | ✅ Never | No fake/verified listings created when Amazon is blocked |
| Permitted API alternative | ℹ️ Documented | Amazon PA-API requires active Associates account + 10 qualifying sales / 30 days |

---

## Step 1 — OCR Text Extraction

**Engine chain:** RapidOCR ONNX → EasyOCR (fallback) → PyTesseract (fallback)

For the Maybelline Fit Me Matte+Poreless image, typical OCR output is:

```
['Maybelline', 'fit me', 'Matte -', '+PORELESS', 'NORMALTOOLY', '30ml']
```

Each engine returns a list of `(text, confidence)` pairs, filtered at `conf > 0.15` and `len >= 2`.
This step is **working correctly**.

---

## Step 2 — `parse_brand_and_product` — Two Bugs Fixed

### Bug 2-A: product_lines sliced to `[:2]`

**Location:** `ai-service/app/services/ocr_service.py` line 144 (pre-fix)

```python
# BEFORE (bug)
product_name = " ".join(product_lines[:2])
# -> "fit me Matte -"   (truncated; missing Poreless/Foundation)

# AFTER (fix)
product_name = " ".join(product_lines[:4])
# -> "fit me Matte - +PORELESS NORMALTOOLY"   (more complete)
```

With 4 lines the name includes all relevant label tokens. The query normaliser then cleans punctuation/noise.

### Bug 2-B: No stripping of trailing/leading lone punctuation

**Location:** Same function, same block

OCR frequently splits "Matte +Poreless" into two lines: `"Matte -"` and `"+PORELESS"`.
When joined, the result is `"fit me Matte -"` — the trailing dash is never removed.

**Fix:** Strip leading/trailing non-word characters from the final joined name:
```python
product_name = re.sub(r'^[^\w]+', '', product_name).strip()
product_name = re.sub(r'[^\w]+$', '', product_name).strip()
```

---

## Step 3 — `generate_search_queries` — Missing Normalisation Fixed

**Location:** `ai-service/app/services/scraping/marketplace_search.py`

### Root cause

The query was assembled as:
```python
base_q = f"{brand} {name}".strip()
```
No sanitisation. Whatever raw text OCR produced went directly to the scraper.

### Observed malformed query (pre-fix)

```
"Maybelline Matte - +PORELESS NORMALTOOLY Amazon"
```

Problems:
- Standalone `-` and `+` are invalid search operators on most marketplaces
- `NORMALTOOLY` is an OCR artefact for "Normal to Oily" — produces irrelevant results
- Appending `" Amazon"` to the query (also removed) caused zero-result searches on amazon.com

### Fix: `_normalize_query` helper added

```python
def _normalize_query(text: str) -> str:
    # 1. Remove lone punctuation tokens (not surrounded by word chars)
    cleaned = re.sub(r'(?<![\w])([+\-*/\\|^~!?.,:;\'"`#@$%]{1,3})(?![\w])', ' ', text)
    # 2. Replace remaining special chars with spaces
    cleaned = re.sub(r'[^\w\s]', ' ', cleaned)
    # 3. Remove OCR noise tokens
    tokens = [t for t in cleaned.split() if t.lower() not in _OCR_NOISE_TOKENS]
    return ' '.join(tokens).strip()
```

OCR noise tokens removed: `normaltooly`, `normaltooily`, `oilysk`, `skintone`, `skintype`, etc.

### Query before vs after fix

| Input | Before | After |
|-------|--------|-------|
| `"Matte - +PORELESS NORMALTOOLY"` | `"Maybelline Matte - +PORELESS NORMALTOOLY Amazon"` | `"Maybelline Matte PORELESS"` |
| `"fit me Matte -"` | `"Maybelline fit me Matte - Amazon"` | `"Maybelline fit me Matte"` |
| `"Fit Me Matte Poreless Foundation"` | `"Maybelline Fit Me Matte Poreless Foundation Amazon"` | `"Maybelline Fit Me Matte Poreless Foundation"` |

### amazon_query / daraz_query / temu_query

The old code appended `" Amazon"`, `" Daraz"`, `" Temu"` to the query passed to each scraper.
This is wrong — scrapers query their own URLs directly; the query string should be just the product search term.

**Fix:** `amazon_query = base_q` (no suffix appended).

---

## Step 4 — Amazon Scraper: Why HTTP 503

**File:** `ai-service/app/services/scraping/amazon_scraper.py`

### Mechanism

Amazon uses Akamai bot-management at the CDN edge layer. The response:

- Returns **HTTP 503** for server-side rendered search requests from non-browser clients
- Response body is **2671 bytes** — a minimal JSON/HTML rejection page
- Body contains `api-services-support@amazon.com` — a known bot-challenge marker
- **Identical response for both malformed and clean queries** — the query content is irrelevant; the block happens at the transport layer before the query is processed

### Live test result (verified 2026-10-18)

```
Query: 'Maybelline Matte - +PORELESS NORMALTOOLY'
  HTTP status: 503  |  Response: 2671 bytes
  Bot markers: ['api-services-support@amazon.com']

Query: 'Maybelline Fit Me Matte Poreless Foundation'
  HTTP status: 503  |  Response: 2671 bytes
  Bot markers: ['api-services-support@amazon.com']
```

### Why it cannot be fixed by changing query text or headers

The block is at the **IP/fingerprint layer**. Amazon's Akamai integration blocks:
- Datacenter/VPS IP ranges (not residential)
- Missing browser TLS fingerprint (JA3 hash mismatch)
- Missing browser JavaScript execution
- Missing browser cookies from prior sessions

No query text change, User-Agent rotation, or header adjustment will bypass this.

### What the scraper does correctly

```python
if resp.status_code in [403, 503, 429]:
    return [RawMarketplaceItem(
        platform="Amazon",
        source_status="blocked",
        status_code="MARKETPLACE_BLOCKED",
        explanation=f"Amazon returned HTTP {resp.status_code} anti-bot protection..."
    )]
```

This is **correct behaviour**: the block is surfaced as `source_status="blocked"` and
`listing_status="MARKETPLACE_BLOCKED"`. No fake listings are created. No CAPTCHA is bypassed.

---

## Step 5 — Permitted Alternatives for Real Amazon Product Data

### Option A: Amazon Product Advertising API (PA-API 5.0 / Creators API)

**Status: Requires affiliate programme approval. Not currently configured.**

| Requirement | Detail |
|-------------|--------|
| Account | Active Amazon Associates account (affiliate) |
| Sales threshold | 10 qualifying sales in past 30 days to maintain access |
| Cost | Free within usage quota; no subscription fee |
| Rate limit | ~8,640 requests/day (scales with affiliate revenue) |
| Credentials needed | Access Key, Secret Key, Partner Tag |
| Supported operations | `SearchItems`, `GetItems` by ASIN |
| Regions | Separate keys per marketplace (amazon.com, amazon.co.uk, etc.) |

**To enable:** The user would need to:
1. Apply for Amazon Associates at [affiliate-program.amazon.com](https://affiliate-program.amazon.com)
2. Generate PA-API credentials from Associates Central → Tools → Product Advertising API
3. Configure `AMAZON_ACCESS_KEY`, `AMAZON_SECRET_KEY`, `AMAZON_PARTNER_TAG` in `.env`
4. Replace the HTML scraper with a PA-API `SearchItems` call

The app is designed to accept this integration: the `scrape_amazon_products` function can
be replaced with a PA-API client without touching any other layer.

### Option B: User-Provided Amazon Product URL (Already Supported)

The URL validator (`url_validator.py`) already validates Amazon URLs:
- Accepts: `amazon.com`, `amazon.in`, `amazon.co.uk`, `amazon.ca`, etc.
- Rejects: placeholder patterns, wrong domains, missing protocol

**If the user provides a direct Amazon product URL** (e.g., from their browser), the app can:
1. Validate the URL format (currently supported)
2. Attempt to fetch the product page directly (not currently implemented — same 503 risk)
3. Accept it as a user-asserted reference URL without fetching (safest approach)

This is the safest supported path for obtaining a real Amazon listing link without
requiring PA-API credentials.

---

## Step 6 — What Was NOT Done

- No CAPTCHA bypassed
- No anti-bot protection circumvented
- No fake Amazon listings created
- No database records deleted or reset
- No unrelated development work started

---

## Files Modified

| File | Change |
|------|--------|
| `ai-service/app/services/ocr_service.py` | `product_lines[:2]` → `[:4]`; strip trailing/leading lone punctuation from product_name |
| `ai-service/app/services/scraping/marketplace_search.py` | Added `_normalize_query` + `_OCR_NOISE_TOKENS`; call normaliser before building query; removed `" Amazon"` / `" Daraz"` / `" Temu"` suffixes; explicitly pass `queries.amazon_query` to `scrape_amazon_products` in `future_to_scraper` |
| `tests/test_ocr_query_normalisation.py` | 36 automated tests covering normalization, query construction, line joining, Amazon 503 mapping, query propagation, and permitted URL validation |

---

## Test Results

```
36 passed (test_ocr_query_normalisation.py) — all tests green in 0.44s
65 passed (marketplace test suite: fixes, phase 6 evidence, url validation, integrity, persistence)
```

### Test coverage breakdown

| Class | Tests | Focus |
|-------|-------|-------|
| `TestNormalizeQuery` | 13 | `_normalize_query`: lone punctuation, noise tokens, whitespace collapse |
| `TestGenerateSearchQueries` | 9 | Query construction, normalisation, token gate, placeholder rejection |
| `TestParseBrandAndProduct` | 8 | 4-line join, punctuation strip, brand/category detection, volume filtering |
| `TestAmazon503Handling` | 6 | 503/403/CAPTCHA → blocked; no fake verified listings; confirmation that cleaned query is passed to `scrape_amazon_products`; user-provided URL validation |

---

## What Is Still Blocked (by Design)

| Platform | Status | Reason |
|----------|--------|--------|
| Amazon (scraper) | ❌ Blocked | Akamai bot-management; HTTP 503 on all automated requests |
| Amazon (PA-API) | ⏳ Not configured | Requires Amazon Associates account + 10 qualifying sales / 30 days |
| Daraz | ❌ Blocked | JS-rendered page; server-side HTML has no product data |
| Temu | ❌ Blocked | Anti-bot / rate limiting |

When all platforms are blocked:
- `source_status = "blocked"` or `"unavailable"`
- `listing_status = "MARKETPLACE_BLOCKED"` or `"UNAVAILABLE"`
- `passed_match_threshold = False`
- `rank = 99` in platform comparison (not presented as recommendation)
- No `VERIFIED_LISTING` records persisted to PostgreSQL

