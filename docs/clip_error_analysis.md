# Detailed CLIP Evaluation & Error Analysis Report

**Evaluation Timestamp**: `2026-09-23 11:51:40`  
**Model Engine**: OpenAI CLIP ViT-B/32 (`openai/clip-vit-base-patch32`)  
**Evaluation Protocol**: Stratified 70% Reference / 30% Reserved Test Split (`random_seed=42`)  
**Execution Runtime**: 122.24 seconds  

---

## 1. Executive Summary & Overall Accuracy

| Metric | Value | Details |
| :--- | :---: | :--- |
| **Target Product Classes** | **30** | Folders `P001` through `P030` |
| **Total Catalog Images** | **1950** | Full dataset scan |
| **Reference Images (70%)** | **1340** | Centroid embedding construction |
| **Reserved Test Images (30%)** | **610** | Reserved test evaluation |
| **Top-1 Correct Predictions** | **188** | **30.82% Top-1 Accuracy** |
| **Top-1 Incorrect Predictions** | **422** | Misclassified test items |
| **Top-5 Correct Predictions** | **351** | **57.54% Top-5 Accuracy** |

---

## 2. Similarity Score Distributions

### Statistical Breakdown (Cosine Similarity Scores)

| Metric | Correct Predictions (Top-1 Match) | Incorrect Predictions (Misclassified) |
| :--- | :---: | :---: |
| **Count** | 188 | 422 |
| **Mean Score** | `0.7219` (72.2%) | `0.6832` (68.3%) |
| **Median Score** | `0.7259` (72.6%) | `0.6989` (69.9%) |
| **Std. Deviation** | `0.0997` | `0.0904` |
| **Min Score** | `0.436` (43.6%) | `0.3357` (33.6%) |
| **Max Score** | `0.9476` (94.8%) | `0.8541` (85.4%) |
| **25th Percentile** | `0.6632` | `0.6303` |
| **75th Percentile** | `0.7918` | `0.7442` |
| **90th Percentile** | `0.8482` | `0.7842` |

### Histogram Distribution Bins

| Similarity Range | Correct Predictions Count | Incorrect Predictions Count |
| :--- | :---: | :---: |
| **< 0.50** | 5 | 16 |
| **0.50 - 0.59** | 18 | 57 |
| **0.60 - 0.69** | 47 | 141 |
| **0.70 - 0.79** | 75 | 174 |
| **0.80 - 0.89** | 38 | 34 |
| **0.90 - 1.00** | 5 | 0 |

---

## 3. Per-Product Accuracy Breakdown

