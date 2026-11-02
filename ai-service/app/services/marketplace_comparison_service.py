"""
Marketplace Comparison & Platform Scoring Service Engine
Calculates a transparent platform comparison score using documented weights:
- Review Trust: 40%
- Rating Score: 25%
- Seller Trust: 20%
- Product Match Confidence: 15%
"""

from typing import List
from app.schemas.marketplace import MarketplaceListing, PlatformComparisonScore, ScoreBreakdown

def calculate_platform_score(listing: MarketplaceListing) -> PlatformComparisonScore:
    """
    Computes transparent multi-factor score for a marketplace listing.
    Formula: Total = (ReviewTrust * 0.40) + (Rating * 0.25) + (SellerTrust * 0.20) + (MatchConf * 0.15)
    """
    if listing.source_status != "available" or listing.match_status == "Not a Match" or not listing.passed_match_threshold:
        status_msg = listing.status_explanation or (
            "Marketplace access restricted" if listing.source_status != "available"
            else "Listing rejected due to product mismatch or low confidence"
        )
        return PlatformComparisonScore(
            platform=listing.platform,
            total_score=0.0,
            rank=99,
            score_breakdown=ScoreBreakdown(
                review_trust_score=0.0,
                rating_score=0.0,
                seller_trust_score=0.0,
                match_confidence_score=0.0
            ),
            recommendation_reason=f"Data unavailable: {status_msg}",
            listing=listing
        )

    # Defensive Gate (Task 8): Do not generate marketplace ranking scores when required real rating/review data is unavailable
    has_real_rating = (listing.rating is not None and listing.rating > 0.0)
    has_real_reviews = (listing.review_count is not None and listing.review_count > 0) or bool(listing.reviews)
    if not has_real_rating and not has_real_reviews:
        return PlatformComparisonScore(
            platform=listing.platform,
            total_score=0.0,
            rank=99,
            score_breakdown=ScoreBreakdown(
                review_trust_score=0.0,
                rating_score=0.0,
                seller_trust_score=0.0,
                match_confidence_score=0.0
            ),
            recommendation_reason="Data unavailable: Live marketplace ratings and reviews are required to generate recommendation ranking scores but are unavailable.",
            listing=listing
        )

    # 1. Review Trust Score (40% weight)
    rev_count = listing.review_count or 0
    if rev_count >= 100:
        review_trust = 95.0
    elif rev_count >= 20:
        review_trust = 85.0
    elif rev_count >= 5:
        review_trust = 70.0
    elif rev_count > 0:
        review_trust = 40.0
    else:
        review_trust = 0.0

    if review_trust > 0.0 and listing.reviews and any(r.verified_purchase for r in listing.reviews):
        review_trust = min(100.0, review_trust + 5.0)

    # 2. Rating Score (25% weight)
    rating = listing.rating or 0.0
    rating_score = min(100.0, max(0.0, (rating / 5.0) * 100.0))

    # 3. Seller Trust Score (20% weight)
    seller = (listing.seller_name or "").lower()
    if "official" in seller or "verified" in seller or "mall" in seller:
        seller_trust = 95.0
    elif seller:
        seller_trust = 75.0
    else:
        seller_trust = 0.0

    # 4. Product Match Confidence Score (15% weight)
    match_conf = listing.match_confidence or 0.0

    total_score = (
        (review_trust * 0.40) +
        (rating_score * 0.25) +
        (seller_trust * 0.20) +
        (match_conf * 0.15)
    )
    total_score = round(min(100.0, max(0.0, total_score)), 1)

    if total_score >= 80.0:
        reason = f"Strong evidence: Verified seller '{listing.seller_name or listing.platform}' with {rating}/5.0 rating and high product match ({match_conf}%)."
    elif total_score >= 60.0:
        reason = f"Moderate evidence: Listing matched with {match_conf}% confidence on {listing.platform}."
    else:
        reason = f"Lower evidence: Limited listing verification or lower product match score ({match_conf}%)."

    return PlatformComparisonScore(
        platform=listing.platform,
        total_score=total_score,
        rank=1,
        score_breakdown=ScoreBreakdown(
            review_trust_score=round(review_trust, 1),
            rating_score=round(rating_score, 1),
            seller_trust_score=round(seller_trust, 1),
            match_confidence_score=round(match_conf, 1)
        ),
        recommendation_reason=reason,
        listing=listing
    )


def compare_marketplace_platforms(listings: List[MarketplaceListing]) -> List[PlatformComparisonScore]:
    """
    Evaluates, scores, and rank-orders all marketplace platform listings.

    Only platforms with total_score > 0 are ranked as active recommendations.
    Unavailable/blocked/rejected platforms are appended at the end with rank=99
    and are clearly NOT ranked recommendations.
    """
    ranked: List[PlatformComparisonScore] = []
    unranked: List[PlatformComparisonScore] = []

    for listing in listings:
        score_obj = calculate_platform_score(listing)
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

    # Unranked platforms get rank 99 (not a recommendation)
    for s in unranked:
        s.rank = 99

    return ranked + unranked
