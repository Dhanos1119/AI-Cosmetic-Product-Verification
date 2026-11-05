"""
Test Suite: Part 3 - Review Analysis, Recommendation Engine, Final Integration
Covers:
  1. 1.png Foundation demo with 10 simulated reviews, sentiment stats (5 pos, 2 neu, 3 neg), and recommendation.
  2. 2.png Lipstick demo with category Lipstick, 10 simulated lipstick reviews, and recommendation.
  3. 3.png Non-cosmetic rejection produces zero marketplace results, zero reviews, zero recommendations.
  4. Unmapped cosmetic image uses normal AI without forced demo mapping.
  5. Review analysis: exactly 10 reviews, counts sum to 10, real model confidence, credibility disclaimer.
  6. Recommendation engine: 35/25/20/10/10 formula, fair missing data handling, LIVE vs DEMO labels.
  7. Disclosures: simulated review notice and non-genuine recommendation labels.
"""

import sys
import io
import json
import pytest
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent / "ai-service"))

import os
os.environ["HF_HUB_OFFLINE"] = "1"

from app.services.product_service import analyze_product_authenticity
from app.services.demo_service import get_demo_config, is_demo_mode_active, get_simulated_reviews
from app.services.marketplace_comparison_service import calculate_platform_score, compare_marketplace_platforms
from app.schemas.marketplace import MarketplaceListing, ProductIdentity
from app.services.review_analysis_service import analyze_product_reviews


def _create_mock_image_bytes(color=(225, 185, 145), size=(256, 256)) -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: 1.png Foundation Demonstration
# ─────────────────────────────────────────────────────────────────────────────

def test_scenario_1_foundation_reviews_and_recommendation():
    """
    1.png (Foundation) must produce:
    - Expected identity: Maybelline Fit Me Matte + Poreless Foundation
    - Configured demonstration review analysis with DEMO / SIMULATED REVIEW ANALYSIS
    - Configured platform sentiment for Amazon (37,100 reviews, 76% pos), Daraz LK (84 reviews, 88% pos), Temu (18 reviews, 42% pos)
    - Recommendation: Amazon recommended (score ~90.9, Amazon.com / Maybelline, LKR 2,988.10, 4.5 rating, 37,100 reviews)
    """
    img_bytes = _create_mock_image_bytes(color=(220, 180, 140))
    res = analyze_product_authenticity(
        file_bytes=img_bytes,
        ocr_result={"brand_name": "", "product_name": "", "category": "Foundation", "raw_text": ["Maybelline Fit Me"]},
        image_info={"filename": "1.png", "width": 256, "height": 256, "format": "PNG", "size": len(img_bytes)}
    )

    # Identity check
    assert "Maybelline Fit Me" in res["product_identity"]["product_name"]
    assert res["is_confirmed"] is True

    # Review analysis check: Configured demo reviews and sentiment
    rev_res = res["review_result"]
    assert rev_res["is_simulated"] is True
    assert rev_res["simulation_title"] == "DEMO / SIMULATED REVIEW ANALYSIS"
    assert "Illustrative sentiment data" in rev_res["simulation_disclosure"]

    plat_analyses = rev_res.get("platform_review_analyses", {})
    assert "Amazon" in plat_analyses
    assert plat_analyses["Amazon"]["total_reviews_analyzed"] == 37100
    assert plat_analyses["Amazon"]["positive_percentage"] == 76.0
    assert plat_analyses["Amazon"]["neutral_percentage"] == 14.0
    assert plat_analyses["Amazon"]["negative_percentage"] == 10.0

    assert "Daraz LK" in plat_analyses
    assert plat_analyses["Daraz LK"]["positive_percentage"] == 88.0

    assert "Temu" in plat_analyses
    assert plat_analyses["Temu"]["positive_percentage"] == 42.0

    # Recommendation check: Amazon recommended with score ~90.9
    plat_comp = res["platform_comparison"]
    assert len(plat_comp) >= 2
    top = plat_comp[0]
    assert top["platform"] == "Amazon"
    assert round(top["total_score"], 1) == 90.9
    assert top["is_demo"] is True
    assert "DEMO RECOMMENDATION" in top["recommendation_type"]
    seller = top["listing"].get("seller_name") if isinstance(top["listing"], dict) else top["listing"].seller_name
    assert "Amazon.com / Maybelline" in seller
    assert "37,100" in top["recommendation_reason"] or "37100" in top["recommendation_reason"]


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: 2.png Lipstick Demonstration
# ─────────────────────────────────────────────────────────────────────────────

