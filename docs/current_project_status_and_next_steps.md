# AI Cosmetic Product Verification — Complete Project Status Audit

**Audit Type**: Read-Only Comprehensive Status Audit
**Audit Date**: 2026-10-16
**Auditor**: Antigravity AI Assistant
**Project Root**: `C:\Users\Dhanoshigan Ratnaraj\AI-Cosmetic-Product-Verification\`

---

## 1. Overall Project Status

**7 development phases have been completed.** The full-stack pipeline is wired end-to-end: Next.js frontend -> Express gateway -> FastAPI AI service -> PostgreSQL, with all 63 backend tests passing. However, a critical dataset integrity problem was discovered: the 100,000-review dataset used for all review analysis is **entirely synthetically generated**, not sourced from the Amazon Beauty Reviews CSV or any real marketplace.

---

## 2. Component-by-Component Status

### A. Cosmetic Product Identification (CLIP + OCR)

| Sub-Component | Status | Evidence |
|:---|:---:|:---|
| OCR (RapidOCR primary, EasyOCR fallback, PyTesseract tertiary) | **VERIFIED COMPLETE** | `ocr_service.py` — full 3-engine cascade implemented |
| OpenAI CLIP ViT-B/32 embedding (512-dim) | **VERIFIED COMPLETE** | `clip_service.py` L36-47 — lazy-loaded, real Hugging Face model |
| Reference centroid cache (30 products x 512-dim) | **VERIFIED COMPLETE** | `data/clip_centroids_vit_b32.npy` — shape [30, 512], created 2026-09-23, 1,340 reference images |
| Image dataset (30 products, 1,950 images, 5 categories) | **VERIFIED COMPLETE** | `data/image_model_dataset/` — 0 corrupted, 0 duplicates per Phase 5 audit |
| Cache integrity validation (SHA-256 checksum) | **VERIFIED COMPLETE** | `clip_service.py` L165-230 — live checksum re-computed and compared on load |
| CLIP accuracy (evaluated on 30% holdout = 610 test images) | **VERIFIED COMPLETE** | Top-1: **30.82%** (188/610), Top-5: **57.54%** (351/610). See `data/clip_evaluation_report.md` |
| OCR brand boost applied to CLIP score | **VERIFIED COMPLETE** | `clip_service.py` L343-348 — +0.15 cosine boost when OCR brand matches catalog |
| Dataset folder / product ID alignment (P013-P018) | **PARTIALLY COMPLETE** | Dataset folders use different brand names than `selected_30_products_final.csv`. 247 images flagged for review; no action taken. |

**Known CLIP Limitations (from evaluation):**
- Top-1 accuracy of 30.82% means 2 in 3 single-image lookups are misidentified at product level
- 1,008 / 1,950 images (51.7%) have cross-class visual similarity issues
- Folder-to-product-ID mapping inconsistency between dataset and CSV reduces matching reliability

---

### B. Marketplace Integration

| Platform | Listing Scraping | Review Text | Status |
|:---|:---:|:---:|:---:|
| Amazon | Attempted (public search page) | **NOT IMPLEMENTED** | PARTIALLY COMPLETE |
| Temu | Attempted (public search page) | **NOT IMPLEMENTED** | BLOCKED (JS rendering) |
| Daraz | Attempted (public catalog search) | **NOT IMPLEMENTED** | PARTIALLY COMPLETE |

**Amazon** (`amazon_scraper.py`):
- Scrapes `https://www.amazon.com/s?k=`. Extracts: title, price, aggregate rating, review count, seller, link.
- Individual customer review text: NOT collected (only aggregate count).
- In practice: Returns HTTP 403/503 or CAPTCHA. Handled cleanly as `source_status="blocked"`.

**Temu** (`temu_scraper.py`):
- JS rendering prevents any data extraction.
- **BUG**: L74-75 hardcodes `rating_val=4.2`, `review_count_val=8` — fabricated data (latent, currently masked by blocked status).
- Individual customer review text: NOT IMPLEMENTED.

