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

class ScoreBreakdown(BaseModel):
    review_trust_score: float  # 40% weight
    rating_score: float        # 25% weight
    seller_trust_score: float  # 20% weight
    match_confidence_score: float # 15% weight

class PlatformComparisonScore(BaseModel):
    platform: str
    total_score: float
    rank: int
    score_breakdown: ScoreBreakdown
    recommendation_reason: str
    listing: MarketplaceListing
