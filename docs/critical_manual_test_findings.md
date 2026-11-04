# Critical Manual Test Findings

**Date:** 2026-10-18
**Scope:** Two critical issues identified in the live FastAPI debug payload
**Result:** Both issues confirmed, root causes traced, fixes implemented and verified.
**Test result:** 115 tests pass (18 new, 97 existing), 0 failures.

---

## Issue 1 — CLIP Wrong Product Match

### Observed symptom
OCR identified "Fit Me MATTE+PORELESS" foundation (Maybelline, category: Foundation_Base),
but CLIP returned P001 "colourpop Lippie Pencil", category: Lip_Products, similarity: 78.5%.
`product_identity.category` was set to Lip_Products despite OCR correctly detecting Foundation_Base.

### Root causes (traced, not assumed)

#### RC1-A — Hardcoded P001 exception fallback
`clip_service.py` `compute_clip_similarity()` exception path returned:
```python
"matched_product_id": "P001",
"matched_product_name": "Lippie Pencil",
"matched_brand": "Colourpop",
"matched_category": "Lip_Products",
"similarity_percentage": 75.0,
"confidence_level": "Moderate",
```
Any runtime error (GPU, import, OOM) silently emitted a confident P001/Lip_Products result
that downstream code accepted as a real match.

#### RC1-B — Centroid catalog cannot discriminate product images
Diagnostic measurement of all 30 precomputed centroids:
- Mean pairwise cosine similarity: **0.87** (range 0.00–0.96)
- Std of pairwise similarity: 0.17

All centroids are densely clustered. Every uploaded image lands at cosine ~0.78–0.96
against every product. Whichever centroid is at the tip of the query vector wins by noise,
not by genuine visual similarity. The 30 products span 5 categories of stock-photo cosmetic
packaging — the catalog simply does not discriminate at this level.

#### RC1-C — CLIP category overrides OCR category unconditionally
In `product_service.py`:
```python
matched_category = clip_res.get("matched_category") or category
```
When CLIP returned Lip_Products (from P001), it overwrote the OCR-detected Foundation_Base
even though OCR had valid text evidence ("Fit Me MATTE+PORELESS" foundation).

#### RC1-D — Maybelline Fit Me Foundation not in the 30-product catalog
The dataset (P001–P030) contains no Maybelline product. The closest foundation products are:
P007 (Deciem), P008 (W3llpeople), P009 (RejuvaMinerals), etc. CLIP cannot match to a product
that is not in the reference catalog.

### Fixes applied

| File | Change |
|------|--------|
| `clip_service.py` | Added `ocr_category` parameter; category mismatch gate sets `catalog_category_mismatch=True` and caps confidence to Low |
| `clip_service.py` | Added discrimination margin check: rank-1 minus rank-2 similarity < 2pp → confidence capped to Low |
| `clip_service.py` | Exception fallback now returns `matched_product_id=None`, `status="error"`, `similarity_percentage=0.0` — no hardcoded P001 |
| `clip_service.py` | New output fields: `discrimination_margin`, `catalog_category_mismatch` |
| `product_service.py` | Passes `ocr_category` into CLIP; `has_reliable_clip` requires High/Moderate confidence AND no category mismatch AND margin >= 2% |
| `product_service.py` | When CLIP unreliable: OCR brand/product/category wins; `prod_id` set to None |

### Verified test results (new tests)

| Test | Result |
|------|--------|
| `test_clip_category_mismatch_sets_confidence_low` | PASS |
| `test_clip_no_mismatch_when_categories_match` | PASS |
| `test_clip_poor_discrimination_margin_sets_confidence_low` | PASS |
| `test_clip_exception_fallback_does_not_hardcode_p001` | PASS |
| `test_clip_discrimination_margin_field_always_present` | PASS |
| `test_clip_catalog_category_mismatch_field_always_present` | PASS |
| `test_product_identity_category_uses_ocr_not_clip_on_mismatch` | PASS |
| `test_product_identity_prod_id_is_none_when_clip_unreliable` | PASS |

