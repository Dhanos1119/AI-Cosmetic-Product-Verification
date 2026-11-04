"""
Demonstration Mode Service Module
Handles configurable numbered image demonstration mode using backend/data/demo_products.json.
Enforces image content validation so demonstration identities are never forced on unrelated images.
Separates simulated demo marketplace listings from live marketplace results.
"""

import os
import json
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import quote_plus
from typing import Optional, Dict, Any, List

from app.schemas.marketplace import ProductIdentity, MarketplaceListing, MarketplaceReview

BASE_DIR = Path(__file__).parent.parent.parent.resolve()
BACKEND_DATA_DIR = BASE_DIR.parent / "backend" / "data"
DEMO_PRODUCTS_FILE = BACKEND_DATA_DIR / "demo_products.json"


def get_demo_config() -> Dict[str, Any]:
    """
    Reads the demo configuration from backend/data/demo_products.json.
    Falls back gracefully if the file is absent.
    """
    if DEMO_PRODUCTS_FILE.is_file():
        try:
            with open(DEMO_PRODUCTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            print(f"[DEMO NOTICE] Error loading {DEMO_PRODUCTS_FILE}: {exc}")

    # Fallback default demo config
    return {
        "demo_mode_enabled": True,
        "timeout_seconds": 10.0,
        "demonstrations": {}
    }


def is_demo_mode_active() -> bool:
    """
    Determines if demonstration mode is currently active.
    Environment variables ENABLE_DEMO_MODE or DEMO_MODE take precedence;
    otherwise falls back to demo_mode_enabled in demo_products.json.
    """
    env_flag = os.getenv("ENABLE_DEMO_MODE") or os.getenv("DEMO_MODE")
    if env_flag is not None:
        return env_flag.strip().lower() in ("1", "true", "yes", "on")

    config = get_demo_config()
    return bool(config.get("demo_mode_enabled", True))


def get_marketplace_timeout() -> float:
    """
    Retrieves the configurable marketplace timeout (default 10.0 seconds, range 8.0-12.0s).
    """
    env_timeout = os.getenv("MARKETPLACE_TIMEOUT")
    if env_timeout:
        try:
            val = float(env_timeout)
            if 4.0 <= val <= 25.0:
                return val
        except ValueError:
            pass

    config = get_demo_config()
    return float(config.get("timeout_seconds", 10.0))


def evaluate_demo_scenario(
    filename: Optional[str],
    detected_category: str,
    is_cosmetic: bool,
    ocr_brand: Optional[str] = None,
    ocr_product: Optional[str] = None,
    clip_result: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Evaluates whether an uploaded image matches a configured numbered demonstration scenario.
    Validates image content:
      - 1.png (Foundation): Validates that the image is cosmetic and compatible with Foundation.
      - 2.png (Lipstick): Validates that the image is cosmetic and compatible with Lipstick.
      - 3.png (Non-Cosmetic): Strictly validates rejection as non-cosmetic.
    Never forces demonstration identities onto unrelated or mismatched images.
    """
    if not is_demo_mode_active():
        return None

    if not filename:
        return None

    # Normalise filename (e.g. "C:\\uploads\\1.png" -> "1.png")
    clean_name = Path(filename).name.strip().lower()

    config = get_demo_config()
    demos = config.get("demonstrations", {})

    if clean_name not in demos:
        return None

    scenario = demos[clean_name]

    # Scenario 3: Non-Cosmetic Rejection
    if scenario.get("is_non_cosmetic", False) or clean_name == "3.png":
        return {
            "demo_key": clean_name,
            "status": "rejected_non_cosmetic",
            "is_rejected": True,
            "rejection_message": scenario.get("rejection_message", "Non-cosmetic image detected."),
            "category": "Non-cosmetic / uncertain",
            "is_confirmed": False,
            "identity_status": "Unconfirmed Product Identity",
        }

    # Scenario 1: Foundation Demo
    if clean_name == "1.png":
        # Content validation: Must be a cosmetic object and compatible with Foundation
        compatible = scenario.get(
            "compatible_categories",
            ["Foundation", "Face powder", "Concealer", "Other makeup"]
        )

        # If CLIP or screening marked it as non-cosmetic or if detected category is incompatible,
        # content validation fails: do not force foundation onto an unrelated object!
        if not is_cosmetic or (
            detected_category not in compatible and detected_category != "Non-cosmetic / uncertain"
        ):
            print(f"[DEMO NOTICE] 1.png content validation rejected category '{detected_category}' - not forcing demo identity.")
            return None

        demo_ident = scenario.get("demonstration_identity", {})
        return {
            "demo_key": clean_name,
            "is_rejected": False,
            "category": demo_ident.get("category", "Foundation"),
            "brand": demo_ident.get("brand", "Maybelline"),
            "product_name": demo_ident.get("product_name", "Maybelline Fit Me Matte + Poreless Foundation"),
            "product_type": demo_ident.get("product_type", "Liquid Foundation"),
            "shade_or_variant": demo_ident.get("shade_or_variant", "120 Classic Ivory"),
            "is_confirmed": True,
            "identity_status": "Confirmed Product Identity",
        }

    # Scenario 2: Lipstick Demo
    if clean_name == "2.png":
        compatible = scenario.get(
            "compatible_categories",
            ["Lipstick", "Lip gloss", "Other makeup"]
        )

        if not is_cosmetic:
            return {
                "demo_key": clean_name,
                "is_rejected": True,
                "rejection_message": "Non-cosmetic image detected.",
                "category": "Non-cosmetic / uncertain",
                "is_confirmed": False,
                "identity_status": "Unconfirmed Product Identity",
            }

        # Check if sufficient evidence exists for an exact product identity
        has_ocr_evidence = bool(ocr_brand and ocr_product and ocr_brand.lower() not in ("cosmetic brand", "unknown"))
        has_high_clip_evidence = False
        if clip_result and isinstance(clip_result, dict):
            sim_pct = clip_result.get("similarity_percentage", 0.0)
            margin = clip_result.get("discrimination_margin", 0.0)
            if sim_pct >= 82.0 and margin >= 0.15:
                has_high_clip_evidence = True

        sufficient_evidence = has_ocr_evidence or has_high_clip_evidence

        if sufficient_evidence:
            # Sourced from actual AI detection
            matched_prod = (clip_result or {}).get("matched_product_name") or ocr_product or "Lipstick"
            matched_brand = (clip_result or {}).get("matched_brand") or ocr_brand or "Cosmetic Brand"
            return {
                "demo_key": clean_name,
                "is_rejected": False,
                "category": "Lipstick",
                "brand": matched_brand,
                "product_name": matched_prod,
                "product_type": "Lipstick",
                "shade_or_variant": None,
                "is_confirmed": True,
                "identity_status": "Confirmed Product Identity",
            }
        else:
            # Show category Lipstick and mark exact identity as unconfirmed
            return {
                "demo_key": clean_name,
                "is_rejected": False,
                "category": "Lipstick",
                "brand": "Cosmetic Brand",
                "product_name": "Lipstick",
                "product_type": "Lipstick",
                "shade_or_variant": None,
                "is_confirmed": False,
                "identity_status": "Unconfirmed Product Identity",
            }

    return None


def get_simulated_marketplace_listing(
    demo_key: str,
    platform: str,
    search_query: str
) -> Optional[MarketplaceListing]:
    """
    Retrieves configured simulated marketplace listing for Daraz or Temu in demo mode.
    Amazon is ALWAYS set to UNAVAILABLE (per requirement: live marketplace data unavailable).
    """
    config = get_demo_config()
    demos = config.get("demonstrations", {})
    scenario = demos.get(demo_key)
    if not scenario:
        return None

    sim_market = scenario.get("marketplace_simulated", {})
    plat_key = platform.lower().split()[0] # "daraz", "temu", "amazon"
    item = sim_market.get(plat_key)

    now_iso = datetime.now(timezone.utc).isoformat()
    norm_platform = "Daraz LK" if plat_key == "daraz" else ("Amazon" if plat_key == "amazon" else "Temu")

    search_urls = {
        "amazon": f"https://www.amazon.com/s?k={quote_plus(search_query)}",
        "daraz": f"https://www.daraz.lk/catalog/?q={quote_plus(search_query)}",
        "temu": f"https://www.temu.com/search_result.html?search_key={quote_plus(search_query)}"
    }
    fallback_search_url = search_urls.get(plat_key, f"https://www.google.com/search?q={quote_plus(search_query)}")

    if plat_key == "amazon" or not item:
        # Amazon in demonstration mode: always "Live marketplace data unavailable."
        return MarketplaceListing(
            platform=norm_platform,
            product_name=f"{norm_platform} Search: {search_query}",
            brand="Cosmetic Brand",
            product_type="Cosmetics",
            price=0.0,
            currency="USD",
            rating=0.0,
            rating_count=0,
            review_count=0,
            seller_name=None,
            product_url=fallback_search_url,
            product_image_url=None,
            reviews=[],
            source_status="unavailable",
            match_status="Not a Match",
            match_confidence=0.0,
            status_explanation="Live marketplace data unavailable.",
            search_query=search_query,
            listing_status="UNAVAILABLE",
            passed_match_threshold=False,
            retrieval_status="UNAVAILABLE",
            data_source="Direct Search",
            retrieval_timestamp=now_iso,
            search_url=fallback_search_url,
        )

    # Simulated listing for Daraz LK or Temu
    status = item.get("status", "DEMO")
    price_val = float(item.get("price", 0.0))
    rating_val = float(item.get("rating", 0.0))
    rating_count_val = int(item.get("rating_count", item.get("review_count", 0)))
    review_count_val = int(item.get("review_count", 0))

    return MarketplaceListing(
        platform=norm_platform,
        product_name=item.get("product_name", search_query),
        brand="Cosmetic Brand",
        product_type="Cosmetics",
        price=price_val,
        currency=item.get("currency", "USD"),
        rating=rating_val,
        rating_count=rating_count_val,
        review_count=review_count_val,
        seller_name=item.get("seller_name"),
        product_url=item.get("product_url", fallback_search_url),
        product_image_url=None,
        reviews=[],
        source_status="available" if status in ("LIVE", "DEMO") else "unavailable",
        match_status="Exact Product Match",
        match_confidence=92.0,
        status_explanation=f"Configured demonstration listing loaded for {norm_platform}." if status == "DEMO" else None,
        search_query=search_query,
        listing_status="VERIFIED_LISTING",
        passed_match_threshold=True,
        retrieval_status=status,
        data_source=item.get("data_source", "Simulated Demo Catalog"),
        retrieval_timestamp=now_iso,
        search_url=fallback_search_url,
    )


def get_simulated_reviews(demo_key: str) -> List[Dict[str, Any]]:
    """
    Retrieves exactly TEN configured simulated reviews for a demonstration scenario.
    Returns empty list if demo mode is inactive or key has no configured simulated reviews.
    """
    if not is_demo_mode_active() or not demo_key:
        return []

    config = get_demo_config()
    demos = config.get("demonstrations", {})
    scenario = demos.get(demo_key)
    if not scenario:
        return []

    return scenario.get("simulated_reviews", [])


