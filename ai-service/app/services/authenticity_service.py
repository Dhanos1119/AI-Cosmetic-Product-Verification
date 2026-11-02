"""
Multi-Modal Product Authenticity Prediction Service Module

Assesses verifiable evidence across modalities:
- Agreement between image OCR text and product catalog references
- Brand and product-name consistency
- Available packaging resolution and visual integrity
- Marketplace listing details and authorized-seller signals (when available)
- Identification of explicit conflicts and missing physical evidence

OUTCOMES:
- NOT_ASSESSED: Insufficient image data or unreadable packaging
- INSUFFICIENT_EVIDENCE: Weak OCR or low visual similarity without corroboration
- INCONSISTENT_INFORMATION: Direct conflict between OCR, CLIP, or listing details
- REQUIRES_MANUAL_VERIFICATION: Packaging appearance aligns with catalog specifications,
  but physical chemical formula, batch codes, and authorized distribution cannot be proven via 2D photo.

IMPORTANT: This system never claims a physical cosmetic product is genuine merely because
CLIP identifies packaging or a marketplace listing exists.
"""

from typing import Dict, Any, List, Optional


def predict_final_authenticity(
    ocr_data: dict,
    clip_data: dict,
    review_data: dict,
    image_info: dict,
    marketplace_listings: Optional[List[Any]] = None,
) -> dict:
    """
    Computes evidence-based product authenticity assessment and ensemble score.
    Returns explicit outcome category, verified evidence list, missing information, and conflicts.
    """
    ocr_data = ocr_data or {}
    clip_data = clip_data or {}
    review_data = review_data or {}
    image_info = image_info or {}

    # 1. OCR Score Component (Weight: 30%)
    ocr_confidence = float(ocr_data.get("confidence", 0.0) or 0.0)
    brand_detected = (ocr_data.get("brand_name") or "").strip()
    is_valid_brand = bool(brand_detected and brand_detected.lower() not in [
        "no text detected", "unknown brand", "cosmetic brand", "unidentified brand", ""
    ])
    product_detected = (ocr_data.get("product_name") or "").strip()
    is_valid_prod = bool(product_detected and product_detected.lower() not in [
        "unidentified product", "cosmetic product", "unknown product", ""
    ])

    ocr_score = (ocr_confidence * 70.0) + (30.0 if is_valid_brand else 10.0)
    ocr_score = min(100.0, max(0.0, ocr_score))

    # 2. CLIP Similarity Component (Weight: 40%)
    clip_confidence_level = clip_data.get("confidence_level", "Low")
    clip_mismatch = clip_data.get("catalog_category_mismatch", False)
    clip_margin = float(clip_data.get("discrimination_margin", 0.0) or 0.0)
    clip_reliable = (
        clip_confidence_level in ("High", "Moderate")
        and not clip_mismatch
        and clip_margin >= 2.0
    )
    raw_clip_score = float(clip_data.get("similarity_percentage", 0.0) or 0.0)
    clip_score = raw_clip_score if clip_reliable else 0.0

    matched_brand = (clip_data.get("matched_brand") or "").strip()
    matched_prod = (clip_data.get("matched_product_name") or "").strip()

    # 3. Review Authenticity Component (Weight: 20%) — only if validated
    raw_review = review_data.get("review_authenticity_score")
    review_validated = (
        review_data.get("authenticity_analysis_status") != "NOT_VALIDATED" and raw_review is not None
    )
    review_score = float(raw_review) if review_validated else None

    # 4. Packaging Integrity Component (Weight: 10%)
    width = image_info.get("width", 800)
    height = image_info.get("height", 600)
    img_valid = image_info.get("image_validation", "valid") == "valid"
    resolution_score = 100.0 if (width >= 600 and height >= 600 and img_valid) else 80.0

    # Weighted Ensemble Calculation — renormalize weights when components are absent
    if review_validated and clip_reliable:
        final_score = (
            (ocr_score * 0.30)
            + (clip_score * 0.40)
            + (review_score * 0.20)
            + (resolution_score * 0.10)
        )
    elif review_validated and not clip_reliable:
        final_score = (
            (ocr_score * 0.50)
            + (review_score * 0.33)
            + (resolution_score * 0.17)
        )
    elif clip_reliable:
        final_score = (
            (ocr_score * 0.375)
            + (clip_score * 0.50)
            + (resolution_score * 0.125)
        )
    else:
        final_score = (
            (ocr_score * 0.75)
            + (resolution_score * 0.25)
        )

    final_score = round(min(99.0, max(15.0, final_score)), 1)
    score_scope = "Packaging appearance similarity" if not clip_reliable else "Packaging appearance & visual catalog similarity"

    # Evidence, Inconsistencies, and Missing Information Collection
    verified_evidence: List[str] = []
    inconsistencies: List[str] = []
    missing_information: List[str] = [
        "Physical chemical composition and active ingredient concentrations cannot be analyzed from images.",
        "Manufacturer batch code / lot number verification against internal factory databases is unavailable.",
        "Tamper-evident seal and internal safety liner integrity cannot be verified online.",
    ]

    # Inspect OCR evidence
    if is_valid_brand:
        verified_evidence.append(f"OCR verified brand text '{brand_detected}' on packaging label ({ocr_confidence * 100:.0f}% confidence).")
    if is_valid_prod:
        verified_evidence.append(f"OCR identified product name '{product_detected}'.")

    # Inspect CLIP evidence
    if clip_reliable:
        verified_evidence.append(
            f"1-NN Reference Bank visual embedding verified packaging similarity ({raw_clip_score}% match to catalog '{matched_brand}')."
        )
    elif raw_clip_score > 0.0 and not clip_mismatch:
        verified_evidence.append(
            f"Visual similarity of {raw_clip_score}% detected, but discrimination margin ({clip_margin:.1f}%) is below high-confidence threshold."
        )

    # Inspect Packaging resolution
    if img_valid and width >= 600 and height >= 600:
        verified_evidence.append(f"Packaging image resolution ({width}x{height} px) is sufficient for label detail verification.")

    # Inspect Conflicts
    if clip_mismatch:
        ocr_cat = ocr_data.get("category", "Unknown")
        clip_cat = clip_data.get("matched_category", "Unknown")
        inconsistencies.append(
            f"Category conflict: OCR label text indicates '{ocr_cat}', but visual embedding matched '{clip_cat}'."
        )

    if is_valid_brand and matched_brand:
        norm_b_ocr = brand_detected.lower().replace(" ", "")
        norm_b_clip = matched_brand.lower().replace(" ", "")
        if norm_b_ocr not in norm_b_clip and norm_b_clip not in norm_b_ocr:
            inconsistencies.append(
                f"Brand mismatch: Packaging label reads '{brand_detected}', but catalog visual match corresponds to '{matched_brand}'."
            )

    # Inspect Marketplace Listing Evidence (if listings supplied)
    verified_listings = []
    if marketplace_listings:
        for m in marketplace_listings:
            passed = getattr(m, "passed_match_threshold", False) if hasattr(m, "passed_match_threshold") else m.get("passed_match_threshold", False)
            if passed:
                verified_listings.append(m)

    if verified_listings:
        verified_evidence.append(f"Retrieved {len(verified_listings)} matching marketplace listing(s) agreeing with product identity.")
        official_sellers = []
        for m in verified_listings:
            s_name = getattr(m, "seller_name", None) if hasattr(m, "seller_name") else m.get("seller_name")
            if s_name and any(kw in s_name.lower() for kw in ("official", "verified", "mall", "direct", "brand")):
                official_sellers.append(s_name)
        if official_sellers:
            verified_evidence.append(f"Listing offered by verified/official storefront: {', '.join(set(official_sellers))}.")
        else:
            missing_information.append("Listing seller is not an authenticated official brand storefront; distributor provenance is unverified.")
    else:
        missing_information.append("No verified authorized marketplace listings could be retrieved for comparison.")

    # Explicit Authenticity Assessment Outcome Determination
    if not img_valid or (not is_valid_brand and not clip_reliable):
        assessment_outcome = "NOT_ASSESSED"
        prediction_badge = "Packaging Suspicious (Very Low Confidence)"
        risk_level = "High Risk"
        recommendation = "Packaging label failed key brand checks or image is unreadable. Exercise caution before purchase."
        explanation = "The uploaded image contains insufficient verifiable text and visual features to evaluate packaging authenticity."

    elif inconsistencies:
        assessment_outcome = "INCONSISTENT_INFORMATION"
        prediction_badge = "Packaging Uncertain (Low Confidence)"
        risk_level = "Elevated Risk"
        recommendation = "Packaging analysis detected inconsistencies between label text, category, or catalog references. Manual inspection recommended."
        explanation = f"Detected conflicting product attributes: {'; '.join(inconsistencies)}."

    elif not clip_reliable or not is_valid_brand:
        assessment_outcome = "INSUFFICIENT_EVIDENCE"
        prediction_badge = "Packaging Plausible (Moderate Confidence)"
        risk_level = "Moderate Risk"
        recommendation = (
            "OCR text analysis is consistent but visual similarity could not be confirmed "
            "(catalog does not contain this product or CLIP confidence is low). "
            "Verify from an authorised seller."
            if not clip_reliable else
            "Packaging appearance shows moderate similarity to catalog references. "
            "This does not confirm the physical product is genuine. Verify from an authorised seller."
        )
        explanation = "Partial packaging alignment was found, but evidence is insufficient to verify consistency across both visual and textual modalities."

    else:
        assessment_outcome = "REQUIRES_MANUAL_VERIFICATION"
        if final_score >= 85.0:
            prediction_badge = "Packaging Verified (High Confidence)"
            risk_level = "Low Risk"
            recommendation = (
                "OCR and visual packaging analysis are consistent with known brand specifications. "
                "Independent verification of the physical product and authorised seller is still recommended."
            )
        else:
            prediction_badge = "Packaging Plausible (Moderate Confidence)"
            risk_level = "Moderate Risk"
            recommendation = (
                "Packaging appearance shows moderate similarity to catalog references. "
                "This does not confirm the physical product is genuine. Verify from an authorised seller."
            )
        explanation = (
            f"Packaging label text ('{brand_detected}') and 1-NN CLIP visual features are consistent with catalog reference specifications. "
            "However, online analysis cannot confirm chemical formulation, inner container safety, or batch code validity; physical inspection is required."
        )

    return {
        "status": "completed",
        "overall_authenticity_score": final_score,
        "prediction_badge": prediction_badge,
        "risk_level": risk_level,
        "recommendation": recommendation,
        "score_scope": score_scope,
        "assessment_outcome": assessment_outcome,
        "assessment_explanation": explanation,
        "verified_evidence": verified_evidence,
        "inconsistencies": inconsistencies,
        "missing_information": missing_information,
        "score_breakdown": {
            "ocr_verification_score": round(ocr_score, 1),
            "clip_similarity_score": round(raw_clip_score, 1),
            "clip_reliable": clip_reliable,
            "clip_contributed": round(clip_score, 1),
            "review_trust_score": round(review_score, 1) if review_validated else 0.0,
            "packaging_integrity_score": round(resolution_score, 1),
        },
        "review_component_included": review_validated,
        "clip_component_included": clip_reliable,
    }
