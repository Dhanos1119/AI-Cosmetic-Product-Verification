"""
Review Analysis Service Module
Separates two distinct concerns:

A. SENTIMENT ANALYSIS (validated baseline)
   Uses the persisted TF-IDF + Logistic Regression model trained on 100,000 REAL Amazon Beauty
   reviews with RATING-DERIVED labels (see app/services/sentiment_service.py). It predicts
   positive / neutral / negative sentiment for actual review text only.
   Note: The model was trained using rating-derived sentiment labels and may have limited
   neutral-class performance due to class imbalance in rating-derived datasets.

B. SUSPICIOUS-REVIEW RISK DETECTION (Explainable Heuristic Indicator)
   No properly sourced, independently labelled real dataset of genuine vs fake reviews exists.
   Therefore authenticity_analysis_status is always NOT_VALIDATED and no synthetic classifier
   is presented as a real fake detector.
   Instead, an explainable heuristic risk indicator evaluates genuinely available evidence:
   - Duplicate or near-duplicate review comment text
   - Rating vs sentiment polarity conflicts (e.g. 5-star rating with negative text)
   - Temporal burst patterns (when calendar timestamps are available and n >= 5)
   - Abnormal reviewer concentration
   Returns INSUFFICIENT_DATA when fewer than 3 reviews are available.
   Clearly distinguished as a rule-based heuristic indicator, not a validated ML classifier.
"""

import sqlite3
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from collections import Counter

from app.services.sentiment_service import (
    analyze_sentiment,
    analyze_review_batch,
    get_model_info,
)

logger = logging.getLogger("ai_service.review_analysis")

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
REVIEWS_DB_PATH = BASE_DIR / "data" / "reviews_100k.db"  # legacy SYNTHETIC benchmark

AUTHENTICITY_STATUS = "NOT_VALIDATED"
AUTHENTICITY_NOTE = (
    "Review authenticity (genuine vs fake) has not been validated. No independently labelled "
    "real-world fraud dataset is available, so no genuine/fake percentage or ML trust score is reported. "
    "Heuristic suspicious-review indicators are provided for explainable risk assessment only."
)
SYNTHETIC_NOTE = (
    "SYNTHETIC BENCHMARK ONLY: generated from templates with randomly assigned OR/CG/INCENTIVIZED "
    "labels. Not real customer data and not evidence about any real product."
)


def _normalize_text_for_comparison(text: str) -> str:
    """Normalizes text by lowercasing and stripping punctuation to detect duplicate comments."""
    if not text:
        return ""
    cleaned = re.sub(r"[^\w\s]", "", text.lower())
    return " ".join(cleaned.split())


def _token_jaccard_similarity(text_a: str, text_b: str) -> float:
    """Computes word-level Jaccard similarity between two texts."""
    tokens_a = set(text_a.lower().split())
    tokens_b = set(text_b.lower().split())
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)
    return len(intersection) / len(union)


