# Genuine OpenAI CLIP ViT-B/32 Product Visual Identification Accuracy Report

**Evaluation Date**: 2026-09-23 11:18:24  
**Model Engine**: OpenAI CLIP ViT-B/32 (`openai/clip-vit-base-patch32`)  
**Dataset Location**: `data/image_model_dataset/`  
**Evaluation Scope**: Authentic cosmetic product visual matching across catalog products `P001` through `P030`.  

> [!IMPORTANT]
> **Model Upgrade**: Replaced handcrafted HSV color + Sobel gradient histograms with genuine pretrained OpenAI CLIP ViT-B/32 Vision Transformer embeddings (512-dim).

## Baseline vs. OpenAI CLIP ViT-B/32 Comparison

| Metric | Previous Handcrafted Baseline | Genuine OpenAI CLIP ViT-B/32 | Improvement |
| :--- | :---: | :---: | :---: |
| **Top-1 Accuracy** | 9.84% (60/610) | **30.82%** (188/610) | **+20.98%** |
| **Top-5 Accuracy** | 29.34% (179/610) | **57.54%** (351/610) | **+28.2%** |
| **Misclassified Test Items** | 550 / 610 | **422** / 610 | **-128 errors** |

---

## Summary Metrics

| Metric | Value |
| :--- | :--- |
| **Target Product Classes** | 30 products (`P001` - `P030`) |
| **Total Scanned Dataset Images** | 1950 images |
| **Reference Index Set (70%)** | 1340 images |
| **Reserved Test Query Set (30%)** | **610** images |
| **Top-1 Correct Predictions** | **188** / 610 |
| **Top-1 Incorrect Predictions** | **422** / 610 |
| **Top-1 Accuracy** | **30.82%** |
| **Top-5 Correct Predictions** | **351** / 610 |
| **Top-5 Accuracy** | **57.54%** |
| **Low-Confidence / Misclassified Items** | **445** images |
| **Evaluation Runtime** | 120.49 seconds |

---

## Per-Product Accuracy Breakdown

| Product ID | Brand | Product Name | Category | Test Images | Top-1 Correct | Top-1 Accuracy | Top-5 Accuracy | Low-Conf Count |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **P001** | colourpop | Lippie Pencil | Lip_Products | 21 | 21 | **100.0%** | **100.0%** | 1 |
| **P002** | sally b's skin yummies | B Glossy Lip Gloss | Lip_Products | 20 | 8 | **40.0%** | **75.0%** | 3 |
| **P003** | penny lane organics | Lip Gloss | Lip_Products | 20 | 6 | **30.0%** | **70.0%** | 2 |
| **P004** | nudus | Amalia | Lip_Products | 20 | 7 | **35.0%** | **65.0%** | 5 |
| **P005** | marienatie | Lipstick | Lip_Products | 21 | 2 | **9.5%** | **61.9%** | 5 |
| **P006** | coastal classic creation | Conch Lipstick | Lip_Products | 21 | 4 | **19.0%** | **57.1%** | 1 |
| **P007** | deciem | Coverage Foundation | Foundation_Base | 21 | 12 | **57.1%** | **76.2%** | 3 |
| **P008** | w3llpeople | Realist Invisible Setting Powder | Foundation_Base | 21 | 7 | **33.3%** | **66.7%** | 5 |
| **P009** | rejuva minerals | Pressed Powder Foundation | Foundation_Base | 21 | 2 | **9.5%** | **38.1%** | 4 |
| **P010** | glossier | Stretch Concealer | Foundation_Base | 21 | 2 | **9.5%** | **42.9%** | 4 |
| **P011** | fenty | MATCH STIX - Matte Skinstick | Foundation_Base | 21 | 6 | **28.6%** | **38.1%** | 3 |
| **P012** | clinique | Even Better Compact Makeup Broad Spectrum SPF 15 | Foundation_Base | 21 | 5 | **23.8%** | **47.6%** | 5 |
| **P013** | zorah biocosmetiques | Liquid Liner | Eye_Products | 21 | 2 | **9.5%** | **42.9%** | 2 |
| **P014** | maia's mineral galaxy | Mineral Eye Brow Liner Charcoal Brown | Eye_Products | 21 | 16 | **76.2%** | **90.5%** | 1 |
| **P015** | lotus cosmetics usa | Mascara | Eye_Products | 21 | 5 | **23.8%** | **52.4%** | 4 |
| **P016** | green people | Volumising Mascara | Eye_Products | 21 | 2 | **9.5%** | **57.1%** | 4 |
| **P017** | c'est moi | Muse Mascara | Eye_Products | 21 | 12 | **57.1%** | **61.9%** | 5 |
| **P018** | alva | Liquid Eye Shadow | Eye_Products | 21 | 7 | **33.3%** | **33.3%** | 4 |
| **P019** | iman | CC Correct & Cover Clay Medium Deep | Foundation_Base | 21 | 4 | **19.0%** | **52.4%** | 6 |
| **P020** | smashbox | 24 Hour CC Spot Concealer | Foundation_Base | 21 | 6 | **28.6%** | **38.1%** | 1 |
| **P021** | dr. hauschka | Dr. Hauschka Translucent Bronzing Tint | Other_Makeup | 21 | 4 | **19.0%** | **38.1%** | 2 |
| **P022** | physicians formula | Physicians Formula Bronze Booster Glow-Boosting BB Cream | Other_Makeup | 21 | 5 | **23.8%** | **52.4%** | 0 |
| **P023** | marcelle | Marcelle BB Cream-to-Powder Makeup | Foundation_Base | 21 | 7 | **33.3%** | **61.9%** | 2 |
| **P024** | cargo cosmetics | Cargo Cosmetics OneBase for Face | Foundation_Base | 21 | 2 | **9.5%** | **52.4%** | 4 |
| **P025** | dior | Junon | Other_Makeup | 21 | 9 | **42.9%** | **71.4%** | 0 |
| **P026** | benefit | dallas dusty rose face powder | Other_Makeup | 21 | 3 | **14.3%** | **33.3%** | 9 |
| **P027** | stila | Stila Stay All Day Bronzer in Medium | Other_Makeup | 21 | 7 | **33.3%** | **57.1%** | 2 |
| **P028** | mineral fusion | Mineral Fusion Bronzer Duo | Other_Makeup | 21 | 7 | **33.3%** | **47.6%** | 7 |
| **P029** | nyx | NYX Mosaic Powder Blush Paradise | Other_Makeup | 21 | 4 | **19.0%** | **81.0%** | 2 |
| **P030** | annabelle | Annabelle Biggy Bronzer Haute Gold | Other_Makeup | 4 | 4 | **100.0%** | **100.0%** | 0 |