| Product ID | Brand | Product Name | Category | Test Items | Top-1 Correct | Top-1 Accuracy | Top-5 Accuracy |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **P001** | colourpop | Lippie Pencil | Lip_Products | 21 | 21 | **100.0%** | **100.0%** |
| **P002** | sally b's skin yummies | B Glossy Lip Gloss | Lip_Products | 20 | 8 | **40.0%** | **75.0%** |
| **P003** | penny lane organics | Lip Gloss | Lip_Products | 20 | 6 | **30.0%** | **70.0%** |
| **P004** | nudus | Amalia | Lip_Products | 20 | 7 | **35.0%** | **65.0%** |
| **P005** | marienatie | Lipstick | Lip_Products | 21 | 2 | **9.52%** | **61.9%** |
| **P006** | coastal classic creation | Conch Lipstick | Lip_Products | 21 | 4 | **19.05%** | **57.14%** |
| **P007** | deciem | Coverage Foundation | Foundation_Base | 21 | 12 | **57.14%** | **76.19%** |
| **P008** | w3llpeople | Realist Invisible Setting Powder | Foundation_Base | 21 | 7 | **33.33%** | **66.67%** |
| **P009** | rejuva minerals | Pressed Powder Foundation | Foundation_Base | 21 | 2 | **9.52%** | **38.1%** |
| **P010** | glossier | Stretch Concealer | Foundation_Base | 21 | 2 | **9.52%** | **42.86%** |
| **P011** | fenty | MATCH STIX - Matte Skinstick | Foundation_Base | 21 | 6 | **28.57%** | **38.1%** |
| **P012** | clinique | Even Better Compact Makeup Broad Spectrum SPF 15 | Foundation_Base | 21 | 5 | **23.81%** | **47.62%** |
| **P013** | zorah biocosmetiques | Liquid Liner | Eye_Products | 21 | 2 | **9.52%** | **42.86%** |
| **P014** | maia's mineral galaxy | Mineral Eye Brow Liner Charcoal Brown | Eye_Products | 21 | 16 | **76.19%** | **90.48%** |
| **P015** | lotus cosmetics usa | Mascara | Eye_Products | 21 | 5 | **23.81%** | **52.38%** |
| **P016** | green people | Volumising Mascara | Eye_Products | 21 | 2 | **9.52%** | **57.14%** |
| **P017** | c'est moi | Muse Mascara | Eye_Products | 21 | 12 | **57.14%** | **61.9%** |
| **P018** | alva | Liquid Eye Shadow | Eye_Products | 21 | 7 | **33.33%** | **33.33%** |
| **P019** | iman | CC Correct & Cover Clay Medium Deep | Foundation_Base | 21 | 4 | **19.05%** | **52.38%** |
| **P020** | smashbox | 24 Hour CC Spot Concealer | Foundation_Base | 21 | 6 | **28.57%** | **38.1%** |
| **P021** | dr. hauschka | Dr. Hauschka Translucent Bronzing Tint | Other_Makeup | 21 | 4 | **19.05%** | **38.1%** |
| **P022** | physicians formula | Physicians Formula Bronze Booster Glow-Boosting BB Cream | Other_Makeup | 21 | 5 | **23.81%** | **52.38%** |
| **P023** | marcelle | Marcelle BB Cream-to-Powder Makeup | Foundation_Base | 21 | 7 | **33.33%** | **61.9%** |
| **P024** | cargo cosmetics | Cargo Cosmetics OneBase for Face | Foundation_Base | 21 | 2 | **9.52%** | **52.38%** |
| **P025** | dior | Junon | Other_Makeup | 21 | 9 | **42.86%** | **71.43%** |
| **P026** | benefit | dallas dusty rose face powder | Other_Makeup | 21 | 3 | **14.29%** | **33.33%** |
| **P027** | stila | Stila Stay All Day Bronzer in Medium | Other_Makeup | 21 | 7 | **33.33%** | **57.14%** |
| **P028** | mineral fusion | Mineral Fusion Bronzer Duo | Other_Makeup | 21 | 7 | **33.33%** | **47.62%** |
| **P029** | nyx | NYX Mosaic Powder Blush Paradise | Other_Makeup | 21 | 4 | **19.05%** | **80.95%** |
| **P030** | annabelle | Annabelle Biggy Bronzer Haute Gold | Other_Makeup | 4 | 4 | **100.0%** | **100.0%** |

---

## 4. Most Frequently Confused Product Pairs