**Daraz** (`daraz_scraper.py`):
- JS rendering prevents card extraction.
- **BUG**: L80 references `img_url` which is never defined — would raise NameError if any cards were parsed.
- Individual customer review text: NOT IMPLEMENTED.

**Product Matching** (`product_matcher.py`):
- 4-factor weighted engine: Brand 35%, Product Name 40%, Type 15%, Variant 10%
- Brand mismatch penalty (caps at 40% when brand absent from title): IMPLEMENTED
- Non-cosmetic category rejection (electronics, apparel, etc.): IMPLEMENTED and tested

**URL Validation** (`url_validator.py`): IMPLEMENTED — protocol, placeholder patterns, domain alignment.

---

### C. Database

| Component | Status | Evidence |
|:---|:---:|:---|
| PostgreSQL connection (SQLAlchemy + psycopg2) | **VERIFIED COMPLETE** | `database/connection.py` — `cosmetic_verification_db`, localhost:5432, test passes |
| SQLite fallback | **VERIFIED COMPLETE** | Auto-fallback when no Postgres credentials available |
| ORM models (7 models) | **VERIFIED COMPLETE** | Product, Marketplace, Seller, MarketplaceListing, CustomerReview, ReviewAnalysis, MarketplaceEvidence |
| Alembic migrations (2 versions) | **VERIFIED COMPLETE** | `database/alembic/versions/` — initial schema + integrity fields migration |
| Product / listing persistence | **VERIFIED COMPLETE** | `products`=2 rows, `marketplace_listings`=2 rows in live DB |
| Customer review persistence (real text) | **NOT VERIFIED** | `customer_reviews` = **0 rows**. No real review text ever collected or persisted |
| Review analysis persistence | **PARTIALLY COMPLETE** | `review_analyses` = 1 legacy placeholder row from early Phase 3 test |
| Persistence gatekeeping (block invalid/blocked/unrelated listings) | **VERIFIED COMPLETE** | `persistence_service.py` L275-332 — multi-rule filter working |

**Current live DB counts (verified from Phase 7 read-only audit):**
- `products`: 2 | `marketplace_listings`: 2 | `customer_reviews`: 0 | `review_analyses`: 1 (placeholder)

---

### D. Frontend and Backend Integration

| Component | Status | Evidence |
|:---|:---:|:---|
| Next.js frontend (App Router, TypeScript) | **VERIFIED COMPLETE** | `frontend/` — `.next/` artifacts present, clean TS build |
| Express gateway (port 5000) | **VERIFIED COMPLETE** | `backend/src/server.js` — proxies upload to FastAPI |
| FastAPI AI service (port 8001) | **VERIFIED COMPLETE** | `ai-service/app/main.py` — full pipeline wired at `/api/analyze` |
| Image upload flow | **VERIFIED COMPLETE** | Express `uploadController.js` -> FastAPI `/api/analyze` |
| CLIP result display (top-5 matches, confidence) | **VERIFIED COMPLETE** | `VerificationResult.tsx` |
| OCR result display | **VERIFIED COMPLETE** | Brand, product name, category, confidence rendered |
| Marketplace results display | **VERIFIED COMPLETE** | Available listings vs. status banners for blocked/unavailable |
| Review analysis display (100k benchmark section) | **VERIFIED COMPLETE** | Authenticity score, label breakdown, sample review cards |
| Blocked/unavailable data error handling | **VERIFIED COMPLETE** | Frontend renders status notices, not empty sections |
| Camera modal / Auth modals | **VERIFIED COMPLETE** | CameraModal, LoginModal, SignupModal, ForgotPasswordModal present |

---

### E. Review Dataset and AI Models — CRITICAL FINDINGS

> [!CAUTION]
> The following findings materially affect the validity of the review analysis component.

#### E.1 — Are the 100,000 reviews real or synthetically generated?

**FINDING: The 100,000 reviews in `data/reviews_100k.db` are 100% SYNTHETICALLY GENERATED by `data/prepare_100k_reviews.py`. They are NOT sourced from the Amazon Beauty Reviews dataset.**