---

## Top Product Misclassification Pairs (Confusion Matrix Summary)

| Actual Product | Predicted (Confused) Product | Misclassified Count |
| :--- | :--- | :---: |
| **P010** (glossier - Stretch Concealer) | **P011** (fenty - MATCH STIX - Matte Skinstick) | 5 |
| **P020** (smashbox - 24 Hour CC Spot Concealer) | **P001** (colourpop - Lippie Pencil) | 5 |
| **P006** (coastal classic creation - Conch Lipstick) | **P027** (stila - Stila Stay All Day Bronzer in Medium) | 4 |
| **P012** (clinique - Even Better Compact Makeup Broad Spectrum SPF 15) | **P001** (colourpop - Lippie Pencil) | 4 |
| **P016** (green people - Volumising Mascara) | **P011** (fenty - MATCH STIX - Matte Skinstick) | 4 |
| **P017** (c'est moi - Muse Mascara) | **P001** (colourpop - Lippie Pencil) | 4 |
| **P021** (dr. hauschka - Dr. Hauschka Translucent Bronzing Tint) | **P027** (stila - Stila Stay All Day Bronzer in Medium) | 4 |
| **P025** (dior - Junon) | **P018** (alva - Liquid Eye Shadow) | 4 |
| **P026** (benefit - dallas dusty rose face powder) | **P014** (maia's mineral galaxy - Mineral Eye Brow Liner Charcoal Brown) | 4 |
| **P026** (benefit - dallas dusty rose face powder) | **P027** (stila - Stila Stay All Day Bronzer in Medium) | 4 |

---

## Sample Test Predictions Log

| Image File | Actual Product | Predicted Top-1 Product | Sim Score | Result |
| :--- | :--- | :--- | :---: | :---: |
| `P001_0036.jpg` | **P001** (colourpop) | **P001** (colourpop) | 86.2% | ✅ CORRECT |
| `P001_0030.jpg` | **P001** (colourpop) | **P001** (colourpop) | 78.1% | ✅ CORRECT |
| `P001_0016.jpg` | **P001** (colourpop) | **P001** (colourpop) | 84.4% | ✅ CORRECT |
| `P001_0051.jpg` | **P001** (colourpop) | **P001** (colourpop) | 88.8% | ✅ CORRECT |
| `P001_0031.jpg` | **P001** (colourpop) | **P001** (colourpop) | 52.9% | ✅ CORRECT |
| `P001_0027.jpg` | **P001** (colourpop) | **P001** (colourpop) | 66.9% | ✅ CORRECT |
| `P001_0018.jpg` | **P001** (colourpop) | **P001** (colourpop) | 78.7% | ✅ CORRECT |
| `P001_0057.jpg` | **P001** (colourpop) | **P001** (colourpop) | 78.9% | ✅ CORRECT |
| `P001_0033.jpg` | **P001** (colourpop) | **P001** (colourpop) | 83.9% | ✅ CORRECT |
| `P001_0019.jpg` | **P001** (colourpop) | **P001** (colourpop) | 84.2% | ✅ CORRECT |
| `P001_0046.jpg` | **P001** (colourpop) | **P001** (colourpop) | 86.7% | ✅ CORRECT |
| `P001_0032.jpg` | **P001** (colourpop) | **P001** (colourpop) | 75.5% | ✅ CORRECT |
| `P001_0010.jpg` | **P001** (colourpop) | **P001** (colourpop) | 89.7% | ✅ CORRECT |
| `P001_0054.jpg` | **P001** (colourpop) | **P001** (colourpop) | 86.7% | ✅ CORRECT |
| `P001_0042.jpg` | **P001** (colourpop) | **P001** (colourpop) | 81.2% | ✅ CORRECT |

---

## Methodology & Data Leakage Safeguards
1. **Genuine Model**: `openai/clip-vit-base-patch32` loaded via PyTorch & Hugging Face `transformers`.
2. **Stratified 70/30 Split**: Deterministic seed (`seed=42`) applied per product folder.
3. **Zero Data Leakage**: Test images were strictly excluded from reference index centroid creation.
4. **Matching Engine**: Cosine similarity dot product against precomputed 512-dim deep vision centroids.