def evaluate_suspicious_review_risk(reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Explainable Suspicious-Review Risk Indicator based solely on genuinely available evidence.
    
    Checks:
    1. Duplicate or near-duplicate comment text
    2. Rating vs sentiment polarity conflicts (e.g. 5.0 rating with negative text, or 1.0 rating with positive text)
    3. Temporal bursts (if >= 5 reviews have calendar dates and > 50% fall on the same day)
    4. Abnormal reviewer concentration (same non-anonymous author posting 3+ times)
    
    Returns INSUFFICIENT_DATA when review count < 3.
    """
    usable = [r for r in (reviews or []) if (r.get("text") or r.get("comment") or r.get("body"))]
    total_count = len(usable)

    if total_count < 3:
        return {
            "status": "INSUFFICIENT_DATA",
            "risk_level": "INSUFFICIENT_DATA",
            "risk_score": None,
            "flag": False,
            "analyzed_review_count": total_count,
            "indicators_detected": [],
            "explanation": f"Insufficient customer review data ({total_count} review(s) available; minimum 3 required) to evaluate statistical suspicious-review patterns.",
            "disclaimer": (
                "Explainable heuristic risk indicator based on available metadata anomalies. "
                "Not a validated machine-learning classifier; does not prove fraud."
            ),
            "is_validated_ml_detector": False,
        }

    indicators_detected: List[Dict[str, Any]] = []

    # 1. Duplicate / Near-Duplicate Comment Text Check
    duplicate_groups = []
    seen_normalized = {}
    for idx, r in enumerate(usable):
        raw_text = r.get("text") or r.get("comment") or r.get("body") or ""
        norm = _normalize_text_for_comparison(raw_text)
        if len(norm) >= 15:  # Ignore very short generic words like "good", "nice"
            if norm in seen_normalized:
                duplicate_groups.append((seen_normalized[norm], idx, raw_text[:80]))
            else:
                seen_normalized[norm] = idx

    # Also check high fuzzy/Jaccard overlap for non-identical texts
    fuzzy_duplicates = []
    for i in range(len(usable)):
        for j in range(i + 1, len(usable)):
            text_i = usable[i].get("text") or usable[i].get("comment") or ""
            text_j = usable[j].get("text") or usable[j].get("comment") or ""
            if text_i and text_j and len(text_i) > 20 and len(text_j) > 20:
                if _normalize_text_for_comparison(text_i) != _normalize_text_for_comparison(text_j):
                    sim = _token_jaccard_similarity(text_i, text_j)
                    if sim >= 0.85:
                        fuzzy_duplicates.append((i, j, sim, text_i[:60]))

    if duplicate_groups or fuzzy_duplicates:
        total_dup = len(duplicate_groups) + len(fuzzy_duplicates)
        sample_snippets = [item[2] for item in (duplicate_groups + fuzzy_duplicates)[:3]]
        indicators_detected.append({
            "indicator": "DUPLICATE_REVIEW_TEXT",
            "severity": "HIGH",
            "description": f"Detected {total_dup} instance(s) of identical or near-duplicate review text across different submissions.",
            "evidence": sample_snippets,
        })

    # 2. Rating vs Sentiment Polarity Conflict Check
    polarity_conflicts = []
    for idx, r in enumerate(usable):
        rating = r.get("rating")
        sentiment = r.get("sentiment")
        confidence = r.get("sentiment_confidence") or 0.0

        if rating is not None and sentiment:
            try:
                r_val = float(rating)
                # 5-star rating with strong negative sentiment
                if r_val >= 4.5 and sentiment == "negative" and confidence >= 0.65:
                    text_snippet = (r.get("text") or r.get("comment") or "")[:80]
                    polarity_conflicts.append(
                        f"Review rated {r_val:.1f}/5.0 but predicted negative sentiment ({confidence * 100:.0f}% confidence): \"{text_snippet}\""
                    )
                # 1-star rating with strong positive sentiment
                elif r_val <= 2.0 and sentiment == "positive" and confidence >= 0.65:
                    text_snippet = (r.get("text") or r.get("comment") or "")[:80]
                    polarity_conflicts.append(
                        f"Review rated {r_val:.1f}/5.0 but predicted positive sentiment ({confidence * 100:.0f}% confidence): \"{text_snippet}\""
                    )
            except (ValueError, TypeError):
                pass

    if polarity_conflicts:
        indicators_detected.append({
            "indicator": "RATING_SENTIMENT_MISMATCH",
            "severity": "MODERATE",
            "description": f"Detected {len(polarity_conflicts)} review(s) where the star rating directly contradicts the review text sentiment.",
            "evidence": polarity_conflicts[:3],
        })

    # 3. Temporal Burst Check (when >= 5 reviews have calendar dates)
    dated_reviews = [r for r in usable if r.get("date") and str(r.get("date")).strip()]
    if len(dated_reviews) >= 5:
        # Extract calendar date (YYYY-MM-DD or readable prefix)
        dates = []
        for r in dated_reviews:
            d_str = str(r.get("date")).strip()
            # Normalize ISO timestamp or date prefix
            match = re.search(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})", d_str)
            if match:
                dates.append(match.group(1))
            elif len(d_str) >= 8:
                dates.append(d_str[:10])

        if dates:
            counts = Counter(dates)
            most_common_date, max_burst = counts.most_common(1)[0]
            if max_burst >= 4 and (max_burst / len(dates)) >= 0.50:
                indicators_detected.append({
                    "indicator": "TEMPORAL_BURST",
                    "severity": "MODERATE",
                    "description": f"Unusual burst: {max_burst} of {len(dates)} reviews ({max_burst / len(dates) * 100:.0f}%) were submitted on date '{most_common_date}'.",
                    "evidence": [f"{max_burst} reviews on {most_common_date}"],
                })

    # 4. Abnormal Reviewer Concentration Check
    named_authors = [
        str(r.get("author")).strip()
        for r in usable
        if r.get("author") and str(r.get("author")).strip().lower() not in ("anonymous", "daraz customer", "customer", "unknown", "")
    ]
    if len(named_authors) >= 4:
        author_counts = Counter(named_authors)
        for author, count in author_counts.most_common(2):
            if count >= 3:
                indicators_detected.append({
                    "indicator": "REPEATED_AUTHOR_PATTERN",
                    "severity": "LOW",
                    "description": f"Reviewer '{author}' authored {count} separate reviews for this listing.",
                    "evidence": [f"{count} reviews by '{author}'"],
                })

    # Risk Level Determination
    has_high = any(ind["severity"] == "HIGH" for ind in indicators_detected)
    has_moderate = any(ind["severity"] == "MODERATE" for ind in indicators_detected)

    if has_high or len(indicators_detected) >= 2:
        risk_level = "ELEVATED"
        flag = True
        explanation = f"Elevated suspicious-review risk: {len(indicators_detected)} anomaly indicator(s) detected across {total_count} collected reviews."
    elif has_moderate or len(indicators_detected) == 1:
        risk_level = "MODERATE"
        flag = False
        explanation = f"Moderate suspicious-review risk: 1 anomaly indicator detected across {total_count} collected reviews. Requires review."
    else:
        risk_level = "LOW"
        flag = False
        explanation = f"Low suspicious-review risk: No duplicate comment text, rating-sentiment conflicts, or temporal bursts detected among {total_count} reviews."

    return {
        "status": "EVALUATED",
        "risk_level": risk_level,
        "risk_score": None,
        "flag": flag,
        "analyzed_review_count": total_count,
        "indicators_detected": indicators_detected,
        "explanation": explanation,
        "disclaimer": (
            "Explainable heuristic risk indicator based on available metadata anomalies. "
            "Not a validated machine-learning classifier; does not prove fraud."
        ),
        "is_validated_ml_detector": False,
    }


def classify_review_sentiment(headline: str, body: str) -> Dict[str, Any]:
    """
    Sentiment (positive/neutral/negative) for one review using the persisted model.
    Includes explicit authenticity status: this endpoint never judges fake vs genuine.
    """
    res = analyze_sentiment(body, headline)
    res["authenticity_analysis_status"] = AUTHENTICITY_STATUS
    res["authenticity_note"] = AUTHENTICITY_NOTE
    return res


def build_marketplace_sentiment(real_reviews: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Sentiment over ACTUAL review text collected from a documented marketplace source.
    If no review text exists, returns an explicit empty status (nothing is fabricated).
    Enriches each review with its predicted sentiment and confidence.
    """
    usable = [
        r for r in (real_reviews or [])
        if (
            str(r.get("text") or "").strip()
            or str(r.get("comment") or "").strip()
            or str(r.get("body") or "").strip()
        )
    ]
    if not usable:
        return {
            "status": "NO_REVIEW_TEXT_AVAILABLE",
            "analyzed_count": 0,
            "counts": {"positive": 0, "neutral": 0, "negative": 0},
            "explanation": "No actual customer review text was collected for this product, so no live sentiment is reported.",
            "analyzed_reviews": [],
        }

    enriched_reviews: List[Dict[str, Any]] = []
    counts = {"positive": 0, "neutral": 0, "negative": 0}

    for r in usable:
        text = r.get("text") or r.get("comment") or r.get("body") or ""
        title = r.get("title") or r.get("headline") or ""
        s_res = analyze_sentiment(text, title)

        enriched_item = dict(r)
        if s_res.get("status") == "ok":
            sent_label = s_res["sentiment"]
            counts[sent_label] += 1
            enriched_item["sentiment"] = sent_label
            enriched_item["sentiment_confidence"] = s_res.get("confidence")
            enriched_item["probabilities"] = s_res.get("probabilities")
        else:
            enriched_item["sentiment"] = None
            enriched_item["sentiment_confidence"] = None
            enriched_item["probabilities"] = None

        enriched_reviews.append(enriched_item)

    analyzed = sum(counts.values())
    model_info = get_model_info()

    return {
        "status": "completed" if analyzed > 0 else "unavailable",
        "analyzed_count": analyzed,
        "counts": counts,
        "model_version": model_info.get("model_version"),
        "label_type": "RATING_DERIVED",
        "source": "marketplace_review_text",
        "analyzed_reviews": enriched_reviews,
        "note": "Trained on rating-derived labels from Amazon Beauty reviews. May have limited neutral-class performance due to class distribution."
    }


def _synthetic_benchmark_summary(
    product_id: Optional[str], brand_name: Optional[str], category: Optional[str]
) -> Optional[Dict[str, Any]]:
    """Development-only summary of the legacy synthetic DB. Never a real-world claim."""
    if not REVIEWS_DB_PATH.exists():
        return None
    try:
        conn = sqlite3.connect(REVIEWS_DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        rows: list = []
        if product_id and product_id.startswith("P"):
            cur.execute("SELECT * FROM reviews WHERE product_id = ?", (product_id,))
            rows = cur.fetchall()
        if not rows and brand_name:
            cur.execute("SELECT * FROM reviews WHERE LOWER(brand) LIKE ?", (f"%{brand_name.strip().lower()}%",))
            rows = cur.fetchall()
        if not rows and category:
            cur.execute("SELECT * FROM reviews WHERE LOWER(category) LIKE ?", (f"%{category.strip().lower()}%",))
            rows = cur.fetchall()
        if not rows:
            conn.close()
            return None
        total = len(rows)
        ratings = [r["rating"] for r in rows if r["rating"] is not None]
        result = {
            "data_scope": "SYNTHETIC_BENCHMARK",
            "disclaimer": SYNTHETIC_NOTE,
            "total_reviews": total,
            "average_rating": round(sum(ratings) / len(ratings), 2) if ratings else None,
            "label_breakdown": {
                "genuine_count": sum(1 for r in rows if r["label"] == "OR"),
                "fake_cg_count": sum(1 for r in rows if r["label"] == "CG"),
                "incentivized_count": sum(1 for r in rows if r["label"] == "INCENTIVIZED"),
            },
        }
        conn.close()
        return result
    except Exception as exc:
        logger.error(f"Synthetic benchmark query failed: {exc}")
        return None


def analyze_product_reviews(
    product_id: Optional[str] = None,
    brand_name: Optional[str] = None,
    product_name: Optional[str] = None,
    category: Optional[str] = None,
    real_reviews: Optional[List[Dict[str, Any]]] = None,
    include_synthetic_benchmark: bool = False,
) -> Dict[str, Any]:
    """
    Builds the review section of the analysis response.

    - Sentiment is computed only from `real_reviews` (actual review text from a documented source).
    - Authenticity is reported as NOT_VALIDATED; no synthetic numbers are presented as real.
    - Evaluates explainable suspicious review indicators based only on genuinely available evidence.
    - `include_synthetic_benchmark=True` adds the legacy synthetic summary under a labelled key.
    """
    marketplace_sentiment = build_marketplace_sentiment(real_reviews)
    model_info = get_model_info()

    # Calculate actual average rating and verified buyer percentage from real reviews
    usable_reviews = [r for r in (real_reviews or []) if (r.get("text") or r.get("comment") or r.get("body"))]
    ratings = [float(r["rating"]) for r in usable_reviews if r.get("rating") is not None and float(r["rating"]) > 0.0]
    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else None

    verified_count = sum(1 for r in usable_reviews if r.get("verified_purchase") is True)
    verified_pct = round((verified_count / len(usable_reviews)) * 100.0, 1) if usable_reviews else None

    # Evaluate explainable suspicious-review risk indicators
    suspicious_risk = evaluate_suspicious_review_risk(marketplace_sentiment.get("analyzed_reviews", []))

    result: Dict[str, Any] = {
        "status": "completed",
        "review_dataset_source": "none_real_review_text" if not real_reviews else "marketplace_review_text",
        "authenticity_analysis_status": AUTHENTICITY_STATUS,
        "authenticity_note": AUTHENTICITY_NOTE,
        "review_authenticity_score": None,
        "authenticity_status": "Not validated",
        "suspicious_review_flag": suspicious_risk.get("flag", False),
        "suspicious_review_risk": suspicious_risk,
        "average_rating": avg_rating,
        "verified_buyer_percentage": verified_pct,
        "sentiment_label": "Not available (no actual review text)",
        "marketplace_sentiment": marketplace_sentiment,
        "sentiment_model": model_info,
        "analyzed_reviews": marketplace_sentiment.get("analyzed_reviews", []),
        "summary": (
            "Review authenticity is NOT VALIDATED. "
            + (
                f"Sentiment analyzed on {marketplace_sentiment['analyzed_count']} actual review(s). "
                f"Suspicious review risk: {suspicious_risk.get('risk_level')}."
                if marketplace_sentiment["analyzed_count"]
                else "No actual customer review text is available for this product."
            )
        ),
    }

    if marketplace_sentiment["analyzed_count"]:
        c = marketplace_sentiment["counts"]
        top = max(c, key=c.get)
        result["sentiment_label"] = top.capitalize()

    if include_synthetic_benchmark:
        bench = _synthetic_benchmark_summary(product_id, brand_name, category)
        if bench:
            result["synthetic_benchmark"] = bench

    return result
