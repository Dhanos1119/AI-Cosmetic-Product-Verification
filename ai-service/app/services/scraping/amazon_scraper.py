"""
Amazon Public Marketplace Scraper Module
Extracts authentic product listings, prices, ratings, and review metrics from Amazon search results.
Handles anti-bot blocks cleanly with source_status='blocked' without bypass.
"""

import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
from typing import List, Optional, Any
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
from app.services.scraping.schemas import RawMarketplaceItem

AMAZON_BASE_URL = "https://www.amazon.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

BOT_CHALLENGE_MARKERS = (
    "Type the characters you see in this image",
    "bm-verify=",
    "/_sec/verify?provider=interstitial",
    "api-services-support@amazon.com",
)

def _get_fast_session():
    """Session configured with zero retries so unreachable/sandboxed networks fail in ms rather than minutes."""
    s = requests.Session()
    adapter = HTTPAdapter(max_retries=Retry(total=0, connect=0, read=0, status=0))
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s


def fetch_amazon_reviews(asin: Optional[str] = None, link: Optional[str] = None, timeout: float = 2.0) -> List[Any]:
    """
    Attempts to fetch genuine customer review text for a matched Amazon product.
    If Amazon blocks, returns CAPTCHA, or times out, returns an empty list cleanly without failing the main scraper.
    """
    if not asin and not link:
        return []

    target_url = (
        f"https://www.amazon.com/product-reviews/{asin}/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews"
        if asin
        else link
    )

    try:
        session = _get_fast_session()
        resp = session.get(target_url, headers=HEADERS, timeout=(timeout, timeout))
        if resp.status_code != 200:
            return []
        if any(marker in resp.text for marker in BOT_CHALLENGE_MARKERS):
            return []

        soup = BeautifulSoup(resp.text, 'html.parser')
        cards = soup.select('div[data-hook="review"]') or soup.select('.review')
        reviews = []
        for card in cards[:10]:
            body = (
                card.select_one('span[data-hook="review-body"] span')
                or card.select_one('.review-text-content span')
                or card.select_one('.review-body')
            )
            comment = body.get_text(strip=True) if body else ""
            if not comment:
                continue

            author_el = card.select_one('.a-profile-name') or card.select_one('.review-author')
            author = author_el.get_text(strip=True) if author_el else "Amazon Customer"

            rating = 5.0
            r_el = (
                card.select_one('i[data-hook="review-star-rating"] span')
                or card.select_one('.review-rating span')
                or card.select_one('.a-icon-alt')
            )
            if r_el:
                m = re.search(r'(\d+(?:\.\d+)?)', r_el.get_text(strip=True))
                if m:
                    try:
                        rating = float(m.group(1))
                    except ValueError:
                        rating = 5.0

            date_el = card.select_one('span[data-hook="review-date"]') or card.select_one('.review-date')
            date_str = date_el.get_text(strip=True) if date_el else None

            vp_el = card.select_one('span[data-hook="avp-badge"]')
            is_vp = bool(vp_el)

            from app.schemas.marketplace import MarketplaceReview
            reviews.append(MarketplaceReview(
                author=author,
                rating=rating,
                comment=comment,
                date=date_str,
                verified_purchase=is_vp
            ))
        return reviews
    except Exception:
        return []


def extract_amazon_card_link(card) -> Optional[str]:
    """
    Extracts the product link from an Amazon search-result card using the href present in the page.
    Supports both legacy markup (h2 > a[href]) and modern markup (.s-title-instructions-style a, /dp/ anchors).
    """
    link_elem = (
        card.select_one('h2 a[href]')
        or card.select_one('.s-title-instructions-style a[href]')
        or card.select_one('a[href*="/dp/"]')
        or card.select_one('a.a-link-normal.s-no-outline[href]')
    )
    if link_elem is None:
        h2 = card.select_one('h2')
        if h2 is not None:
            parent_anchor = h2.find_parent('a', href=True)
            if parent_anchor is not None:
                link_elem = parent_anchor

    href = (link_elem.get('href') or '').strip() if link_elem is not None else ''
    if not href or href.startswith('#') or href.lower().startswith('javascript:'):
        return None
    return urljoin(AMAZON_BASE_URL, href)


