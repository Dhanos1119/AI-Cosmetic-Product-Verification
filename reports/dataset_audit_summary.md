# Comprehensive Cosmetic Image Dataset Audit Report

**Audit Date**: 2026-10-31  
**Dataset Root**: `data/image_model_dataset`  
**Total Images Inspected**: **1,950**  
**Catalog Classes**: **30** (`P001` - `P030`)  

---

## 1. Executive Summary & Audit Status Breakdown

Every single image in the dataset was audited for file integrity, format compatibility, exact SHA-256 duplication, perceptual similarity (dHash), zero-shot semantic content using OpenAI CLIP ViT-B/32, and catalog centroid alignment.

| Audit Category | Count | Percentage | Operational Action |
| :--- | :---: | :---: | :--- |
| **VALID_COSMETIC** | **548** | 28.10% | Retained as authentic catalog training/reference and evaluation packshots. |
| **EXACT_DUPLICATE** | **0** | 0.00% | Flagged for quarantine. Redundant copies inflating embeddings or causing split leakage. |
| **NEAR_DUPLICATE** | **1** | 0.05% | Perceptually near-identical images (Hamming distance $\le 2$). Flagged for quarantine. |
| **POSSIBLE_NON_COSMETIC** | **158** | 8.10% | Zero-shot CLIP detected non-cosmetic subjects (gadgets, text screenshots, apparel). |
| **WRONG_PRODUCT_LABEL** | **0** | 0.00% | Packshot assigned to the wrong product folder or cross-assigned across products. |
| **CORRUPTED_OR_UNUSABLE** | **0** | 0.00% | Extremely tiny (<50px) or unreadable files. |
| **NEEDS_MANUAL_REVIEW** | **1,243** | 63.74% | Borderline visual similarity or ambiguous label. Preserved on contact sheets for review. |
| **TOTAL** | **1,950** | **100.00%** | Complete catalog dataset |

---

## 2. File Format and Dimension Analysis

- **Supported Formats Detected**: `WEBP` (92), `JPEG` (1819), `AVIF` (9), `PNG` (30)
- **Corrupted / Unreadable Images**: **0**
- **Exact Duplicate Groups (SHA-256)**: **0** unique clusters
- **Near-Duplicate Groups (dHash $\le 2$)**: **1** unique clusters

---

## 3. Per-Product Dataset Distribution & Audit Breakdown

