"""
Independent Verification Script:
1. Verifies reproduced accuracy on 557 genuine cosmetic test images.
2. Evaluates full 610-query untouched benchmark.
3. Evaluates non-cosmetic rejection performance on the 144 quarantined non-cosmetic images.
4. Generates per-product performance breakdowns and confusion analysis.
"""
import csv
import json
from collections import defaultdict, Counter
from pathlib import Path
import numpy as np
from sklearn.metrics import f1_score

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"

TEST_NPZ = DATA_DIR / "clip_test_embeddings.npz"
CLEANED_REF_NPZ = DATA_DIR / "clip_reference_embeddings_cleaned.npz"
OCR_CACHE_JSON = DATA_DIR / "ocr_test_cache.json"
MANIFEST_CSV = REPORTS_DIR / "quarantine_manifest.csv"
PRODUCTS_CSV = DATA_DIR / "selected_30_products_final.csv"


def main():
    print("=" * 80)
    print("INDEPENDENT REPRODUCIBILITY & NON-COSMETIC REJECTION VERIFICATION")
    print("=" * 80)

    # 1. Load catalog
    catalog = {}
    with open(PRODUCTS_CSV, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            pid = r["product_id"].strip()
            catalog[pid] = {
                "brand": r["brand"].strip().lower(),
                "name": r["product_name"].strip().lower(),
                "category": r["category"].strip(),
            }
    sorted_pids = sorted(list(catalog.keys()))

    # 2. Load test set
    test_data = np.load(TEST_NPZ)
    test_embs = test_data["embeddings"].astype(np.float32)
    test_pids = [str(p) for p in test_data["product_ids"]]
    test_paths = [str(p).replace("\\", "/") for p in test_data["rel_paths"]]

    # 3. Load manifest
    manifest_paths = set()
    manifest_by_action = defaultdict(list)
    if MANIFEST_CSV.exists():
        with open(MANIFEST_CSV, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                p = r["original_path"].replace("\\", "/")
                manifest_paths.add(p)
                manifest_by_action[r["action"]].append(p)

    valid_test_indices = [i for i, p in enumerate(test_paths) if p not in manifest_paths]
    quarantined_test_indices = [i for i, p in enumerate(test_paths) if p in manifest_paths]

    print(f"Total test queries:                 {len(test_paths)}")
    print(f"Genuine cosmetic test queries:      {len(valid_test_indices)}")
    print(f"Quarantined test artifacts:         {len(quarantined_test_indices)}")

    # 4. Load cleaned reference bank
    cleaned_ref = np.load(CLEANED_REF_NPZ)
    ref_embs = cleaned_ref["embeddings"].astype(np.float32)
    ref_pids = [str(p) for p in cleaned_ref["product_ids"]]

    pid_map = defaultdict(list)
    for idx, pid in enumerate(ref_pids):
        pid_map[pid].append(idx)

    # 5. Load OCR cache
    with open(OCR_CACHE_JSON, "r", encoding="utf-8") as f:
        raw_ocr = json.load(f)
        ocr_cache = {k.replace("\\", "/"): v for k, v in raw_ocr.items()}

    type_keywords = ['mascara', 'liner', 'lipstick', 'gloss', 'foundation', 'powder', 'concealer', 'bronzer', 'blush', 'shadow', 'pencil']

    def predict_image(q_emb, rel_p):
        dot_sims = np.dot(ref_embs, q_emb)
        sims = np.zeros(len(sorted_pids), dtype=np.float32)
        for idx, pid in enumerate(sorted_pids):
            idxs = pid_map.get(pid, [])
            sims[idx] = np.max(dot_sims[idxs]) if idxs else 0.0

        ocr_info = ocr_cache.get(rel_p, {})
        brand = ocr_info.get("brand_name", "").strip().lower()
        ocr_text = (ocr_info.get("product_name", "") + " " + brand).lower()

        raw_sims = sims.copy()
        for idx, pid in enumerate(sorted_pids):
            cat_b = catalog[pid]["brand"]
            cat_n = catalog[pid]["name"]
            boost = 0.0
            if brand and brand not in ["no text detected", "unknown brand", "unidentified product", ""]:
                if brand in cat_b or cat_b in brand:
                    boost += 0.08

            for kw in type_keywords:
                if kw in ocr_text and kw in cat_n:
                    boost += 0.03
                    break

            if boost > 0:
                sims[idx] = min(0.99, sims[idx] + boost)

        ranked_indices = np.argsort(sims)[::-1]
        ranked_pids = [sorted_pids[i] for i in ranked_indices]
        return ranked_pids, sims[ranked_indices], raw_sims

    # ---------------------------------------------------------
    # PART A: Valid Cosmetic Test Evaluation (557 images)
    # ---------------------------------------------------------
    correct_t1_val = 0
    correct_t5_val = 0
    y_true_val = []
    y_pred_val = []
    per_product_val = defaultdict(lambda: {"total": 0, "correct": 0})

    for i in valid_test_indices:
        q = test_embs[i]
        t_pid = test_pids[i]
        p_path = test_paths[i]

        ranked_pids, ranked_sims, _ = predict_image(q, p_path)
        pred_top1 = ranked_pids[0]

        y_true_val.append(t_pid)
        y_pred_val.append(pred_top1)

        per_product_val[t_pid]["total"] += 1
        if pred_top1 == t_pid:
            correct_t1_val += 1
            per_product_val[t_pid]["correct"] += 1
        if t_pid in ranked_pids[:5]:
            correct_t5_val += 1

    t1_acc_val = (correct_t1_val / len(valid_test_indices)) * 100.0
    t5_acc_val = (correct_t5_val / len(valid_test_indices)) * 100.0
    macro_f1_val = f1_score(y_true_val, y_pred_val, labels=sorted_pids, average="macro", zero_division=0) * 100.0
    weighted_f1_val = f1_score(y_true_val, y_pred_val, labels=sorted_pids, average="weighted", zero_division=0) * 100.0

    print("\n--- RESULTS ON 557 GENUINE COSMETIC PACKSHOTS ---")
    print(f"Top-1 Accuracy:     {t1_acc_val:.2f}% ({correct_t1_val}/{len(valid_test_indices)})")
    print(f"Top-5 Accuracy:     {t5_acc_val:.2f}% ({correct_t5_val}/{len(valid_test_indices)})")
    print(f"Macro F1-Score:     {macro_f1_val:.2f}%")
    print(f"Weighted F1-Score:  {weighted_f1_val:.2f}%")

    # ---------------------------------------------------------
    # PART B: Full Untouched Test Benchmark (610 images)
    # ---------------------------------------------------------
    correct_t1_full = 0
    correct_t5_full = 0
    y_true_full = []
    y_pred_full = []

    for i in range(len(test_paths)):
        q = test_embs[i]
        t_pid = test_pids[i]
        p_path = test_paths[i]

        ranked_pids, ranked_sims, _ = predict_image(q, p_path)
        pred_top1 = ranked_pids[0]

        y_true_full.append(t_pid)
        y_pred_full.append(pred_top1)

        if pred_top1 == t_pid:
            correct_t1_full += 1
        if t_pid in ranked_pids[:5]:
            correct_t5_full += 1

    t1_acc_full = (correct_t1_full / len(test_paths)) * 100.0
    t5_acc_full = (correct_t5_full / len(test_paths)) * 100.0
    macro_f1_full = f1_score(y_true_full, y_pred_full, labels=sorted_pids, average="macro", zero_division=0) * 100.0

    print("\n--- RESULTS ON FULL UNTOUCHED 610-QUERY BENCHMARK ---")
    print(f"Top-1 Accuracy:     {t1_acc_full:.2f}% ({correct_t1_full}/{len(test_paths)})")
    print(f"Top-5 Accuracy:     {t5_acc_full:.2f}% ({correct_t5_full}/{len(test_paths)})")
    print(f"Macro F1-Score:     {macro_f1_full:.2f}%")

    # ---------------------------------------------------------
    # PART C: Non-Cosmetic Rejection Analysis on 53 Quarantined Test Artifacts
    # ---------------------------------------------------------
    print("\n--- NON-COSMETIC REJECTION PERFORMANCE (53 QUARANTINED TEST ARTIFACTS) ---")
    non_cos_pids = []
    non_cos_sims = []
    non_cos_margins = []

    for i in quarantined_test_indices:
        q = test_embs[i]
        p_path = test_paths[i]
        ranked_pids, ranked_sims, _ = predict_image(q, p_path)
        non_cos_pids.append(ranked_pids[0])
        non_cos_sims.append(ranked_sims[0])
        margin = ranked_sims[0] - ranked_sims[1]
        non_cos_margins.append(margin)

    # In production clip_service: does any non-cosmetic get rejected?
    # No, because the pipeline has no Out-of-Scope / Non-Cosmetic detector!
    print(f"Number of non-cosmetic artifacts tested: {len(quarantined_test_indices)}")
    print(f"Number of non-cosmetic artifacts rejected: 0 (0.0% rejection rate)")
    print(f"All 53 non-cosmetics were assigned cosmetic product IDs!")
    print(f"Average similarity score for non-cosmetic artifacts: {np.mean(non_cos_sims)*100:.1f}%")
    print(f"Score range: min={np.min(non_cos_sims)*100:.1f}%, max={np.max(non_cos_sims)*100:.1f}%")
    print(f"Top assigned products to non-cosmetics: {Counter(non_cos_pids).most_common(5)}")

    # ---------------------------------------------------------
    # PART D: Per-Product Breakdown
    # ---------------------------------------------------------
    print("\n--- PER-PRODUCT ACCURACY BREAKDOWN (557 Genuine Cosmetics) ---")
    for pid in sorted_pids:
        d = per_product_val[pid]
        tot = d["total"]
        cor = d["correct"]
        pct = (cor / tot * 100.0) if tot > 0 else 0.0
        print(f"  {pid} ({catalog[pid]['brand']} - {catalog[pid]['name'][:28]:<28}): {pct:>5.1f}% ({cor}/{tot})")

    # Save verification JSON
    verification_output = {
        "valid_cosmetic_queries": len(valid_test_indices),
        "valid_cosmetic_top1_acc": round(t1_acc_val, 2),
        "valid_cosmetic_top5_acc": round(t5_acc_val, 2),
        "valid_cosmetic_macro_f1": round(macro_f1_val, 2),
        "full_benchmark_queries": len(test_paths),
        "full_benchmark_top1_acc": round(t1_acc_full, 2),
        "full_benchmark_top5_acc": round(t5_acc_full, 2),
        "full_benchmark_macro_f1": round(macro_f1_full, 2),
        "quarantined_test_count": len(quarantined_test_indices),
        "non_cosmetic_rejection_rate": 0.0,
        "mean_non_cosmetic_similarity_pct": round(float(np.mean(non_cos_sims) * 100), 2),
    }

    with open(REPORTS_DIR / "verification_reproduced_metrics.json", "w", encoding="utf-8") as f:
        json.dump(verification_output, f, indent=2)
    print(f"\nSaved verification metrics to reports/verification_reproduced_metrics.json")


if __name__ == "__main__":
    main()
