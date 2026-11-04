# Phase 1: CLIP Dataset & Project Architecture Inspection Audit

**Date**: 2026-10-31  
**Project**: AI-Based Cosmetic Product Verification and Marketplace Review Analysis System  
**Repository Root**: `C:\Users\Dhanoshigan Ratnaraj\AI-Cosmetic-Product-Verification`  
**Dataset Location**: `C:\Users\Dhanoshigan Ratnaraj\AI-Cosmetic-Product-Verification\data\image_model_dataset`  

---

## 1. Project Architecture & Component Inventory

| Component | File / Directory Path | Role & Operational Status |
| :--- | :--- | :--- |
| **Active Dataset** | [`data/image_model_dataset/`](file:///C:/Users/Dhanoshigan Ratnaraj/AI-Cosmetic-Product-Verification/data/image_model_dataset) | Contains 1950 product packshots organized by category and product ID |
| **Product Catalog** | [`data/selected_30_products_final.csv`](file:///C:/Users/Dhanoshigan Ratnaraj/AI-Cosmetic-Product-Verification/data/selected_30_products_final.csv) | Official 30-product catalog (`P001` - `P030`) |
| **Dataset Metadata** | [`data/image_dataset_metadata.csv`](file:///C:/Users/Dhanoshigan Ratnaraj/AI-Cosmetic-Product-Verification/data/image_dataset_metadata.csv) | Per-image resolution, source URL, format, and initial validation labels |
| **CLIP Service** | [`ai-service/app/services/clip_service.py`](file:///C:/Users/Dhanoshigan Ratnaraj/AI-Cosmetic-Product-Verification/ai-service/app/services/clip_service.py) | Production multimodal feature extraction and 1-NN similarity ranking |
| **OCR Service** | [`ai-service/app/services/ocr_service.py`](file:///C:/Users/Dhanoshigan Ratnaraj/AI-Cosmetic-Product-Verification/ai-service/app/services/ocr_service.py) | RapidOCR ONNX / EasyOCR label parsing and brand normalisation |
| **Centroid Cache** | [`data/clip_centroids_vit_b32.npy`](file:///C:/Users/Dhanoshigan Ratnaraj/AI-Cosmetic-Product-Verification/data/clip_centroids_vit_b32.npy) | 30x512 matrix of reference mean centroids |
| **Reference Bank** | [`data/clip_reference_embeddings.npz`](file:///C:/Users/Dhanoshigan Ratnaraj/AI-Cosmetic-Product-Verification/data/clip_reference_embeddings.npz) | 1,340 reference feature vectors (512-dim) for 1-NN max-pooling |
| **Test Query Bank** | [`data/clip_test_embeddings.npz`](file:///C:/Users/Dhanoshigan Ratnaraj/AI-Cosmetic-Product-Verification/data/clip_test_embeddings.npz) | 610 test query feature vectors (512-dim) reserved for evaluation |
| **Evaluation Script** | [`ai-service/scripts/evaluate_clip.py`](file:///C:/Users/Dhanoshigan Ratnaraj/AI-Cosmetic-Product-Verification/ai-service/scripts/evaluate_clip.py) | Evaluates baseline single-centroid matching |
| **Experiments Runner** | [`ai-service/scripts/run_clip_experiments.py`](file:///C:/Users/Dhanoshigan Ratnaraj/AI-Cosmetic-Product-Verification/ai-service/scripts/run_clip_experiments.py) | Benchmarks 6 matching methods on 70/30 split |

---

## 2. Catalog Products & Dataset Distribution

Total Catalog Products: **30** (`P001` - `P030`)  
Total Images on Disk: **1950** across 4 active category folders (`Skin_Care` is currently empty)  
Reference Embeddings: **1340** (68.7%) | Test Embeddings: **610** (31.3%)  

| Product ID | Brand | Product Name | Category | Folder Name | Image Count | Split (Ref / Test) |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **P001** | colourpop | Lippie Pencil | Lip_Products | `P001_Colourpop_LippiePencil` | 67 | 46 / 21 |
| **P002** | sally b's skin yummies | B Glossy Lip Gloss | Lip_Products | `P002_SallyBSSkinYummies_BGlossyLipGloss` | 65 | 45 / 20 |
| **P003** | penny lane organics | Lip Gloss | Lip_Products | `P003_PennyLaneOrganics_LipGloss` | 66 | 46 / 20 |
| **P004** | nudus | Amalia | Lip_Products | `P004_Nudus_Amalia` | 66 | 46 / 20 |
| **P005** | marienatie | Lipstick | Lip_Products | `P005_Marienatie_Lipstick` | 67 | 46 / 21 |
| **P006** | coastal classic creation | Conch Lipstick | Lip_Products | `P006_CoastalClassicCreation_ConchLipstick` | 67 | 46 / 21 |
| **P007** | deciem | Coverage Foundation | Foundation_Base | `P007_Deciem_CoverageFoundation` | 67 | 46 / 21 |
| **P008** | w3llpeople | Realist Invisible Setting Powder | Foundation_Base | `P008_W3Llpeople_RealistInvisibleSettingPowder` | 67 | 46 / 21 |
| **P009** | rejuva minerals | Pressed Powder Foundation | Foundation_Base | `P009_RejuvaMinerals_PressedPowderFoundation` | 67 | 46 / 21 |
| **P010** | glossier | Stretch Concealer | Foundation_Base | `P010_Glossier_StretchConcealer` | 67 | 46 / 21 |
| **P011** | fenty | MATCH STIX - Matte Skinstick | Foundation_Base | `P011_Fenty_MatchStixMatteSkinstick` | 67 | 46 / 21 |
| **P012** | clinique | Even Better Compact Makeup Broad Spectrum SPF 15 | Foundation_Base | `P012_Clinique_EvenBetterCompactMakeupBroadSpectrumSpf15` | 67 | 46 / 21 |
| **P013** | zorah biocosmetiques | Liquid Liner | Eye_Products | `P013_ZorahBiocosmetiques_LiquidLiner` | 67 | 46 / 21 |
| **P014** | maia's mineral galaxy | Mineral Eye Brow Liner Charcoal Brown | Eye_Products | `P014_MaiaSMineralGalaxy_MineralEyeBrowLinerCharcoalBrown` | 67 | 46 / 21 |
| **P015** | lotus cosmetics usa | Mascara | Eye_Products | `P015_LotusCosmeticsUsa_Mascara` | 67 | 46 / 21 |
| **P016** | green people | Volumising Mascara | Eye_Products | `P016_GreenPeople_VolumisingMascara` | 67 | 46 / 21 |
| **P017** | c'est moi | Muse Mascara | Eye_Products | `P017_CEstMoi_MuseMascara` | 67 | 46 / 21 |
| **P018** | alva | Liquid Eye Shadow | Eye_Products | `P018_Alva_LiquidEyeShadow` | 67 | 46 / 21 |
| **P019** | iman | CC Correct & Cover Clay Medium Deep | Foundation_Base | `P019_Iman_CcCorrectCoverClayMediumDeep` | 67 | 46 / 21 |
| **P020** | smashbox | 24 Hour CC Spot Concealer | Foundation_Base | `P020_Smashbox_24HourCcSpotConcealer` | 67 | 46 / 21 |
| **P021** | dr. hauschka | Dr. Hauschka Translucent Bronzing Tint | Other_Makeup | `P021_DrHauschka_DrHauschkaTranslucentBronzingTint` | 67 | 46 / 21 |
| **P022** | physicians formula | Physicians Formula Bronze Booster Glow-Boosting BB Cream | Other_Makeup | `P022_PhysiciansFormula_PhysiciansFormulaBronzeBoosterGlowBoostingBbCream` | 67 | 46 / 21 |
| **P023** | marcelle | Marcelle BB Cream-to-Powder Makeup | Foundation_Base | `P023_Marcelle_MarcelleBbCreamToPowderMakeup` | 67 | 46 / 21 |
| **P024** | cargo cosmetics | Cargo Cosmetics OneBase for Face | Foundation_Base | `P024_CargoCosmetics_CargoCosmeticsOnebaseForFace` | 67 | 46 / 21 |
| **P025** | dior | Junon | Other_Makeup | `P025_Dior_Junon` | 67 | 46 / 21 |
| **P026** | benefit | dallas dusty rose face powder | Other_Makeup | `P026_Benefit_DallasDustyRoseFacePowder` | 67 | 46 / 21 |
| **P027** | stila | Stila Stay All Day Bronzer in Medium | Other_Makeup | `P027_Stila_StilaStayAllDayBronzerInMedium` | 67 | 46 / 21 |
| **P028** | mineral fusion | Mineral Fusion Bronzer Duo | Other_Makeup | `P028_MineralFusion_MineralFusionBronzerDuo` | 67 | 46 / 21 |
| **P029** | nyx | NYX Mosaic Powder Blush Paradise | Other_Makeup | `P029_Nyx_NyxMosaicPowderBlushParadise` | 67 | 46 / 21 |
| **P030** | annabelle | Annabelle Biggy Bronzer Haute Gold | Other_Makeup | `P030_Annabelle_AnnabelleBiggyBronzerHauteGold` | 11 | 7 / 4 |

---

## 3. Analysis of Existing Production Prediction Pipeline

Inspection of [`ai-service/app/services/clip_service.py`](file:///C:/Users/Dhanoshigan Ratnaraj/AI-Cosmetic-Product-Verification/ai-service/app/services/clip_service.py) confirms the following workflow:
1. **Model**: Pretrained `openai/clip-vit-base-patch32` via HuggingFace `transformers`. Outputs projected 512-dimensional L2-normalized embeddings.
2. **Production Matching Method**: **1-NN Reference Bank (Max-Pooling) + OCR Brand Boost** (Method 7).
   - Computes cosine similarity between query vector $q$ and all 1,340 reference vectors in `clip_reference_embeddings.npz`.
   - Takes the maximum similarity per product ID: $S_{pid} = \max_{i \in Ref(pid)} (v_i \cdot q)$.
   - If OCR detects a brand matching the product catalog brand, applies `+0.15` similarity boost (capped at `0.99`).
   - Fallback: Uses `clip_centroids_vit_b32.npy` single-centroid dot product if the reference bank file is missing.
3. **Thresholds & Gating**:
   - High Confidence: $\ge 80.0\%$ similarity, margin $\ge 2\%$, no category conflict.
   - Possible Match: $\ge 60.0\%$ and $< 80.0\%$, margin $\ge 2\%$.
   - Low Confidence: $< 60.0\%$ OR margin $< 2\%$ OR category mismatch.
   - Category Mismatch Gate: Caps confidence at 'Low' if OCR category conflicts with CLIP top hit.

---

## 4. Benchmark Baseline Metrics (Prior to Dataset Cleaning)

Based on verified evaluation logs in [`docs/clip_accuracy_comparison.md`](file:///C:/Users/Dhanoshigan Ratnaraj/AI-Cosmetic-Product-Verification/docs/clip_accuracy_comparison.md) on the strict 70/30 split (Seed 42, 610 test queries):

| Evaluation Method | Top-1 Accuracy | Top-5 Accuracy | Macro F1 | Note |
| :--- | :---: | :---: | :---: | :--- |
| **Method 1: Single-Centroid Baseline** | **30.82%** (188/610) | 57.54% (351/610) | 30.63% | Baseline centroid averaging collapse |
| **Method 2: 1-NN Reference Bank** | **58.03%** (354/610) | 75.57% (461/610) | 58.78% | Nearest-neighbor matching without OCR |
| **Method 3: 3-NN Reference Bank** | **56.56%** (345/610) | 75.57% (461/610) | 57.29% | Top-3 reference average |
| **Method 4: K-Means Sub-Centroids (k=3)** | **37.87%** (231/610) | 61.80% (377/610) | 38.61% | Compact prototypes |
| **Method 6: Production OCR + Centroid** | **30.66%** (187/610) | 57.87% (353/610) | 30.40% | OCR boost on single centroid |
| **Method 7: 1-NN Reference Bank + OCR Boost** | **58.36%** (356/610) | 76.07% (464/610) | 59.11% | **Current Live Production Pipeline** |

### Key Target for Dataset Cleaning & Optimization:
- Baseline: **58.36%** Top-1 Accuracy.
- Goal: **> 60.0%** Genuine Top-1 Accuracy achieved through systematic dataset cleaning, outlier/noise removal, duplicate deduplication, and data augmentation.

---
*Report generated automatically by `scripts/inspect_phase1_dataset.py` on 2026-10-31.*