"""
CLIP Confidence Threshold Calibration Script
Empirically tests CLIP cosine similarity scores across:
1. Authentic catalog test set images (610 reserved test query images)
2. Synthetic non-catalog images (Solid white, solid black, Gaussian noise, random color patches, simple shapes)

Calculates precision, recall, false positive rate (FPR), and coverage for candidate thresholds.
"""

import sys
import io
import csv
import json
import random
import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.resolve()
AI_SERVICE_DIR = BASE_DIR / "ai-service"
DATASET_DIR = BASE_DIR / "data" / "image_model_dataset"
CSV_PRODUCTS = BASE_DIR / "data" / "selected_30_products_final.csv"

if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

from app.services.clip_service import extract_image_embedding, _extract_image_file_embedding, _load_or_build_product_index


def generate_synthetic_non_catalog_images():
    """Generates synthetic non-catalog benchmark images."""
    imgs = {}
    
    # 1. Solid White
    img_white = Image.new("RGB", (300, 300), color=(255, 255, 255))
    imgs["solid_white.jpg"] = img_white

    # 2. Solid Black
    img_black = Image.new("RGB", (300, 300), color=(0, 0, 0))
    imgs["solid_black.jpg"] = img_black

    # 3. Random Gaussian Noise
    noise_arr = np.random.randint(0, 256, (300, 300, 3), dtype=np.uint8)
    imgs["gaussian_noise.jpg"] = Image.fromarray(noise_arr)

    # 4. Geometric Checkerboard Pattern
    arr_check = np.zeros((300, 300, 3), dtype=np.uint8)
    for r in range(0, 300, 30):
        for c in range(0, 300, 30):
            if (r // 30 + c // 30) % 2 == 0:
                arr_check[r:r+30, c:c+30] = [255, 255, 255]
    imgs["checkerboard.jpg"] = Image.fromarray(arr_check)

    # 5. Non-Cosmetic Object Drawing (e.g. Red Stop Sign Shape)
    img_shape = Image.new("RGB", (300, 300), color=(240, 240, 240))
    draw = ImageDraw.Draw(img_shape)
    draw.polygon([(100, 30), (200, 30), (270, 100), (270, 200), (200, 270), (100, 270), (30, 200), (30, 100)], fill=(200, 30, 30))
    draw.text((100, 140), "STOP", fill=(255, 255, 255))
    imgs["stop_sign.jpg"] = img_shape

    return imgs


def run_threshold_calibration():
    print("=" * 80)
    print("CLIP CONFIDENCE THRESHOLD CALIBRATION INVESTIGATION")
    print("=" * 80)

    (pids, product_catalog), centroids_mat = _load_or_build_product_index()
    print(f"Loaded {centroids_mat.shape[0]} catalog product centroids (dimension {centroids_mat.shape[1]}).\n")

    # 1. Test Synthetic Non-Catalog Images
    print("--- 1. Non-Catalog / Synthetic Image Cosine Similarities ---")
    non_catalog_images = generate_synthetic_non_catalog_images()
    non_catalog_results = []

    for name, img in non_catalog_images.items():
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        vec = extract_image_embedding(buf.getvalue())
        sims = np.dot(centroids_mat, vec)
        top_idx = int(np.argmax(sims))
        top_pid = pids[top_idx]
        top_score = float(sims[top_idx])
        top_pct = round(top_score * 100, 1)

        info = product_catalog[top_pid]
        print(f"  Non-Catalog '{name}': Max Sim = {top_score:.4f} ({top_pct}%) -> Matched {top_pid} ({info['brand']} - {info['product_name']})")
        non_catalog_results.append({
            "image_name": name,
            "matched_pid": top_pid,
            "matched_brand": info['brand'],
            "matched_name": info['product_name'],
            "similarity_score": round(top_score, 4),
            "similarity_percentage": top_pct
        })

    # 2. Test Reserved 30% Catalog Test Set (610 images)
    print("\n--- 2. Reserved 30% Catalog Test Set Analysis (610 Query Images) ---")
    random.seed(42)
    test_scores_correct = []
    test_scores_incorrect = []

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

            shuffled = imgs.copy()
            random.shuffle(shuffled)
            ref_count = max(1, int(len(imgs) * 0.70))
            test_set = shuffled[ref_count:]

            for img_path in test_set:
                vec = _extract_image_file_embedding(str(img_path))
                if vec is None:
                    continue
                sims = np.dot(centroids_mat, vec)
                top_idx = int(np.argmax(sims))
                pred_pid = pids[top_idx]
                score = float(sims[top_idx])

                if pred_pid == pid:
                    test_scores_correct.append(score)
                else:
                    test_scores_incorrect.append(score)

    print(f"Total Correct Predictions (Top-1): {len(test_scores_correct)}")
    print(f"Total Incorrect Predictions (Misclassified): {len(test_scores_incorrect)}")

    # 3. Evaluate Threshold Candidates
    print("\n--- 3. Candidate Threshold Precision / Recall / Unknown Rate Trade-Offs ---")
    candidate_thresholds = [0.50, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85]
    
    print(f"{'Threshold':<10} | {'Accepted Correct':<18} | {'Accepted Incorrect':<19} | {'Precision (%)':<15} | {'Coverage (%)':<15} | {'UNKNOWN Rate (%)':<17}")
    print("-" * 105)

    all_scores = [(s, True) for s in test_scores_correct] + [(s, False) for s in test_scores_incorrect]
    total_queries = len(all_scores)

    threshold_tradeoffs = []

    for t in candidate_thresholds:
        acc_correct = sum(1 for s, is_c in all_scores if is_c and s >= t)
        acc_incorrect = sum(1 for s, is_c in all_scores if not is_c and s >= t)
        accepted_total = acc_correct + acc_incorrect
        unknown_total = total_queries - accepted_total

        precision = round((acc_correct / accepted_total) * 100, 2) if accepted_total > 0 else 0.0
        coverage = round((accepted_total / total_queries) * 100, 2)
        unknown_rate = round((unknown_total / total_queries) * 100, 2)

        print(f"{t:<10.2f} | {acc_correct:<18} | {acc_incorrect:<19} | {precision:<15.2f} | {coverage:<15.2f} | {unknown_rate:<17.2f}")

        threshold_tradeoffs.append({
            "threshold_score": t,
            "threshold_pct": round(t * 100, 1),
            "accepted_correct_count": acc_correct,
            "accepted_incorrect_count": acc_incorrect,
            "accepted_total": accepted_total,
            "unknown_count": unknown_total,
            "precision_pct": precision,
            "coverage_pct": coverage,
            "unknown_rate_pct": unknown_rate
        })

    print("-" * 105)


if __name__ == "__main__":
    run_threshold_calibration()