Evidence from `prepare_100k_reviews.py`:
- Review bodies selected via `random.choice()` from only 5 positive templates, 4 negative templates, 5 fake templates, and 3 incentivized templates
- Authors generated from a 30-name x 16-initial list
- IDs are sequential `REV_000001` through `REV_100000`
- Dates are randomly assigned in 2025-01-01 to 2026-03-28
- **No row corresponds to any real Amazon reviewer, real purchase, or real product**

#### E.2 — Do OR/CG/INCENTIVIZED labels come from a documented source?

**FINDING: Labels are ASSIGNED BY CODE via `random.random()`. There is no independently labelled ground-truth dataset.**

```python
# prepare_100k_reviews.py L143-173 (simplified)
roll = random.random()
if roll < 0.70:   label = "OR"           # 70% genuine
elif roll < 0.90: label = "CG"           # 20% fake
else:             label = "INCENTIVIZED" # 10% incentivized
```

Labels were mechanically assigned by a RNG, not by human annotation or a verified academic dataset.

#### E.3 — Were exactly 100,000 records selected from the original Amazon CSV?

**FINDING: NO.** The Amazon CSV (701,528 rows) was inspected and `beauty_reviews_prepared.csv` was generated as a copy with a rating-derived `sentiment` column added. ZERO rows from either file were used to populate `reviews_100k.db`.

From `docs/phase7_dataset_inspection_report.md`: *"No model training executed: Model training postponed to future pipeline steps."*

#### E.4 — Were there 80,000 training and 20,000 testing records from the real dataset?

**FINDING: NO.** No 80k/20k train/test split exists. The NLP classifier (`review_analysis_service.py` L49-54) trains on a 6,000-row sample from the **synthetic** DB at service startup. No holdout set exists.

#### E.5 — Was a sentiment model trained on original review data?

**FINDING: NO.** The TF-IDF + Logistic Regression classifier:
- Trains on 6,000 rows from the synthetic `reviews_100k.db` at cold start
- Learns from mechanically-assigned OR/CG labels, not real human annotations
- Is NOT a persisted model artifact (retrained from scratch on every cold start)
- Has NOT been evaluated for accuracy, precision, or recall on any real data

#### E.6 — Was a fake/deceptive review model trained on independently labelled data?

**FINDING: NO.** No independently labelled deceptive review dataset has been used. No academic dataset (Yelp, PAN, AMT, etc.) has been incorporated. All "fake" labels come from random assignment.

#### E.7 — Are reported trust/genuine percentages based on real marketplace reviews?

**FINDING: NO.** All review percentages displayed in the UI (88% verified buyers, 20% fake/CG, etc.) are derived from the synthetic DB constructed with predetermined ratios (70%/20%/10%) and hardcoded verified purchase probabilities. These are **simulation parameters**, not empirical marketplace measurements.

#### E.8 — Is the model loaded and used by the running FastAPI service?

**FINDING: PARTIALLY.** The review analysis pipeline IS invoked on every `/api/analyze` request, the DB IS queried, and the TF-IDF classifier IS trained in-memory at first use. However, since the underlying data and labels are synthetic, the classifier learns patterns from template text, not real review writing behavior.

---

## 3. Test and Build Results

### 3.1 Backend PyTest Suite

**Command run**: `& "ai-service\venv\Scripts\python.exe" -m pytest tests/ -v --tb=short`
**Result**: **63 / 63 PASSED** (38.98 seconds, exit code 0)

| Test File | Tests | Passed | Failed |
|:---|:---:|:---:|:---:|
| `test_api_analyze_live.py` | 1 | 1 | 0 |
| `test_clip_cache_validation.py` | 6 | 6 | 0 |
| `test_clip_embedding_shape.py` | 1 | 1 | 0 |
| `test_database_persistence.py` | 10 | 10 | 0 |
| `test_full_stack_e2e.py` | 2 | 2 | 0 |
| `test_marketplace_integrity_audit.py` | 10 | 10 | 0 |
| `test_marketplace_persistence.py` | 10 | 10 | 0 |
| `test_marketplace_url_validation.py` | 8 | 8 | 0 |
| `test_phase6_matching_evidence_quality.py` | 8 | 8 | 0 |
| `test_postgres_connection.py` | 1 | 1 | 0 |
| `test_review_analysis.py` | 4 | 4 | 0 |

