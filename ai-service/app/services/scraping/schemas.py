from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class SearchQueryBundle(BaseModel):
    base_query: str
    amazon_query: str
    daraz_query: str
    temu_query: str
    brand: str
    product_name: str

class RawMarketplaceItem(BaseModel):
    platform: str
    raw_title: str
    brand: Optional[str] = None
    price_str: Optional[str] = None
    price_val: Optional[float] = 0.0
    currency: Optional[str] = "USD"
    rating_val: Optional[float] = 0.0
    rating_count_val: Optional[int] = 0
    review_count_val: Optional[int] = 0
    seller: Optional[str] = None
    link: Optional[str] = None
    image_link: Optional[str] = None
    source_status: str = "available"  # "available" | "blocked" | "unavailable"
    explanation: Optional[str] = None
    # Marketplace-native identifier taken from the page itself (e.g. Amazon data-asin). Used only for de-duplication.
    listing_id: Optional[str] = None
    # Precise outcome for non-available or extracted items:
    # MARKETPLACE_BLOCKED | NOT_RETRIEVABLE (client-rendered page, no server HTML data) | NO_MATCH_FOUND | SCRAPER_ERROR | SUCCESS | PARTIAL_DATA | INVALID_URL
    status_code: Optional[str] = None
    reviews: Optional[List[Any]] = []

