# Known Limitations and Backlog — Marketplace Data Integrity

## Overview
This document records known data-integrity limitations, edge cases, and backlog items in the marketplace scraping, product-matching, and scoring pipelines. These items have been identified during PostgreSQL persistence auditing and frontend/backend integration testing, and are preserved as backlog items for a dedicated future data-integrity enhancement phase.

---

## 1. Unrelated Marketplace Listing Titles
- **Symptom**: Products with ambiguous or broad categories (e.g. `P001` - `Lip_Products`) may occasionally receive search queries that return unrelated marketplace items (e.g. `Fresh Kiss Glossy Lip Balm` instead of `Maybelline Fit Me Matte + Poreless Foundation`).
- **Root Cause**: Query generation relies partly on catalog category taxonomy, and scrapers may fall back to broad keyword searches when exact matches are missing.
- **Backlog Item**: Implement strict product-line keyword boundary filters in scraper query generators before executing external HTTP calls.

---

## 2. Placeholder Listing Records & Status Strings
- **Symptom**: Platform status messages such as `"No Daraz listings returned"`, `"Temu Protection Active"`, and `"No matching listings found"` were historically passed in the `platform_comparison` payload.
- **Root Cause**: Scraper modules return non-listing status strings inside standard listing response schemas to inform the UI of scraper access restrictions or anti-bot protections.
- **Backlog Item**: Separate platform operational status badges from actual product listing cards in both backend response payloads and database persistence routines.

---

## 3. Unidentified Product Marketplace Searches
- **Symptom**: When an image has low OCR text detection (`"No Text Detected"`) and low CLIP confidence (`"Unidentified Product"`), executing broad marketplace searches produces irrelevant results (e.g. Bluetooth headsets, charging cables, or generic electronics).
- **Root Cause**: Absence of an identity gatekeeper allowed fallback queries like `"Unidentified Product"` or `"cosmetic"` to hit external marketplace search APIs.
- **Backlog Item**: Enforce an explicit identity confidence gatekeeper that aborts external marketplace scraping when detected brand and product identity fall below minimum confidence thresholds.

---

## 4. Product-Listing Matching Validation
- **Symptom**: Listings from marketplace search results may be accepted based solely on brand substring presence without verifying product line, shade, or volume.
- **Root Cause**: Basic string matching algorithms lack semantic awareness of cosmetic line names (e.g. distinguishing `Matte + Poreless Foundation` from `SuperStay Concealer`).
- **Backlog Item**: Implement multi-field semantic similarity scoring comparing detected brand, product name, volume/shade, and category boundary keywords.

---

## 5. Duplicate Listing Persistence Audit
- **Symptom**: Repeated analysis runs for the same image or product may generate multiple listing records if source URLs vary slightly due to tracking parameters (e.g. `?ref=search`).
- **Root Cause**: Canonical URL normalization was not enforced prior to database primary key/unique constraint checks.
- **Backlog Item**: Introduce canonical URL stripping and hash-based deduplication in `persistence_service.py`.

---

## 6. Trust Score Reliability Limitations
- **Symptom**: Missing marketplace seller names or review counts could inadvertently default to neutral baseline scores (e.g. `50.0/100`), potentially inflating trust ratings when zero empirical evidence exists.
- **Root Cause**: Default value initializers in legacy scoring functions treated missing data as neutral rather than unverified.
- **Backlog Item**: Restructure platform comparison scoring to require positive verified evidence for all weighted dimensions, defaulting missing fields to `0.0` with explicit "Insufficient Evidence" UI badges.

---

## Summary Status
All 6 items above are formally logged into the project backlog and documented. The frontend verification dashboard handles these known limitations gracefully by displaying explicit status badges, disclaimers, and separation of raw identification from authenticity prediction.