**Warnings (non-breaking)**:
1. `StarletteDeprecationWarning` - use `httpx2` with testclient
2. `torch.ao.quantization` deprecated (EasyOCR dependency) - harmless
3. `PydanticDeprecatedSince20` - `.dict()` in `product_service.py` L113-116 will break in Pydantic V3

> [!NOTE]
> All 63 tests pass. The review analysis tests only verify that the synthetic DB is queried correctly. They do NOT validate that review data is real or that model accuracy is meaningful.

### 3.2 Verified Evaluation Metrics

| Component | Metric | Verified Value | Source |
|:---|:---:|:---:|:---|
| CLIP Top-1 Accuracy | 30.82% | VERIFIED | `data/clip_evaluation_report.md` (2026-09-23) |
| CLIP Top-5 Accuracy | 57.54% | VERIFIED | Same file |
| Review NLP Classifier Accuracy | UNKNOWN | NOT MEASURED | No evaluation script or holdout set exists |
| Fake Review Detection Precision/Recall | UNKNOWN | NOT MEASURED | No independently labelled test set |

---

## 4. Component Status Table

| Component | Status | Evidence Path | Remaining Work |
|:---|:---:|:---|:---|
| OCR (3-engine cascade) | VERIFIED COMPLETE | `ai-service/app/services/ocr_service.py` | None |
| CLIP ViT-B/32 embedding | VERIFIED COMPLETE | `ai-service/app/services/clip_service.py` | None |
| CLIP centroid cache (30x512) | VERIFIED COMPLETE | `data/clip_centroids_vit_b32.npy` + metadata | None |
| CLIP accuracy evaluation | VERIFIED COMPLETE | `data/clip_evaluation_report.md` (Top-1=30.82%) | Consider accuracy improvements |
| Image dataset (1,950 images, 30 products) | VERIFIED COMPLETE | `data/image_model_dataset/` | 247 images need review |
| Dataset folder/product ID alignment | PARTIALLY COMPLETE | Phase 5 audit — P013-P018 brand mismatch | Correct CSV-to-folder mapping |
| Amazon scraper | PARTIALLY COMPLETE | `amazon_scraper.py` — blocked by CAPTCHA in practice | Proxy layer or official API |
| Temu scraper | BLOCKED | `temu_scraper.py` — JS rendering prevents access | Requires browser automation |
| Daraz scraper | PARTIALLY COMPLETE | `daraz_scraper.py` — JS rendered, no cards parsed | Fix `img_url` NameError bug |
| Product matcher (multi-factor) | VERIFIED COMPLETE | `product_matcher.py` | None |
| URL validation | VERIFIED COMPLETE | `url_validator.py` | None |
| Individual review text scraping | NOT IMPLEMENTED | All 3 scrapers — aggregate count only | JS scraping or official API needed |
| PostgreSQL connection | VERIFIED COMPLETE | `database/connection.py` | None |
| Database ORM models (7 models) | VERIFIED COMPLETE | `database/models/` | None |
| Alembic migrations | VERIFIED COMPLETE | `database/alembic/versions/` | None |
| Product/listing persistence | VERIFIED COMPLETE | `persistence_service.py` | None |
| Customer review persistence | NOT VERIFIED | `customer_reviews` = 0 rows | Needs real review text source |
| Review analysis persistence | PARTIALLY COMPLETE | `review_analyses` = 1 placeholder row | Needs real analysis |
| 100k review DB | VERIFIED COMPLETE (SYNTHETIC) | `data/reviews_100k.db`, `prepare_100k_reviews.py` | REPLACE with real Amazon pipeline |
| Amazon Beauty Reviews CSV (701k rows) | NOT USED | `data/review_dataset/raw/amazon_beauty_reviews_dataset.csv` | Build train/test pipeline |
| Sentiment model (real data) | NOT IMPLEMENTED | No training script exists | Train on real Amazon reviews |
| Fake-review classifier (real labels) | NOT IMPLEMENTED | No independently labelled dataset | Obtain real labelled data |
| NLP classifier evaluation | NOT IMPLEMENTED | No precision/recall/F1 metrics | Evaluate on holdout set |
| FastAPI service wiring | VERIFIED COMPLETE | `ai-service/app/main.py`, `routes/analysis.py` | None |
| Express gateway | VERIFIED COMPLETE | `backend/src/server.js` | None |
| Next.js frontend | VERIFIED COMPLETE | `frontend/` — build artifacts present | None |
| Full pipeline E2E | VERIFIED COMPLETE | `test_full_stack_e2e.py` — 2/2 pass | None |
| Pydantic V2 `.dict()` warning | WARNING | `product_service.py` L113-116 | Replace with `.model_dump()` |
| Temu rating fabrication risk | WARNING | `temu_scraper.py` L74-75 | Remove hardcoded fallback values |
| Daraz `img_url` NameError | BUG | `daraz_scraper.py` L80 | Fix undefined variable |

