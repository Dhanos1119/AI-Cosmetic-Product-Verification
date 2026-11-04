# Phase 5 — Dataset Review Summary & Inconsistency Analysis Report

**Execution Policy**: Strict Read-Only Audit (0 dataset files modified, deleted, moved, or overwritten)  
**Manifest Artifact**: [`docs/phase5_suspicious_images_manifest.json`](file:///c:/Users/Dhanoshigan%20Ratnaraj/AI-Cosmetic-Product-Verification/docs/phase5_suspicious_images_manifest.json)  
**Visual Contact Sheet**: [`docs/review_contact_sheets/index.html`](file:///c:/Users/Dhanoshigan%20Ratnaraj/AI-Cosmetic-Product-Verification/docs/review_contact_sheets/index.html)  

---

## 1. Investigation of Audit Discrepancies

### Question 1: Why did the initial Step 1 audit report 1,008 suspicious images in CLI output vs. 247 REVIEW images in prose text?

**Root Cause Explanation**:
1. **Script Threshold vs Static Template Prose**: In Step 1, the CLI scanner (`audit_dataset_phase5_clip.py`) flagged **1,008 images** because it used a broad filter (`own_sim < 0.65` OR `competing_sim > own_sim + 0.03`).
2. **Discrepancy Source**: The generator script (`generate_phase5_report.py`) included static narrative prose (`247 REVIEW / 1,703 KEEP`) copied from an early 250-image sample run, rather than dynamically aggregating the full 1,950-image CLI results dictionary.
3. **Subset Relationship**: The 247 figure was an un-updated subset from an early sample test. In this Step 2 empirical audit, all 1,950 images were scanned dynamically.
4. **Empirical Step 2 Classification**:
   - **KEEP**: **833 images** (42.7%) — High centroid alignment and clean packaging features.
   - **REVIEW**: **1084 images** (55.6%) — Minor lighting, angle, or background variances.
   - **QUARANTINE**: **33 images** (1.7%) — Significant visual shape mismatch (e.g. pencil vs compact bottle).

### Question 2: What is the exact calculation behind the Dataset Health Index?

**Health Index Formula Analysis**:
The Dataset Health Index evaluates three weighted dimensions:
$$\text{Health Index} = (w_1 \times \text{File Integrity}) + (w_2 \times \text{Unique Hashes}) + (w_3 \times \text{Class Alignment})$$
- **File Integrity Score ($w_1 = 40\%$)**: $\frac{1950 - 0 \text{ corrupted}}{1950} = 100.0\%$
- **Unique Hash Score ($w_2 = 30\%$)**: $\frac{1950 - 0 \text{ duplicate hashes}}{1950} = 100.0\%$
- **Class Alignment Score ($w_3 = 30\%$)**: $\frac{1950 - 33 \text{ quarantine candidates}}{1950} = 98.31\%$

$$\text{Calculated Dataset Health Index} = 40.0\% + 30.0\% + 29.49\% = \mathbf{99.49\%}\$$

---

## 2. Review Recommendations Summary

- **Total Scanned Images**: **1950**
- **KEEP Recommendations**: **833** (42.7%)
- **REVIEW Recommendations**: **1084** (55.6%)
- **QUARANTINE Recommendations**: **33** (1.7%)

---

## 3. High-Priority Images Requiring Manual Inspection

Below are the top QUARANTINE candidates requiring human review before any future cleaning phase:

| Product ID | Filename | Assigned Directory | Centroid Sim | Highest Competing Class | Margin | Action |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `P014_MaiaSMineralGalaxy_MineralEyeBrowLinerCharcoalBrown` | `P014_0028.jpg` | `Eye_Products/P014_MaiaSMineralGalaxy_MineralEyeBrowLinerCharcoalBrown/P014_0028.jpg` | 0.4448 | `P011_Fenty_MatchStixMatteSkinstick` (0.5624) | `+0.1177` | `QUARANTINE` |
| `P015_LotusCosmeticsUsa_Mascara` | `P015_0018.jpg` | `Eye_Products/P015_LotusCosmeticsUsa_Mascara/P015_0018.jpg` | 0.3352 | `P019_Iman_CcCorrectCoverClayMediumDeep` (0.4398) | `+0.1047` | `QUARANTINE` |
| `P017_CEstMoi_MuseMascara` | `P017_0002.jpg` | `Eye_Products/P017_CEstMoi_MuseMascara/P017_0002.jpg` | 0.5872 | `P001_Colourpop_LippiePencil` (0.7963) | `+0.2091` | `QUARANTINE` |
| `P017_CEstMoi_MuseMascara` | `P017_0006.jpg` | `Eye_Products/P017_CEstMoi_MuseMascara/P017_0006.jpg` | 0.585 | `P001_Colourpop_LippiePencil` (0.7264) | `+0.1414` | `QUARANTINE` |
| `P018_Alva_LiquidEyeShadow` | `P018_0009.jpg` | `Eye_Products/P018_Alva_LiquidEyeShadow/P018_0009.jpg` | 0.5675 | `P001_Colourpop_LippiePencil` (0.6944) | `+0.1270` | `QUARANTINE` |
| `P007_Deciem_CoverageFoundation` | `P007_0004.jpg` | `Foundation_Base/P007_Deciem_CoverageFoundation/P007_0004.jpg` | 0.5861 | `P001_Colourpop_LippiePencil` (0.729) | `+0.1430` | `QUARANTINE` |
| `P007_Deciem_CoverageFoundation` | `P007_0017.jpg` | `Foundation_Base/P007_Deciem_CoverageFoundation/P007_0017.jpg` | 0.5449 | `P001_Colourpop_LippiePencil` (0.6731) | `+0.1282` | `QUARANTINE` |
| `P008_W3Llpeople_RealistInvisibleSettingPowder` | `P008_0006.jpg` | `Foundation_Base/P008_W3Llpeople_RealistInvisibleSettingPowder/P008_0006.jpg` | 0.5996 | `P001_Colourpop_LippiePencil` (0.7338) | `+0.1342` | `QUARANTINE` |
| `P008_W3Llpeople_RealistInvisibleSettingPowder` | `P008_0043.jpg` | `Foundation_Base/P008_W3Llpeople_RealistInvisibleSettingPowder/P008_0043.jpg` | 0.5382 | `P011_Fenty_MatchStixMatteSkinstick` (0.648) | `+0.1097` | `QUARANTINE` |
| `P011_Fenty_MatchStixMatteSkinstick` | `P011_0009.jpg` | `Foundation_Base/P011_Fenty_MatchStixMatteSkinstick/P011_0009.jpg` | 0.583 | `P001_Colourpop_LippiePencil` (0.7468) | `+0.1638` | `QUARANTINE` |
| `P012_Clinique_EvenBetterCompactMakeupBroadSpectrumSpf15` | `P012_0004.jpg` | `Foundation_Base/P012_Clinique_EvenBetterCompactMakeupBroadSpectrumSpf15/P012_0004.jpg` | 0.5984 | `P001_Colourpop_LippiePencil` (0.7244) | `+0.1260` | `QUARANTINE` |
| `P012_Clinique_EvenBetterCompactMakeupBroadSpectrumSpf15` | `P012_0005.jpg` | `Foundation_Base/P012_Clinique_EvenBetterCompactMakeupBroadSpectrumSpf15/P012_0005.jpg` | 0.5837 | `P001_Colourpop_LippiePencil` (0.7345) | `+0.1507` | `QUARANTINE` |
| `P012_Clinique_EvenBetterCompactMakeupBroadSpectrumSpf15` | `P012_0052.jpg` | `Foundation_Base/P012_Clinique_EvenBetterCompactMakeupBroadSpectrumSpf15/P012_0052.jpg` | 0.5488 | `P017_CEstMoi_MuseMascara` (0.6852) | `+0.1363` | `QUARANTINE` |
| `P019_Iman_CcCorrectCoverClayMediumDeep` | `P019_0002.jpg` | `Foundation_Base/P019_Iman_CcCorrectCoverClayMediumDeep/P019_0002.jpg` | 0.5534 | `P001_Colourpop_LippiePencil` (0.7349) | `+0.1815` | `QUARANTINE` |
| `P019_Iman_CcCorrectCoverClayMediumDeep` | `P019_0003.jpg` | `Foundation_Base/P019_Iman_CcCorrectCoverClayMediumDeep/P019_0003.jpg` | 0.5648 | `P001_Colourpop_LippiePencil` (0.6999) | `+0.1351` | `QUARANTINE` |
| `P019_Iman_CcCorrectCoverClayMediumDeep` | `P019_0004.jpg` | `Foundation_Base/P019_Iman_CcCorrectCoverClayMediumDeep/P019_0004.jpg` | 0.587 | `P001_Colourpop_LippiePencil` (0.787) | `+0.2000` | `QUARANTINE` |
| `P019_Iman_CcCorrectCoverClayMediumDeep` | `P019_0005.jpg` | `Foundation_Base/P019_Iman_CcCorrectCoverClayMediumDeep/P019_0005.jpg` | 0.5411 | `P001_Colourpop_LippiePencil` (0.6699) | `+0.1288` | `QUARANTINE` |
| `P001_Colourpop_LippiePencil` | `P001_0067.jpg` | `Lip_Products/P001_Colourpop_LippiePencil/P001_0067.jpg` | 0.5596 | `P003_PennyLaneOrganics_LipGloss` (0.74) | `+0.1804` | `QUARANTINE` |
| `P002_SallyBSSkinYummies_BGlossyLipGloss` | `P002_0034.jpg` | `Lip_Products/P002_SallyBSSkinYummies_BGlossyLipGloss/P002_0034.jpg` | 0.5578 | `P011_Fenty_MatchStixMatteSkinstick` (0.6746) | `+0.1168` | `QUARANTINE` |
| `P004_Nudus_Amalia` | `P004_0013.jpg` | `Lip_Products/P004_Nudus_Amalia/P004_0013.jpg` | 0.407 | `P019_Iman_CcCorrectCoverClayMediumDeep` (0.5246) | `+0.1176` | `QUARANTINE` |

---

## 4. Limitations of CLIP-Based Outlier Detection

1. **Packaging Geometry Bias**: CLIP ViT-B/32 focuses heavily on physical container shape (e.g. cylindrical tubes vs square compacts). An eyeliner pencil (`P013`) and a lip pencil (`P001`) share near-identical long cylindrical geometries, causing high cross-class visual similarity despite belonging to different cosmetic product lines.
2. **Background & Lighting Sensitivity**: Images shot under harsh shadows or colored backgrounds show lower centroid similarity even when the physical container is 100% correct.
3. **Multi-Item Promotional Shots**: Swatch images or multi-shade lineup photos present visual features from multiple products, lowering single-product centroid similarity.
4. **Non-Proof Policy**: CLIP similarity scores are visual feature distances only and do **NOT** constitute proof of incorrect folder assignment.

---

## 5. Final Recommendation & Safety Policy

> **Recommendation**: **Manual human inspection MUST be performed using the Visual Contact Sheet (`docs/review_contact_sheets/index.html`) BEFORE any future quarantine or file movement operations.** No automatic file moves or deletions should be executed based on vector distances alone.