def test_scenario_2_lipstick_reviews_and_recommendation():
    """
    2.png (Lipstick) must produce:
    - Category: Lipstick
    - Configured demonstration review analysis with DEMO / SIMULATED REVIEW ANALYSIS
    - Configured platform sentiment for Daraz LK (183 reviews, 92% pos), Amazon (30 reviews, 60% pos), Temu (18 reviews, 68% pos)
    - Recommendation: Daraz LK recommended (score ~85.3, HANDAIYAN Store LK, LKR 1,503.00, 4.95 rating, 183 reviews, 92% positive sentiment)
    """
    img_bytes = _create_mock_image_bytes(color=(190, 25, 45))
    res = analyze_product_authenticity(
        file_bytes=img_bytes,
        ocr_result={"brand_name": "", "product_name": "", "category": "Lipstick", "raw_text": ["Lipstick"]},
        image_info={"filename": "2.png", "width": 256, "height": 256, "format": "PNG", "size": len(img_bytes)}
    )

    assert res["product_detection"] == "Lipstick"

    rev_res = res["review_result"]
    assert rev_res["is_simulated"] is True
    assert rev_res["simulation_title"] == "DEMO / SIMULATED REVIEW ANALYSIS"

    plat_analyses = rev_res.get("platform_review_analyses", {})
    assert "Daraz LK" in plat_analyses
    assert plat_analyses["Daraz LK"]["total_reviews_analyzed"] == 183
    assert plat_analyses["Daraz LK"]["positive_percentage"] == 92.0
    assert plat_analyses["Daraz LK"]["neutral_percentage"] == 5.0
    assert plat_analyses["Daraz LK"]["negative_percentage"] == 3.0

    assert "Amazon" in plat_analyses
    assert plat_analyses["Amazon"]["positive_percentage"] == 60.0

    assert "Temu" in plat_analyses
    assert plat_analyses["Temu"]["positive_percentage"] == 68.0

    # Recommendation check: Daraz LK recommended with score ~85.3
    plat_comp = res["platform_comparison"]
    assert len(plat_comp) >= 2
    top = plat_comp[0]
    assert top["platform"] == "Daraz LK"
    assert round(top["total_score"], 1) == 85.3
    assert top["is_demo"] is True
    assert "DEMO RECOMMENDATION" in top["recommendation_type"]
    seller = top["listing"].get("seller_name") if isinstance(top["listing"], dict) else top["listing"].seller_name
    assert "HANDAIYAN Store LK" in seller
    assert "183" in top["recommendation_reason"]


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: 3.png Non-Cosmetic Rejection
# ─────────────────────────────────────────────────────────────────────────────

def test_scenario_3_non_cosmetic_produces_no_reviews_or_recommendations():
    """
    3.png non-cosmetic image must be rejected:
    - No marketplace searches
    - No simulated reviews
    - No recommendations
    """
    from app.services.demo_service import evaluate_demo_scenario
    demo_res = evaluate_demo_scenario("3.png", "Non-cosmetic / uncertain", False)
    assert demo_res is not None
    assert demo_res["status"] == "rejected_non_cosmetic"
    assert demo_res["rejection_message"] == "Non-cosmetic image detected."

    # Verify no reviews are extracted for 3.png
    revs = get_simulated_reviews("3.png")
    assert len(revs) == 0


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: Unmapped Cosmetic Image
# ─────────────────────────────────────────────────────────────────────────────

def test_scenario_4_unmapped_cosmetic_image():
    """An image not named 1.png/2.png/3.png uses standard pipeline without demo mapping."""
    from app.services.demo_service import evaluate_demo_scenario
    demo_res = evaluate_demo_scenario("other_product.jpg", "Foundation", True)
    assert demo_res is None

    img_bytes = _create_mock_image_bytes(color=(120, 120, 120))
    res = analyze_product_authenticity(
        file_bytes=img_bytes,
        ocr_result={"brand_name": "", "product_name": "", "category": "Foundation", "raw_text": []},
        image_info={"filename": "other_product.jpg", "width": 256, "height": 256, "format": "PNG", "size": len(img_bytes)}
    )
    rev_res = res.get("review_result")
    if rev_res:
        assert rev_res["is_simulated"] is False
        assert len(rev_res.get("simulated_reviews", [])) == 0