---

## 5. Dataset Provenance Findings

### Amazon Beauty Reviews Dataset
- **File**: `data/review_dataset/raw/amazon_beauty_reviews_dataset.csv`
- **Size**: 211.56 MB, 701,528 rows, 10 columns
- **Real data**: Yes — real Amazon reviews with rating, title, text, asin, user_id, verified_purchase, helpful_vote
- **Usage**: NOT USED for model training. Inspected only.
- **Label gap**: No explicit fake/real ground-truth label column exists. Must use proxy heuristics.

### 100k Synthetic Review DB
- **File**: `data/reviews_100k.db` (34.47 MB) + `data/reviews_100k_dataset.jsonl.gz` (2.26 MB)
- **Generation**: `data/prepare_100k_reviews.py` — pure Python random generation
- **Content**: 100,000 synthetic reviews from 17 total template strings
- **Labels**: Mechanically assigned (70% OR, 20% CG, 10% INCENTIVIZED) via `random.random()`
- **VERDICT**: NOT a real review dataset. Cannot be used for academic or production validation.

### Prepared Amazon CSV
- **File**: `data/review_dataset/processed/beauty_reviews_prepared.csv` (228 MB)
- **Content**: Amazon CSV + rating-derived `sentiment` column (negative/neutral/positive)
- **Usage**: NOT USED for model training

---

## 6. Marketplace Review Collection Status

| Platform | Aggregate Rating | Review Count | Individual Review Text | Verified Purchase Flag |
|:---|:---:|:---:|:---:|:---:|
| Amazon | Available (when not blocked) | Available (when not blocked) | NOT COLLECTED | NOT COLLECTED |
| Temu | BLOCKED (JS rendering) | BLOCKED | NOT IMPLEMENTED | NOT IMPLEMENTED |
| Daraz | BLOCKED (JS rendering) | BLOCKED | NOT IMPLEMENTED | NOT IMPLEMENTED |

**Current workaround concern**: `marketplace_search.py` L131-137 inserts a synthetic placeholder review (`author="Verified Purchaser"`, `comment="Authentic product listing verified on {platform}."`) for any matched listing. This is fabricated data inserted into the pipeline and DB.

---

## 7. Current Development Stage Analysis

### Q1: What is the last stage demonstrably completed?

**Phase 7 infrastructure — with a critical validity caveat.**

All 7 phases are code-complete and the full pipeline runs end-to-end. However, Phase 7's review component was delivered using a synthetic benchmark dataset, making the review authenticity scoring and NLP classifier output scientifically invalid.

### Q2: What stage are we currently stuck at?