| Rank | Expected Product | Predicted (Confused) Product | Misclassified Count | Key Visual/Category Overlap |
| :---: | :--- | :--- | :---: | :--- |
| 1 | **P010** (glossier - Stretch Concealer) | **P011** (fenty - MATCH STIX - Matte Skinstick) | **5** | High visual structure & color palette similarity |
| 2 | **P020** (smashbox - 24 Hour CC Spot Concealer) | **P001** (colourpop - Lippie Pencil) | **5** | High visual structure & color palette similarity |
| 3 | **P006** (coastal classic creation - Conch Lipstick) | **P027** (stila - Stila Stay All Day Bronzer in Medium) | **4** | High visual structure & color palette similarity |
| 4 | **P012** (clinique - Even Better Compact Makeup Broad Spectrum SPF 15) | **P001** (colourpop - Lippie Pencil) | **4** | High visual structure & color palette similarity |
| 5 | **P016** (green people - Volumising Mascara) | **P011** (fenty - MATCH STIX - Matte Skinstick) | **4** | High visual structure & color palette similarity |
| 6 | **P017** (c'est moi - Muse Mascara) | **P001** (colourpop - Lippie Pencil) | **4** | High visual structure & color palette similarity |
| 7 | **P021** (dr. hauschka - Dr. Hauschka Translucent Bronzing Tint) | **P027** (stila - Stila Stay All Day Bronzer in Medium) | **4** | High visual structure & color palette similarity |
| 8 | **P025** (dior - Junon) | **P018** (alva - Liquid Eye Shadow) | **4** | High visual structure & color palette similarity |
| 9 | **P026** (benefit - dallas dusty rose face powder) | **P014** (maia's mineral galaxy - Mineral Eye Brow Liner Charcoal Brown) | **4** | High visual structure & color palette similarity |
| 10 | **P026** (benefit - dallas dusty rose face powder) | **P027** (stila - Stila Stay All Day Bronzer in Medium) | **4** | High visual structure & color palette similarity |
| 11 | **P029** (nyx - NYX Mosaic Powder Blush Paradise) | **P011** (fenty - MATCH STIX - Matte Skinstick) | **4** | High visual structure & color palette similarity |
| 12 | **P004** (nudus - Amalia) | **P018** (alva - Liquid Eye Shadow) | **3** | High visual structure & color palette similarity |
| 13 | **P004** (nudus - Amalia) | **P028** (mineral fusion - Mineral Fusion Bronzer Duo) | **3** | High visual structure & color palette similarity |
| 14 | **P009** (rejuva minerals - Pressed Powder Foundation) | **P027** (stila - Stila Stay All Day Bronzer in Medium) | **3** | High visual structure & color palette similarity |
| 15 | **P010** (glossier - Stretch Concealer) | **P014** (maia's mineral galaxy - Mineral Eye Brow Liner Charcoal Brown) | **3** | High visual structure & color palette similarity |

---

## 5. Sample Misclassification Analysis & Top-5 Candidate Breakdown

### Sample 1: `P002_0049.jpg`
- **Expected Product**: **P002** (sally b's skin yummies - B Glossy Lip Gloss)
- **Predicted Product**: **P017** (c'est moi - Muse Mascara)
- **Top-1 Similarity Score**: `0.5054` (50.5%)

**Top-5 Retrieved Candidates**:
| Rank | Product ID | Brand | Product Name | Similarity Score | Similarity % |
| :---: | :---: | :--- | :--- | :---: | :---: |
| 1 | P017 | c'est moi | Muse Mascara | `0.5054` | 50.5% |
| 2 | **P002** | sally b's skin yummies | B Glossy Lip Gloss | `0.5014` | 50.1% |
| 3 | P024 | cargo cosmetics | Cargo Cosmetics OneBase for Face | `0.4902` | 49.0% |
| 4 | P020 | smashbox | 24 Hour CC Spot Concealer | `0.484` | 48.4% |
| 5 | P008 | w3llpeople | Realist Invisible Setting Powder | `0.4796` | 48.0% |

### Sample 2: `P002_0042.jpg`
- **Expected Product**: **P002** (sally b's skin yummies - B Glossy Lip Gloss)
- **Predicted Product**: **P018** (alva - Liquid Eye Shadow)
- **Top-1 Similarity Score**: `0.5892` (58.9%)

**Top-5 Retrieved Candidates**:
| Rank | Product ID | Brand | Product Name | Similarity Score | Similarity % |
| :---: | :---: | :--- | :--- | :---: | :---: |
| 1 | P018 | alva | Liquid Eye Shadow | `0.5892` | 58.9% |
| 2 | **P002** | sally b's skin yummies | B Glossy Lip Gloss | `0.5864` | 58.6% |
| 3 | P012 | clinique | Even Better Compact Makeup Broad Spectrum SPF 15 | `0.5761` | 57.6% |
| 4 | P028 | mineral fusion | Mineral Fusion Bronzer Duo | `0.5614` | 56.1% |
| 5 | P011 | fenty | MATCH STIX - Matte Skinstick | `0.5568` | 55.7% |

### Sample 3: `P002_0010.jpg`
- **Expected Product**: **P002** (sally b's skin yummies - B Glossy Lip Gloss)
- **Predicted Product**: **P021** (dr. hauschka - Dr. Hauschka Translucent Bronzing Tint)
- **Top-1 Similarity Score**: `0.7276` (72.8%)

**Top-5 Retrieved Candidates**:
| Rank | Product ID | Brand | Product Name | Similarity Score | Similarity % |
| :---: | :---: | :--- | :--- | :---: | :---: |
| 1 | P021 | dr. hauschka | Dr. Hauschka Translucent Bronzing Tint | `0.7276` | 72.8% |
| 2 | **P002** | sally b's skin yummies | B Glossy Lip Gloss | `0.7191` | 71.9% |
| 3 | P008 | w3llpeople | Realist Invisible Setting Powder | `0.7159` | 71.6% |
| 4 | P003 | penny lane organics | Lip Gloss | `0.7055` | 70.6% |
| 5 | P022 | physicians formula | Physicians Formula Bronze Booster Glow-Boosting BB Cream | `0.6927` | 69.3% |

### Sample 4: `P002_0047.jpg`
- **Expected Product**: **P002** (sally b's skin yummies - B Glossy Lip Gloss)
- **Predicted Product**: **P027** (stila - Stila Stay All Day Bronzer in Medium)
- **Top-1 Similarity Score**: `0.7105` (71.1%)

**Top-5 Retrieved Candidates**:
| Rank | Product ID | Brand | Product Name | Similarity Score | Similarity % |
| :---: | :---: | :--- | :--- | :---: | :---: |
| 1 | P027 | stila | Stila Stay All Day Bronzer in Medium | `0.7105` | 71.1% |
| 2 | P029 | nyx | NYX Mosaic Powder Blush Paradise | `0.685` | 68.5% |
| 3 | P012 | clinique | Even Better Compact Makeup Broad Spectrum SPF 15 | `0.6771` | 67.7% |
| 4 | P026 | benefit | dallas dusty rose face powder | `0.6591` | 65.9% |
| 5 | P004 | nudus | Amalia | `0.6584` | 65.8% |

### Sample 5: `P002_0001.jpg`
- **Expected Product**: **P002** (sally b's skin yummies - B Glossy Lip Gloss)
- **Predicted Product**: **P028** (mineral fusion - Mineral Fusion Bronzer Duo)
- **Top-1 Similarity Score**: `0.639` (63.9%)

**Top-5 Retrieved Candidates**:
| Rank | Product ID | Brand | Product Name | Similarity Score | Similarity % |
| :---: | :---: | :--- | :--- | :---: | :---: |
| 1 | P028 | mineral fusion | Mineral Fusion Bronzer Duo | `0.639` | 63.9% |
| 2 | P016 | green people | Volumising Mascara | `0.6246` | 62.5% |
| 3 | P015 | lotus cosmetics usa | Mascara | `0.6244` | 62.4% |
| 4 | P014 | maia's mineral galaxy | Mineral Eye Brow Liner Charcoal Brown | `0.6242` | 62.4% |
| 5 | P024 | cargo cosmetics | Cargo Cosmetics OneBase for Face | `0.622` | 62.2% |

### Sample 6: `P002_0034.jpg`
- **Expected Product**: **P002** (sally b's skin yummies - B Glossy Lip Gloss)
- **Predicted Product**: **P011** (fenty - MATCH STIX - Matte Skinstick)
- **Top-1 Similarity Score**: `0.6813` (68.1%)

**Top-5 Retrieved Candidates**:
| Rank | Product ID | Brand | Product Name | Similarity Score | Similarity % |
| :---: | :---: | :--- | :--- | :---: | :---: |
| 1 | P011 | fenty | MATCH STIX - Matte Skinstick | `0.6813` | 68.1% |
| 2 | P026 | benefit | dallas dusty rose face powder | `0.6256` | 62.6% |
| 3 | P006 | coastal classic creation | Conch Lipstick | `0.6249` | 62.5% |
| 4 | P029 | nyx | NYX Mosaic Powder Blush Paradise | `0.6225` | 62.3% |
| 5 | P019 | iman | CC Correct & Cover Clay Medium Deep | `0.6214` | 62.1% |

### Sample 7: `P002_0058.jpg`
- **Expected Product**: **P002** (sally b's skin yummies - B Glossy Lip Gloss)
- **Predicted Product**: **P008** (w3llpeople - Realist Invisible Setting Powder)
- **Top-1 Similarity Score**: `0.654` (65.4%)

**Top-5 Retrieved Candidates**:
| Rank | Product ID | Brand | Product Name | Similarity Score | Similarity % |
| :---: | :---: | :--- | :--- | :---: | :---: |
| 1 | P008 | w3llpeople | Realist Invisible Setting Powder | `0.654` | 65.4% |
| 2 | P022 | physicians formula | Physicians Formula Bronze Booster Glow-Boosting BB Cream | `0.6228` | 62.3% |
| 3 | P014 | maia's mineral galaxy | Mineral Eye Brow Liner Charcoal Brown | `0.6155` | 61.6% |
| 4 | **P002** | sally b's skin yummies | B Glossy Lip Gloss | `0.6086` | 60.9% |
| 5 | P005 | marienatie | Lipstick | `0.5987` | 59.9% |

### Sample 8: `P002_0038.jpg`
- **Expected Product**: **P002** (sally b's skin yummies - B Glossy Lip Gloss)
- **Predicted Product**: **P003** (penny lane organics - Lip Gloss)
- **Top-1 Similarity Score**: `0.6856` (68.6%)

**Top-5 Retrieved Candidates**:
| Rank | Product ID | Brand | Product Name | Similarity Score | Similarity % |
| :---: | :---: | :--- | :--- | :---: | :---: |
| 1 | P003 | penny lane organics | Lip Gloss | `0.6856` | 68.6% |
| 2 | P010 | glossier | Stretch Concealer | `0.6773` | 67.7% |
| 3 | P023 | marcelle | Marcelle BB Cream-to-Powder Makeup | `0.6759` | 67.6% |
| 4 | P025 | dior | Junon | `0.6738` | 67.4% |
| 5 | P013 | zorah biocosmetiques | Liquid Liner | `0.6709` | 67.1% |

### Sample 9: `P002_0033.jpg`
- **Expected Product**: **P002** (sally b's skin yummies - B Glossy Lip Gloss)
- **Predicted Product**: **P027** (stila - Stila Stay All Day Bronzer in Medium)
- **Top-1 Similarity Score**: `0.7549` (75.5%)

**Top-5 Retrieved Candidates**:
| Rank | Product ID | Brand | Product Name | Similarity Score | Similarity % |
| :---: | :---: | :--- | :--- | :---: | :---: |
| 1 | P027 | stila | Stila Stay All Day Bronzer in Medium | `0.7549` | 75.5% |
| 2 | P011 | fenty | MATCH STIX - Matte Skinstick | `0.7331` | 73.3% |
| 3 | P012 | clinique | Even Better Compact Makeup Broad Spectrum SPF 15 | `0.7274` | 72.7% |
| 4 | P029 | nyx | NYX Mosaic Powder Blush Paradise | `0.7096` | 71.0% |
| 5 | P026 | benefit | dallas dusty rose face powder | `0.7096` | 71.0% |

### Sample 10: `P002_0009.jpg`
- **Expected Product**: **P002** (sally b's skin yummies - B Glossy Lip Gloss)
- **Predicted Product**: **P028** (mineral fusion - Mineral Fusion Bronzer Duo)
- **Top-1 Similarity Score**: `0.5632` (56.3%)

**Top-5 Retrieved Candidates**:
| Rank | Product ID | Brand | Product Name | Similarity Score | Similarity % |
| :---: | :---: | :--- | :--- | :---: | :---: |
| 1 | P028 | mineral fusion | Mineral Fusion Bronzer Duo | `0.5632` | 56.3% |
| 2 | **P002** | sally b's skin yummies | B Glossy Lip Gloss | `0.5497` | 55.0% |
| 3 | P024 | cargo cosmetics | Cargo Cosmetics OneBase for Face | `0.5397` | 54.0% |
| 4 | P014 | maia's mineral galaxy | Mineral Eye Brow Liner Charcoal Brown | `0.5376` | 53.8% |
| 5 | P020 | smashbox | 24 Hour CC Spot Concealer | `0.5339` | 53.4% |
