"""
Daraz Public Marketplace Scraper Module
Queries Daraz catalog search endpoint for authentic cosmetic product listings.
Extracts real listings, prices, sellers, ratings, and customer reviews.
Handles anti-bot blocks cleanly with source_status='blocked'/'unavailable'.
"""

import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from typing import List
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
from app.services.scraping.schemas import RawMarketplaceItem
from app.services.scraping.url_scraper import fetch_daraz_reviews_and_ratings

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "x-requested-with": "XMLHttpRequest",
}

DARAZ_CHALLENGE_MARKERS = ("x5secdata", "/_____tmd_____/punish", "punish?x5secdata", "nocaptcha")

def _get_fast_session():
    """Session configured with zero retries so unreachable/sandboxed networks fail in ms rather than minutes."""
    s = requests.Session()
    adapter = HTTPAdapter(max_retries=Retry(total=0, connect=0, read=0, status=0))
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s


def scrape_daraz_products(query: str, max_results: int = 3) -> List[RawMarketplaceItem]:
    """
    Queries Daraz public marketplace search for authentic cosmetic listings.
    1. Uses Daraz's public AJAX catalog endpoint to retrieve structured product listings.
    2. Extracts real prices (LKR), seller names, ratings, and review counts.
    3. Fetches actual customer reviews for matching items using public review endpoints.
    4. Falls back to HTML parsing if AJAX is unavailable.
    """
    clean_query = query.strip()
    if not clean_query:
        return [RawMarketplaceItem(
            platform="Daraz",
            raw_title="No Daraz query provided",
            source_status="unavailable",
            status_code="EMPTY_QUERY",
            explanation="Empty search query provided to Daraz scraper."
        )]

    ajax_url = f"https://www.daraz.lk/catalog/?q={quote_plus(clean_query)}&ajax=true"

    try:
        session = _get_fast_session()
        resp = session.get(ajax_url, headers=HEADERS, timeout=(3.0, 4.0))

        # 1. Anti-bot status checks
        if resp.status_code in [403, 503, 429]:
            return [RawMarketplaceItem(
                platform="Daraz",
                raw_title="Daraz Access Restricted",
                source_status="blocked",
                status_code="MARKETPLACE_BLOCKED",
                explanation=f"Daraz server returned HTTP {resp.status_code} anti-bot defense."
            )]

        low_text = resp.text.lower()
        if any(marker in low_text for marker in DARAZ_CHALLENGE_MARKERS):
            return [RawMarketplaceItem(
                platform="Daraz",
                raw_title="Daraz Access Restricted",
                source_status="blocked",
                status_code="MARKETPLACE_BLOCKED",
                explanation=f"Daraz returned a CAPTCHA / slider verification page (HTTP {resp.status_code})."
            )]

        # 2. Attempt JSON extraction from AJAX endpoint
        items: List[RawMarketplaceItem] = []
        try:
            data = resp.json()
            list_items = data.get("mods", {}).get("listItems", [])
            if list_items:
                for it in list_items[:max_results]:
                    name = it.get("name") or "Daraz Cosmetic Product"
                    item_id = str(it.get("itemId") or it.get("nid") or "")
                    item_url = it.get("itemUrl")
                    if item_url and item_url.startswith("//"):
                        item_url = "https:" + item_url
                    elif item_url and not item_url.startswith("http"):
                        item_url = f"https://www.daraz.lk{item_url}"

                    try:
                        price_val = float(it.get("price") or 0.0)
                    except (ValueError, TypeError):
                        price_val = 0.0

                    price_str = it.get("priceShow") or (f"Rs. {price_val:,.2f}" if price_val > 0 else None)
                    seller = it.get("sellerName")

                    try:
                        rating_val = float(it.get("ratingScore") or 0.0)
                    except (ValueError, TypeError):
                        rating_val = 0.0

                    try:
                        review_count = int(it.get("review") or 0)
                    except (ValueError, TypeError):
                        review_count = 0

                    img_url = it.get("image")

                    # Fetch real customer reviews from public endpoint if item_id and url exist
                    card_reviews = []
                    if item_id and item_url:
                        avg_r, rate_c, rev_c, revs = fetch_daraz_reviews_and_ratings(item_id, item_url, timeout=2)
                        if revs:
                            card_reviews = revs
                        if avg_r > 0:
                            rating_val = avg_r
                        if rev_c > 0:
                            review_count = rev_c

                    has_complete_data = (price_val > 0.0 and (rating_val > 0.0 or bool(card_reviews)))

                    items.append(RawMarketplaceItem(
                        platform="Daraz",
                        raw_title=name,
                        price_str=price_str,
                        price_val=price_val,
                        currency="LKR",
                        rating_val=rating_val,
                        rating_count_val=review_count,
                        review_count_val=review_count,
                        seller=seller,
                        link=item_url,
                        image_link=img_url,
                        source_status="available",
                        status_code="SUCCESS" if has_complete_data else "PARTIAL_DATA",
                        reviews=card_reviews,
                        explanation=f"Extracted verified Daraz listing with {len(card_reviews)} customer review(s)."
                    ))

                if items:
                    return items
        except (ValueError, TypeError):
            pass

        # 3. Fallback: Parse HTML if AJAX response was not pure JSON
        soup = BeautifulSoup(resp.text, 'html.parser')
        cards = soup.select('div[data-qa-locator="product-item"]') or soup.select('.c1_t2i')

        if not cards:
            return [RawMarketplaceItem(
                platform="Daraz",
                raw_title="No Daraz listings returned",
                source_status="unavailable",
                status_code="NOT_RETRIEVABLE",
                explanation=(
                    f"Daraz search responded (HTTP {resp.status_code}) with a client-side JavaScript shell containing no "
                    "product data in server HTML. Listings require executing Daraz's JavaScript."
                )
            )]

        for card in cards[:max_results]:
            title_elem = card.select_one('.c165B3') or card.select_one('a[title]')
            title = title_elem.get_text(strip=True) if title_elem else "Daraz Product"

            link_elem = card.select_one('a')
            link = link_elem['href'] if link_elem and 'href' in link_elem.attrs else None
            if link and link.startswith('//'):
                link = "https:" + link

            price_elem = card.select_one('.c3g2v4') or card.select_one('.c1358e')
            price_str = price_elem.get_text(strip=True) if price_elem else None

            price_val = 0.0
            try:
                digits = ''.join(c for c in (price_str or "") if c.isdigit() or c == '.')
                price_val = float(digits) if digits else 0.0
            except ValueError:
                price_val = 0.0

            seller_elem = card.select_one('.c2pr16') or card.select_one('.seller-name')
            seller_val = seller_elem.get_text(strip=True) if seller_elem else None

            img_elem = card.select_one('img')
            img_url = img_elem.get('src') if img_elem is not None else None

            card_rating_val = 0.0
            card_rating_count = 0
            card_review_count = 0
            card_reviews = []

            if link:
                m_id = re.search(r'-i(\d+)', link)
                if m_id:
                    item_id = m_id.group(1)
                    avg_r, rate_c, rev_c, rev_items = fetch_daraz_reviews_and_ratings(item_id, link, timeout=4)
                    if avg_r > 0.0:
                        card_rating_val = avg_r
                        card_rating_count = rate_c
                        card_review_count = rev_c
                    if rev_items:
                        card_reviews = rev_items

            has_complete_data = (price_val > 0.0 and (card_rating_val > 0.0 or bool(card_reviews)))

            items.append(RawMarketplaceItem(
                platform="Daraz",
                raw_title=title,
                price_str=price_str,
                price_val=price_val,
                currency="LKR",
                rating_val=card_rating_val,
                rating_count_val=card_rating_count,
                review_count_val=card_review_count,
                seller=seller_val,
                link=link,
                image_link=img_url,
                source_status="available",
                status_code="SUCCESS" if has_complete_data else "PARTIAL_DATA",
                reviews=card_reviews,
                explanation=f"Extracted Daraz listing with {len(card_reviews)} review(s)."
            ))

        return items if items else [RawMarketplaceItem(
            platform="Daraz",
            raw_title="No matching Daraz listings",
            source_status="unavailable",
            status_code="NO_MATCH_FOUND",
            explanation="No Daraz products matched the search query."
        )]

    except Exception as exc:
        return [RawMarketplaceItem(
            platform="Daraz",
            raw_title="Daraz Connection Error",
            source_status="blocked",
            status_code="SCRAPER_ERROR",
            explanation=f"Network error querying Daraz: {str(exc)}"
        )]