**Phase 7 — Review Model Validity.** The fake-review detector and all review metrics are derived from synthetic data with randomly assigned labels.

### Q3: What is the single biggest blocker?

> [!IMPORTANT]
> **The 100k synthetic review DB must be replaced by a real training pipeline built on the 701,528-row Amazon Beauty Reviews CSV. The OR/CG/INCENTIVIZED labelling needs a defensible methodology (heuristic proxies based on `verified_purchase`, rating extremes, and duplicate text detection). The TF-IDF model must be trained, evaluated (precision/recall/F1 on a 20k holdout), and saved as a persisted artifact.**

### Q4: Which earlier work can be reused?

All of the following are fully reusable without modification:
- CLIP model, centroid cache, image dataset
- OCR pipeline (3-engine cascade)
- All 7 database ORM models and persistence service
- Product matching engine and URL validator
- All frontend components and rendering logic
- FastAPI route structure
- Amazon Beauty Reviews CSV (already on disk, prepared copy available)

### Q5: Which work must be corrected?

| Item | File | Required Correction |
|:---|:---|:---|
| Synthetic 100k review DB | `data/reviews_100k.db`, `prepare_100k_reviews.py` | Replace with real Amazon data pipeline |
| TF-IDF classifier training source | `review_analysis_service.py` L48-55 | Retrain on real Amazon CSV with heuristic labels |
| Synthetic review placeholder | `marketplace_search.py` L131-137 | Remove fabricated review text |
| Daraz `img_url` NameError | `daraz_scraper.py` L80 | Fix undefined variable |
| Temu hardcoded rating/review | `temu_scraper.py` L74-75 | Remove fabricated defaults |
| Pydantic V2 deprecation | `product_service.py` L113-116 | `.dict()` -> `.model_dump()` |

### Q6: What is the next task we should perform?

**Build a real review training and evaluation pipeline from the Amazon CSV.**

Steps:
1. Create `data/build_real_review_dataset.py`
2. Sample 100,000 records from `beauty_reviews_prepared.csv` using stratified sampling
3. Apply proxy-heuristic labels: unverified + 5-star + detected duplicate text = CG candidate; verified=True + normal rating = OR
4. Create 80/20 train/test split (80,000 training, 20,000 testing)
5. Train TF-IDF + LogisticRegression classifier
6. Evaluate: precision, recall, F1 on 20k holdout
7. Save model as `ai-service/app/models/review_classifier.pkl`
8. Update `review_analysis_service.py` to load persisted model instead of retraining

### Q7: What tasks should NOT be started yet?

- Do NOT add proxy layers or new scrapers until the review model is valid
- Do NOT redesign CLIP architecture until the review problem is resolved
- Do NOT add new frontend pages until backend data validity is established
- Do NOT attempt production deployment with synthetic review data

---

## 8. Bugs Found During Audit (Read-Only — Not Fixed)

| # | File | Line | Bug | Severity |
|:---:|:---|:---:|:---|:---:|
| 1 | `daraz_scraper.py` | 80 | `img_url` referenced but never defined — NameError if Daraz cards ever parse | Medium |
| 2 | `temu_scraper.py` | 74-75 | Hardcoded `rating_val=4.2`, `review_count_val=8` — fabricated data in fallback | Medium |
| 3 | `product_service.py` | 113-116 | `.dict()` deprecated in Pydantic V2, will break in V3 | Low |
| 4 | `marketplace_search.py` | 131-137 | Synthetic placeholder review inserted into pipeline for matched listings | Data Integrity |
| 5 | Dataset folders | — | P013-P018 folder brand names differ from `selected_30_products_final.csv` entries | Data Integrity |

---

## 9. Prioritized Next Steps Roadmap

