from typing import Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, status, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database.connection import get_db
from app.services.image_service import validate_and_inspect_image, resize_image_if_needed
from app.services.ocr_service import extract_text_from_image
from app.services.product_service import analyze_product_authenticity
from app.schemas.response import AnalysisResponse, ErrorResponse

router = APIRouter(prefix="/api", tags=["Analysis"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}

@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request / Invalid File"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
def analyze_image(
    file: UploadFile = File(...),
    product_url: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    POST /api/analyze

    Accepts an uploaded image file using field name 'file'.
    Validates image format, executes real OCR text extraction (brand & product detection),
    CLIP similarity, marketplace evaluation, sentiment analysis, and persists results to PostgreSQL.
    """
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No image file provided. Expected multipart form field: file"
        )

    # Validate content type header if present
    content_type = (file.content_type or "").lower()
    filename_lower = file.filename.lower()
    
    is_allowed = (
        content_type in ALLOWED_CONTENT_TYPES or
        filename_lower.endswith((".jpg", ".jpeg", ".png", ".webp"))
    )

    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{file.content_type}'. Only JPG, JPEG, PNG, and WEBP images are allowed."
        )

    try:
        # Read uploaded file bytes synchronously (prevents AnyIO event loop block)
        file_bytes = file.file.read()

        if not file_bytes or len(file_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes)."
            )

        # Safely resize oversized images to prevent slow transfer & inference latency
        file_bytes = resize_image_if_needed(file_bytes, max_dim=1600)

        # 1. Inspect and validate image using Pillow & OpenCV
        img_info = validate_and_inspect_image(file_bytes, file.filename)

        # 2. Execute Real OCR Pipeline for brand & product extraction
        ocr_result = extract_text_from_image(file_bytes)

        # 3. Execute multi-modal product authenticity analysis & PostgreSQL persistence
        product_result = analyze_product_authenticity(
            file_bytes,
            ocr_result=ocr_result,
            image_info=img_info,
            db=db,
            user_product_url=product_url
        )

        # 3.1 Non-cosmetic rejection response
        if product_result.get("status") == "rejected_non_cosmetic":
            rejection_msg = product_result.get("message") or "Non-cosmetic image detected."
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "rejected_non_cosmetic",
                    "message": rejection_msg,
                    "success": False,
                    "filename": img_info["filename"],
                    "product_detection": "Non-cosmetic / uncertain",
                    "marketplace_listings": [],
                    "platform_comparison": [],
                    "screening_details": product_result.get("clip_result", {}).get("screening_details")
                }
            )

        response_data = {
            "success": True,
            "filename": img_info["filename"],
            "image_validation": img_info["image_validation"],
            "width": img_info["width"],
            "height": img_info["height"],
            "format": img_info["format"],
            "size": img_info["size"],
            "ocr_status": ocr_result["status"],
            "brand_name": ocr_result.get("brand_name"),
            "product_name": ocr_result.get("product_name"),
            "ocr_result": ocr_result,
            "product_detection": product_result["product_detection"],
            "clip_similarity": product_result["clip_similarity"],
            "clip_result": product_result.get("clip_result"),
            "review_authenticity": product_result["review_authenticity"],
            "review_result": product_result.get("review_result"),
            "authenticity_prediction": product_result["authenticity_prediction"],
            "authenticity_result": product_result.get("authenticity_result"),
            "product_identity": product_result.get("product_identity"),
            "is_confirmed": product_result.get("is_confirmed", False),
            "identity_status": product_result.get("identity_status", "Unconfirmed Product Identity"),
            "visual_similarity_disclaimer": product_result.get("visual_similarity_disclaimer", "Visual similarity indicates packaging shape and aesthetic resemblance to reference catalog images; it does not confirm or prove product authenticity."),
            "marketplace_listings": product_result.get("marketplace_listings", []),
            "platform_comparison": product_result.get("platform_comparison", []),
            "db_persisted": product_result.get("db_persisted", False)
        }

        return JSONResponse(status_code=status.HTTP_200_OK, content=response_data)


    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during image processing: {str(exc)}"
        )


@router.get("/reviews/{product_id}")
async def get_product_reviews(product_id: str, include_synthetic_benchmark: bool = False):
    """
    GET /api/reviews/{product_id}
    Returns review analysis status for a catalog product. Authenticity is NOT_VALIDATED and no
    real review text is stored, so sentiment is empty. The legacy synthetic benchmark is only
    returned (clearly labelled) when include_synthetic_benchmark=true.
    """
    from app.services.review_analysis_service import analyze_product_reviews
    res = analyze_product_reviews(product_id=product_id, include_synthetic_benchmark=include_synthetic_benchmark)
    return JSONResponse(status_code=status.HTTP_200_OK, content={"success": True, "data": res})


@router.post("/reviews/sentiment")
async def review_sentiment(payload: dict):
    """
    POST /api/reviews/sentiment
    Predicts positive/neutral/negative sentiment (rating-derived baseline model) for supplied
    review text. This is NOT a fake-review detector.
    """
    from app.services.review_analysis_service import classify_review_sentiment
    headline = payload.get("headline", "") or payload.get("title", "")
    body = payload.get("body", "") or payload.get("text", "")
    res = classify_review_sentiment(headline, body)
    return JSONResponse(status_code=status.HTTP_200_OK, content={"success": res["status"] == "ok", "data": res})


@router.post("/reviews/classify")
async def classify_review(payload: dict):
    """
    POST /api/reviews/classify  (kept for compatibility; same behaviour as /reviews/sentiment)
    Returns sentiment only. Deceptive/fake classification was removed (not validated).
    """
    return await review_sentiment(payload)


@router.post("/marketplace/scrape-url")
async def scrape_marketplace_url(payload: dict, db: Session = Depends(get_db)):
    """
    POST /api/marketplace/scrape-url
    Scrapes product metadata and actual customer reviews from a user-submitted marketplace URL.
    Enriches with review sentiment and suspicious flags, and persists to PostgreSQL.
    Never bypasses anti-bot challenges or access controls.
    """
    url = payload.get("url")
    platform = payload.get("platform")
    if not url or not isinstance(url, str) or not url.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required field: url")

    from app.services.scraping.url_scraper import scrape_user_product_url
    from app.services.review_service import analyze_review_authenticity

    item = scrape_user_product_url(url.strip(), expected_platform=platform)

    real_reviews = []
    for rv in (item.reviews or []):
        if rv.comment:
            real_reviews.append({
                "text": rv.comment,
                "comment": rv.comment,
                "rating": rv.rating,
                "author": rv.author or "Anonymous",
                "date": rv.date,
                "verified_purchase": rv.verified_purchase or False,
                "platform": item.platform
            })

    review_res = analyze_review_authenticity(
        brand_name=item.brand or "Unknown Brand",
        product_name=item.raw_title or "Cosmetic Product",
        category="Cosmetic Product",
        real_reviews=real_reviews
    )

    # Enrich item.reviews with sentiment and suspicious flag
    analyzed_map = {}
    for ar in review_res.get("analyzed_reviews", []):
        key = (ar.get("comment") or ar.get("text") or "").strip()
        if key:
            analyzed_map[key] = ar

    for rv in (item.reviews or []):
        key = (rv.comment or "").strip()
        if key in analyzed_map:
            ar = analyzed_map[key]
            rv.sentiment = ar.get("sentiment")
            rv.sentiment_confidence = ar.get("sentiment_confidence")
            rv.suspicious_flag = ar.get("suspicious_flag", False)
            rv.suspicious_reason = ar.get("suspicious_reason")

    db_persisted = False
    if db is not None and item.source_status == "available":
        try:
            from app.schemas.marketplace import ProductIdentity as ProductIdentitySchema, MarketplaceListing as MarketplaceListingSchema
            from database.persistence_service import (
                get_or_create_product,
                get_or_create_marketplace,
                get_or_create_seller,
                upsert_marketplace_listing,
                save_customer_reviews,
                upsert_review_analysis,
            )

            prod_id_schema = ProductIdentitySchema(
                brand=item.brand or "Unknown Brand",
                product_name=item.raw_title or "Cosmetic Product",
                product_type="Cosmetic Product",
                category="Cosmetic Product",
                product_id=None,
                shade_or_variant=None
            )
            db_product = get_or_create_product(db, prod_id_schema)
            db_mkt = get_or_create_marketplace(db, item.platform)
            db_seller = get_or_create_seller(db, db_mkt.id, item.seller)

            listing_schema = MarketplaceListingSchema(
                platform=item.platform,
                product_name=item.raw_title,
                brand=item.brand or "Unknown Brand",
                product_type="Cosmetic Product",
                price=item.price_val,
                currency=item.currency or "USD",
                rating=item.rating_val,
                rating_count=item.rating_count_val,
                review_count=item.review_count_val,
                seller_name=item.seller,
                product_url=item.link,
                product_image_url=item.image_link,
                reviews=item.reviews,
                source_status=item.source_status,
                match_status="Exact Product Match",
                match_confidence=100.0,
                status_explanation=item.explanation,
                search_query=item.link,
                listing_status=item.status_code or "VERIFIED_LISTING",
                passed_match_threshold=True
            )
            db_listing = upsert_marketplace_listing(db, db_product, db_mkt, db_seller, listing_schema)
            if item.reviews:
                save_customer_reviews(db, db_listing, item.reviews)
            upsert_review_analysis(db, db_listing, review_res)
            db.commit()
            db_persisted = True
        except Exception:
            if db:
                db.rollback()
            db_persisted = False

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "data": item.model_dump(),
            "review_result": review_res,
            "db_persisted": db_persisted
        }
    )