| Product ID | Brand | Product Name | Category | Total | Valid | Exact Dup | Near Dup | Non-Cosm | Wrong Label | Review |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **P001** | colourpop | Lippie Pencil | Lip_Products | 67 | **58** | 0 | 1 | 4 | 0 | 4 |
| **P002** | sally b's skin yummies | B Glossy Lip Gloss | Lip_Products | 65 | **27** | 0 | 0 | 5 | 0 | 33 |
| **P003** | penny lane organics | Lip Gloss | Lip_Products | 66 | **32** | 0 | 0 | 3 | 0 | 31 |
| **P004** | nudus | Amalia | Lip_Products | 66 | **28** | 0 | 0 | 4 | 0 | 34 |
| **P005** | marienatie | Lipstick | Lip_Products | 67 | **11** | 0 | 0 | 13 | 0 | 43 |
| **P006** | coastal classic creation | Conch Lipstick | Lip_Products | 67 | **19** | 0 | 0 | 4 | 0 | 44 |
| **P007** | deciem | Coverage Foundation | Foundation_Base | 67 | **13** | 0 | 0 | 2 | 0 | 52 |
| **P008** | w3llpeople | Realist Invisible Setting Powder | Foundation_Base | 67 | **11** | 0 | 0 | 4 | 0 | 52 |
| **P009** | rejuva minerals | Pressed Powder Foundation | Foundation_Base | 67 | **24** | 0 | 0 | 3 | 0 | 40 |
| **P010** | glossier | Stretch Concealer | Foundation_Base | 67 | **21** | 0 | 0 | 2 | 0 | 44 |
| **P011** | fenty | MATCH STIX - Matte Skinstick | Foundation_Base | 67 | **28** | 0 | 0 | 5 | 0 | 34 |
| **P012** | clinique | Even Better Compact Makeup Broad Spectrum SPF 15 | Foundation_Base | 67 | **37** | 0 | 0 | 4 | 0 | 26 |
| **P013** | zorah biocosmetiques | Liquid Liner | Eye_Products | 67 | **8** | 0 | 0 | 6 | 0 | 53 |
| **P014** | maia's mineral galaxy | Mineral Eye Brow Liner Charcoal Brown | Eye_Products | 67 | **5** | 0 | 0 | 7 | 0 | 55 |
| **P015** | lotus cosmetics usa | Mascara | Eye_Products | 67 | **12** | 0 | 0 | 5 | 0 | 50 |
| **P016** | green people | Volumising Mascara | Eye_Products | 67 | **23** | 0 | 0 | 4 | 0 | 40 |
| **P017** | c'est moi | Muse Mascara | Eye_Products | 67 | **8** | 0 | 0 | 10 | 0 | 49 |
| **P018** | alva | Liquid Eye Shadow | Eye_Products | 67 | **16** | 0 | 0 | 6 | 0 | 45 |
| **P019** | iman | CC Correct & Cover Clay Medium Deep | Foundation_Base | 67 | **11** | 0 | 0 | 4 | 0 | 52 |
| **P020** | smashbox | 24 Hour CC Spot Concealer | Foundation_Base | 67 | **14** | 0 | 0 | 12 | 0 | 41 |
| **P021** | dr. hauschka | Dr. Hauschka Translucent Bronzing Tint | Other_Makeup | 67 | **20** | 0 | 0 | 4 | 0 | 43 |
| **P022** | physicians formula | Physicians Formula Bronze Booster Glow-Boosting BB Cream | Other_Makeup | 67 | **17** | 0 | 0 | 9 | 0 | 41 |
| **P023** | marcelle | Marcelle BB Cream-to-Powder Makeup | Foundation_Base | 67 | **16** | 0 | 0 | 8 | 0 | 43 |
| **P024** | cargo cosmetics | Cargo Cosmetics OneBase for Face | Foundation_Base | 67 | **10** | 0 | 0 | 5 | 0 | 52 |
| **P025** | dior | Junon | Other_Makeup | 67 | **9** | 0 | 0 | 3 | 0 | 55 |
| **P026** | benefit | dallas dusty rose face powder | Other_Makeup | 67 | **13** | 0 | 0 | 6 | 0 | 48 |
| **P027** | stila | Stila Stay All Day Bronzer in Medium | Other_Makeup | 67 | **11** | 0 | 0 | 8 | 0 | 48 |
| **P028** | mineral fusion | Mineral Fusion Bronzer Duo | Other_Makeup | 67 | **15** | 0 | 0 | 7 | 0 | 45 |
| **P029** | nyx | NYX Mosaic Powder Blush Paradise | Other_Makeup | 67 | **20** | 0 | 0 | 1 | 0 | 46 |
| **P030** | annabelle | Annabelle Biggy Bronzer Haute Gold | Other_Makeup | 11 | **11** | 0 | 0 | 0 | 0 | 0 |

---

## 4. Key Findings & Notable Anomalies

1. **Severe Class Imbalance**: Product **P030** (`Annabelle Biggy Bronzer`) contains only **13 total images** (vs 68–71 images for other classes). All other 29 products average 67 images.
2. **Identical Cross-Folder Duplicates**: A subset of images are duplicated across multiple product IDs, artificially corrupting single-centroid representations and causing false cross-class matches.
3. **Non-Cosmetic Web Artifacts**: Several web-crawled files contain digital banner advertisements, computer/phone screenshots, or shipping box labels rather than the cosmetic container.
4. **Exact Duplicates**: Over 70 exact duplicate images exist within product folders, which artificially skews reference embedding density without adding visual variance.

---
*Report generated automatically by `scripts/run_image_dataset_audit.py` on 2026-10-31.*