| Priority | Task | Reason | Dependencies | Completion Criteria |
|:---:|:---|:---|:---|:---|
| P1 (Critical) | Build real Amazon review pipeline (`data/build_real_review_dataset.py`) | Core validity — all review analysis currently synthetic | Amazon CSV on disk | Script samples 100k rows, applies heuristic labels, 80/20 split, saves SQLite + JSONL.gz |
| P2 (Critical) | Train and evaluate TF-IDF classifier on real Amazon data | Review model needs real data and measurable accuracy | P1 complete | Classifier persisted as `.pkl`; precision/recall/F1 measured on 20k holdout |
| P3 (Critical) | Update `review_analysis_service.py` to load persisted model | Eliminate synthetic re-training on cold start | P2 complete | Model loaded from file; accuracy metrics logged at startup |
| P4 (Medium) | Fix `daraz_scraper.py` `img_url` NameError | Latent crash bug unmasked if JS scraping is implemented | None | Variable defined or removed |
| P5 (Medium) | Remove Temu hardcoded rating/review values | Prevents fabricated data if Temu unblocks | None | `rating_val` defaults to None, not 4.2 |
| P6 (Medium) | Replace `.dict()` with `.model_dump()` in `product_service.py` | Pydantic V3 compatibility | None | Deprecation warnings eliminated |
| P7 (Medium) | Remove synthetic placeholder review from `marketplace_search.py` | Data integrity — fake review comment pollutes DB | None | `sample_reviews` only holds actual scraped data |
| P8 (Low) | Correct dataset folder / product ID alignment (P013-P030) | CLIP accuracy depends on correct folder-to-product mapping | P1-P3 complete | CSV entries match folder names in `image_model_dataset/` |
| P9 (Low) | Improve CLIP Top-1 accuracy (currently 30.82%) | Better identification accuracy | P8 complete | Dataset cleanup of 247 flagged images; threshold re-calibration |
| P10 (Future) | Real individual review text collection | Complete review authenticity pipeline | Amazon PA-API or labelled dataset access | `customer_reviews` table populated with real review text |

---

## 10. Known Risks and Limitations

| Risk | Impact | Mitigation |
|:---|:---:|:---|
| 100k review DB is synthetic; OR/CG labels are RNG-assigned | Critical | Replace with real Amazon data pipeline (P1-P3) |
| CLIP Top-1 accuracy is 30.82% — 2 in 3 products misidentified | High | Dataset cleanup + possible fine-tuning |
| Amazon scraping blocked by CAPTCHA in live environment | High | Accept limitation; transparently display "unavailable" |
| Temu JS rendering blocks all data access | High | Browser automation or remove from scope |
| Daraz img_url NameError masked by JS blocking | Medium | Fix before implementing JS scraping |
| Pydantic V2 -> V3 deprecation | Low-Medium | Proactively fix .dict() -> .model_dump() |
| Synthetic review placeholder in marketplace_search.py | Medium | Remove fabricated review comment from pipeline |
| P013-P018 folder/product ID mismatch | Medium | Audit and correct folder-to-ID mapping |

---

## 11. Executive Summary

**We are currently at Phase 7 (Review Dataset Integration) — infrastructure complete.**

**The main blocker is** that the 100,000-review dataset driving all review analysis, the OR/CG/INCENTIVIZED classifier labels, the reported review authenticity scores, and the TF-IDF deceptive review classifier are all derived from synthetically generated data produced by `data/prepare_100k_reviews.py`, not from the real 701,528-row Amazon Beauty Reviews CSV that is already present at `data/review_dataset/raw/amazon_beauty_reviews_dataset.csv`.

**The next task is** to build a real Amazon review sampling, heuristic-labelling, and model training pipeline (`data/build_real_review_dataset.py`) that selects 100,000 records from the Amazon CSV, applies defensible proxy heuristics for label assignment, creates a proper 80/20 train/test split, trains the TF-IDF + Logistic Regression classifier, evaluates it on the 20k holdout with precision/recall/F1 metrics, and saves the model as a persisted `.pkl` artifact — then updates `review_analysis_service.py` to load the real model instead of retraining from synthetic data.

---

*Report compiled by Antigravity AI Assistant (2026-10-16) — READ-ONLY audit. No code, database records, environment variables, or files were modified.*
