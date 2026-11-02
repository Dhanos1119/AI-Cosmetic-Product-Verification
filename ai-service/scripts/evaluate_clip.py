"""
CLIP Product-Level Accuracy Evaluation Script (Genuine OpenAI CLIP ViT-B/32)
Evaluates Top-1 & Top-5 Product Identification Accuracy across 30 Target Product Folders (P001 - P030).

Uses a strict 70/30 Stratified Split:
- 70% Reference Images (used exclusively to compute product centroid embeddings)
- 30% Test Images (reserved exclusively for testing; zero overlap with reference set)

Generates:
1. data/clip_evaluation_results.csv (Per-test image predictions)
2. data/clip_evaluation_summary.json (Machine-readable JSON metrics & confusion matrix)
3. data/clip_evaluation_report.md (Human-readable Markdown report)
"""

import os
import sys
import csv
import json
import random
import time
from pathlib import Path
from collections import defaultdict
import numpy as np
import torch

# Resolve project paths
BASE_DIR = Path(__file__).parent.parent.parent.resolve()
AI_SERVICE_DIR = BASE_DIR / "ai-service"
DATASET_DIR = BASE_DIR / "data" / "image_model_dataset"
CSV_PRODUCTS = BASE_DIR / "data" / "selected_30_products_final.csv"
OUTPUT_DIR = BASE_DIR / "data"

CSV_OUT = OUTPUT_DIR / "clip_evaluation_results.csv"
JSON_OUT = OUTPUT_DIR / "clip_evaluation_summary.json"
MD_OUT = OUTPUT_DIR / "clip_evaluation_report.md"

# Add ai-service to sys.path to import production feature extraction functions
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

from app.services.clip_service import _extract_image_file_embedding as extract_image_embedding