def scrape_amazon_products(query: str, max_results: int = 3) -> List[RawMarketplaceItem]:
    """
    Queries Amazon public search endpoint for cosmetic product listings.
    Extracts real titles, canonical links, prices, ratings, and review metrics.
    """
    clean_query = query.strip()
    if not clean_query:
        return [RawMarketplaceItem(
            platform="Amazon",
            raw_title="No query provided",
            source_status="unavailable",
            status_code="EMPTY_QUERY",
            explanation="Empty search query provided to Amazon scraper."
        )]

    url = f"https://www.amazon.com/s?k={quote_plus(clean_query)}"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=(3.0, 4.0))

        # 1. Anti-bot status checks
        if resp.status_code in [403, 503, 429]:
            return [RawMarketplaceItem(
                platform="Amazon",
                raw_title="Amazon Access Blocked",
                source_status="blocked",
                status_code="MARKETPLACE_BLOCKED",
                explanation=f"Amazon returned HTTP {resp.status_code} anti-bot protection."
            )]

        if any(marker in resp.text for marker in BOT_CHALLENGE_MARKERS):
            return [RawMarketplaceItem(
                platform="Amazon",
                raw_title="Amazon Captcha Blocked",
                source_status="blocked",
                status_code="MARKETPLACE_BLOCKED",
                explanation="Amazon returned a CAPTCHA / bot-verification page. Not bypassed."
            )]

        soup = BeautifulSoup(resp.text, 'html.parser')
        search_results = soup.select('div[data-component-type="s-search-result"]')

        if not search_results:
            return [RawMarketplaceItem(
                platform="Amazon",
                raw_title="No matching listings found",
                source_status="unavailable",
                status_code="NO_MATCH_FOUND",
                explanation=f"Amazon responded (HTTP {resp.status_code}) but contained no search-result cards for this query."
            )]

        items: List[RawMarketplaceItem] = []
        for card in search_results:
            if len(items) >= max_results:
                break

            # 2. Full Product Title Extraction
            title = None
            title_anchor = (
                card.select_one('.s-title-instructions-style a.a-text-normal')
                or card.select_one('a.s-line-clamp-2')
                or card.select_one('a.s-line-clamp-3')
                or card.select_one('h2 a span')
                or card.select_one('h2 a')
            )
            if title_anchor:
                title = title_anchor.get_text(strip=True)

            h2 = card.select_one('h2')
            brand_in_card = h2.get_text(strip=True) if h2 else ""

            if not title:
                title = brand_in_card

            # If brand is in h2 but not in title, prepend it so product matcher recognizes brand alignment
            if brand_in_card and title and brand_in_card.lower() not in title.lower() and len(brand_in_card) < 30:
                title = f"{brand_in_card} {title}"

            if not title:
                continue

            # 3. Canonical Product Link
            link = extract_amazon_card_link(card)
            asin = (card.get('data-asin') or '').strip() or None

            # 4. Price and Currency Extraction
            price_val = 0.0
            price_str = None
            currency = "USD"
            price_elem = card.select_one('.a-price .a-offscreen')
            if price_elem:
                price_str = price_elem.get_text(strip=True)
                if "lkr" in price_str.lower() or "rs" in price_str.lower():
                    currency = "LKR"
                elif "usd" in price_str.lower() or "$" in price_str:
                    currency = "USD"

                m = re.search(r'[\d,]+(?:\.\d+)?', price_str)
                if m:
                    try:
                        price_val = float(m.group(0).replace(',', ''))
                    except ValueError:
                        price_val = 0.0

            # 5. Rating Extraction
            rating_val = 0.0
            rating_elem = card.select_one('[aria-label*="out of 5 stars"]') or card.select_one('.a-icon-alt')
            if rating_elem:
                r_text = rating_elem.get('aria-label') or rating_elem.get_text(strip=True)
                m = re.search(r'(\d+(?:\.\d+)?)', r_text)
                if m:
                    try:
                        rating_val = float(m.group(1))
                    except ValueError:
                        rating_val = 0.0

            # 6. Review Count Extraction
            review_count = 0
            star_el = card.select_one('[aria-label*="stars"]') or card.select_one('.a-icon-alt')
            if star_el:
                row = star_el.find_parent('div', class_='a-row') or star_el.find_parent('div')
                if row:
                    for s in row.select('span'):
                        txt = s.get_text(strip=True).replace('(', '').replace(')', '').replace(',', '').strip()
                        if 'k' in txt.lower():
                            m_k = re.search(r'(\d+(?:\.\d+)?)', txt)
                            if m_k:
                                review_count = int(float(m_k.group(1)) * 1000)
                                break
                        elif re.match(r'^\d+$', txt) and int(txt) > 0:
                            review_count = int(txt)
                            break

            if review_count == 0:
                rev_el = card.select_one('a.s-underline-text span.s-underline-text') or card.select_one('span[aria-label*="ratings"]')
                if rev_el:
                    txt = rev_el.get_text(strip=True).replace('(', '').replace(')', '').replace(',', '').strip()
                    if 'k' in txt.lower():
                        m_k = re.search(r'(\d+(?:\.\d+)?)', txt)
                        if m_k:
                            review_count = int(float(m_k.group(1)) * 1000)
                    else:
                        m_num = re.search(r'\d+', txt)
                        if m_num:
                            review_count = int(m_num.group(0))

            # 7. Image
            img_elem = card.select_one('img.s-image')
            img_url = img_elem['src'] if img_elem and 'src' in img_elem.attrs else None

            # Amazon search cards do not expose verified merchant seller names, so seller is None
            seller_val = None

            card_reviews = []
            if len(items) == 0 and (asin or link):
                card_reviews = fetch_amazon_reviews(asin=asin, link=link, timeout=2.0)

            items.append(RawMarketplaceItem(
                platform="Amazon",
                raw_title=title,
                price_str=price_str,
                price_val=price_val,
                currency=currency,
                rating_val=rating_val,
                rating_count_val=review_count,
                review_count_val=review_count,
                seller=seller_val,
                link=link,
                image_link=img_url,
                listing_id=asin,
                reviews=card_reviews,
                source_status="available",
                status_code="SUCCESS" if (price_val > 0.0 and (rating_val > 0.0 or review_count > 0)) else "PARTIAL_DATA",
                explanation=f"Extracted verified Amazon listing with {len(card_reviews)} review(s): {title[:50]}"
            ))

        return items if items else [RawMarketplaceItem(
            platform="Amazon",
            raw_title="No matching listings",
            source_status="unavailable",
            status_code="NO_MATCH_FOUND",
            explanation="Amazon search cards were present but none contained a valid product title."
        )]

    except Exception as exc:
        return [RawMarketplaceItem(
            platform="Amazon",
            raw_title="Amazon Service Connection Failed",
            source_status="blocked",
            status_code="SCRAPER_ERROR",
            explanation=f"Network error querying Amazon: {str(exc)}"
        )]
