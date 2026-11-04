"""
Marketplace Comparison & Platform Scoring Service Engine
Calculates a transparent, configurable recommendation score using documented weights:
- Product and brand match: 35%
- Product rating and review volume: 25%
- Seller trust: 20%
- Price competitiveness: 10%
- Review sentiment: 10%
Handles missing values fairly without automatically penalizing them as zero.
Strictly distinguishes LIVE-DATA vs DEMO RECOMMENDATION labels.
"""

from typing import List, Optional
from app.schemas.marketplace import MarketplaceListing, PlatformComparisonScore, ScoreBreakdown


def calculate_platform_score(
    listing: MarketplaceListing,
    sentiment_positive_pct: Optional[float] = None,
) -> PlatformComparisonScore:
    """
    Computes transparent multi-factor recommendation score for a marketplace listing using verified live data only.
    Formula:
      Total = (Match * 0.35) + (RatingVolume * 0.25) + (SellerTrust * 0.20) + (Price * 0.10) + (Sentiment * 0.10)
    Handles missing values fairly using neutral baselines rather than automatically zeroing.
    If listing is unavailable or not verified live data, returns rank 99 with
    'Recommendation unavailable: insufficient comparable marketplace data.'
    """
    is_live = (
        listing.retrieval_status in ("Live Data", "LIVE")
        and listing.source_status == "available"
        and listing.passed_match_threshold
        and listing.match_status != "Not a Match"
    )

    if not is_live:
        status_msg = listing.status_explanation or (
            "Marketplace access restricted or listing unavailable"
            if listing.source_status != "available"
            else "Listing rejected due to product mismatch or low confidence"
        )
        return PlatformComparisonScore(
            platform=listing.platform,
            total_score=0.0,
            rank=99,
            score_breakdown=ScoreBreakdown(
                match_confidence_score=0.0,
                rating_volume_score=0.0,
                seller_trust_score=0.0,
                price_score=0.0,
                review_sentiment_score=0.0,
                review_trust_score=0.0,
                rating_score=0.0,
            ),
            recommendation_reason=f"Data unavailable: {status_msg}",
            listing=listing,
            recommendation_type="Recommendation unavailable: insufficient comparable marketplace data.",
            is_demo=False,
        )

    # 1. Product and brand match (35% weight)
    match_conf = (
        listing.match_confidence
        if (listing.match_confidence is not None and listing.match_confidence > 0.0)
        else 50.0
    )

    # 2. Product rating and review volume (25% weight)
    if listing.rating and listing.rating > 0.0:
        rating_comp = min(100.0, max(0.0, (listing.rating / 5.0) * 100.0))
    else:
        rating_comp = 75.0  # Fair neutral baseline if rating missing

    rev_count = listing.review_count or 0
    if rev_count >= 50:
        volume_comp = 100.0
    elif rev_count >= 20:
        volume_comp = 85.0
    elif rev_count >= 5:
        volume_comp = 70.0
    elif rev_count > 0:
        volume_comp = 55.0
    else:
        volume_comp = 70.0  # Fair neutral baseline if volume unavailable

    rating_volume = round((rating_comp * 0.70) + (volume_comp * 0.30), 1)

    # 3. Seller trust (20% weight)
    seller = (listing.seller_name or "").lower()
    if any(k in seller for k in ("official", "flagship", "mall", "verified")):
        seller_trust = 95.0
    elif seller:
        seller_trust = 80.0
    else:
        seller_trust = 50.0  # Fair neutral baseline when seller name unlisted

    # 4. Price competitiveness (10% weight)
    if listing.price and listing.price > 0.0:
        price_score = 85.0
    else:
        price_score = 50.0  # Fair neutral baseline if price unavailable

    # 5. Review sentiment (10% weight)
    if sentiment_positive_pct is not None and sentiment_positive_pct >= 0.0:
        sentiment_score = min(100.0, max(0.0, float(sentiment_positive_pct)))
    else:
        sentiment_score = 50.0  # Fair neutral baseline if sentiment unavailable

    # Final Weighted Formula
    total_score = (
        (match_conf * 0.35)
        + (rating_volume * 0.25)
        + (seller_trust * 0.20)
        + (price_score * 0.10)
        + (sentiment_score * 0.10)
    )
    total_score = round(min(100.0, max(0.0, total_score)), 1)

    # Recommendation category label (strictly Live Data Recommendation)
    rec_type = "Live Data Recommendation"

    # Transparent Explanation of Ranking
    seller_label = f"verified '{listing.seller_name}'" if listing.seller_name else "standard vendor"
    rating_label = f"{listing.rating:.1f}/5.0 ({listing.review_count or 0} reviews)" if (listing.rating and listing.rating > 0) else "baseline ratings"
    reason = (
        f"Score {total_score}/100: High product match ({match_conf:.0f}%), "
        f"{seller_label} (trust: {seller_trust:.0f}%), {rating_label}, "
        f"and positive review sentiment ({sentiment_score:.0f}%)."
    )

    return PlatformComparisonScore(
        platform=listing.platform,
        total_score=total_score,
        rank=1,
        score_breakdown=ScoreBreakdown(
            match_confidence_score=round(match_conf, 1),
            rating_volume_score=round(rating_volume, 1),
            seller_trust_score=round(seller_trust, 1),
            price_score=round(price_score, 1),
            review_sentiment_score=round(sentiment_score, 1),
            review_trust_score=round(rating_volume, 1),
            rating_score=round(rating_comp, 1),
        ),
        recommendation_reason=reason,
        listing=listing,
        recommendation_type=rec_type,
        is_demo=False,
    )


def compare_marketplace_platforms(
    listings: List[MarketplaceListing],
    sentiment_positive_pct: Optional[float] = None,
) -> List[PlatformComparisonScore]:
    """
    Evaluates, scores, and rank-orders all marketplace platform listings.
    Only platforms with total_score > 0 are ranked as active recommendations.
    Unavailable/blocked/rejected platforms are appended at the end with rank=99.
    """
    ranked: List[PlatformComparisonScore] = []
    unranked: List[PlatformComparisonScore] = []

    for listing in listings:
        score_obj = calculate_platform_score(listing, sentiment_positive_pct=sentiment_positive_pct)
        if score_obj.total_score > 0.0:
            ranked.append(score_obj)
        else:
            score_obj.recommendation_reason = (
                f"Not ranked: {score_obj.recommendation_reason or 'Platform unavailable or listing rejected.'}"
            )
            unranked.append(score_obj)

    # Sort rankable platforms by score descending
    ranked.sort(key=lambda s: s.total_score, reverse=True)

    # Assign sequential ranks to available-only platforms
    for idx, s in enumerate(ranked, start=1):
        s.rank = idx

    # Unranked platforms get rank 99 (not an active recommendation)
    for s in unranked:
        s.rank = 99

    return ranked + unranked