def run_evaluation():
    print("=" * 75)
    print("STARTING GENUINE OPENAI CLIP ViT-B/32 PRODUCT EVALUATION (P001 - P030)")
    print("=" * 75)

    start_time = time.time()

    # 1. Load Product Catalog Metadata from CSV
    product_catalog = {}
    if CSV_PRODUCTS.exists():
        with open(CSV_PRODUCTS, mode='r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                pid = row['product_id'].strip()
                product_catalog[pid] = {
                    'product_id': pid,
                    'brand': row['brand'].strip(),
                    'product_name': row['product_name'].strip(),
                    'category': row['category'].strip(),
                    'product_type': row.get('product_type', row['category']).strip()
                }

    # 2. Discover Product Folders & Execute Stratified Split (70% Reference / 30% Test)
    random.seed(42)  # Deterministic seed for exact reproducibility
    
    reference_images_by_pid = defaultdict(list)
    test_images_by_pid = defaultdict(list)
    total_scanned_images = 0
    missing_or_empty_folders = []

    if not DATASET_DIR.exists():
        print(f"[ERROR] Dataset directory not found at: {DATASET_DIR}")
        return

    expected_pids = [f"P{i:03d}" for i in range(1, 31)]
    found_pids = set()

    for cat_dir in sorted(DATASET_DIR.iterdir()):
        if not cat_dir.is_dir() or cat_dir.name.startswith('_'):
            continue
        for folder in sorted(cat_dir.iterdir()):
            if not folder.is_dir():
                continue
            pid = folder.name.split('_')[0]
            imgs = sorted([f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']], key=lambda x: x.name)
            if not imgs:
                missing_or_empty_folders.append(folder.name)
                continue

            found_pids.add(pid)
            total_scanned_images += len(imgs)
            
            # Deterministic shuffle per product folder
            shuffled = imgs.copy()
            random.shuffle(shuffled)
            
            # 70% Reference set / 30% Reserved Test set
            ref_count = max(1, int(len(imgs) * 0.70))
            ref_set = shuffled[:ref_count]
            test_set = shuffled[ref_count:]
            
            reference_images_by_pid[pid].extend(ref_set)
            test_images_by_pid[pid].extend(test_set)
            
            if pid not in product_catalog:
                parts = folder.name.split('_', 2)
                product_catalog[pid] = {
                    'product_id': pid,
                    'brand': parts[1] if len(parts) > 1 else 'Brand',
                    'product_name': parts[2] if len(parts) > 2 else folder.name,
                    'category': cat_dir.name,
                    'product_type': cat_dir.name
                }

    missing_pids = [pid for pid in expected_pids if pid not in found_pids]
    active_pids = sorted(list(found_pids))

    print(f"Dataset Location: {DATASET_DIR}")
    print(f"Product Classes Found: {len(active_pids)} / 30 target products ({active_pids[0]} to {active_pids[-1]})")
    if missing_pids:
        print(f"Missing Product Classes: {missing_pids}")
    print(f"Total Scanned Dataset Images: {total_scanned_images}")
    print(f"Reference / Catalog Index Set (70%): {sum(len(v) for v in reference_images_by_pid.values())} images")
    print(f"Reserved Test Query Set (30%): {sum(len(v) for v in test_images_by_pid.values())} images")
    print("Data Leakage Safeguard: Reference set and Test set have ZERO overlap.\n")

    # 3. Compute Product Centroid Embeddings EXCLUSIVELY from Reference Set using OpenAI CLIP ViT-B/32
    print("Extracting 512-dim Deep Vision Transformer Embeddings from Reference Images...")
    centroids = []
    pid_index_map = []

    for idx, pid in enumerate(active_pids, start=1):
        ref_files = reference_images_by_pid[pid]
        vecs = [extract_image_embedding(str(p)) for p in ref_files]
        vecs = [v for v in vecs if v is not None]
        if vecs:
            avg_vec = np.mean(vecs, axis=0)
            avg_norm = np.linalg.norm(avg_vec)
            if avg_norm > 0:
                avg_vec = avg_vec / avg_norm
            centroids.append(avg_vec)
            pid_index_map.append(pid)
            print(f"  [{idx}/30] Processed Centroid for {pid} ({len(vecs)} reference images)")
        else:
            print(f"[WARNING] Could not extract valid CLIP embeddings for reference set of product {pid}")

    centroids_mat = np.array(centroids, dtype=np.float32)  # Matrix shape: (Num_Active_Products, 512)
    print(f"\nBuilt catalog CLIP centroid matrix for {len(pid_index_map)} active product classes.\n")

    # 4. Evaluate Reserved Test Set Images
    print("Executing OpenAI CLIP Product Identification Inference on Reserved Test Images...")
    
    test_results = []
    per_product_stats = defaultdict(lambda: {'total': 0, 'top1_correct': 0, 'top5_correct': 0, 'low_confidence': 0})
    confusion_matrix = defaultdict(lambda: defaultdict(int))
    misclassified_images = []
    low_confidence_predictions = []

    total_test_images = 0
    total_top1_correct = 0
    total_top5_correct = 0

    for pid in active_pids:
        test_files = test_images_by_pid[pid]
        for img_path in test_files:
            total_test_images += 1
            query_vec = extract_image_embedding(str(img_path))
            if query_vec is None:
                print(f"[WARNING] Skipping unreadable image: {img_path.name}")
                continue

            # Cosine similarity vector dot product against precomputed centroids
            sims = np.dot(centroids_mat, query_vec)
            top_indices = np.argsort(sims)[::-1][:5]

            top5_pids = [pid_index_map[idx] for idx in top_indices]
            top1_pid = top5_pids[0]
            top1_score = float(sims[top_indices[0]])
            top1_pct = round(top1_score * 100, 1)

            is_top1_correct = (top1_pid == pid)
            is_top5_correct = (pid in top5_pids)
            is_low_confidence = (top1_pct < 60.0)

            if is_top1_correct:
                total_top1_correct += 1
                per_product_stats[pid]['top1_correct'] += 1

            if is_top5_correct:
                total_top5_correct += 1
                per_product_stats[pid]['top5_correct'] += 1

            if is_low_confidence:
                per_product_stats[pid]['low_confidence'] += 1

            per_product_stats[pid]['total'] += 1
            confusion_matrix[pid][top1_pid] += 1

            # Format top 5 matching results
            top5_summary = "; ".join([
                f"Rank #{r+1}: {pid_index_map[idx]} ({round(float(sims[idx])*100, 1)}%)"
                for r, idx in enumerate(top_indices)
            ])

            record = {
                'image_filename': img_path.name,
                'rel_path': str(img_path.relative_to(BASE_DIR)).replace('\\', '/'),
                'actual_product_id': pid,
                'actual_brand': product_catalog[pid]['brand'],
                'actual_product_name': product_catalog[pid]['product_name'],
                'actual_category': product_catalog[pid]['category'],
                'predicted_top1_product_id': top1_pid,
                'predicted_top1_brand': product_catalog[top1_pid]['brand'],
                'predicted_top1_product_name': product_catalog[top1_pid]['product_name'],
                'top1_similarity_score': round(top1_score, 4),
                'top1_similarity_percentage': top1_pct,
                'top1_result': "CORRECT" if is_top1_correct else "INCORRECT",
                'top5_result': "CORRECT" if is_top5_correct else "INCORRECT",
                'top5_predictions': top5_summary
            }
            test_results.append(record)

            if not is_top1_correct:
                misclassified_images.append(record)

            if is_low_confidence or not is_top1_correct:
                low_confidence_predictions.append(record)

    top1_accuracy = round((total_top1_correct / total_test_images) * 100, 2) if total_test_images > 0 else 0.0
    top5_accuracy = round((total_top5_correct / total_test_images) * 100, 2) if total_test_images > 0 else 0.0
    total_incorrect = total_test_images - total_top1_correct

    elapsed_sec = round(time.time() - start_time, 2)

    # 5. Output 1: Save Detailed CSV Results File
    fieldnames = [
        'image_filename', 'rel_path', 'actual_product_id', 'actual_brand', 'actual_product_name', 'actual_category',
        'predicted_top1_product_id', 'predicted_top1_brand', 'predicted_top1_product_name',
        'top1_similarity_score', 'top1_similarity_percentage', 'top1_result', 'top5_result', 'top5_predictions'
    ]

    with open(CSV_OUT, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(test_results)
    print(f"\nSaved detailed per-image evaluation results to: {CSV_OUT}")

    # 6. Build Confusion Matrix Dict & Top Confusion Pairs
    conf_matrix_dict = {}
    top_confusion_pairs = []
    for actual_pid in active_pids:
        conf_matrix_dict[actual_pid] = {}
        for pred_pid in active_pids:
            cnt = confusion_matrix[actual_pid][pred_pid]
            conf_matrix_dict[actual_pid][pred_pid] = cnt
            if actual_pid != pred_pid and cnt > 0:
                top_confusion_pairs.append({
                    'actual_product_id': actual_pid,
                    'actual_brand': product_catalog[actual_pid]['brand'],
                    'actual_product_name': product_catalog[actual_pid]['product_name'],
                    'predicted_product_id': pred_pid,
                    'predicted_brand': product_catalog[pred_pid]['brand'],
                    'predicted_product_name': product_catalog[pred_pid]['product_name'],
                    'misclassified_count': cnt
                })

    top_confusion_pairs.sort(key=lambda x: x['misclassified_count'], reverse=True)

    # 7. Output 2: Save JSON Summary File
    per_product_json = {}
    for pid in active_pids:
        st = per_product_stats[pid]
        acc1 = round((st['top1_correct'] / st['total']) * 100, 1) if st['total'] > 0 else 0.0
        acc5 = round((st['top5_correct'] / st['total']) * 100, 1) if st['total'] > 0 else 0.0
        per_product_json[pid] = {
            'brand': product_catalog[pid]['brand'],
            'product_name': product_catalog[pid]['product_name'],
            'category': product_catalog[pid]['category'],
            'test_images_count': st['total'],
            'top1_correct': st['top1_correct'],
            'top1_incorrect': st['total'] - st['top1_correct'],
            'top1_accuracy_pct': acc1,
            'top5_correct': st['top5_correct'],
            'top5_accuracy_pct': acc5,
            'low_confidence_count': st['low_confidence']
        }

    summary_json = {
        'eval_timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
        'eval_dataset': "data/image_model_dataset",
        'model_name': "OpenAI CLIP ViT-B/32 Vision Transformer (Hugging Face)",
        'evaluation_type': "Authentic Product Visual Identification (P001 - P030)",
        'dataset_scope_note': "Evaluates product identification accuracy across authentic product catalog folders. Counterfeit detection requires paired authentic vs. fake samples and cannot be independently validated on authentic-only data.",
        'split_ratio': "70% Reference / 30% Reserved Test (Zero Data Leakage)",
        'random_seed': 42,
        'total_product_classes': len(active_pids),
        'missing_or_empty_folders': missing_or_empty_folders,
        'missing_product_ids': missing_pids,
        'total_scanned_dataset_images': total_scanned_images,
        'total_reference_images': sum(len(v) for v in reference_images_by_pid.values()),
        'total_test_images': total_test_images,
        'previous_baseline': {
            'top1_accuracy_pct': 9.84,
            'top5_accuracy_pct': 29.34,
            'feature_pipeline': "Handcrafted HSV Color + Sobel Edge Histograms"
        },
        'top1_correct_count': total_top1_correct,
        'top1_incorrect_count': total_incorrect,
        'top1_accuracy_pct': top1_accuracy,
        'top5_correct_count': total_top5_correct,
        'top5_accuracy_pct': top5_accuracy,
        'total_misclassified_images': len(misclassified_images),
        'total_low_confidence_predictions': len(low_confidence_predictions),
        'execution_time_seconds': elapsed_sec,
        'per_product_breakdown': per_product_json,
        'top_confusion_pairs': top_confusion_pairs[:15],
        'confusion_matrix': conf_matrix_dict
    }

    with open(JSON_OUT, mode='w', encoding='utf-8') as f:
        json.dump(summary_json, f, indent=2)
    print(f"Saved machine-readable metric summary to: {JSON_OUT}")

    # 8. Output 3: Save Markdown Report File
    md_lines = [
        "# Genuine OpenAI CLIP ViT-B/32 Product Visual Identification Accuracy Report",
        "",
        f"**Evaluation Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"**Model Engine**: OpenAI CLIP ViT-B/32 (`openai/clip-vit-base-patch32`)  ",
        f"**Dataset Location**: `data/image_model_dataset/`  ",
        f"**Evaluation Scope**: Authentic cosmetic product visual matching across catalog products `P001` through `P030`.  ",
        "",
        "> [!IMPORTANT]",
        "> **Model Upgrade**: Replaced handcrafted HSV color + Sobel gradient histograms with genuine pretrained OpenAI CLIP ViT-B/32 Vision Transformer embeddings (512-dim).",
        "",
        "## Baseline vs. OpenAI CLIP ViT-B/32 Comparison",
        "",
        "| Metric | Previous Handcrafted Baseline | Genuine OpenAI CLIP ViT-B/32 | Improvement |",
        "| :--- | :---: | :---: | :---: |",
        f"| **Top-1 Accuracy** | 9.84% (60/610) | **{top1_accuracy}%** ({total_top1_correct}/{total_test_images}) | **+{round(top1_accuracy - 9.84, 2)}%** |",
        f"| **Top-5 Accuracy** | 29.34% (179/610) | **{top5_accuracy}%** ({total_top5_correct}/{total_test_images}) | **+{round(top5_accuracy - 29.34, 2)}%** |",
        f"| **Misclassified Test Items** | 550 / 610 | **{total_incorrect}** / {total_test_images} | **-{550 - total_incorrect} errors** |",
        "",
        "---",
        "",
        "## Summary Metrics",
        "",
        "| Metric | Value |",
        "| :--- | :--- |",
        f"| **Target Product Classes** | {len(active_pids)} products (`P001` - `P030`) |",
        f"| **Total Scanned Dataset Images** | {total_scanned_images} images |",
        f"| **Reference Index Set (70%)** | {sum(len(v) for v in reference_images_by_pid.values())} images |",
        f"| **Reserved Test Query Set (30%)** | **{total_test_images}** images |",
        f"| **Top-1 Correct Predictions** | **{total_top1_correct}** / {total_test_images} |",
        f"| **Top-1 Incorrect Predictions** | **{total_incorrect}** / {total_test_images} |",
        f"| **Top-1 Accuracy** | **{top1_accuracy}%** |",
        f"| **Top-5 Correct Predictions** | **{total_top5_correct}** / {total_test_images} |",
        f"| **Top-5 Accuracy** | **{top5_accuracy}%** |",
        f"| **Low-Confidence / Misclassified Items** | **{len(low_confidence_predictions)}** images |",
        f"| **Evaluation Runtime** | {elapsed_sec} seconds |",
        "",
        "---",
        "",
        "## Per-Product Accuracy Breakdown",
        "",
        "| Product ID | Brand | Product Name | Category | Test Images | Top-1 Correct | Top-1 Accuracy | Top-5 Accuracy | Low-Conf Count |",
        "| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |"
    ]

    for pid in active_pids:
        st = per_product_stats[pid]
        acc1 = round((st['top1_correct'] / st['total']) * 100, 1) if st['total'] > 0 else 0.0
        acc5 = round((st['top5_correct'] / st['total']) * 100, 1) if st['total'] > 0 else 0.0
        b = product_catalog[pid]['brand']
        n = product_catalog[pid]['product_name']
        c = product_catalog[pid]['category']
        md_lines.append(f"| **{pid}** | {b} | {n} | {c} | {st['total']} | {st['top1_correct']} | **{acc1}%** | **{acc5}%** | {st['low_confidence']} |")

    md_lines.extend([
        "",
        "---",
        "",
        "## Top Product Misclassification Pairs (Confusion Matrix Summary)",
        "",
        "| Actual Product | Predicted (Confused) Product | Misclassified Count |",
        "| :--- | :--- | :---: |"
    ])

    if top_confusion_pairs:
        for pair in top_confusion_pairs[:10]:
            md_lines.append(f"| **{pair['actual_product_id']}** ({pair['actual_brand']} - {pair['actual_product_name']}) | **{pair['predicted_product_id']}** ({pair['predicted_brand']} - {pair['predicted_product_name']}) | {pair['misclassified_count']} |")
    else:
        md_lines.append("| *None* | *No misclassifications recorded* | 0 |")

    md_lines.extend([
        "",
        "---",
        "",
        "## Sample Test Predictions Log",
        "",
        "| Image File | Actual Product | Predicted Top-1 Product | Sim Score | Result |",
        "| :--- | :--- | :--- | :---: | :---: |"
    ])

    sample_items = test_results[:15]
    for res in sample_items:
        status_badge = "✅ CORRECT" if res['top1_result'] == "CORRECT" else "❌ INCORRECT"
        md_lines.append(f"| `{res['image_filename']}` | **{res['actual_product_id']}** ({res['actual_brand']}) | **{res['predicted_top1_product_id']}** ({res['predicted_top1_brand']}) | {res['top1_similarity_percentage']}% | {status_badge} |")

    md_lines.extend([
        "",
        "---",
        "",
        "## Methodology & Data Leakage Safeguards",
        "1. **Genuine Model**: `openai/clip-vit-base-patch32` loaded via PyTorch & Hugging Face `transformers`.",
        "2. **Stratified 70/30 Split**: Deterministic seed (`seed=42`) applied per product folder.",
        "3. **Zero Data Leakage**: Test images were strictly excluded from reference index centroid creation.",
        "4. **Matching Engine**: Cosine similarity dot product against precomputed 512-dim deep vision centroids."
    ])

    with open(MD_OUT, mode='w', encoding='utf-8') as f:
        f.write("\n".join(md_lines))
    print(f"Saved human-readable Markdown evaluation report to: {MD_OUT}\n")

    print("=" * 75)
    print(f"OPENAI CLIP ViT-B/32 EVALUATION COMPLETE!")
    print(f"  TOP-1 ACCURACY: {top1_accuracy}% ({total_top1_correct}/{total_test_images})")
    print(f"  TOP-5 ACCURACY: {top5_accuracy}% ({total_top5_correct}/{total_test_images})")
    print(f"  TOTAL MISCLASSIFIED TEST IMAGES: {total_incorrect}")
    print("=" * 75)

if __name__ == "__main__":
    run_evaluation()
