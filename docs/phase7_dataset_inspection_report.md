# Phase 7 — Dataset Inspection Report: Amazon Beauty Reviews

## 1. Executive Summary

This report documents the thorough inspection and structure analysis of the **Amazon Beauty Reviews Dataset** (`amazon_beauty_reviews_dataset.csv`). The dataset was inspected iteratively in chunks without loading unneeded objects into memory. A prepared copy containing a rating-derived sentiment target variable was generated in `data/review_dataset/processed/beauty_reviews_prepared.csv`, leaving the original raw CSV untouched.

> [!NOTE]
> **Dataset File**: `data/review_dataset/raw/amazon_beauty_reviews_dataset.csv`  
> **Prepared Dataset File**: `data/review_dataset/processed/beauty_reviews_prepared.csv`  
> **Inspection Timestamp**: 2026-09-25 14:38:07  
> **Total Records Processed**: 701,528

---

## 2. Dataset Overview & Schema Inspection

| Metric | Value |
| :--- | :--- |
| **Total Row Count** | **701,528** |
| **Total Column Count** | **10** |
| **Raw CSV File Size** | `211.56 MB` |
| **Processed CSV File Size** | `217.53 MB` |
| **Timestamp Range** | `00:00.0` to `59:59.9` |
| **Unique ASINs (Products)** | **115,709** |
| **Unique Parent ASINs** | **112,565** |
| **Unique User IDs (Reviewers)** | **631,986** |

### Column Names and Data Types

| # | Column Name | Raw Data Type | Missing Count | Missing Percentage | Description / Sample Value |
| :---: | :--- | :--- | :---: | :---: | :--- |
| 1 | `rating` | `int64` | 0 | 0.00% | Star rating (1 to 5 integer) |
| 2 | `title` | `object` | 160 | 0.02% | Short review title text |
| 3 | `text` | `object` | 212 | 0.03% | Detailed review comment body |
| 4 | `images` | `object` | 0 | 0.00% | Image attachments string representation |
| 5 | `asin` | `object` | 0 | 0.00% | Unique product identifier (ASIN) |
| 6 | `parent_asin` | `object` | 0 | 0.00% | Parent product family ASIN |
| 7 | `user_id` | `object` | 0 | 0.00% | Customer reviewer account ID |
| 8 | `timestamp` | `object` | 0 | 0.00% | Review creation timestamp string |
| 9 | `helpful_vote` | `int64` | 0 | 0.00% | Count of helpful votes received |
| 10 | `verified_purchase` | `bool` | 0 | 0.00% | Boolean flag for verified buyer status |

---

## 3. Data Integrity & Missing Value Analysis

> [!IMPORTANT]
> - **Empty Title Count**: **160** reviews (0.02% of dataset) have missing or whitespace-only titles.
> - **Empty Review Text Count**: **825** reviews (0.12% of dataset) have missing or whitespace-only text content.
> - **Exact Full-Row Duplicates**: **7,275** rows (1.04% of dataset) are exact byte-for-byte duplicate entries.
> - **User + ASIN + Text Duplicates**: **7,276** reviews (1.04% of dataset) share identical `user_id`, `asin`, and `text`.

---

## 4. Distribution Analysis

### 4.1 Rating Distribution (1 to 5 Stars)

| Rating Star | Count | Percentage | Sentiment Category |
| :---: | :---: | :---: | :--- |
| **1 Star** | 102,080 | 14.55% | `negative` |
| **2 Stars** | 43,034 | 6.13% | `negative` |
| **3 Stars** | 56,307 | 8.03% | `neutral` |
| **4 Stars** | 79,381 | 11.32% | `positive` |
| **5 Stars** | 420,726 | 59.97% | `positive` |

#### Consolidated Rating-Derived Sentiment Summary
- **Positive Sentiment (4–5 Stars)**: **500,107** (71.29%)
- **Neutral Sentiment (3 Stars)**: **56,307** (8.03%)
- **Negative Sentiment (1–2 Stars)**: **145,114** (20.69%)

### 4.2 Verified Purchase Distribution

| Verified Buyer Status | Count | Percentage |
| :---: | :---: | :---: |
| **Verified Purchase (`True`)** | **634,969** | **90.51%** |
| **Unverified Purchase (`False`)** | **66,559** | **9.49%** |

---

## 5. Review Text Statistics

Linguistic property metrics computed across all non-empty review bodies:

| Metric | Character Length (`text`) | Word Count (`text`) |
| :--- | :---: | :---: |
| **Minimum** | 1 | 0 |
| **Maximum** | 14,989 | 2,585 |
| **Mean (Average)** | 173.08 | 32.76 |
| **Median** | 102.00 | 19.00 |
| **Standard Deviation** | 246.94 | 45.98 |

---

## 6. Fake / Real Review Label Audit

> [!WARNING]
> **Explicit Ground-Truth Label Audit Result**: **NO EXPLICIT GROUND-TRUTH FAKE/REAL LABEL FOUND**.
> 
> - The dataset does **not** contain explicit binary classification columns such as `is_fake`, `label`, `deceptive`, or `cg_or`.
> - **Rule Compliance**: As mandated, no fake/real label was invented or assumed.
> - **Metadata Proxy Indicators Available**:
>   1. `verified_purchase` (`True`/`False`): Unverified purchases combined with extreme ratings (1 or 5 stars) serve as a standard domain proxy for potential incentivized/deceptive reviews.
>   2. `helpful_vote` count: High vs zero helpfulness votes.
>   3. Duplicate review text detection across different user accounts.

---

## 7. Prepared Copy & Rating-Derived Sentiment Field

A processed copy was saved to:
`data/review_dataset/processed/beauty_reviews_prepared.csv`

### Processing Operations Applied:
1. Added column `sentiment`:
   - **`negative`**: for rating values 1 and 2
   - **`neutral`**: for rating value 3
   - **`positive`**: for rating values 4 and 5
2. All original 10 columns preserved.
3. Original raw dataset in `data/review_dataset/raw/amazon_beauty_reviews_dataset.csv` left untouched.

---

## 8. Compliance & Next Steps Summary

- [x] **Raw CSV preserved**: `data/review_dataset/raw/amazon_beauty_reviews_dataset.csv`
- [x] **No model training executed**: Model training postponed to future pipeline steps.
- [x] **No PostgreSQL database inserts executed**: Database tables remain untouched.
- [x] **No database records deleted**: All database records preserved.

