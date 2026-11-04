# Phase 1 Database Architecture and Design Specification

**System**: AI-Based Cosmetic Product Verification and Recommendation System  
**Document Version**: 1.0.0  
**Date**: 2026-09-23  

---

## 1. Existing Schema Inspection Findings & Reusable Components

Prior to designing the relational database layer, existing Pydantic data transfer schemas and service models were audited to prevent data model duplication and preserve 100% backward API contract compatibility:

| Existing Pydantic Schema | Target ORM Entity | Field Alignment & Reusable Mapping |
| :--- | :--- | :--- |
| `ProductIdentity` ([`ai-service/app/schemas/marketplace.py`](file:///c:/Users/Dhanoshigan%20Ratnaraj/AI-Cosmetic-Product-Verification/ai-service/app/schemas/marketplace.py)) | **`Product`** | Maps `brand`, `product_name`, `product_type`, `category`, `product_id`, and `shade_or_variant`. |
| `RawMarketplaceItem` ([`ai-service/app/services/scraping/schemas.py`](file:///c:/Users/Dhanoshigan%20Ratnaraj/AI-Cosmetic-Product-Verification/ai-service/app/services/scraping/schemas.py)) | **`MarketplaceListing`** | Maps `platform`, `raw_title`, `price_val`, `currency`, `rating_val`, `review_count_val`, `seller`, `link`, `image_link`, `source_status`, and `explanation`. |
| `MarketplaceListing` ([`ai-service/app/schemas/marketplace.py`](file:///c:/Users/Dhanoshigan%20Ratnaraj/AI-Cosmetic-Product-Verification/ai-service/app/schemas/marketplace.py)) | **`MarketplaceListing`** & **`Seller`** | Maps listing metrics, seller details, `match_status`, `match_confidence`, and `status_explanation`. |
| `MarketplaceReview` ([`ai-service/app/schemas/marketplace.py`](file:///c:/Users/Dhanoshigan%20Ratnaraj/AI-Cosmetic-Product-Verification/ai-service/app/schemas/marketplace.py)) | **`CustomerReview`** | Maps `author`, `rating`, `comment`, `date`, and `verified_purchase`. |
| `ReviewResultDetails` ([`ai-service/app/schemas/response.py`](file:///c:/Users/Dhanoshigan%20Ratnaraj/AI-Cosmetic-Product-Verification/ai-service/app/schemas/response.py)) | **`ReviewAnalysis`** | Maps `review_authenticity_score`, `sentiment_label`, `average_rating`, `verified_buyer_percentage`, `authenticity_status`, `suspicious_review_flag`, and `summary`. |
| `PlatformComparisonScore` & `ScoreBreakdown` | **`MarketplaceEvidence`** | Maps `total_score`, `rank`, `review_trust_score` (40%), `rating_score` (25%), `seller_trust_score` (20%), `match_confidence_score` (15%), and `recommendation_reason`. |

---

## 2. Entity-Relationship Diagram (ERD)

```mermaid
erDiagram
    PRODUCTS ||--o{ MARKETPLACE_LISTINGS : "has listings"
    MARKETPLACES ||--o{ SELLERS : "hosts"
    MARKETPLACES ||--o{ MARKETPLACE_LISTINGS : "hosts"
    SELLERS ||--o{ MARKETPLACE_LISTINGS : "operates"
    MARKETPLACE_LISTINGS ||--o{ CUSTOMER_REVIEWS : "contains"
    MARKETPLACE_LISTINGS ||--o| REVIEW_ANALYSES : "evaluated by"
    MARKETPLACE_LISTINGS ||--o| MARKETPLACE_EVIDENCE : "scored by"

    PRODUCTS {
        uuid id PK
        string product_id UK
        string brand
        string product_name
        string product_type
        string category
        string shade_or_variant
        datetime created_at
        datetime updated_at
    }

    MARKETPLACES {
        uuid id PK
        string platform_code UK
        string platform_name
        string base_url
        string api_type
        string currency_code
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    SELLERS {
        uuid id PK
        uuid marketplace_id FK
        string seller_name
        string seller_url
        boolean is_official_store
        float seller_rating
        string verified_status
        datetime created_at
        datetime updated_at
    }

    MARKETPLACE_LISTINGS {
        uuid id PK
        uuid product_id FK
        uuid marketplace_id FK
        uuid seller_id FK
        string raw_title
        float price
        string currency
        float rating
        int review_count
        string product_url UK
        string product_image_url
        string source_status
        string match_status
        float match_confidence
        text status_explanation
        datetime last_scraped_at
        datetime created_at
        datetime updated_at
    }

    CUSTOMER_REVIEWS {
        uuid id PK
        uuid listing_id FK
        string author
        float rating
        text comment_text
        string review_date
        boolean is_verified_purchase
        datetime created_at
    }

    REVIEW_ANALYSES {
        uuid id PK
        uuid listing_id FK_UK
        float review_authenticity_score
        string sentiment_label
        float sentiment_score
        float average_rating
        float verified_buyer_percentage
        string authenticity_status
        boolean suspicious_review_flag
        text summary
        datetime analyzed_at
    }

    MARKETPLACE_EVIDENCE {
        uuid id PK
        uuid listing_id FK_UK
        float total_score
        int rank
        float review_trust_score
        float rating_score
        float seller_trust_score
        float match_confidence_score
        text recommendation_reason
        datetime evaluated_at
    }
```

---

## 3. Detailed Entity & Table Specifications

### 3.1 `Product` (`products` table)
Stores authentic cosmetic catalog products against which uploaded query images and marketplace listings are verified.

- **`id`** (`UUID`, Primary Key, Default: `uuid4`)
- **`product_id`** (`String(50)`, Unique, Indexed, Required) — e.g. `"P001"`, `"P030"`.
- **`brand`** (`String(100)`, Required, Indexed) — e.g. `"Colourpop"`, `"Glossier"`.
- **`product_name`** (`String(255)`, Required) — e.g. `"Lippie Pencil"`.
- **`product_type`** (`String(100)`, Required) — e.g. `"Lippie Pencil"`, `"Stretch Concealer"`.
- **`category`** (`String(100)`, Required) — e.g. `"Lip_Products"`, `"Foundation_Base"`.
- **`shade_or_variant`** (`String(100)`, Optional) — e.g. `"BFF / Warm Nude"`.
- **`created_at`** (`DateTime(timezone=True)`, Server Default: `UTC NOW`)
- **`updated_at`** (`DateTime(timezone=True)`, Server Default: `UTC NOW`, OnUpdate: `UTC NOW`)
- **Unique Constraints**: `uq_products_product_id` (`product_id`), `uq_products_brand_name_variant` (`brand`, `product_name`, `shade_or_variant`)
- **Indexes**: `idx_products_product_id`, `idx_products_brand`

### 3.2 `Marketplace` (`marketplaces` table)
Registry of supported e-commerce marketplace platforms.

- **`id`** (`UUID`, Primary Key, Default: `uuid4`)
- **`platform_code`** (`String(50)`, Unique, Required) — e.g. `"amazon"`, `"daraz"`, `"temu"`.
- **`platform_name`** (`String(100)`, Required) — e.g. `"Amazon"`, `"Daraz"`, `"Temu"`.
- **`base_url`** (`String(255)`, Required) — e.g. `"https://www.amazon.com"`.
- **`api_type`** (`String(50)`, Required) — `"http_scraper"`, `"official_api"`, `"proxy_api"`.
- **`currency_code`** (`String(10)`, Required, Default: `"USD"`)
- **`is_active`** (`Boolean`, Required, Default: `True`)
- **`created_at`** (`DateTime(timezone=True)`, Server Default: `UTC NOW`)
- **`updated_at`** (`DateTime(timezone=True)`, Server Default: `UTC NOW`)
- **Unique Constraints**: `uq_marketplaces_platform_code` (`platform_code`)

### 3.3 `Seller` (`sellers` table)
Merchant/vendor identities selling products across marketplaces.

- **`id`** (`UUID`, Primary Key, Default: `uuid4`)
- **`marketplace_id`** (`UUID`, Foreign Key -> `marketplaces.id` ON DELETE CASCADE, Required, Indexed)
- **`seller_name`** (`String(150)`, Required) — e.g. `"Amazon Verified Seller"`, `"Daraz Mall Verified Store"`.
- **`seller_url`** (`String(500)`, Optional)
- **`is_official_store`** (`Boolean`, Required, Default: `False`)
- **`seller_rating`** (`Float`, Optional) — 0.0 to 5.0 rating score.
- **`verified_status`** (`String(50)`, Required, Default: `"unverified"`) — `"verified_official"`, `"verified_third_party"`, `"unverified"`.
- **`created_at`** (`DateTime(timezone=True)`, Server Default: `UTC NOW`)
- **`updated_at`** (`DateTime(timezone=True)`, Server Default: `UTC NOW`)
- **Unique Constraints**: `uq_sellers_marketplace_name` (`marketplace_id`, `seller_name`)
- **Indexes**: `idx_sellers_marketplace_id`

### 3.4 `MarketplaceListing` (`marketplace_listings` table)
Scraped or API-extracted marketplace listings linked to catalog products.

- **`id`** (`UUID`, Primary Key, Default: `uuid4`)
- **`product_id`** (`UUID`, Foreign Key -> `products.id` ON DELETE CASCADE, Required, Indexed)
- **`marketplace_id`** (`UUID`, Foreign Key -> `marketplaces.id` ON DELETE CASCADE, Required, Indexed)
- **`seller_id`** (`UUID`, Foreign Key -> `sellers.id` ON DELETE SET NULL, Optional, Indexed)
- **`raw_title`** (`String(500)`, Required)
- **`price`** (`Float`, Optional, Default: `0.0`)
- **`currency`** (`String(10)`, Optional, Default: `"USD"`)
- **`rating`** (`Float`, Optional, Default: `0.0`)
- **`review_count`** (`Integer`, Optional, Default: `0`)
- **`product_url`** (`String(1000)`, Optional, Indexed) — Source URL.
- **`product_image_url`** (`String(1000)`, Optional)
- **`source_status`** (`String(50)`, Required, Default: `"available"`) — `"available"`, `"blocked"`, `"unavailable"`.
- **`match_status`** (`String(50)`, Required, Default: `"Not a Match"`) — `"Exact Product Match"`, `"Possible Match"`, `"Not a Match"`.
- **`match_confidence`** (`Float`, Required, Default: `0.0`) — Percentage 0.0 to 100.0.
- **`status_explanation`** (`Text`, Optional)
- **`last_scraped_at`** (`DateTime(timezone=True)`, Server Default: `UTC NOW`, Required) — Retrieval timestamp.
- **`created_at`** (`DateTime(timezone=True)`, Server Default: `UTC NOW`)
- **`updated_at`** (`DateTime(timezone=True)`, Server Default: `UTC NOW`)
- **Unique Constraints**: `uq_listings_marketplace_url` (`marketplace_id`, `product_url`) (Prevents duplicate listing URLs per platform)
- **Indexes**: `idx_listings_product_marketplace`, `idx_listings_match_confidence`

### 3.5 `CustomerReview` (`customer_reviews` table)
Scraped or extracted customer review samples attached to a listing.

- **`id`** (`UUID`, Primary Key, Default: `uuid4`)
- **`listing_id`** (`UUID`, Foreign Key -> `marketplace_listings.id` ON DELETE CASCADE, Required, Indexed)
- **`author`** (`String(150)`, Optional, Default: `"Anonymous"`)
- **`rating`** (`Float`, Optional, Default: `0.0`)
- **`comment_text`** (`Text`, Optional)
- **`review_date`** (`String(50)`, Optional)
- **`is_verified_purchase`** (`Boolean`, Required, Default: `False`)
- **`created_at`** (`DateTime(timezone=True)`, Server Default: `UTC NOW`)
- **Indexes**: `idx_reviews_listing_id`

### 3.6 `ReviewAnalysis` (`review_analyses` table)
NLP and sentiment evaluation results for a listing's customer reviews.

- **`id`** (`UUID`, Primary Key, Default: `uuid4`)
- **`listing_id`** (`UUID`, Foreign Key -> `marketplace_listings.id` ON DELETE CASCADE, Unique, Required)
- **`review_authenticity_score`** (`Float`, Required) — Score 0.0 to 100.0.
- **`sentiment_label`** (`String(50)`, Required) — e.g. `"Highly Positive"`, `"Positive"`, `"Mixed"`, `"Negative"`.
- **`sentiment_score`** (`Float`, Optional) — Score -1.0 to 1.0.
- **`average_rating`** (`Float`, Required, Default: `0.0`)
- **`verified_buyer_percentage`** (`Float`, Required, Default: `0.0`)
- **`authenticity_status`** (`String(100)`, Required) — e.g. `"Authentic Reviews Verified"`.
- **`suspicious_review_flag`** (`Boolean`, Required, Default: `False`)
- **`summary`** (`Text`, Optional)
- **`analyzed_at`** (`DateTime(timezone=True)`, Server Default: `UTC NOW`)
- **Unique Constraints**: `uq_review_analyses_listing_id` (`listing_id`)

### 3.7 `MarketplaceEvidence` (`marketplace_evidence` table)
Transparent multi-factor evidence score breakdown for platform comparisons.

- **`id`** (`UUID`, Primary Key, Default: `uuid4`)
- **`listing_id`** (`UUID`, Foreign Key -> `marketplace_listings.id` ON DELETE CASCADE, Unique, Required)
- **`total_score`** (`Float`, Required) — Score 0.0 to 100.0.
- **`rank`** (`Integer`, Required, Default: `1`)
- **`review_trust_score`** (`Float`, Required) — 40% weight component.
- **`rating_score`** (`Float`, Required) — 25% weight component.
- **`seller_trust_score`** (`Float`, Required) — 20% weight component.
- **`match_confidence_score`** (`Float`, Required) — 15% weight component.
- **`recommendation_reason`** (`Text`, Required)
- **`evaluated_at`** (`DateTime(timezone=True)`, Server Default: `UTC NOW`)
- **Unique Constraints**: `uq_marketplace_evidence_listing_id` (`listing_id`)

---

## 4. Missing-Value Handling Strategy

| Data Field | Nullable? | Default Value / Missing-Value Behavior |
| :--- | :---: | :--- |
| `price` | Yes | Defaults to `0.0`; `currency` defaults to `"USD"`. |
| `rating` | Yes | Defaults to `0.0` (indicates no rating or unrated item). |
| `review_count` | Yes | Defaults to `0`. |
| `seller_id` | Yes | `NULL` if listing seller is unparsed or unavailable. |
| `product_url` | Yes | `NULL` if source URL unavailable; status set to `"unavailable"`. |
| `status_explanation` | Yes | `NULL` when status is `"available"`. Populated with diagnostic reason when `"blocked"` or `"unavailable"`. |

---

## 5. Database Connection & Migration Configuration

- **ORM**: SQLAlchemy 2.x
- **Migration Tool**: Alembic 1.13+
- **Environment Configuration**: `DATABASE_URL` set in `.env`.
- **Dual Dialect Support**: Supports PostgreSQL (`postgresql+psycopg2://...`) as production standard and SQLite (`sqlite:///...`) for local unit testing and development.
