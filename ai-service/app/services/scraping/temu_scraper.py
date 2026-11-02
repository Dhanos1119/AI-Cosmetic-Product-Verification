"""
Temu Public Marketplace Scraper Module
Queries Temu public product search.
Handles anti-bot/CAPTCHA restrictions cleanly with source_status='blocked'.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from typing import List
from app.services.scraping.schemas import RawMarketplaceItem

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}

def scrape_temu_products(query: str, max_results: int = 3) -> List[RawMarketplaceItem]:
    """
    Queries Temu public marketplace endpoint.
    Temu strictly requires dynamic JS execution or app token authentication; returns clean blocked status if restricted.
    """
    url = f"https://www.temu.com/search_result.html?search_key={quote_plus(query)}"
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        if resp.status_code in [403, 503, 429]:
            return [RawMarketplaceItem(
                platform="Temu",
                raw_title="Temu Access Restricted",
                source_status="blocked",
                status_code="MARKETPLACE_BLOCKED",
                explanation=f"Temu server returned HTTP {resp.status_code} security protection."
            )]

        soup = BeautifulSoup(resp.text, 'html.parser')
        low_text = resp.text.lower()

        # Explicit CAPTCHA / challenge page (reported, never bypassed).
        # NOTE: a plain 'verify' substring is NOT used: normal Temu pages contain config keys such as
        # 'verifyAuthToken', which previously caused every response to be labelled as anti-bot blocked.
        if "captcha" in low_text:
            return [RawMarketplaceItem(
                platform="Temu",
                raw_title="Temu Protection Active",
                source_status="blocked",
                status_code="MARKETPLACE_BLOCKED",
                explanation=f"Temu returned a CAPTCHA / bot-verification page (HTTP {resp.status_code}). Not bypassed; no listing data retrieved."
            )]

        # Temu uses dynamic client JS rendering; product cards are not in the server HTML
        if not soup.select('.product-item'):
            return [RawMarketplaceItem(
                platform="Temu",
                raw_title="No Temu listings returned",
                source_status="unavailable",
                status_code="NOT_RETRIEVABLE",
                explanation=(
                    f"Temu search endpoint responded (HTTP {resp.status_code}) with a client-rendered page containing no "
                    "product data in the server HTML. Listings require executing Temu's JavaScript and its "
                    "anti-bot/session verification, which this scraper does not attempt. Whether the product exists on Temu is unknown."
                )
            )]

        items = []
        cards = soup.select('.product-item')
        for card in cards[:max_results]:
            title_elem = card.select_one('.title') or card.select_one('a')
            title = title_elem.get_text(strip=True) if title_elem else "Temu Cosmetic Listing"

            link_elem = card.select_one('a')
            link = f"https://www.temu.com{link_elem['href']}" if link_elem and 'href' in link_elem.attrs else None

            price_elem = card.select_one('.price')
            price_str = price_elem.get_text(strip=True) if price_elem else None

            price_val = 0.0
            try:
                digits = ''.join(c for c in (price_str or "") if c.isdigit() or c == '.')
                price_val = float(digits) if digits else 0.0
            except ValueError:
                price_val = 0.0

            seller_elem = card.select_one('.merchant-name')
            seller_val = seller_elem.get_text(strip=True) if seller_elem else None

            # Rating / review count are not parsed from Temu cards, so they are left at 0 (unknown)
            # rather than assigned hardcoded values.
            items.append(RawMarketplaceItem(
                platform="Temu",
                raw_title=title,
                price_str=price_str,
                price_val=price_val,
                currency="USD",
                rating_val=0.0,
                review_count_val=0,
                seller=seller_val,
                link=link,
                source_status="available",
                status_code="PARTIAL_DATA"
            ))

        return items if items else [RawMarketplaceItem(
            platform="Temu",
            raw_title="No matching Temu listings",
            source_status="unavailable",
            status_code="NO_MATCH_FOUND",
            explanation="No Temu products matched the query."
        )]

    except Exception as exc:
        return [RawMarketplaceItem(
            platform="Temu",
            raw_title="Temu Connection Error",
            source_status="blocked",
            status_code="SCRAPER_ERROR",
            explanation=f"Network error querying Temu: {str(exc)}"
        )]
