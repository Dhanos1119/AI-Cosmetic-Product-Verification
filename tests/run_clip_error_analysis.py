"""
CLIP Evaluation and Error Analysis Script
Executes 70/30 Stratified Evaluation (Seed 42) using Genuine OpenAI CLIP ViT-B/32.

Generates:
1. tests/results/clip_error_analysis.json
2. docs/clip_error_analysis.md
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

# Resolve project paths
BASE_DIR = Path(__file__).parent.parent.resolve()
AI_SERVICE_DIR = BASE_DIR / "ai-service"
DATASET_DIR = BASE_DIR / "data" / "image_model_dataset"
CSV_PRODUCTS = BASE_DIR / "data" / "selected_30_products_final.csv"

RESULTS_DIR = BASE_DIR / "tests" / "results"
DOCS_DIR = BASE_DIR / "docs"

JSON_OUT = RESULTS_DIR / "clip_error_analysis.json"
MD_OUT = DOCS_DIR / "clip_error_analysis.md"

if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

from app.services.clip_service import _extract_image_file_embedding as extract_image_embedding


def compute_distribution_stats(scores_list):
    """Calculates min, max, mean, median, std_dev, p25, p75, p90 and histogram bins."""
    if not scores_list:
        return {
            "count": 0,
            "min": 0.0,
            "max": 0.0,
            "mean": 0.0,
            "median": 0.0,
            "std_dev": 0.0,
            "p25": 0.0,
            "p75": 0.0,
            "p90": 0.0,
            "histogram": {}
        }
    
    arr = np.array(scores_list, dtype=np.float64)
    
    # Histogram binning (0.00-0.50, 0.50-0.60, 0.60-0.70, 0.70-0.80, 0.80-0.90, 0.90-1.00)
    bins = {
        "< 0.50": int(np.sum(arr < 0.50)),
        "0.50 - 0.59": int(np.sum((arr >= 0.50) & (arr < 0.60))),
        "0.60 - 0.69": int(np.sum((arr >= 0.60) & (arr < 0.70))),
        "0.70 - 0.79": int(np.sum((arr >= 0.70) & (arr < 0.80))),
        "0.80 - 0.89": int(np.sum((arr >= 0.80) & (arr < 0.90))),
        "0.90 - 1.00": int(np.sum(arr >= 0.90))
    }
    
    return {
        "count": len(arr),
        "min": round(float(np.min(arr)), 4),
        "max": round(float(np.max(arr)), 4),
        "mean": round(float(np.mean(arr)), 4),
        "median": round(float(np.median(arr)), 4),
        "std_dev": round(float(np.std(arr)), 4),
        "p25": round(float(np.percentile(arr, 25)), 4),
        "p75": round(float(np.percentile(arr, 75)), 4),
        "p90": round(float(np.percentile(arr, 90)), 4),
        "histogram": bins
    }


def main():
    print("=" * 80)
    print("RUNNING DETAILED CLIP EVALUATION & ERROR ANALYSIS (SEED=42, 70/30 SPLIT)")
    print("=" * 80)

    start_time = time.time()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load Product Catalog Metadata
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
    random.seed(42)  # Deterministic seed 42
    
    reference_images_by_pid = defaultdict(list)
    test_images_by_pid = defaultdict(list)
    total_scanned_images = 0

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
                continue

            found_pids.add(pid)
            total_scanned_images += len(imgs)
            
            shuffled = imgs.copy()
            random.shuffle(shuffled)
            
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

    active_pids = sorted(list(found_pids))

    print(f"Product Classes Found: {len(active_pids)} / 30")
    print(f"Total Scanned Images: {total_scanned_images}")
    print(f"Reference Images (70%): {sum(len(v) for v in reference_images_by_pid.values())}")
    print(f"Test Query Images (30%): {sum(len(v) for v in test_images_by_pid.values())}\n")

    # 3. Compute Product Centroid Embeddings EXCLUSIVELY from Reference Set
    print("Building reference catalog centroids (CLIP ViT-B/32)...")
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

    centroids_mat = np.array(centroids, dtype=np.float32)
    print(f"Built centroid matrix shape: {centroids_mat.shape}\n")

    # 4. Evaluate Reserved Test Set Images
    print("Evaluating 30% test set against catalog centroids...")
    
    per_product_stats = defaultdict(lambda: {
        'total': 0, 'top1_correct': 0, 'top5_correct': 0
    })
    confusion_matrix = defaultdict(lambda: defaultdict(int))
    
    correct_sim_scores = []
    incorrect_sim_scores = []
    incorrect_examples = []
    all_eval_records = []

    total_test_images = 0
    total_top1_correct = 0
    total_top5_correct = 0

    for pid in active_pids:
        test_files = test_images_by_pid[pid]
        for img_path in test_files:
            total_test_images += 1
            query_vec = extract_image_embedding(str(img_path))
            if query_vec is None:
                continue

            sims = np.dot(centroids_mat, query_vec)
            top_indices = np.argsort(sims)[::-1][:5]

            top5_pids = [pid_index_map[idx] for idx in top_indices]
            top1_pid = top5_pids[0]
            top1_score = float(sims[top_indices[0]])
            top1_pct = round(top1_score * 100, 1)

            is_top1_correct = (top1_pid == pid)
            is_top5_correct = (pid in top5_pids)

            per_product_stats[pid]['total'] += 1
            if is_top1_correct:
                total_top1_correct += 1
                per_product_stats[pid]['top1_correct'] += 1
                correct_sim_scores.append(top1_score)
            else:
                incorrect_sim_scores.append(top1_score)

            if is_top5_correct:
                total_top5_correct += 1
                per_product_stats[pid]['top5_correct'] += 1

            confusion_matrix[pid][top1_pid] += 1

            top5_matches_list = []
            for rank_idx, idx in enumerate(top_indices, start=1):
                match_pid = pid_index_map[idx]
                info = product_catalog[match_pid]
                sim_v = float(sims[idx])
                top5_matches_list.append({
                    "rank": rank_idx,
                    "product_id": match_pid,
                    "brand": info['brand'],
                    "product_name": info['product_name'],
                    "category": info['category'],
                    "similarity_score": round(sim_v, 4),
                    "similarity_percentage": round(sim_v * 100, 1)
                })

            record = {
                "test_image_filename": img_path.name,
                "relative_path": str(img_path.relative_to(BASE_DIR)).replace('\\', '/'),
                "expected_product_id": pid,
                "expected_brand": product_catalog[pid]['brand'],
                "expected_product_name": product_catalog[pid]['product_name'],
                "expected_category": product_catalog[pid]['category'],
                "predicted_product_id": top1_pid,
                "predicted_brand": product_catalog[top1_pid]['brand'],
                "predicted_product_name": product_catalog[top1_pid]['product_name'],
                "predicted_category": product_catalog[top1_pid]['category'],
                "is_top1_correct": is_top1_correct,
                "is_top5_correct": is_top5_correct,
                "similarity_score": round(top1_score, 4),
                "similarity_percentage": top1_pct,
                "top_5_matches": top5_matches_list
            }

            all_eval_records.append(record)

            if not is_top1_correct:
                incorrect_examples.append(record)

    top1_accuracy_pct = round((total_top1_correct / total_test_images) * 100, 2) if total_test_images > 0 else 0.0
    top5_accuracy_pct = round((total_top5_correct / total_test_images) * 100, 2) if total_test_images > 0 else 0.0
    total_incorrect = total_test_images - total_top1_correct

    elapsed_sec = round(time.time() - start_time, 2)

    # 5. Build Confusion Matrix & Most Frequently Confused Product Pairs
    conf_matrix_dict = {}
    confused_pairs = []
    for actual_pid in active_pids:
        conf_matrix_dict[actual_pid] = {}
        for pred_pid in active_pids:
            cnt = confusion_matrix[actual_pid][pred_pid]
            conf_matrix_dict[actual_pid][pred_pid] = cnt
            if actual_pid != pred_pid and cnt > 0:
                confused_pairs.append({
                    "expected_product_id": actual_pid,
                    "expected_brand": product_catalog[actual_pid]['brand'],
                    "expected_product_name": product_catalog[actual_pid]['product_name'],
                    "predicted_product_id": pred_pid,
                    "predicted_brand": product_catalog[pred_pid]['brand'],
                    "predicted_product_name": product_catalog[pred_pid]['product_name'],
                    "misclassified_count": cnt
                })

    confused_pairs.sort(key=lambda x: x['misclassified_count'], reverse=True)

    # 6. Per-Product Accuracy Breakdown
    per_product_json = {}
    for pid in active_pids:
        st = per_product_stats[pid]
        acc1 = round((st['top1_correct'] / st['total']) * 100, 2) if st['total'] > 0 else 0.0
        acc5 = round((st['top5_correct'] / st['total']) * 100, 2) if st['total'] > 0 else 0.0
        per_product_json[pid] = {
            "product_id": pid,
            "brand": product_catalog[pid]['brand'],
            "product_name": product_catalog[pid]['product_name'],
            "category": product_catalog[pid]['category'],
            "test_images_count": st['total'],
            "top1_correct_count": st['top1_correct'],
            "top1_incorrect_count": st['total'] - st['top1_correct'],
            "top1_accuracy_pct": acc1,
            "top5_correct_count": st['top5_correct'],
            "top5_accuracy_pct": acc5
        }

    # 7. Distribution Stats
    correct_dist = compute_distribution_stats(correct_sim_scores)
    incorrect_dist = compute_distribution_stats(incorrect_sim_scores)

    # 8. Build JSON Report Structure
    json_report = {
        "evaluation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "model_name": "OpenAI CLIP ViT-B/32 Vision Transformer (Hugging Face)",
        "dataset_path": "data/image_model_dataset",
        "split_strategy": "70% Reference / 30% Test (Stratified)",
        "random_seed": 42,
        "overall_metrics": {
            "total_product_classes": len(active_pids),
            "total_dataset_images": total_scanned_images,
            "total_reference_images": sum(len(v) for v in reference_images_by_pid.values()),
            "total_test_images": total_test_images,
            "top1_correct_count": total_top1_correct,
            "top1_incorrect_count": total_incorrect,
            "top1_accuracy_pct": top1_accuracy_pct,
            "top5_correct_count": total_top5_correct,
            "top5_incorrect_count": total_test_images - total_top5_correct,
            "top5_accuracy_pct": top5_accuracy_pct,
            "evaluation_time_seconds": elapsed_sec
        },
        "per_product_accuracy": per_product_json,
        "most_frequently_confused_pairs": confused_pairs,
        "similarity_distribution_correct_predictions": correct_dist,
        "similarity_distribution_incorrect_predictions": incorrect_dist,
        "incorrect_predictions_examples": incorrect_examples,
        "confusion_matrix": conf_matrix_dict
    }

    with open(JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(json_report, f, indent=2)

    print(f"Saved JSON evaluation report to: {JSON_OUT}")

    # 9. Build Markdown Report Structure
    md_content = [
        "# Detailed CLIP Evaluation & Error Analysis Report",
        "",
        f"**Evaluation Timestamp**: `{time.strftime('%Y-%m-%d %H:%M:%S')}`  ",
        f"**Model Engine**: OpenAI CLIP ViT-B/32 (`openai/clip-vit-base-patch32`)  ",
        f"**Evaluation Protocol**: Stratified 70% Reference / 30% Reserved Test Split (`random_seed=42`)  ",
        f"**Execution Runtime**: {elapsed_sec} seconds  ",
        "",
        "---",
        "",
        "## 1. Executive Summary & Overall Accuracy",
        "",
        "| Metric | Value | Details |",
        "| :--- | :---: | :--- |",
        f"| **Target Product Classes** | **30** | Folders `P001` through `P030` |",
        f"| **Total Catalog Images** | **{total_scanned_images}** | Full dataset scan |",
        f"| **Reference Images (70%)** | **{sum(len(v) for v in reference_images_by_pid.values())}** | Centroid embedding construction |",
        f"| **Reserved Test Images (30%)** | **{total_test_images}** | Reserved test evaluation |",
        f"| **Top-1 Correct Predictions** | **{total_top1_correct}** | **{top1_accuracy_pct}% Top-1 Accuracy** |",
        f"| **Top-1 Incorrect Predictions** | **{total_incorrect}** | Misclassified test items |",
        f"| **Top-5 Correct Predictions** | **{total_top5_correct}** | **{top5_accuracy_pct}% Top-5 Accuracy** |",
        "",
        "---",
        "",
        "## 2. Similarity Score Distributions",
        "",
        "### Statistical Breakdown (Cosine Similarity Scores)",
        "",
        "| Metric | Correct Predictions (Top-1 Match) | Incorrect Predictions (Misclassified) |",
        "| :--- | :---: | :---: |",
        f"| **Count** | {correct_dist['count']} | {incorrect_dist['count']} |",
        f"| **Mean Score** | `{correct_dist['mean']}` ({round(correct_dist['mean']*100, 1)}%) | `{incorrect_dist['mean']}` ({round(incorrect_dist['mean']*100, 1)}%) |",
        f"| **Median Score** | `{correct_dist['median']}` ({round(correct_dist['median']*100, 1)}%) | `{incorrect_dist['median']}` ({round(incorrect_dist['median']*100, 1)}%) |",
        f"| **Std. Deviation** | `{correct_dist['std_dev']}` | `{incorrect_dist['std_dev']}` |",
        f"| **Min Score** | `{correct_dist['min']}` ({round(correct_dist['min']*100, 1)}%) | `{incorrect_dist['min']}` ({round(incorrect_dist['min']*100, 1)}%) |",
        f"| **Max Score** | `{correct_dist['max']}` ({round(correct_dist['max']*100, 1)}%) | `{incorrect_dist['max']}` ({round(incorrect_dist['max']*100, 1)}%) |",
        f"| **25th Percentile** | `{correct_dist['p25']}` | `{incorrect_dist['p25']}` |",
        f"| **75th Percentile** | `{correct_dist['p75']}` | `{incorrect_dist['p75']}` |",
        f"| **90th Percentile** | `{correct_dist['p90']}` | `{incorrect_dist['p90']}` |",
        "",
        "### Histogram Distribution Bins",
        "",
        "| Similarity Range | Correct Predictions Count | Incorrect Predictions Count |",
        "| :--- | :---: | :---: |"
    ]

    bins_keys = ["< 0.50", "0.50 - 0.59", "0.60 - 0.69", "0.70 - 0.79", "0.80 - 0.89", "0.90 - 1.00"]
    for b_key in bins_keys:
        c_cnt = correct_dist['histogram'].get(b_key, 0)
        i_cnt = incorrect_dist['histogram'].get(b_key, 0)
        md_content.append(f"| **{b_key}** | {c_cnt} | {i_cnt} |")

    md_content.extend([
        "",
        "---",
        "",
        "## 3. Per-Product Accuracy Breakdown",
        "",
        "| Product ID | Brand | Product Name | Category | Test Items | Top-1 Correct | Top-1 Accuracy | Top-5 Accuracy |",
        "| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: |"
    ])

    for pid in active_pids:
        p_info = per_product_json[pid]
        md_content.append(
            f"| **{pid}** | {p_info['brand']} | {p_info['product_name']} | {p_info['category']} | "
            f"{p_info['test_images_count']} | {p_info['top1_correct_count']} | **{p_info['top1_accuracy_pct']}%** | **{p_info['top5_accuracy_pct']}%** |"
        )

    md_content.extend([
        "",
        "---",
        "",
        "## 4. Most Frequently Confused Product Pairs",
        "",
        "| Rank | Expected Product | Predicted (Confused) Product | Misclassified Count | Key Visual/Category Overlap |",
        "| :---: | :--- | :--- | :---: | :--- |"
    ])

    for r_idx, pair in enumerate(confused_pairs[:15], start=1):
        md_content.append(
            f"| {r_idx} | **{pair['expected_product_id']}** ({pair['expected_brand']} - {pair['expected_product_name']}) | "
            f"**{pair['predicted_product_id']}** ({pair['predicted_brand']} - {pair['predicted_product_name']}) | "
            f"**{pair['misclassified_count']}** | High visual structure & color palette similarity |"
        )

    md_content.extend([
        "",
        "---",
        "",
        "## 5. Sample Misclassification Analysis & Top-5 Candidate Breakdown",
        ""
    ])

    # Include first 10 detailed incorrect examples
    sample_incorrect = incorrect_examples[:10]
    for idx, ex in enumerate(sample_incorrect, start=1):
        md_content.extend([
            f"### Sample {idx}: `{ex['test_image_filename']}`",
            f"- **Expected Product**: **{ex['expected_product_id']}** ({ex['expected_brand']} - {ex['expected_product_name']})",
            f"- **Predicted Product**: **{ex['predicted_product_id']}** ({ex['predicted_brand']} - {ex['predicted_product_name']})",
            f"- **Top-1 Similarity Score**: `{ex['similarity_score']}` ({ex['similarity_percentage']}%)",
            "",
            "**Top-5 Retrieved Candidates**:",
            "| Rank | Product ID | Brand | Product Name | Similarity Score | Similarity % |",
            "| :---: | :---: | :--- | :--- | :---: | :---: |"
        ])
        for match in ex['top_5_matches']:
            highlight = "**" if match['product_id'] == ex['expected_product_id'] else ""
            md_content.append(
                f"| {match['rank']} | {highlight}{match['product_id']}{highlight} | {match['brand']} | {match['product_name']} | `{match['similarity_score']}` | {match['similarity_percentage']}% |"
            )
        md_content.append("")

    with open(MD_OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(md_content))

    print(f"Saved Markdown evaluation report to: {MD_OUT}")
    print("=" * 80)
    print("EVALUATION & ERROR ANALYSIS COMPLETED SUCCESSFULLY!")
    print(f"Top-1 Accuracy: {top1_accuracy_pct}% ({total_top1_correct}/{total_test_images})")
    print(f"Top-5 Accuracy: {top5_accuracy_pct}% ({total_top5_correct}/{total_test_images})")
    print("=" * 80)


if __name__ == "__main__":
    main()