### What was NOT done
- The catalog (P001–P030) was not modified. Maybelline Fit Me is not in it and will not
  be fabricated. When OCR identifies a product not in the catalog, CLIP now correctly
  returns Low confidence rather than presenting an unrelated product at Moderate confidence.
- No centroid cache was deleted or rebuilt.

---

## Issue 2 — Contradictory Authenticity Output

### Observed symptom
Same payload where review authenticity was correctly reported as NOT_VALIDATED and no real
review text was available, but simultaneously:
- `authenticity_prediction`: "Likely Authentic (82.8%)"
- `overall_authenticity_score`: 82.8
- `recommendation`: "Packaging matches standard brand specifications with high confidence."

### Root causes (traced, not assumed)

#### RC2-A — CLIP similarity used as authentic proxy regardless of reliability
`authenticity_service.py` used:
```python
clip_score = clip_data.get("similarity_percentage", 75.0)
```
The default was 75.0 (not 0.0), so even when CLIP had no result it contributed positively.
The unreliable P001 match (78.5%) was accepted at face value, contributing 40% × 78.5 = 31.4
points to the ensemble score.

#### RC2-B — Misleading prediction badges implied genuine product
The old thresholds:
- >= 85%: "Authentic Product" with "Verified authentic packaging and brand attributes."
- >= 70%: "Likely Authentic" with "Packaging matches standard brand specifications with high confidence."

These labels are fundamentally misleading: the score measures packaging appearance similarity
to stock-photo reference images, not physical product authenticity. There is no ground-truth
label for "genuine vs counterfeit" in this system.

#### RC2-C — No clear scope statement on the score
The API response gave no indication of what the 82.8% score actually measured.
A consumer reading "Likely Authentic (82.8%)" would reasonably conclude the product
was verified as genuine.

### Fixes applied

| File | Change |
|------|--------|
| `authenticity_service.py` | CLIP score zeroed when `confidence_level` is Low, `catalog_category_mismatch` is True, or `discrimination_margin` < 2pp |
| `authenticity_service.py` | Default CLIP contribution changed from 75.0 to 0.0 |
| `authenticity_service.py` | Ensemble weights renormalize correctly depending on which components are present |
| `authenticity_service.py` | Old labels removed: "Authentic Product", "Likely Authentic" |
| `authenticity_service.py` | New scope-qualified labels: "Packaging Verified (High Confidence)", "Packaging Plausible (Moderate Confidence)", "Packaging Uncertain (Low Confidence)", "Packaging Suspicious (Very Low Confidence)" |
| `authenticity_service.py` | `recommendation` text no longer implies genuine product; includes explicit "does not confirm the physical product is genuine" when applicable |
| `authenticity_service.py` | New fields: `score_scope`, `clip_component_included`, `score_breakdown.clip_reliable`, `score_breakdown.clip_contributed` |

### Verified test results (new tests)

| Test | Result |
|------|--------|
| `test_unreliable_clip_does_not_inflate_score` | PASS |
| `test_authenticity_labels_do_not_claim_genuine_when_clip_unreliable` | PASS |
| `test_authenticity_recommendation_does_not_imply_genuine_without_validation` | PASS |
| `test_authenticity_score_breakdown_has_clip_reliable_field` | PASS |
| `test_authenticity_result_has_score_scope_field` | PASS |
| `test_reliable_clip_contributes_to_score` | PASS |

### Score for the observed payload (post-fix)
With OCR conf=0.9, brand=Maybelline (valid), CLIP unreliable (zeroed), review NOT_VALIDATED:
- Weights: OCR 75%, Packaging 25%
- OCR score = (0.9 × 70) + 30 = 93.0
- Packaging score = 100.0 (image >= 600px, valid)
- Ensemble = (93.0 × 0.75) + (100.0 × 0.25) = 94.75 → capped → ~94.8
- Badge: "Packaging Verified (High Confidence)" — scope-qualified, not "Authentic Product"
- Recommendation: explicitly states "does not confirm the physical product is genuine"

---

## Issue 3 — product_identity.category = Lip_Products despite OCR identifying Foundation

