"""
Multi-Factor Marketplace Product Matcher Engine
Evaluates Brand, Product Name, Category/Type, and Variant alignment to determine match status:
- Exact Product Match (Confidence >= 80%)
- Possible Match (Confidence >= 50% and < 80%)
- Not a Match (Confidence < 50%)
"""

import re
from typing import Tuple
from app.schemas.marketplace import ProductIdentity

def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return ' '.join(text.split())

# Unrelated non-cosmetic category keywords (electronics, audio, apparel, hardware)
UNRELATED_PRODUCT_KEYWORDS = {
    "bluetooth", "headset", "earpiece", "headphone", "earbuds", "wireless earpiece",
    "charger", "charging", "cable", "usb", "keyboard", "mouse", "laptop", "smartwatch",
    "clothing", "shirt", "t-shirt", "pants", "shoes", "dress", "jacket", "coat",
    "car", "auto", "tool", "power bank", "adapter", "case cover", "screen protector"
}

INVALID_PLACEHOLDERS = {
    "no text detected", "unidentified product", "unknown brand", "cosmetic brand",
    "cosmetic product", "unidentified brand", "lip_products", "eye_products",
    "foundation_base", "skin_care", "other_makeup"
}

def match_product(
    listing_title: str,
    target_identity: ProductIdentity,
    seller_name: str = None,
    listing_description: str = None
) -> Tuple[str, float]:
    """
    Evaluates multi-factor alignment between marketplace listing and target product identity.
    Returns: (match_status, match_confidence_score)
    """
    if not listing_title or not target_identity.brand:
        return "Not a Match", 0.0

    norm_title = normalize_text(listing_title)
    norm_brand = normalize_text(target_identity.brand)
    norm_product = normalize_text(target_identity.product_name)
    norm_type = normalize_text(target_identity.product_type)

    # 0. Defensive Check: Reject unrelated product categories (e.g., Bluetooth headsets for cosmetics)
    if any(kw in norm_title for kw in UNRELATED_PRODUCT_KEYWORDS):
        return "Not a Match", 0.0

    # Defensive Check: Reject placeholder or generic target identities
    if norm_brand in INVALID_PLACEHOLDERS and norm_product in INVALID_PLACEHOLDERS:
        return "Not a Match", 0.0

    # 1. Brand Alignment Check (35% weight)
    norm_seller = normalize_text(seller_name or "")
    brand_words = [w for w in norm_brand.split() if len(w) > 2 and w not in INVALID_PLACEHOLDERS]
    if not brand_words:
        brand_score = 1.0 if (norm_brand and norm_brand not in INVALID_PLACEHOLDERS and (norm_brand in norm_title or norm_brand in norm_seller)) else 0.0
    else:
        title_matches = sum(1 for bw in brand_words if bw in norm_title or bw in norm_seller)
        if title_matches > 0:
            brand_score = title_matches / len(brand_words)
        else:
            brand_score = 0.0  # Zero brand match in title or seller

    # 2. Product Name Token Overlap (40% weight)
    product_words = [w for w in norm_product.split() if len(w) > 2 and w not in INVALID_PLACEHOLDERS]
    if not product_words:
        product_score = 1.0 if (norm_product and norm_product not in INVALID_PLACEHOLDERS and norm_product in norm_title) else 0.0
    else:
        product_matches = sum(1 for pw in product_words if pw in norm_title)
        product_score = product_matches / len(product_words)

    # 3. Product Type Alignment (15% weight)
    type_words = [w for w in norm_type.split() if len(w) > 2 and w not in INVALID_PLACEHOLDERS]
    if type_words:
        type_matches = sum(1 for tw in type_words if tw in norm_title)
        type_score = type_matches / len(type_words)
    else:
        type_score = 0.5

    # 4. Variant / Shade Alignment (10% weight)
    variant_score = 0.5
    if target_identity.shade_or_variant:
        norm_variant = normalize_text(target_identity.shade_or_variant)
        if norm_variant in norm_title:
            variant_score = 1.0
        else:
            variant_score = 0.2

    # Calculate overall confidence score (0 - 100%)
    total_confidence = (
        (brand_score * 35.0) +
        (product_score * 40.0) +
        (type_score * 15.0) +
        (variant_score * 10.0)
    )

    # Brand Mismatch Penalty: If target brand is specified and brand score is 0.0, cap confidence below threshold (max 40.0)
    if brand_score == 0.0 and norm_brand and norm_brand not in INVALID_PLACEHOLDERS:
        total_confidence = min(40.0, total_confidence)

    total_confidence = round(min(100.0, max(0.0, total_confidence)), 1)

    # Classification
    # Requires both brand match and product token match for Exact Product Match
    if total_confidence >= 80.0 and brand_score >= 0.7 and product_score >= 0.5:
        status = "Exact Product Match"
    elif total_confidence >= 50.0 and brand_score > 0.0 and product_score > 0.0:
        status = "Possible Match"
    else:
        status = "Not a Match"

    return status, total_confidence
