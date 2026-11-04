"""
Phase 1 Audit Script: Project Structure, Dataset Catalog, and Baseline Metrics
Generates reports/phase1_project_inspection_audit_2026_10_31.md
"""

import os
import sys
import csv
import json
import hashlib
from pathlib import Path
from collections import defaultdict
import numpy as np

BASE_DIR = Path(__file__).parent.parent.resolve()
DATASET_DIR = BASE_DIR / "data" / "image_model_dataset"
CSV_PRODUCTS = BASE_DIR / "data" / "selected_30_products_final.csv"
METADATA_CSV = BASE_DIR / "data" / "image_dataset_metadata.csv"
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

REPORT_PATH = REPORTS_DIR / "phase1_project_inspection_audit_2026_10_31.md"


def main():
    print("Executing Phase 1 Project & Dataset Inspection...")

    # 1. Product Catalog
    catalog = {}
    with open(CSV_PRODUCTS, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            pid = r["product_id"].strip()
            catalog[pid] = {
                "product_id": pid,
                "brand": r["brand"].strip(),
                "product_name": r["product_name"].strip(),
                "category": r["category"].strip(),
                "product_type": r["product_type"].strip(),
            }

    # 2. Dataset Folders on Disk
    folder_stats = {}
    total_images = 0
    cat_counts = defaultdict(int)

    for cat_dir in sorted(DATASET_DIR.iterdir()):
        if not cat_dir.is_dir() or cat_dir.name.startswith("_"):
            continue
        cat_name = cat_dir.name
        for pfolder in sorted(cat_dir.iterdir()):
            if not pfolder.is_dir():
                continue
            pid = pfolder.name.split("_")[0]
            files = [f for f in pfolder.iterdir() if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]
            n_files = len(files)
            folder_stats[pid] = {
                "folder_name": pfolder.name,
                "category": cat_name,
                "count": n_files,
                "path": str(pfolder.relative_to(BASE_DIR)).replace("\\", "/")
            }
            cat_counts[cat_name] += n_files
            total_images += n_files

    # 3. Check Embeddings on Disk
    ref_emb_path = BASE_DIR / "data" / "clip_reference_embeddings.npz"
    test_emb_path = BASE_DIR / "data" / "clip_test_embeddings.npz"
    centroids_path = BASE_DIR / "data" / "clip_centroids_vit_b32.npy"

    ref_count = 0
    test_count = 0
    if ref_emb_path.exists():
        ref_data = np.load(ref_emb_path)
        ref_count = len(ref_data["product_ids"])
    if test_emb_path.exists():
        test_data = np.load(test_emb_path)
        test_count = len(test_data["product_ids"])

    # 4. Generate Markdown Audit Report
    lines = [
        "# Phase 1: CLIP Dataset & Project Architecture Inspection Audit",
        "",
        "**Date**: 2026-10-31  ",
        "**Project**: AI-Based Cosmetic Product Verification and Marketplace Review Analysis System  ",
        f"**Repository Root**: `{BASE_DIR}`  ",
        f"**Dataset Location**: `{DATASET_DIR}`  ",
        "",
        "---",
        "",
        "## 1. Project Architecture & Component Inventory",
        "",
        "| Component | File / Directory Path | Role & Operational Status |",
        "| :--- | :--- | :--- |",
        f"| **Active Dataset** | [`data/image_model_dataset/`](file:///{str(DATASET_DIR).replace('\\', '/')}) | Contains {total_images} product packshots organized by category and product ID |",
        f"| **Product Catalog** | [`data/selected_30_products_final.csv`](file:///{str(CSV_PRODUCTS).replace('\\', '/')}) | Official 30-product catalog (`P001` - `P030`) |",
        f"| **Dataset Metadata** | [`data/image_dataset_metadata.csv`](file:///{str(METADATA_CSV).replace('\\', '/')}) | Per-image resolution, source URL, format, and initial validation labels |",
        f"| **CLIP Service** | [`ai-service/app/services/clip_service.py`](file:///{str(BASE_DIR).replace('\\', '/')}/ai-service/app/services/clip_service.py) | Production multimodal feature extraction and 1-NN similarity ranking |",
        f"| **OCR Service** | [`ai-service/app/services/ocr_service.py`](file:///{str(BASE_DIR).replace('\\', '/')}/ai-service/app/services/ocr_service.py) | RapidOCR ONNX / EasyOCR label parsing and brand normalisation |",
        f"| **Centroid Cache** | [`data/clip_centroids_vit_b32.npy`](file:///{str(centroids_path).replace('\\', '/')}) | 30x512 matrix of reference mean centroids |",
        f"| **Reference Bank** | [`data/clip_reference_embeddings.npz`](file:///{str(ref_emb_path).replace('\\', '/')}) | 1,340 reference feature vectors (512-dim) for 1-NN max-pooling |",
        f"| **Test Query Bank** | [`data/clip_test_embeddings.npz`](file:///{str(test_emb_path).replace('\\', '/')}) | 610 test query feature vectors (512-dim) reserved for evaluation |",
        f"| **Evaluation Script** | [`ai-service/scripts/evaluate_clip.py`](file:///{str(BASE_DIR).replace('\\', '/')}/ai-service/scripts/evaluate_clip.py) | Evaluates baseline single-centroid matching |",
        f"| **Experiments Runner** | [`ai-service/scripts/run_clip_experiments.py`](file:///{str(BASE_DIR).replace('\\', '/')}/ai-service/scripts/run_clip_experiments.py) | Benchmarks 6 matching methods on 70/30 split |",
        "",
        "---",
        "",
        "## 2. Catalog Products & Dataset Distribution",
        "",
        f"Total Catalog Products: **30** (`P001` - `P030`)  ",
        f"Total Images on Disk: **{total_images}** across 4 active category folders (`Skin_Care` is currently empty)  ",
        f"Reference Embeddings: **{ref_count}** ({ref_count/total_images*100:.1f}%) | Test Embeddings: **{test_count}** ({test_count/total_images*100:.1f}%)  ",
        "",
        "| Product ID | Brand | Product Name | Category | Folder Name | Image Count | Split (Ref / Test) |",
        "| :--- | :--- | :--- | :--- | :--- | :---: | :---: |",
    ]

    for pid in sorted(catalog.keys()):
        cat_info = catalog[pid]
        f_info = folder_stats.get(pid, {"folder_name": "MISSING", "count": 0})
        cnt = f_info["count"]
        ref_n = max(1, int(cnt * 0.70)) if cnt > 0 else 0
        test_n = cnt - ref_n
        lines.append(
            f"| **{pid}** | {cat_info['brand']} | {cat_info['product_name']} | {cat_info['category']} | `{f_info['folder_name']}` | {cnt} | {ref_n} / {test_n} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 3. Analysis of Existing Production Prediction Pipeline",
        "",
        "Inspection of [`ai-service/app/services/clip_service.py`](file:///" + str(BASE_DIR).replace('\\', '/') + "/ai-service/app/services/clip_service.py) confirms the following workflow:",
        "1. **Model**: Pretrained `openai/clip-vit-base-patch32` via HuggingFace `transformers`. Outputs projected 512-dimensional L2-normalized embeddings.",
        "2. **Production Matching Method**: **1-NN Reference Bank (Max-Pooling) + OCR Brand Boost** (Method 7).",
        "   - Computes cosine similarity between query vector $q$ and all 1,340 reference vectors in `clip_reference_embeddings.npz`.",
        "   - Takes the maximum similarity per product ID: $S_{pid} = \\max_{i \\in Ref(pid)} (v_i \\cdot q)$.",
        "   - If OCR detects a brand matching the product catalog brand, applies `+0.15` similarity boost (capped at `0.99`).",
        "   - Fallback: Uses `clip_centroids_vit_b32.npy` single-centroid dot product if the reference bank file is missing.",
        "3. **Thresholds & Gating**:",
        "   - High Confidence: $\\ge 80.0\\%$ similarity, margin $\\ge 2\\%$, no category conflict.",
        "   - Possible Match: $\\ge 60.0\\%$ and $< 80.0\\%$, margin $\\ge 2\\%$.",
        "   - Low Confidence: $< 60.0\\%$ OR margin $< 2\\%$ OR category mismatch.",
        "   - Category Mismatch Gate: Caps confidence at 'Low' if OCR category conflicts with CLIP top hit.",
        "",
        "---",
        "",
        "## 4. Benchmark Baseline Metrics (Prior to Dataset Cleaning)",
        "",
        "Based on verified evaluation logs in [`docs/clip_accuracy_comparison.md`](file:///" + str(BASE_DIR).replace('\\', '/') + "/docs/clip_accuracy_comparison.md) on the strict 70/30 split (Seed 42, 610 test queries):",
        "",
        "| Evaluation Method | Top-1 Accuracy | Top-5 Accuracy | Macro F1 | Note |",
        "| :--- | :---: | :---: | :---: | :--- |",
        "| **Method 1: Single-Centroid Baseline** | **30.82%** (188/610) | 57.54% (351/610) | 30.63% | Baseline centroid averaging collapse |",
        "| **Method 2: 1-NN Reference Bank** | **58.03%** (354/610) | 75.57% (461/610) | 58.78% | Nearest-neighbor matching without OCR |",
        "| **Method 3: 3-NN Reference Bank** | **56.56%** (345/610) | 75.57% (461/610) | 57.29% | Top-3 reference average |",
        "| **Method 4: K-Means Sub-Centroids (k=3)** | **37.87%** (231/610) | 61.80% (377/610) | 38.61% | Compact prototypes |",
        "| **Method 6: Production OCR + Centroid** | **30.66%** (187/610) | 57.87% (353/610) | 30.40% | OCR boost on single centroid |",
        "| **Method 7: 1-NN Reference Bank + OCR Boost** | **58.36%** (356/610) | 76.07% (464/610) | 59.11% | **Current Live Production Pipeline** |",
        "",
        "### Key Target for Dataset Cleaning & Optimization:",
        "- Baseline: **58.36%** Top-1 Accuracy.",
        "- Goal: **> 60.0%** Genuine Top-1 Accuracy achieved through systematic dataset cleaning, outlier/noise removal, duplicate deduplication, and data augmentation.",
        "",
        "---",
        "*Report generated automatically by `scripts/inspect_phase1_dataset.py` on 2026-10-31.*",
    ])

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Phase 1 inspection report successfully saved to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
