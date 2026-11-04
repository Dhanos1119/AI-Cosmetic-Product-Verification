from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.schemas.marketplace import ProductIdentity, MarketplaceListing, PlatformComparisonScore

class HealthResponse(BaseModel):
    status: str
    service: str

class OcrResultDetails(BaseModel):
    status: str
    engine: Optional[str] = None
    raw_text: List[str]
    brand_name: Optional[str] = None
    product_name: Optional[str] = None
    category: Optional[str] = None
    confidence: float
    total_lines_detected: int

class TopProductMatchDetails(BaseModel):
    rank: int
    product_id: str
    brand: str
    product_name: str
    category: str
    folder_name: str
    similarity_score: float
    similarity_percentage: float

class ClipResultDetails(BaseModel):
    status: str
    message: Optional[str] = None
    matched_product_id: Optional[str] = None
    matched_product_name: Optional[str] = None
    matched_brand: Optional[str] = None
    matched_category: Optional[str] = None
    matched_folder: Optional[str] = None
    similarity_score: float
    similarity_percentage: float
    match_status: str
    confidence_level: str
    vector_dimension: int
    model: str
    matching_method: Optional[str] = None
    screening_details: Optional[Dict[str, Any]] = None
    top_matches: List[TopProductMatchDetails] = []

class ReviewResultDetails(BaseModel):
    status: str
    review_dataset_source: Optional[str] = None
    authenticity_analysis_status: str = "NOT_VALIDATED"
    authenticity_note: Optional[str] = None
    review_authenticity_score: Optional[float] = None
    sentiment_label: str
    average_rating: Optional[float] = None
    verified_buyer_percentage: Optional[float] = None
    authenticity_status: str
    suspicious_review_flag: bool
    summary: str
    marketplace_sentiment: Optional[Dict[str, Any]] = None
    sentiment_model: Optional[Dict[str, Any]] = None
    synthetic_benchmark: Optional[Dict[str, Any]] = None
    suspicious_review_risk: Optional[Dict[str, Any]] = None
    analyzed_reviews: Optional[List[Dict[str, Any]]] = None
    is_simulated: Optional[bool] = False
    simulation_title: Optional[str] = None
    simulation_disclosure: Optional[str] = None
    credibility_assessment_label: Optional[str] = None
    positive_themes: Optional[List[str]] = []
    negative_themes: Optional[List[str]] = []
    sentiment_stats: Optional[Dict[str, Any]] = None
    simulated_reviews: Optional[List[Dict[str, Any]]] = []

class AuthenticityResultDetails(BaseModel):
    status: str
    overall_authenticity_score: float
    prediction_badge: str
    risk_level: str
    recommendation: str
    assessment_outcome: Optional[str] = "REQUIRES_MANUAL_VERIFICATION"
    score_scope: Optional[str] = None
    verified_evidence: Optional[List[str]] = []
    inconsistencies: Optional[List[str]] = []
    missing_information: Optional[List[str]] = []
    assessment_explanation: Optional[str] = None
    score_breakdown: Dict[str, Any]

class AnalysisResponse(BaseModel):
    success: bool
    filename: str
    image_validation: str
    width: int
    height: int
    format: str
    size: int
    ocr_status: str
    brand_name: Optional[str] = None
    product_name: Optional[str] = None
    ocr_result: Optional[OcrResultDetails] = None
    product_detection: str
    clip_similarity: str
    clip_result: Optional[ClipResultDetails] = None
    review_authenticity: str
    review_result: Optional[ReviewResultDetails] = None
    authenticity_prediction: str
    authenticity_result: Optional[AuthenticityResultDetails] = None
    product_identity: Optional[ProductIdentity] = None
    is_confirmed: Optional[bool] = None
    identity_status: Optional[str] = None
    visual_similarity_disclaimer: Optional[str] = None
    marketplace_listings: Optional[List[MarketplaceListing]] = []
    platform_comparison: Optional[List[PlatformComparisonScore]] = []
    db_persisted: Optional[bool] = None

class ErrorResponse(BaseModel):
    success: bool
    message: str
