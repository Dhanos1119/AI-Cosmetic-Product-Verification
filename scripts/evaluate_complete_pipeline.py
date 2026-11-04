"""
Task 6 Evaluation Script:
Evaluates the complete end-to-end pipeline:
1. Non-cosmetic screening gate performance on 53 quarantined test artifacts
2. False rejection rate on 557 genuine cosmetic test queries
3. Genuine cosmetic Top-1, Top-5 accuracy and Macro F1
4. Per-product breakdown across all 30 products
5. Per-query inference latency benchmark
"""
import csv
import json
import time
from collections import defaultdict, Counter
from pathlib import Path
import numpy as np
from sklearn.metrics import f1_score
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"

TEST_NPZ = DATA_DIR / "clip_test_embeddings.npz"
CLEANED_REF_NPZ = DATA_DIR / "clip_reference_embeddings_cleaned.npz"
MANIFEST_CSV = REPORTS_DIR / "quarantine_manifest.csv"
PRODUCTS_CSV = DATA_DIR / "selected_30_products_final.csv"
OCR_CACHE_JSON = DATA_DIR / "ocr_test_cache.json"

import sys
sys.path.append(str(BASE_DIR / "ai-service"))
from app.services.clip_service import screen_cosmetic_image, _get_screening_text_features

def main():
    print("=" * 80)
    print("TASK 6: END-TO-END PIPELINE SCREENING AND ACCURACY VERIFICATION")
    print("=" * 80)

    # 1. Load Catalog
    catalog = {}
    with open(PRODUCTS_CSV, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            pid = r["product_id"].strip()
            catalog[pid] = {
                "brand": r["brand"].strip(),
                "name": r["product_name"].strip(),
                "category": r["category"].strip(),
            }
    sorted_pids = sorted(list(catalog.keys()))

    # 2. Load Reference Bank
    cleaned_ref = np.load(CLEANED_REF_NPZ)
    ref_embs = cleaned_ref["embeddings"].astype(np.float32)
    ref_pids = [str(p) for p in cleaned_ref["product_ids"]]
    pid_indices = defaultdict(list)
    for idx, pid in enumerate(ref_pids):
        pid_indices[pid].append(idx)

    # 3. Load Test Embeddings and Metadata
    test_data = np.load(TEST_NPZ)
    test_embs = test_data["embeddings"].astype(np.float32)
    test_pids = [str(p) for p in test_data["product_ids"]]
    test_paths = [str(p).replace("\\", "/") for p in test_data["rel_paths"]]

    # 4. Load Quarantine Manifest
    manifest_paths = set()
    if MANIFEST_CSV.exists():
        with open(MANIFEST_CSV, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                manifest_paths.add(r["original_path"].replace("\\", "/"))

    valid_indices = [i for i, p in enumerate(test_paths) if p not in manifest_paths]
    quarantined_indices = [i for i, p in enumerate(test_paths) if p in manifest_paths]

    # 5. Load OCR Cache
    with open(OCR_CACHE_JSON, "r", encoding="utf-8") as f:
        raw_ocr = json.load(f)
        ocr_cache = {k.replace("\\", "/"): v for k, v in raw_ocr.items()}

    print(f"Genuine Cosmetic Test Packshots:  {len(valid_indices)}")
    print(f"Quarantined Non-Cosmetic Artifacts: {len(quarantined_indices)}")

    # -------------------------------------------------------------
    # PART A: Evaluate Non-Cosmetic Screening on 53 Quarantined Artifacts
    # -------------------------------------------------------------
    print("\n--- EVALUATING SCREENING GATE ON NON-COSMETIC ARTIFACTS ---")
    rejected_count = 0
    ambiguous_count = 0
    passed_non_cosmetic = 0

    non_cos_latencies = []
    for i in quarantined_indices:
        q_vec = test_embs[i]
        rel_p = test_paths[i]
        ocr_item = ocr_cache.get(rel_p, {})
        detected_brand = ocr_item.get("brand_name", "")

        t0 = time.perf_counter()
        ref_sims = np.dot(ref_embs, q_vec)
        cat_sim = float(np.max(ref_sims))
        screen_res = screen_cosmetic_image(q_vec, cat_sim, detected_brand)
        t1 = time.perf_counter()
        non_cos_latencies.append((t1 - t0) * 1000.0)

        if screen_res.get("status") == "rejected_non_cosmetic":
            rejected_count += 1
        elif screen_res.get("status") == "ambiguous_input":
            ambiguous_count += 1
        else:
            passed_non_cosmetic += 1

    strict_rejection_rate = (rejected_count / len(quarantined_indices)) * 100.0
    controlled_rejection_rate = ((rejected_count + ambiguous_count) / len(quarantined_indices)) * 100.0
    print(f"Strict Rejection Rate (rejected_non_cosmetic): {strict_rejection_rate:.2f}% ({rejected_count}/{len(quarantined_indices)})")
    print(f"Ambiguous / Flagged Rate:                     {(ambiguous_count / len(quarantined_indices)) * 100.0:.2f}% ({ambiguous_count}/{len(quarantined_indices)})")
    print(f"Total Controlled Interception Rate:           {controlled_rejection_rate:.2f}% ({rejected_count + ambiguous_count}/{len(quarantined_indices)})")
    print(f"False Acceptance Rate (passed non-cosmetic):  {(passed_non_cosmetic / len(quarantined_indices)) * 100.0:.2f}% ({passed_non_cosmetic}/{len(quarantined_indices)})")

    # -------------------------------------------------------------
    # PART B: False Rejection & Product ID Accuracy on 557 Genuine Packshots
    # -------------------------------------------------------------
    print("\n--- EVALUATING GENUINE COSMETICS (ACCURACY & FALSE REJECTION) ---")
    false_rejections = 0
    ambiguous_genuine = 0
    correct_t1 = 0
    correct_t5 = 0
    y_true = []
    y_pred = []
    product_stats = defaultdict(lambda: {"total": 0, "correct": 0, "rejected": 0})
    category_stats = defaultdict(lambda: {"total": 0, "correct": 0})

    genuine_latencies = []

    type_keywords = ['mascara', 'liner', 'lipstick', 'gloss', 'foundation', 'powder', 'concealer', 'bronzer', 'blush', 'shadow', 'pencil']

    for i in valid_indices:
        q_vec = test_embs[i]
        t_pid = test_pids[i]
        rel_p = test_paths[i]
        ocr_item = ocr_cache.get(rel_p, {})
        detected_brand = ocr_item.get("brand_name", "").strip().lower()
        ocr_text = (ocr_item.get("product_name", "") + " " + detected_brand).lower()

        t0 = time.perf_counter()
        # 1-NN similarity
        ref_sims = np.dot(ref_embs, q_vec)
        raw_sims = np.zeros(len(sorted_pids), dtype=np.float32)
        for idx, pid in enumerate(sorted_pids):
            idxs = pid_indices.get(pid, [])
            raw_sims[idx] = float(np.max(ref_sims[idxs])) if idxs else 0.0

        cat_sim = float(np.max(raw_sims))
        screen_res = screen_cosmetic_image(q_vec, cat_sim, detected_brand)

        # Multi-evidence OCR boost
        sims = raw_sims.copy()
        for idx, pid in enumerate(sorted_pids):
            cat_b = catalog[pid]["brand"].lower()
            cat_n = catalog[pid]["name"].lower()
            boost = 0.0
            if detected_brand and detected_brand not in ["no text detected", "unknown brand", "unidentified product", ""]:
                if detected_brand in cat_b or cat_b in detected_brand:
                    boost += 0.08
            for kw in type_keywords:
                if kw in ocr_text and kw in cat_n:
                    boost += 0.03
                    break
            if boost > 0:
                sims[idx] = min(0.99, sims[idx] + boost)

        ranked_indices = np.argsort(sims)[::-1]
        ranked_pids = [sorted_pids[idx] for idx in ranked_indices]
        t1 = time.perf_counter()
        genuine_latencies.append((t1 - t0) * 1000.0)

        pred_top1 = ranked_pids[0]

        product_stats[t_pid]["total"] += 1
        cat_name = catalog[t_pid]["category"]
        category_stats[cat_name]["total"] += 1

        if screen_res.get("status") == "rejected_non_cosmetic":
            false_rejections += 1
            product_stats[t_pid]["rejected"] += 1
            # Still count for accuracy tracking
        elif screen_res.get("status") == "ambiguous_input":
            ambiguous_genuine += 1

        y_true.append(t_pid)
        y_pred.append(pred_top1)

        if pred_top1 == t_pid:
            correct_t1 += 1
            product_stats[t_pid]["correct"] += 1
            category_stats[cat_name]["correct"] += 1
        if t_pid in ranked_pids[:5]:
            correct_t5 += 1

    t1_acc = (correct_t1 / len(valid_indices)) * 100.0
    t5_acc = (correct_t5 / len(valid_indices)) * 100.0
    macro_f1 = f1_score(y_true, y_pred, labels=sorted_pids, average="macro", zero_division=0) * 100.0
    false_rejection_rate = (false_rejections / len(valid_indices)) * 100.0
    ambiguous_rate = (ambiguous_genuine / len(valid_indices)) * 100.0

    print(f"Genuine Top-1 Accuracy:            {t1_acc:.2f}% ({correct_t1}/{len(valid_indices)})")
    print(f"Genuine Top-5 Accuracy:            {t5_acc:.2f}% ({correct_t5}/{len(valid_indices)})")
    print(f"Macro F1-Score:                    {macro_f1:.2f}%")
    print(f"False Rejection Rate (genuine):    {false_rejection_rate:.2f}% ({false_rejections}/{len(valid_indices)})")
    print(f"Ambiguous Handling Rate (genuine): {ambiguous_rate:.2f}% ({ambiguous_genuine}/{len(valid_indices)})")
    print(f"Average Inference Latency:         {np.mean(genuine_latencies):.2f} ms (p95: {np.percentile(genuine_latencies, 95):.2f} ms)")

    print("\n--- CATEGORY BREAKDOWN ---")
    for cat, d in sorted(category_stats.items()):
        acc = (d["correct"] / d["total"] * 100.0) if d["total"] > 0 else 0.0
        print(f"  {cat:<18}: {acc:>5.2f}% ({d['correct']}/{d['total']})")

    print("\n--- PER-PRODUCT BREAKDOWN ---")
    for pid in sorted_pids:
        st = product_stats[pid]
        acc = (st["correct"] / st["total"] * 100.0) if st["total"] > 0 else 0.0
        rej = st["rejected"]
        print(f"  {pid} ({catalog[pid]['brand'][:12]:<12} - {catalog[pid]['name'][:24]:<24}): {acc:>5.1f}% ({st['correct']}/{st['total']}) [FR: {rej}]")

    summary_data = {
        "genuine_queries": len(valid_indices),
        "quarantined_artifacts": len(quarantined_indices),
        "genuine_top1_acc": round(t1_acc, 2),
        "genuine_top5_acc": round(t5_acc, 2),
        "macro_f1": round(macro_f1, 2),
        "strict_non_cosmetic_rejection_rate": round(strict_rejection_rate, 2),
        "controlled_interception_rate": round(controlled_rejection_rate, 2),
        "false_rejection_rate": round(false_rejection_rate, 2),
        "avg_latency_ms": round(float(np.mean(genuine_latencies)), 2),
        "p95_latency_ms": round(float(np.percentile(genuine_latencies, 95)), 2),
        "category_performance": {cat: round((d["correct"]/d["total"]*100.0), 2) for cat, d in category_stats.items()}
    }

    with open(REPORTS_DIR / "complete_pipeline_evaluation.json", "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
    print(f"\nSaved pipeline evaluation report to reports/complete_pipeline_evaluation.json")

if __name__ == "__main__":
    main()
