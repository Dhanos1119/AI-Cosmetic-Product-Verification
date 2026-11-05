"""
Product Analysis & Verification Service Orchestrator Module
"""

from app.services.clip_service import compute_clip_similarity
from app.services.review_service import analyze_review_authenticity
from app.services.review_analysis_service import analyze_platform_reviews
from app.services.authenticity_service import predict_final_authenticity
from app.schemas.marketplace import ProductIdentity
from app.services.scraping.marketplace_search import search_all_marketplaces
from app.services.marketplace_comparison_service import compare_marketplace_platforms
from app.services.demo_service import (
    evaluate_demo_scenario,
    get_simulated_reviews,
    get_demo_marketplace_sentiment,
    is_demo_mode_active,
)
from typing import Optional
from sqlalchemy.orm import Session
from database.persistence_service import persist_analysis_results

INVALID_BRANDS = {"no text detected", "unknown brand", "cosmetic brand", "unidentified brand", ""}
INVALID_PRODUCTS = {"unidentified product", "cosmetic product", "unknown product", ""}

def analyze_product_authenticity(
    file_bytes: bytes,
    ocr_result: dict = None,
    image_info: dict = None,
    db: Optional[Session] = None,
    user_product_url: Optional[str] = None
) -> dict:
    """
    Orchestrates multi-modal AI analysis:
    1. Visual Embedding Similarity (CLIP)
    2. Normalized Product Identity Creation & Gatekeeping Validation
    3. Marketplace Product Search & Verification (Amazon, Daraz, Temu)
    4. Platform Comparison & Evidence Scoring
    5. Review Authenticity & Ensemble Authenticity Score
    6. Database Persistence (PostgreSQL / SQLite via Session)
    """
    ocr_data = ocr_result or {}
    img_data = image_info or {}

    raw_ocr_brand = (ocr_data.get("brand_name") or "").strip()
    raw_ocr_prod = (ocr_data.get("product_name") or "").strip()
    category = ocr_data.get("category") or "Cosmetic Product"

    has_valid_ocr_brand = bool(raw_ocr_brand and raw_ocr_brand.lower() not in INVALID_BRANDS)
    has_valid_ocr_prod = bool(raw_ocr_prod and raw_ocr_prod.lower() not in INVALID_PRODUCTS)
    has_valid_ocr = has_valid_ocr_brand or has_valid_ocr_prod

    # 1. Compute CLIP Visual Dataset Embedding Similarity & Top 5 Product Matches
    ocr_category_for_clip = category if has_valid_ocr else None
    clip_res = compute_clip_similarity(
        file_bytes,
        brand_name=raw_ocr_brand if has_valid_ocr_brand else None,
        ocr_category=ocr_category_for_clip,
    )

    # 1.1 Non-cosmetic rejection check
    if clip_res.get("status") == "rejected_non_cosmetic":
        return {
            "status": "rejected_non_cosmetic",
            "message": clip_res.get("message", "Please upload a cosmetic product image."),
            "product_detection": "Rejected Non-Cosmetic",
            "clip_similarity": "Rejected",
            "clip_result": clip_res,
            "review_authenticity": "N/A - Non-Cosmetic Input",
            "review_result": None,
            "authenticity_prediction": "Rejected",
            "authenticity_result": {
                "status": "rejected_non_cosmetic",
                "overall_authenticity_score": 0.0,
                "prediction_badge": "Rejected (Non-Cosmetic)",
                "risk_level": "High",
                "recommendation": "Please upload a cosmetic product image.",
                "assessment_outcome": "REJECTED_NON_COSMETIC",
                "score_scope": "Non-Cosmetic Input",
                "verified_evidence": [],
                "inconsistencies": ["Input image was identified as a non-cosmetic artifact."],
                "missing_information": ["Valid cosmetic packaging, bottle, jar, or makeup swatch"],
                "assessment_explanation": "Screening detected non-cosmetic visual features (diagram, banner, screenshot, or unrelated object).",
                "score_breakdown": {
                    "visual_packaging_integrity": 0.0,
                    "marketplace_price_trust": 0.0,
                    "customer_sentiment_trust": 0.0,
                    "suspicious_review_penalty": 0.0
                }
            },
            "product_identity": ProductIdentity(
                brand="Non-Cosmetic",
                product_name="Rejected Image",
                product_type="Non-Cosmetic",
                category="Non-Cosmetic",
                product_id=None,
                shade_or_variant=None
            ),
            "marketplace_listings": [],
            "platform_comparison": [],
            "db_persisted": False
        }

    clip_percentage = clip_res.get("similarity_percentage", 0.0)
    clip_confidence = clip_res.get("confidence_level", "Low")
    clip_mismatch = clip_res.get("catalog_category_mismatch", False)
    clip_margin = clip_res.get("discrimination_margin", 0.0)
    # CLIP is considered reliable only when confidence is High/Moderate AND there is no
    # category conflict with OCR AND the centroids discriminated clearly (margin >= 2%)
    has_reliable_clip = (
        clip_confidence in ["High", "Moderate"]
        and not clip_mismatch
        and clip_margin >= 2.0
    )

    # Resolve granular category from supported categories:
    # Foundation, Lipstick, Concealer, Face powder, Blush, Eyeshadow, Eyeliner, Mascara, Lip gloss, Other makeup
    cat_info = clip_res.get("category_classification") or {}
    detected_cat = cat_info.get("category") or clip_res.get("detected_category")

    if detected_cat:
        matched_category = detected_cat
    elif has_reliable_clip and clip_res.get("matched_category"):
        raw_c = clip_res["matched_category"].replace('_', ' ').title()
        if "Foundation" in raw_c:
            matched_category = "Foundation"
        elif "Lip" in raw_c:
            matched_category = "Lipstick"
        elif "Eye" in raw_c:
            matched_category = "Eyeshadow"
        else:
            matched_category = "Other makeup"
    else:
        matched_category = "Other makeup"

    # Evaluate Demonstration Mode Scenario (from backend/data/demo_products.json)
    filename = img_data.get("filename") or ""
    demo_eval = evaluate_demo_scenario(
        filename=filename,
        detected_category=matched_category,
        is_cosmetic=(clip_res.get("status") != "rejected_non_cosmetic"),
        ocr_brand=raw_ocr_brand if has_valid_ocr_brand else None,
        ocr_product=raw_ocr_prod if has_valid_ocr_prod else None,
        clip_result=clip_res,
    )

    # If demo scenario dictates non-cosmetic rejection (e.g. 3.png)
    if demo_eval and demo_eval.get("is_rejected"):
        return {
            "status": "rejected_non_cosmetic",
            "message": demo_eval.get("rejection_message", "Non-cosmetic image detected."),
            "product_detection": "Non-cosmetic / uncertain",
            "clip_similarity": "Rejected",
            "clip_result": clip_res,
            "review_authenticity": "N/A - Non-Cosmetic Input",
            "review_result": None,
            "authenticity_prediction": "Rejected",
            "authenticity_result": {
                "status": "rejected_non_cosmetic",
                "overall_authenticity_score": 0.0,
                "prediction_badge": "Rejected (Non-Cosmetic)",
                "risk_level": "High",
                "recommendation": demo_eval.get("rejection_message", "Non-cosmetic image detected."),
                "assessment_outcome": "REJECTED_NON_COSMETIC",
                "score_scope": "Non-Cosmetic Input",
                "verified_evidence": [],
                "inconsistencies": ["Input image was identified as a non-cosmetic object."],
                "missing_information": ["Valid cosmetic packaging, bottle, jar, or makeup container"],
                "assessment_explanation": "Screening detected non-cosmetic visual features.",
                "score_breakdown": {
                    "visual_packaging_integrity": 0.0,
                    "marketplace_price_trust": 0.0,
                    "customer_sentiment_trust": 0.0,
                    "suspicious_review_penalty": 0.0
                }
            },
            "product_identity": ProductIdentity(
                brand="Non-Cosmetic",
                product_name="Rejected Image",
                product_type="Non-Cosmetic",
                category="Non-cosmetic / uncertain",
                product_id=None,
                shade_or_variant=None
            ),
            "marketplace_listings": [],
            "platform_comparison": [],
            "db_persisted": False
        }

    # Exact product identification when sufficient evidence exists
    has_exact_evidence = bool(
        (has_valid_ocr_brand and has_valid_ocr_prod)
        or (has_valid_ocr_brand and has_reliable_clip and clip_percentage >= 80.0)
    )

    is_confirmed = has_exact_evidence
    identity_status = "Confirmed Product Identity" if is_confirmed else "Unconfirmed Product Identity"

    # Determine Normalized Product Identity
    if demo_eval and not demo_eval.get("is_rejected"):
        matched_category = demo_eval.get("category", matched_category)
        matched_brand = demo_eval.get("brand", "Cosmetic Brand")
        matched_product = demo_eval.get("product_name", f"{matched_category} Product")
        is_confirmed = demo_eval.get("is_confirmed", False)
        identity_status = demo_eval.get("identity_status", "Unconfirmed Product Identity")
        prod_id = None
        demo_key = demo_eval.get("demo_key")
    elif has_valid_ocr:
        matched_brand = raw_ocr_brand if has_valid_ocr_brand else clip_res.get("matched_brand", "Cosmetic Brand")
        matched_product = raw_ocr_prod if has_valid_ocr_prod else clip_res.get("matched_product_name", f"{matched_category} Product")
        prod_id = clip_res.get("matched_product_id") if has_reliable_clip else None
        demo_key = None
    elif has_reliable_clip:
        matched_brand = clip_res.get("matched_brand", "Unknown Brand")
        matched_product = clip_res.get("matched_product_name", f"{matched_category} Product")
        prod_id = clip_res.get("matched_product_id")
        demo_key = None
    else:
        matched_brand = raw_ocr_brand or clip_res.get("matched_brand") or "Cosmetic Brand"
        matched_product = raw_ocr_prod or clip_res.get("matched_product_name") or f"{matched_category} Product"
        prod_id = None
        demo_key = None

    display_product_name = matched_product if is_confirmed else f"{matched_product} (Identity Unconfirmed)"

    # 2. Construct Normalized Product Identity Schema
    product_identity = ProductIdentity(
        brand=matched_brand,
        product_name=display_product_name,
        product_type=matched_category,
        category=matched_category,
        product_id=prod_id if is_confirmed else None,
        shade_or_variant=None
    )

    # 3. Search Marketplaces & Execute Multi-Factor Product Matching
    # Whenever candidate brand or product text is identifiable (and input is cosmetic),
    # automatically execute marketplace search across Amazon, Daraz, and Temu.
    has_user_url = bool(user_product_url and isinstance(user_product_url, str) and user_product_url.strip())
    has_searchable_tokens = bool(
        (matched_brand and matched_brand.lower() not in INVALID_BRANDS)
        or (matched_product and matched_product.lower() not in INVALID_PRODUCTS)
    )

    if has_valid_ocr or has_reliable_clip or has_searchable_tokens or has_user_url or demo_key:
        marketplace_listings = search_all_marketplaces(
            product_identity,
            user_product_url=user_product_url,
            demo_key=demo_key
        )
        mkt_status = "Marketplace search completed"
    else:
        # Prevent marketplace searching only when product identity is entirely unidentifiable
        marketplace_listings = []
        mkt_status = "Product identity insufficient for marketplace comparison"

    # 4. Review sentiment on ACTUAL review text, or configured demonstration reviews for demo scenarios
    real_reviews = []
    for m in marketplace_listings:
        for rv in (m.reviews or []):
            if rv.comment:
                real_reviews.append({
                    "text": rv.comment,
                    "comment": rv.comment,
                    "rating": rv.rating,
                    "author": rv.author or "Anonymous",
                    "date": rv.date,
                    "verified_purchase": rv.verified_purchase or False,
                    "platform": m.platform
                })

    is_demo_scenario = bool(demo_key in ("1.png", "2.png") and is_demo_mode_active())
    simulated_reviews = get_simulated_reviews(demo_key) if is_demo_scenario else []
    demo_sentiment_data = get_demo_marketplace_sentiment(demo_key) if is_demo_scenario else None

    review_res = analyze_review_authenticity(
        brand_name=matched_brand,
        product_name=matched_product,
        product_id=prod_id,
        category=matched_category,
        real_reviews=real_reviews,
        simulated_reviews=simulated_reviews,
        demo_key=demo_key if is_demo_scenario else None
    )

    # 4b. Independent Platform-wise review analysis for Amazon, Daraz LK, Temu
    platform_review_analyses = {}
    for target_plat in ["Amazon", "Daraz LK", "Temu"]:
        plat_reviews = []
        plat_listing = None
        for m in marketplace_listings:
            plat_name = m.platform or m.platform_name or ""
            if target_plat.lower() in plat_name.lower():
                plat_listing = m
                for rv in (m.reviews or []):
                    if rv.comment:
                        plat_reviews.append({
                            "text": rv.comment,
                            "comment": rv.comment,
                            "rating": rv.rating,
                            "author": rv.author or "Anonymous",
                            "date": rv.date,
                            "verified_purchase": rv.verified_purchase or False,
                            "platform": target_plat
                        })

        if demo_sentiment_data and target_plat in demo_sentiment_data:
            # Load configured demonstration sentiment data for demo presentation
            plat_demo = demo_sentiment_data[target_plat]
            tot = int(plat_demo.get("review_count", 10))
            pos_p = float(plat_demo.get("positive_percentage", 70.0))
            neu_p = float(plat_demo.get("neutral_percentage", 15.0))
            neg_p = float(plat_demo.get("negative_percentage", 15.0))
            pos_c = round((pos_p / 100.0) * tot)
            neu_c = round((neu_p / 100.0) * tot)
            neg_c = max(0, tot - pos_c - neu_c)

            analysis = {
                "platform": target_plat,
                "status": "completed",
                "status_message": f"Demonstration sentiment analysis configured for {target_plat}.",
                "has_reviews": True,
                "is_demo": True,
                "total_reviews_retrieved": tot,
                "total_reviews_analyzed": tot,
                "counts": {
                    "positive": pos_c,
                    "neutral": neu_c,
                    "negative": neg_c
                },
                "positive_percentage": pos_p,
                "neutral_percentage": neu_p,
                "negative_percentage": neg_p,
                "overall_sentiment": plat_demo.get("overall_sentiment", "Positive"),
                "positive_themes": plat_demo.get("positive_themes", []),
                "negative_themes": plat_demo.get("negative_themes", []),
                "summary": plat_demo.get("summary", ""),
                "analyzed_reviews": simulated_reviews,
                "source_info": f"{target_plat} Demonstration Data",
                "average_rating": plat_demo.get("rating") or (plat_listing.rating if plat_listing else 4.0),
                "listing_rating": plat_demo.get("rating") or (plat_listing.rating if plat_listing else 4.0),
                "listing_review_count": tot,
                "product_url": plat_listing.product_url if plat_listing else None,
            }
        else:
            analysis = analyze_platform_reviews(
                platform_name=target_plat,
                reviews=plat_reviews,
                category=matched_category
            )
            if plat_listing:
                analysis["listing_rating"] = plat_listing.rating
                analysis["listing_review_count"] = plat_listing.review_count
                analysis["product_url"] = plat_listing.product_url

        platform_review_analyses[target_plat] = analysis

    review_res["platform_review_analyses"] = platform_review_analyses

    # 5. Execute 5-Factor Marketplace Recommendation Scoring using independent platform review data
    if marketplace_listings:
        pos_pct = review_res.get("sentiment_stats", {}).get("positive_percentage", 50.0)
        platform_comparison = compare_marketplace_platforms(
            marketplace_listings,
            platform_review_analyses=platform_review_analyses,
            sentiment_positive_pct=pos_pct
        )
    else:
        platform_comparison = []

    # Enrich each MarketplaceListing's reviews with the sentiment prediction and suspicious flags
    analyzed_map = {}
    for ar in review_res.get("analyzed_reviews", []):
        key = (ar.get("comment") or ar.get("text") or "").strip()
        if key:
            analyzed_map[key] = ar

    for m in marketplace_listings:
        if m.reviews:
            for rv in m.reviews:
                key = (rv.comment or "").strip()
                if key in analyzed_map:
                    ar = analyzed_map[key]
                    rv.sentiment = ar.get("sentiment")
                    rv.sentiment_confidence = ar.get("sentiment_confidence")
                    rv.suspicious_flag = ar.get("suspicious_flag", False)
                    rv.suspicious_reason = ar.get("suspicious_reason")

    # 5. Predict Overall Authenticity Ensemble Score & Evidence-Based Outcome
    authenticity_res = predict_final_authenticity(
        ocr_data=ocr_data,
        clip_data=clip_res,
        review_data=review_res,
        image_info=img_data,
        marketplace_listings=marketplace_listings
    )

    res_dict = {
        "product_detection": matched_category,
        "clip_similarity": f"{clip_res['similarity_percentage']}% ({clip_res['match_status']})",
        "clip_result": clip_res,
        "review_authenticity": f"{review_res['authenticity_analysis_status']} ({review_res['sentiment_label']})",
        "review_result": review_res,
        "authenticity_prediction": f"{authenticity_res['prediction_badge']} ({authenticity_res['overall_authenticity_score']}%)",
        "authenticity_result": authenticity_res,
        "product_identity": product_identity.model_dump(),
        "is_confirmed": is_confirmed,
        "identity_status": identity_status,
        "visual_similarity_disclaimer": "Visual similarity indicates packaging shape and aesthetic resemblance to reference catalog images; it does not confirm or prove product authenticity.",
        "marketplace_status": mkt_status,
        "marketplace_listings": [m.model_dump() for m in marketplace_listings],
        "platform_comparison": [p.model_dump() for p in platform_comparison]
    }

    # 6. Persist to Database if DB Session is provided
    if db is not None:
        res_dict = persist_analysis_results(db, res_dict)

    return res_dict