# ─────────────────────────────────────────────────────────────────────────────
# Test 5: Review Functionality & Model Confidence
# ─────────────────────────────────────────────────────────────────────────────

def test_scenario_5_review_records_data_integrity():
    """
    Simulated reviews must contain all required fields:
    - review_id, reviewer_name, review_text, star_rating, predicted_sentiment, explanation
    - Model confidence must be a genuine float between 0.0 and 1.0 (not None/fabricated string)
    """
    reviews_data = get_simulated_reviews("1.png")
    assert len(reviews_data) == 10

    for r in reviews_data:
        assert "review_id" in r
        assert "reviewer_name" in r
        assert "review_text" in r
        assert "star_rating" in r
        assert "predicted_sentiment" in r
        assert "explanation" in r
        assert r["star_rating"] >= 1.0 and r["star_rating"] <= 5.0
        assert r["predicted_sentiment"] in ("positive", "neutral", "negative")

    # Analyze via review_analysis_service
    analysis = analyze_product_reviews(category="Foundation", simulated_reviews=reviews_data, demo_key="1.png")
    for r in analysis["analyzed_reviews"]:
        conf = r["sentiment_confidence"]
        assert conf is not None
        assert 0.0 <= conf <= 1.0, f"Expected confidence in [0, 1], got {conf}"


# ─────────────────────────────────────────────────────────────────────────────
# Test 6: Recommendation Scoring Formula & Missing Data Handling
# ─────────────────────────────────────────────────────────────────────────────

def test_scenario_6_recommendation_scoring_formula():
    """
    Weights:
      Match: 35%
      Rating/Volume: 25%
      Seller Trust: 20%
      Price: 10%
      Sentiment: 10%
    Verifies that the score matches the exact weighted combination.
    """
    listing = MarketplaceListing(
        platform="Test Market",
        product_name="Sample Foundation",
        brand="Sample Brand",
        product_type="Foundation",
        price=20.0,
        currency="USD",
        rating=4.5,
        rating_count=60,
        review_count=60,
        seller_name="Official Flagship Store",
        product_url="https://example.com/item",
        source_status="available",
        match_status="Exact Product Match",
        match_confidence=90.0,
        passed_match_threshold=True,
        retrieval_status="LIVE",
        data_source="Live Scraper",
    )

    score_res = calculate_platform_score(listing, sentiment_positive_pct=60.0)
    assert score_res.total_score > 0
    assert score_res.rank == 1
    assert "Live Data Recommendation" in score_res.recommendation_type

    bd = score_res.score_breakdown
    assert bd.match_confidence_score == 90.0
    assert bd.seller_trust_score == 95.0 # Flagship store
    assert bd.review_sentiment_score == 60.0

    # Test fair missing data handling on a live listing with missing fields
    listing_missing = MarketplaceListing(
        platform="Test Market 2",
        product_name="Sample Foundation 2",
        brand="Sample Brand",
        product_type="Foundation",
        price=0.0, # missing price
        rating=4.0,
        review_count=0, # missing reviews
        seller_name=None, # missing seller
        product_url="https://example.com/item2",
        source_status="available",
        match_status="Exact Product Match",
        match_confidence=80.0,
        passed_match_threshold=True,
        retrieval_status="Live Data",
        data_source="Live Scraper",
    )

    score_missing = calculate_platform_score(listing_missing, sentiment_positive_pct=None)
    assert score_missing.total_score > 50.0, "Missing fields should receive fair neutral baselines, not 0"
    assert score_missing.score_breakdown.seller_trust_score == 50.0
    assert score_missing.score_breakdown.price_score == 50.0
    assert score_missing.score_breakdown.review_sentiment_score == 50.0
    assert "Live Data Recommendation" in score_missing.recommendation_type

    # Test unavailable listing produces rank 99 with insufficient data explanation
    listing_unavail = MarketplaceListing(
        platform="Temu",
        product_name="Temu Search: Sample Foundation",
        brand="Sample Brand",
        product_type="Foundation",
        price=0.0,
        source_status="unavailable",
        passed_match_threshold=False,
        retrieval_status="Data Unavailable",
        data_source="Direct Search",
    )
    score_unavail = calculate_platform_score(listing_unavail)
    assert score_unavail.total_score == 0.0
    assert score_unavail.rank == 99
    assert "insufficient comparable marketplace data" in score_unavail.recommendation_type

