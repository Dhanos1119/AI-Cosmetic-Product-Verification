from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ProductIdentity(BaseModel):
    brand: str
    product_name: str
    product_type: str
    category: str
    product_id: Optional[str] = None
    shade_or_variant: Optional[str] = None

class MarketplaceReview(BaseModel):
    author: Optional[str] = "Anonymous"
    rating: Optional[float] = 0.0
    comment: Optional[str] = None
    date: Optional[str] = None
    verified_purchase: Optional[bool] = False
    sentiment: Optional[str] = None
    sentiment_confidence: Optional[float] = None
    suspicious_flag: Optional[bool] = False
    suspicious_reason: Optional[str] = None

class MarketplaceListing(BaseModel):
    platform: str  # Amazon, Daraz, Temu, etc.
    product_name: str
    brand: str
    product_type: str
    shade_or_variant: Optional[str] = None
    price: Optional[float] = 0.0
    currency: Optional[str] = "USD"
    rating: Optional[float] = 0.0
    rating_count: Optional[int] = 0
    review_count: Optional[int] = 0
    seller_name: Optional[str] = None
    product_url: Optional[str] = None
    product_image_url: Optional[str] = None
    reviews: Optional[List[MarketplaceReview]] = []
    source_status: str = "available"  # "available" | "blocked" | "unavailable"
    match_status: str = "Not a Match"  # "Exact Product Match" | "Possible Match" | "Not a Match"
    match_confidence: float = 0.0  # Percentage 0.0 - 100.0
    status_explanation: Optional[str] = None
    search_query: Optional[str] = None
    listing_status: str = "UNAVAILABLE"  # VERIFIED_LISTING | NO_MATCH_FOUND | MARKETPLACE_BLOCKED | SCRAPER_ERROR | UNAVAILABLE | REJECTED_LOW_MATCH_CONFIDENCE
    passed_match_threshold: bool = False
    retrieval_status: str = "UNAVAILABLE"  # LIVE | DEMO | UNAVAILABLE
    data_source: Optional[str] = None      # Live Scraper | Simulated Demo Catalog | Direct Search
    retrieval_timestamp: Optional[str] = None # ISO-8601 string
    search_url: Optional[str] = None       # Direct working search URL

class ScoreBreakdown(BaseModel):
    match_confidence_score: float = 0.0    # 35% weight: Product and brand match
    rating_volume_score: float = 0.0       # 25% weight: Product rating and review volume
    seller_trust_score: float = 0.0        # 20% weight: Seller trust
    price_score: float = 0.0               # 10% weight: Price competitiveness
    review_sentiment_score: float = 0.0    # 10% weight: Review sentiment
    # Compatibility aliases
    review_trust_score: Optional[float] = 0.0
    rating_score: Optional[float] = 0.0

class PlatformComparisonScore(BaseModel):
    platform: str
    total_score: float
    rank: int
    score_breakdown: ScoreBreakdown
    recommendation_reason: str
    listing: MarketplaceListing
    recommendation_type: Optional[str] = None # LIVE-DATA RECOMMENDATION | DEMO RECOMMENDATION — BASED ON SIMULATED DATA | Recommendation unavailable: insufficient comparable marketplace data.
    is_demo: Optional[bool] = False
