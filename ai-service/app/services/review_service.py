"""
Review Sentiment & Authenticity-Status Service Module

Sentiment is computed only on actual review text. Authenticity is reported as NOT_VALIDATED
(see review_analysis_service.py).
"""

from typing import List, Optional, Dict, Any
from app.services.review_analysis_service import analyze_product_reviews


def analyze_review_authenticity(
    brand_name: str = None,
    product_name: str = None,
    product_id: str = None,
    category: str = None,
    real_reviews: Optional[List[Dict[str, Any]]] = None,
    simulated_reviews: Optional[List[Dict[str, Any]]] = None,
    demo_key: Optional[str] = None,
) -> dict:
    """
    Returns the review section: real-text sentiment (if any), simulated reviews when applicable,
    and authenticity status NOT_VALIDATED.
    """
    return analyze_product_reviews(
        product_id=product_id,
        brand_name=brand_name,
        product_name=product_name,
        category=category,
        real_reviews=real_reviews,
        simulated_reviews=simulated_reviews,
        demo_key=demo_key,
    )
