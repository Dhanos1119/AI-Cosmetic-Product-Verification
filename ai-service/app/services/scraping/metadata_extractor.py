"""
Product Metadata Extractor Module
Extracts structured product data (JSON-LD) and robust HTML selectors from marketplace pages.
Extracts only fields actually present on the page; never invents or fabricates data.
"""

import json
import re
from typing import Optional, List, Dict, Any, Tuple
from bs4 import BeautifulSoup
from app.schemas.marketplace import MarketplaceReview


def extract_json_ld_products(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    Finds and parses all JSON-LD <script type="application/ld+json"> blocks.
    Extracts all schema.org Product or IndividualProduct entities.
    """
    products = []
    scripts = soup.select('script[type="application/ld+json"]')

    for script in scripts:
        raw_text = script.string or script.get_text()
        if not raw_text or not raw_text.strip():
            continue
        try:
            data = json.loads(raw_text.strip())
        except (json.JSONDecodeError, TypeError, ValueError):
            continue

        items_to_check = []
        if isinstance(data, list):
            items_to_check.extend(data)
        elif isinstance(data, dict):
            if "@graph" in data and isinstance(data["@graph"], list):
                items_to_check.extend(data["@graph"])
            else:
                items_to_check.append(data)

        for item in items_to_check:
            if not isinstance(item, dict):
                continue
            item_type = item.get("@type")
            is_product = False
            if isinstance(item_type, str) and item_type.lower() in ("product", "individualproduct", "productgroup"):
                is_product = True
            elif isinstance(item_type, list) and any(isinstance(t, str) and t.lower() in ("product", "individualproduct") for t in item_type):
                is_product = True

            if is_product:
                products.append(item)

    return products


def parse_price(val: Any) -> Tuple[float, Optional[str]]:
    """
    Safely parses numeric price and string representation.
    Returns (price_float, price_str).
    """
    if val is None:
        return 0.0, None
    if isinstance(val, (int, float)):
        return float(val), f"{float(val):.2f}"

    str_val = str(val).strip()
    if not str_val:
        return 0.0, None

    # Search for numeric price pattern (handles Rs. 1,250, $11.49, etc.)
    match = re.search(r'(\d+(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)', str_val)
    if match:
        num_str = match.group(1).replace(',', '')
        try:
            return float(num_str), str_val
        except ValueError:
            pass

    return 0.0, None


def parse_rating(val: Any) -> float:
    """Safely parses a rating value out of 5."""
    if val is None:
        return 0.0
    try:
        f = float(val)
        return round(min(5.0, max(0.0, f)), 1)
    except (ValueError, TypeError):
        return 0.0


def parse_review_count(val: Any) -> int:
    """Safely parses review count integer."""
    if val is None:
        return 0
    if isinstance(val, int):
        return max(0, val)
    cleaned = ''.join(c for c in str(val) if c.isdigit())
    try:
        return int(cleaned) if cleaned else 0
    except ValueError:
        return 0


def extract_from_json_ld(product_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts product fields from a schema.org Product JSON-LD dictionary.
    """
    # 1. Title
    title = product_data.get("name") or product_data.get("headline")
    if title:
        title = str(title).strip()

    # 2. Brand
    brand = None
    brand_obj = product_data.get("brand")
    if isinstance(brand_obj, dict):
        brand = brand_obj.get("name")
    elif isinstance(brand_obj, str):
        brand = brand_obj.strip()

    # 3. Price & Currency & Seller from Offers
    price_val = 0.0
    price_str = None
    currency = "USD"
    seller = None
    offers = product_data.get("offers")

    offer_item = None
    if isinstance(offers, list) and offers:
        offer_item = offers[0]
    elif isinstance(offers, dict):
        offer_item = offers

    if offer_item:
        raw_price = offer_item.get("price") or offer_item.get("lowPrice") or offer_item.get("highPrice")
        price_val, price_str = parse_price(raw_price)
        currency = offer_item.get("priceCurrency") or "USD"
        seller_obj = offer_item.get("seller")
        if isinstance(seller_obj, dict):
            seller = seller_obj.get("name")
        elif isinstance(seller_obj, str):
            seller = seller_obj.strip()

    # 4. Aggregate Rating & Distinct Rating / Review Counts
    rating_val = 0.0
    rating_count_val = 0
    review_count_val = 0
    agg = product_data.get("aggregateRating")
    if isinstance(agg, dict):
        rating_val = parse_rating(agg.get("ratingValue"))
        r_cnt = parse_review_count(agg.get("ratingCount"))
        rev_cnt = parse_review_count(agg.get("reviewCount"))
        rating_count_val = r_cnt if r_cnt > 0 else rev_cnt
        review_count_val = rev_cnt if rev_cnt > 0 else r_cnt

    # 5. Image
    image_url = None
    img_data = product_data.get("image")
    if isinstance(img_data, list) and img_data:
        image_url = img_data[0] if isinstance(img_data[0], str) else img_data[0].get("url")
    elif isinstance(img_data, dict):
        image_url = img_data.get("url")
    elif isinstance(img_data, str):
        image_url = img_data

    # 6. Customer Reviews (only actual reviews present in the payload)
    reviews_list: List[MarketplaceReview] = []
    raw_reviews = product_data.get("review") or product_data.get("reviews")
    if isinstance(raw_reviews, dict):
        raw_reviews = [raw_reviews]
    if isinstance(raw_reviews, list):
        for r in raw_reviews:
            if not isinstance(r, dict):
                continue
            body = r.get("reviewBody") or r.get("description")
            if not body or not str(body).strip():
                continue
            author_val = "Anonymous"
            auth_obj = r.get("author")
            if isinstance(auth_obj, dict):
                author_val = auth_obj.get("name") or "Anonymous"
            elif isinstance(auth_obj, str) and auth_obj.strip():
                author_val = auth_obj.strip()

            r_rating = 0.0
            r_rating_obj = r.get("reviewRating")
            if isinstance(r_rating_obj, dict):
                r_rating = parse_rating(r_rating_obj.get("ratingValue"))
            elif isinstance(r_rating_obj, (int, float, str)):
                r_rating = parse_rating(r_rating_obj)

            date_val = r.get("datePublished")
            reviews_list.append(MarketplaceReview(
                author=author_val,
                rating=r_rating,
                comment=str(body).strip(),
                date=str(date_val) if date_val else None,
                verified_purchase=False
            ))

    return {
        "title": title,
        "brand": brand,
        "price_val": price_val,
        "price_str": price_str,
        "currency": currency,
        "rating_val": rating_val,
        "rating_count_val": rating_count_val,
        "review_count_val": review_count_val,
        "seller": seller,
        "image_link": image_url,
        "reviews": reviews_list,
        "source": "json_ld"
    }


def extract_from_html_selectors(soup: BeautifulSoup, platform: Optional[str] = None) -> Dict[str, Any]:
    """
    Extracts product fields using platform-tailored and general HTML selectors.
    Never fabricates missing fields.
    """
    plat = (platform or "").lower().strip()

    title = None
    brand = None
    price_val = 0.0
    price_str = None
    currency = None
    rating_val = 0.0
    rating_count_val = 0
    review_count_val = 0
    seller = None
    image_link = None
    reviews_list: List[MarketplaceReview] = []

    # 1. Product Title Selectors
    title_selectors = []
    if "amazon" in plat:
        title_selectors = ["#productTitle", "h1#title span", ".product-title-word-break"]
    elif "daraz" in plat:
        title_selectors = [".pdp-mod-product-badge-title", "h1.pdp-title", ".pdp-product-title"]
        currency = "LKR"
    elif "temu" in plat:
        title_selectors = [".goods-title", "h1.title", ".product-detail-title"]
    
    # Generic fallbacks
    title_selectors.extend(["h1.product-title", "h1[itemprop='name']", "meta[property='og:title']", "h1"])

    for sel in title_selectors:
        elem = soup.select_one(sel)
        if elem:
            if elem.name == "meta":
                val = (elem.get("content") or "").strip()
            else:
                val = elem.get_text(strip=True)
            if val and len(val) > 2 and val.lower() not in ("daraz", "amazon", "temu"):
                title = val
                break

    # 2. Brand Selectors
    brand_selectors = ["#bylineInfo", "a#bylineInfo", ".pdp-product-brand a", ".brand-name", "meta[property='product:brand']"]
    for sel in brand_selectors:
        elem = soup.select_one(sel)
        if elem:
            if elem.name == "meta":
                b_val = (elem.get("content") or "").strip()
            else:
                b_val = elem.get_text(strip=True)
            b_clean = re.sub(r'^(brand:\s*|visit the\s*|\s*store$)', '', b_val, flags=re.IGNORECASE).strip()
            if b_clean:
                brand = b_clean
                break

    # 3. Price Selectors
    price_selectors = [
        ".a-price .a-offscreen", "#priceblock_ourprice", "#priceblock_dealprice",
        ".apexPriceToPay .a-offscreen", ".pdp-price", ".pdp-product-price",
        ".goods-price", ".price", "meta[property='product:price:amount']", "meta[property='og:price:amount']"
    ]
    for sel in price_selectors:
        elem = soup.select_one(sel)
        if elem:
            raw_p = elem.get("content") if elem.name == "meta" else elem.get_text(strip=True)
            p_val, p_str = parse_price(raw_p)
            if p_val > 0.0:
                price_val = p_val
                price_str = p_str
                break

    # Currency from meta tag if available
    curr_elem = soup.select_one("meta[property='product:price:currency']") or soup.select_one("meta[property='og:price:currency']")
    if curr_elem and curr_elem.get("content"):
        currency = curr_elem.get("content").strip().upper()

    # 4. Rating Selectors
    rating_selectors = [
        "#acrPopover span.a-icon-alt", ".a-icon-star span.a-icon-alt",
        ".score .score-average", ".pdp-review-summary__stars", ".rating-score"
    ]
    for sel in rating_selectors:
        elem = soup.select_one(sel)
        if elem:
            r_text = elem.get_text(strip=True)
            # Match patterns like "4.5 out of 5" or "4.5"
            match = re.search(r'(\d+(\.\d+)?)', r_text)
            if match:
                rating_val = parse_rating(match.group(1))
                if rating_val > 0.0:
                    break

    # 5. Rating Count & Review Count Selectors
    rev_count_selectors = [
        "#acrCustomerReviewText", "span[data-hook='total-review-count']",
        ".count", ".pdp-review-summary__link", ".total-reviews"
    ]
    for sel in rev_count_selectors:
        elem = soup.select_one(sel)
        if elem:
            c_text = elem.get_text(strip=True)
            cnt = parse_review_count(c_text)
            if cnt > 0:
                rating_count_val = cnt
                review_count_val = cnt
                break

    # 6. Seller Selectors
    seller_selectors = [
        "#tabular-buybox .tabular-buybox-text[tabular-attribute-name='Sold by']",
        "#merchant-info a", ".seller-name__detail-name", ".seller-name", ".merchant-name"
    ]
    for sel in seller_selectors:
        elem = soup.select_one(sel)
        if elem:
            s_val = elem.get_text(strip=True)
            if s_val and len(s_val) > 1:
                seller = s_val
                break

    # 7. Image Selectors
    img_selectors = [
        "#landingImage", "#imgBlkFront", ".pdp-mod-common-image", "meta[property='og:image']", "img.main-image"
    ]
    for sel in img_selectors:
        elem = soup.select_one(sel)
        if elem:
            src = elem.get("content") if elem.name == "meta" else (elem.get("src") or elem.get("data-src"))
            if src and src.startswith("http"):
                image_link = src
                break

    # 8. Customer Reviews Elements (only if present in HTML)
    review_cards = soup.select('div[data-hook="review"]') or soup.select('.review-item')
    for card in review_cards[:5]:
        body_elem = card.select_one('.review-text-content span') or card.select_one('.review-content') or card.select_one('.review-body')
        if not body_elem:
            continue
        body_text = body_elem.get_text(strip=True)
        if not body_text:
            continue

        author_elem = card.select_one('.a-profile-name') or card.select_one('.review-author')
        author_text = author_elem.get_text(strip=True) if author_elem else "Anonymous"

        card_rating = 0.0
        r_elem = card.select_one('.review-rating span') or card.select_one('.rating')
        if r_elem:
            m = re.search(r'(\d+(\.\d+)?)', r_elem.get_text(strip=True))
            if m:
                card_rating = parse_rating(m.group(1))

        date_elem = card.select_one('span[data-hook="review-date"]') or card.select_one('.review-date')
        date_text = date_elem.get_text(strip=True) if date_elem else None

        verified_badge = bool(card.select_one('span[data-hook="avp-badge"]') or card.select_one('.verified-purchase'))

        reviews_list.append(MarketplaceReview(
            author=author_text,
            rating=card_rating,
            comment=body_text,
            date=date_text,
            verified_purchase=verified_badge
        ))

    return {
        "title": title,
        "brand": brand,
        "price_val": price_val,
        "price_str": price_str,
        "currency": currency,
        "rating_val": rating_val,
        "rating_count_val": rating_count_val,
        "review_count_val": review_count_val,
        "seller": seller,
        "image_link": image_link,
        "reviews": reviews_list,
        "source": "html_selectors"
    }


def extract_daraz_embedded_state(html: str, url: Optional[str] = None) -> Dict[str, Any]:
    """
    Extracts product tracking state embedded in Daraz PDP HTML (e.g. pdpTrackingData or __moduleData__).
    Extracts real price, currency, brand, item_id, and product name directly from the page state.
    """
    result = {
        "title": None,
        "brand": None,
        "price_val": 0.0,
        "price_str": None,
        "currency": None,
        "item_id": None,
        "seller": None,
    }
    
    data = None
    
    # Method 1: Check pdpTrackingData JavaScript string / object
    idx = html.find("var pdpTrackingData =")
    if idx != -1:
        end_idx = html.find(";\n", idx)
        if end_idx == -1:
            end_idx = html.find(";", idx)
        if end_idx != -1:
            raw_val = html[idx + len("var pdpTrackingData ="):end_idx].strip()
            try:
                if raw_val.startswith('"'):
                    unquoted = json.loads(raw_val)
                    data = json.loads(unquoted) if isinstance(unquoted, str) else unquoted
                else:
                    data = json.loads(raw_val)
            except Exception:
                pass
                
    # Method 2: Check __moduleData__ JavaScript object
    if not data or not isinstance(data, dict):
        idx_mod = html.find("var __moduleData__ =")
        if idx_mod != -1:
            try:
                mod_content = html[idx_mod + len("var __moduleData__ ="):].lstrip()
                mod_json, _ = json.JSONDecoder().raw_decode(mod_content)
                data = mod_json.get("data", {}).get("root", {}).get("fields", {}).get("tracking", {})
            except Exception:
                pass

    if isinstance(data, dict):
        # 1. Price
        raw_price = data.get("pdt_price")
        if raw_price:
            p_val, p_str = parse_price(raw_price)
            if p_val > 0.0:
                result["price_val"] = p_val
                result["price_str"] = p_str or str(raw_price)

        # 2. Currency
        curr = data.get("core", {}).get("currencyCode")
        country = data.get("core", {}).get("country")
        if curr and str(curr).strip():
            result["currency"] = str(curr).strip().upper()
        elif country:
            country_curr_map = {"LK": "LKR", "PK": "PKR", "BD": "BDT", "NP": "NPR", "MM": "MMK"}
            result["currency"] = country_curr_map.get(str(country).strip().upper())

        # 3. Brand
        b_name = data.get("brand_name")
        if b_name and str(b_name).strip():
            result["brand"] = str(b_name).strip()

        # 4. Title / Product Name
        p_name = data.get("pdt_name")
        if p_name and str(p_name).strip():
            result["title"] = str(p_name).strip()

        # 5. Item ID / SKU
        sku = data.get("pdt_sku")
        if sku:
            sku_str = str(sku).strip()
            if "_" in sku_str:
                sku_str = sku_str.split("_")[0]
            result["item_id"] = sku_str

        # 6. Seller
        s_name = data.get("seller_name")
        if s_name and str(s_name).strip():
            result["seller"] = str(s_name).strip()

    # Locale / URL fallback for currency and item_id if URL is known
    if url:
        if not result["item_id"]:
            m_id = re.search(r'-i(\d+)', url)
            if m_id:
                result["item_id"] = m_id.group(1)
        if not result["currency"]:
            if ".lk" in url:
                result["currency"] = "LKR"
            elif ".pk" in url:
                result["currency"] = "PKR"
            elif ".com.bd" in url:
                result["currency"] = "BDT"
            elif ".np" in url:
                result["currency"] = "NPR"

    return result


def extract_product_metadata(html: str, platform: Optional[str] = None, url: Optional[str] = None) -> Dict[str, Any]:
    """
    Extracts product metadata from HTML, prioritizing structured JSON-LD data
    with robust HTML selector and embedded state fallbacks.
    Returns parsed fields and operational data completeness status:
    - SUCCESS: title + (price > 0 or rating > 0 or reviews present)
    - PARTIAL_DATA: title present, but key fields (rating, price, or reviews) are missing
    - UNAVAILABLE: no usable product title or data found in HTML
    """
    if not html or not html.strip():
        return {
            "status": "UNAVAILABLE",
            "explanation": "Empty HTML content received.",
            "title": None,
            "brand": None,
            "price_val": 0.0,
            "price_str": None,
            "currency": None,
            "rating_val": 0.0,
            "rating_count_val": 0,
            "review_count_val": 0,
            "seller": None,
            "image_link": None,
            "reviews": []
        }

    soup = BeautifulSoup(html, 'html.parser')

    # 1. Attempt JSON-LD extraction
    json_ld_products = extract_json_ld_products(soup)
    extracted = None
    if json_ld_products:
        extracted = extract_from_json_ld(json_ld_products[0])

    # 2. Attempt HTML selectors extraction
    html_extracted = extract_from_html_selectors(soup, platform=platform)

    # 3. Merge: prefer JSON-LD fields when present; fill gaps from HTML selectors
    if extracted:
        for key in ["title", "brand", "price_str", "seller", "image_link"]:
            if not extracted.get(key) and html_extracted.get(key):
                extracted[key] = html_extracted[key]
        if (not extracted.get("price_val") or extracted["price_val"] == 0.0) and html_extracted.get("price_val", 0.0) > 0.0:
            extracted["price_val"] = html_extracted["price_val"]
            if html_extracted.get("currency"):
                extracted["currency"] = html_extracted["currency"]
        if (not extracted.get("rating_val") or extracted["rating_val"] == 0.0) and html_extracted.get("rating_val", 0.0) > 0.0:
            extracted["rating_val"] = html_extracted["rating_val"]
        if (not extracted.get("rating_count_val") or extracted["rating_count_val"] == 0) and html_extracted.get("rating_count_val", 0) > 0:
            extracted["rating_count_val"] = html_extracted["rating_count_val"]
        if (not extracted.get("review_count_val") or extracted["review_count_val"] == 0) and html_extracted.get("review_count_val", 0) > 0:
            extracted["review_count_val"] = html_extracted["review_count_val"]
        if not extracted.get("reviews") and html_extracted.get("reviews"):
            extracted["reviews"] = html_extracted["reviews"]
    else:
        extracted = html_extracted

    # 4. Daraz Embedded State Extraction (pdpTrackingData / __moduleData__)
    plat_str = (platform or "").lower()
    is_daraz = "daraz" in plat_str or (url and "daraz" in url.lower()) or ("pdpTrackingData" in html) or ("__moduleData__" in html)
    if is_daraz:
        daraz_state = extract_daraz_embedded_state(html, url=url)
        if daraz_state.get("price_val", 0.0) > 0.0:
            extracted["price_val"] = daraz_state["price_val"]
            extracted["price_str"] = daraz_state["price_str"]
        if daraz_state.get("currency"):
            extracted["currency"] = daraz_state["currency"]
        if daraz_state.get("brand") and (not extracted.get("brand") or extracted.get("brand").lower() in ("no brand", "none", "")):
            extracted["brand"] = daraz_state["brand"]
        if not extracted.get("title") and daraz_state.get("title"):
            extracted["title"] = daraz_state["title"]
        if daraz_state.get("seller") and not extracted.get("seller"):
            extracted["seller"] = daraz_state["seller"]
        if daraz_state.get("item_id"):
            extracted["item_id"] = daraz_state["item_id"]

    # 5. Currency Evidence Validation:
    # Keep currency as LKR only when supported by page/locale evidence; do not default unknown currencies to USD.
    if not extracted.get("currency"):
        if is_daraz:
            if (url and ".lk" in url.lower()) or "daraz.lk" in html.lower() or "country\":\"lk\"" in html.lower():
                extracted["currency"] = "LKR"
            elif (url and ".pk" in url.lower()) or "daraz.pk" in html.lower() or "country\":\"pk\"" in html.lower():
                extracted["currency"] = "PKR"
            elif (url and ".com.bd" in url.lower()) or "country\":\"bd\"" in html.lower():
                extracted["currency"] = "BDT"
            elif (url and ".np" in url.lower()) or "country\":\"np\"" in html.lower():
                extracted["currency"] = "NPR"
            else:
                extracted["currency"] = None
        elif "amazon" in plat_str:
            extracted["currency"] = "USD"
        else:
            extracted["currency"] = None

    title = extracted.get("title")
    if not title:
        return {
            "status": "UNAVAILABLE",
            "explanation": "Page contained no readable product title in structured data or HTML.",
            **extracted
        }

    # Determine status: SUCCESS vs PARTIAL_DATA
    has_price = (extracted.get("price_val", 0.0) > 0.0)
    has_rating = (extracted.get("rating_val", 0.0) > 0.0)
    has_reviews = bool(extracted.get("reviews"))

    if has_price and (has_rating or has_reviews):
        status = "SUCCESS"
        explanation = "Extracted product title, price, and marketplace rating/review data."
    else:
        status = "PARTIAL_DATA"
        missing = []
        if not has_price:
            missing.append("price")
        if not has_rating:
            missing.append("rating")
        if not has_reviews:
            missing.append("reviews")
        explanation = f"Extracted product title '{title}' but missing: {', '.join(missing)}."

    extracted["status"] = status
    extracted["explanation"] = explanation
    return extracted