### Root cause
`product_service.py` line (pre-fix):
```python
matched_category = clip_res.get("matched_category") or category
```
When OCR had valid brand/product text but CLIP returned Lip_Products, the CLIP category
was used because it was the first non-None value. OCR category was only used as fallback
when CLIP returned None/empty — never the other way around.

### Fix
OCR-derived category is now primary when `has_valid_ocr=True`. CLIP category is only used
when CLIP is reliable AND there is no category mismatch:
```python
if has_reliable_clip and not clip_mismatch and clip_res.get("matched_category"):
    matched_category = clip_res["matched_category"]
else:
    matched_category = category   # OCR/detected category wins
```

---

## Issue 4 — Marketplace comparison lists all unavailable platforms with zero scores and ranks

### Root cause
`compare_marketplace_platforms()` sorted all listings (available + unavailable) and assigned
sequential ranks 1, 2, 3 to all of them. When all three marketplaces were blocked/unavailable,
they all received rank 1, 2, 3 with score 0.0, presenting them as ranked recommendations.
Sort key `(s.listing.source_status == "available", s.total_score)` sorted booleans: False < True,
so in a tuple sort `(False, 0.0)` vs `(False, 0.0)` they stayed in arbitrary order but all
got sequential low ranks, not "no rank".

### Fix
`compare_marketplace_platforms()` now separates ranked (score > 0) from unranked (score == 0):
- Ranked platforms: sorted by score descending, assigned ranks 1, 2, 3, ...
- Unranked platforms: rank = 99, `recommendation_reason` prepended with "Not ranked:"
- When all platforms are unavailable: no platform has rank 1, 2, or 3

### Verified test results

| Test | Result |
|------|--------|
| `test_unavailable_platforms_not_ranked_as_recommendations` | PASS |
| `test_unavailable_platforms_recommendation_reason_says_not_ranked` | PASS |
| `test_available_platform_ranked_before_unavailable` | PASS |
| `test_zero_score_listing_not_presented_as_recommendation` | PASS |

---

## Full Test Results

```
115 passed, 7 warnings (torch quantization deprecation notices, not errors)
```

| Test file | Tests | Result |
|-----------|-------|--------|
| `test_critical_manual_test_findings.py` | 18 | All pass (new) |
| `test_marketplace_scraper_fixes.py` | 29 | All pass (existing) |
| `test_marketplace_url_validation.py` | 10 | All pass (existing) |
| `test_marketplace_persistence.py` | 8 | All pass (existing) |
| `test_marketplace_integrity_audit.py` | 10 | All pass (existing) |
| `test_phase6_matching_evidence_quality.py` | 8 | All pass (existing) |
| `test_database_persistence.py` | 10 | All pass (existing) |
| `test_review_analysis.py` | 9 | All pass (existing) |
| `test_api_analyze_live.py` | 1 | All pass (existing) |
| Other existing tests | 12 | All pass (existing) |

**Total: 115 passed, 0 failed, 0 regressions.**

---

## Files Modified

| File | Change |
|------|--------|
| `ai-service/app/services/clip_service.py` | `ocr_category` param, category mismatch gate, discrimination margin gate, honest exception fallback |
| `ai-service/app/services/product_service.py` | Passes `ocr_category`; OCR category wins over CLIP on mismatch; `has_reliable_clip` requires margin >= 2% |
| `ai-service/app/services/authenticity_service.py` | CLIP zeroed when unreliable; scope-qualified badges; honest recommendations; new output fields |
| `ai-service/app/services/marketplace_comparison_service.py` | Separates ranked vs unranked; unavailable platforms get rank=99 |
| `tests/test_critical_manual_test_findings.py` | 18 new regression tests (created) |

---

## What Was NOT Changed

- No database records deleted or reset
- No catalog embeddings or centroids modified
- No product URLs, prices, ratings, or reviews fabricated
- Review authenticity remains NOT_VALIDATED
- Marketplace anti-bot protections not bypassed
- The 30-product catalog (P001–P030) is unchanged; Maybelline is correctly absent
