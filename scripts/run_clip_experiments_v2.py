"""
Phase 6: Comprehensive Controlled CLIP Accuracy Experiments
Evaluates candidate architectures on the fixed, untouched 610-image test set:
- Method 1: Original Single-Centroid Baseline (Noisy Ref Bank)
- Method 2: Cleaned Single-Centroid Baseline
- Method 3: Original 1-NN Reference Bank (Noisy Ref Bank)
- Method 4: Cleaned 1-NN Reference Bank (Purged 92 non-cosmetic artifacts)
- Method 5: Cleaned 3-NN Reference Bank (Top-3 Cosine Similarity Average)
- Method 6: Cleaned K-Means Multi-Prototypes (k=3 per class)
- Method 7: Cleaned + Augmented 1-NN Reference Bank (Balanced sparse classes + diverse packshot views)
- Method 8: Cleaned 1-NN + OCR Brand Boost
- Method 9: Cleaned + Augmented 1-NN + Tuned OCR Brand & Title Matching (Target Architecture)

Generates:
- reports/clip_baseline_metrics.json
- reports/clip_experiment_comparison.csv
- reports/clip_experiment_confusion_matrices.json
"""
import csv
import json
import time
from collections import defaultdict
from pathlib import Path
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import f1_score, confusion_matrix

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"

TEST_NPZ = DATA_DIR / "clip_test_embeddings.npz"
ORIG_REF_NPZ = DATA_DIR / "clip_reference_embeddings.npz"
CLEANED_REF_NPZ = DATA_DIR / "clip_reference_embeddings_cleaned.npz"
AUG_REF_NPZ = DATA_DIR / "clip_reference_embeddings_augmented_combined.npz"
OCR_CACHE_JSON = DATA_DIR / "ocr_test_cache.json"
PRODUCTS_CSV = DATA_DIR / "selected_30_products_final.csv"

OUTPUT_METRICS_JSON = REPORTS_DIR / "clip_baseline_metrics.json"
OUTPUT_COMPARISON_CSV = REPORTS_DIR / "clip_experiment_comparison.csv"
OUTPUT_CONFUSION_JSON = REPORTS_DIR / "clip_experiment_confusion_matrices.json"


def load_catalog():
    catalog = {}
    with open(PRODUCTS_CSV, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            pid = r["product_id"].strip()
            catalog[pid] = {
                "product_id": pid,
                "brand": r["brand"].strip().lower(),
                "product_name": r["product_name"].strip().lower(),
                "category": r["category"].strip(),
                "product_type": r.get("product_type", r["category"]).strip(),
            }
    return catalog


def build_centroids(pids, embeddings, sorted_pids):
    by_pid = defaultdict(list)
    for p, e in zip(pids, embeddings):
        by_pid[p].append(e)
    centroids = []
    for p in sorted_pids:
        vecs = by_pid.get(p, [])
        if vecs:
            c = np.mean(vecs, axis=0)
            c = c / np.linalg.norm(c)
        else:
            c = np.zeros(512, dtype=np.float32)
        centroids.append(c)
    return np.array(centroids, dtype=np.float32)


def build_kmeans_prototypes(pids, embeddings, sorted_pids, k=3):
    by_pid = defaultdict(list)
    for p, e in zip(pids, embeddings):
        by_pid[p].append(e)
    proto_vecs = []
    proto_pids = []
    for p in sorted_pids:
        vecs = np.array(by_pid.get(p, []))
        if len(vecs) == 0:
            continue
        n_clusters = min(k, len(vecs))
        if n_clusters == 1 or len(vecs) <= n_clusters:
            for v in vecs:
                proto_vecs.append(v / np.linalg.norm(v))
                proto_pids.append(p)
        else:
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=5).fit(vecs)
            for c in kmeans.cluster_centers_:
                c_norm = c / np.linalg.norm(c)
                proto_vecs.append(c_norm)
                proto_pids.append(p)
    return np.array(proto_vecs, dtype=np.float32), proto_pids


def evaluate_method(name, predict_fn, test_embs, test_pids, test_paths, sorted_pids):
    total = len(test_pids)
    top1_correct = 0
    top5_correct = 0
    y_true = []
    y_pred = []
    per_product = defaultdict(lambda: {"total": 0, "top1": 0, "top5": 0})

    start_t = time.perf_counter()
    for i in range(total):
        q_emb = test_embs[i]
        true_pid = test_pids[i]
        rel_p = test_paths[i]

        ranked_pids, scores = predict_fn(q_emb, rel_p)

        pred_top1 = ranked_pids[0]
        y_true.append(true_pid)
        y_pred.append(pred_top1)

        is_top1 = (pred_top1 == true_pid)
        is_top5 = (true_pid in ranked_pids[:5])

        if is_top1:
            top1_correct += 1
        if is_top5:
            top5_correct += 1

        per_product[true_pid]["total"] += 1
        if is_top1:
            per_product[true_pid]["top1"] += 1
        if is_top5:
            per_product[true_pid]["top5"] += 1

    elapsed = time.perf_counter() - start_t
    latency_ms = (elapsed / total) * 1000.0

    top1_acc = (top1_correct / total) * 100.0
    top5_acc = (top5_correct / total) * 100.0
    macro_f1 = f1_score(y_true, y_pred, labels=sorted_pids, average="macro", zero_division=0) * 100.0
    weighted_f1 = f1_score(y_true, y_pred, labels=sorted_pids, average="weighted", zero_division=0) * 100.0
    conf_mat = confusion_matrix(y_true, y_pred, labels=sorted_pids).tolist()

    per_prod_summary = {}
    for pid in sorted_pids:
        d = per_product[pid]
        tot = d["total"]
        t1 = d["top1"]
        per_prod_summary[pid] = {
            "test_count": tot,
            "top1_correct": t1,
            "top1_accuracy_pct": round((t1 / tot) * 100.0, 2) if tot > 0 else 0.0,
        }

    return {
        "method_name": name,
        "top1_accuracy_pct": round(top1_acc, 2),
        "top1_correct": top1_correct,
        "total_test": total,
        "top5_accuracy_pct": round(top5_acc, 2),
        "top5_correct": top5_correct,
        "macro_f1_pct": round(macro_f1, 2),
        "weighted_f1_pct": round(weighted_f1, 2),
        "latency_ms_per_query": round(latency_ms, 3),
        "per_product": per_prod_summary,
        "confusion_matrix": conf_mat,
    }


def main():
    print("=" * 80)
    print("PHASE 6: COMPREHENSIVE CONTROLLED EXPERIMENT SUITE")
    print("=" * 80)

    catalog = load_catalog()
    sorted_pids = sorted(list(catalog.keys()))

    # Load Untouched Test Set (610 images)
    test_data = np.load(TEST_NPZ)
    test_embs = test_data["embeddings"].astype(np.float32)
    test_pids = [str(p) for p in test_data["product_ids"]]
    test_paths = [str(p).replace("\\", "/") for p in test_data["rel_paths"]]
    print(f"Loaded Untouched Test Benchmark: {len(test_pids)} queries across {len(set(test_pids))} product classes.")

    # Load OCR Cache
    ocr_cache = {}
    if OCR_CACHE_JSON.exists():
        with open(OCR_CACHE_JSON, "r", encoding="utf-8") as f:
            raw_ocr = json.load(f)
            for k, v in raw_ocr.items():
                ocr_cache[k.replace("\\", "/")] = v
    print(f"Loaded OCR Cache: {len(ocr_cache)} records.")

    # Load Datasets
    orig_ref = np.load(ORIG_REF_NPZ)
    orig_ref_embs = orig_ref["embeddings"].astype(np.float32)
    orig_ref_pids = [str(p) for p in orig_ref["product_ids"]]

    cleaned_ref = np.load(CLEANED_REF_NPZ)
    cleaned_ref_embs = cleaned_ref["embeddings"].astype(np.float32)
    cleaned_ref_pids = [str(p) for p in cleaned_ref["product_ids"]]

    aug_ref = np.load(AUG_REF_NPZ)
    aug_ref_embs = aug_ref["embeddings"].astype(np.float32)
    aug_ref_pids = [str(p) for p in aug_ref["product_ids"]]

    print(f"Original Reference Bank: {len(orig_ref_pids)} vectors")
    print(f"Cleaned Reference Bank:  {len(cleaned_ref_pids)} vectors")
    print(f"Augmented Reference Bank:{len(aug_ref_pids)} vectors")

    # Precompute Centroids
    orig_centroids = build_centroids(orig_ref_pids, orig_ref_embs, sorted_pids)
    cleaned_centroids = build_centroids(cleaned_ref_pids, cleaned_ref_embs, sorted_pids)

    # Precompute K-Means Prototypes (k=3)
    proto_embs, proto_pids = build_kmeans_prototypes(cleaned_ref_pids, cleaned_ref_embs, sorted_pids, k=3)

    # Index maps for fast 1-NN and 3-NN max/top-k pooling
    def build_pid_idx_map(pids_list):
        idx_map = defaultdict(list)
        for idx, pid in enumerate(pids_list):
            idx_map[pid].append(idx)
        return idx_map

    orig_ref_idx_map = build_pid_idx_map(orig_ref_pids)
    cleaned_ref_idx_map = build_pid_idx_map(cleaned_ref_pids)
    aug_ref_idx_map = build_pid_idx_map(aug_ref_pids)
    proto_idx_map = build_pid_idx_map(proto_pids)

    results = []

    # -------------------------------------------------------------
    # Method 1: Original Single-Centroid Baseline (Noisy Ref Bank)
    # -------------------------------------------------------------
    def pred_m1(q_emb, rel_p):
        sims = np.dot(orig_centroids, q_emb)
        ranked_indices = np.argsort(sims)[::-1]
        ranked_pids = [sorted_pids[i] for i in ranked_indices]
        return ranked_pids, sims[ranked_indices]

    res_m1 = evaluate_method("Method 1: Original Baseline Single-Centroid", pred_m1, test_embs, test_pids, test_paths, sorted_pids)
    res_m1["ram_kb"] = round(orig_centroids.nbytes / 1024.0, 1)
    results.append(res_m1)

    # -------------------------------------------------------------
    # Method 2: Cleaned Single-Centroid Baseline
    # -------------------------------------------------------------
    def pred_m2(q_emb, rel_p):
        sims = np.dot(cleaned_centroids, q_emb)
        ranked_indices = np.argsort(sims)[::-1]
        ranked_pids = [sorted_pids[i] for i in ranked_indices]
        return ranked_pids, sims[ranked_indices]

    res_m2 = evaluate_method("Method 2: Cleaned Single-Centroid", pred_m2, test_embs, test_pids, test_paths, sorted_pids)
    res_m2["ram_kb"] = round(cleaned_centroids.nbytes / 1024.0, 1)
    results.append(res_m2)

    # -------------------------------------------------------------
    # Method 3: Original 1-NN Reference Bank (Original Noisy Ref Bank)
    # -------------------------------------------------------------
    def pred_m3(q_emb, rel_p):
        dot_sims = np.dot(orig_ref_embs, q_emb)
        sims = np.zeros(len(sorted_pids), dtype=np.float32)
        for idx, pid in enumerate(sorted_pids):
            idxs = orig_ref_idx_map.get(pid, [])
            sims[idx] = np.max(dot_sims[idxs]) if idxs else 0.0
        ranked_indices = np.argsort(sims)[::-1]
        ranked_pids = [sorted_pids[i] for i in ranked_indices]
        return ranked_pids, sims[ranked_indices]

    res_m3 = evaluate_method("Method 3: Original 1-NN Reference Bank (1340)", pred_m3, test_embs, test_pids, test_paths, sorted_pids)
    res_m3["ram_kb"] = round(orig_ref_embs.nbytes / 1024.0, 1)
    results.append(res_m3)

    # -------------------------------------------------------------
    # Method 4: Cleaned 1-NN Reference Bank (1248 Packshots)
    # -------------------------------------------------------------
    def pred_m4(q_emb, rel_p):
        dot_sims = np.dot(cleaned_ref_embs, q_emb)
        sims = np.zeros(len(sorted_pids), dtype=np.float32)
        for idx, pid in enumerate(sorted_pids):
            idxs = cleaned_ref_idx_map.get(pid, [])
            sims[idx] = np.max(dot_sims[idxs]) if idxs else 0.0
        ranked_indices = np.argsort(sims)[::-1]
        ranked_pids = [sorted_pids[i] for i in ranked_indices]
        return ranked_pids, sims[ranked_indices]

    res_m4 = evaluate_method("Method 4: Cleaned 1-NN Reference Bank (1248)", pred_m4, test_embs, test_pids, test_paths, sorted_pids)
    res_m4["ram_kb"] = round(cleaned_ref_embs.nbytes / 1024.0, 1)
    results.append(res_m4)

    # -------------------------------------------------------------
    # Method 5: Cleaned 3-NN Reference Bank (Top-3 Average Cosine Sim)
    # -------------------------------------------------------------
    def pred_m5(q_emb, rel_p):
        dot_sims = np.dot(cleaned_ref_embs, q_emb)
        sims = np.zeros(len(sorted_pids), dtype=np.float32)
        for idx, pid in enumerate(sorted_pids):
            idxs = cleaned_ref_idx_map.get(pid, [])
            if idxs:
                top_k = np.sort(dot_sims[idxs])[::-1][:3]
                sims[idx] = np.mean(top_k)
            else:
                sims[idx] = 0.0
        ranked_indices = np.argsort(sims)[::-1]
        ranked_pids = [sorted_pids[i] for i in ranked_indices]
        return ranked_pids, sims[ranked_indices]

    res_m5 = evaluate_method("Method 5: Cleaned 3-NN Reference Bank (Top-3 Average)", pred_m5, test_embs, test_pids, test_paths, sorted_pids)
    res_m5["ram_kb"] = round(cleaned_ref_embs.nbytes / 1024.0, 1)
    results.append(res_m5)

    # -------------------------------------------------------------
    # Method 6: Cleaned Multi-Prototypes / K-Means (k=3 per product)
    # -------------------------------------------------------------
    def pred_m6(q_emb, rel_p):
        dot_sims = np.dot(proto_embs, q_emb)
        sims = np.zeros(len(sorted_pids), dtype=np.float32)
        for idx, pid in enumerate(sorted_pids):
            idxs = proto_idx_map.get(pid, [])
            sims[idx] = np.max(dot_sims[idxs]) if idxs else 0.0
        ranked_indices = np.argsort(sims)[::-1]
        ranked_pids = [sorted_pids[i] for i in ranked_indices]
        return ranked_pids, sims[ranked_indices]

    res_m6 = evaluate_method("Method 6: Cleaned K-Means Multi-Prototypes (k=3)", pred_m6, test_embs, test_pids, test_paths, sorted_pids)
    res_m6["ram_kb"] = round(proto_embs.nbytes / 1024.0, 1)
    results.append(res_m6)

    # -------------------------------------------------------------
    # Method 7: Cleaned + Augmented 1-NN Reference Bank (1428 vectors)
    # -------------------------------------------------------------
    def pred_m7(q_emb, rel_p):
        dot_sims = np.dot(aug_ref_embs, q_emb)
        sims = np.zeros(len(sorted_pids), dtype=np.float32)
        for idx, pid in enumerate(sorted_pids):
            idxs = aug_ref_idx_map.get(pid, [])
            sims[idx] = np.max(dot_sims[idxs]) if idxs else 0.0
        ranked_indices = np.argsort(sims)[::-1]
        ranked_pids = [sorted_pids[i] for i in ranked_indices]
        return ranked_pids, sims[ranked_indices]

    res_m7 = evaluate_method("Method 7: Cleaned + Augmented 1-NN (1428 vectors)", pred_m7, test_embs, test_pids, test_paths, sorted_pids)
    res_m7["ram_kb"] = round(aug_ref_embs.nbytes / 1024.0, 1)
    results.append(res_m7)

    # -------------------------------------------------------------
    # Method 8: Cleaned 1-NN + OCR Brand Boost
    # -------------------------------------------------------------
    def pred_m8(q_emb, rel_p):
        dot_sims = np.dot(cleaned_ref_embs, q_emb)
        sims = np.zeros(len(sorted_pids), dtype=np.float32)
        for idx, pid in enumerate(sorted_pids):
            idxs = cleaned_ref_idx_map.get(pid, [])
            sims[idx] = np.max(dot_sims[idxs]) if idxs else 0.0

        # OCR brand boost
        ocr_info = ocr_cache.get(rel_p, {})
        brand = ocr_info.get("brand_name", "").strip().lower()
        if brand and brand not in ["no text detected", "unknown brand", "unidentified product", ""]:
            for idx, pid in enumerate(sorted_pids):
                cat_brand = catalog[pid]["brand"]
                if brand in cat_brand or cat_brand in brand:
                    sims[idx] = min(0.99, sims[idx] + 0.15)

        ranked_indices = np.argsort(sims)[::-1]
        ranked_pids = [sorted_pids[i] for i in ranked_indices]
        return ranked_pids, sims[ranked_indices]

    res_m8 = evaluate_method("Method 8: Cleaned 1-NN + OCR Brand Boost", pred_m8, test_embs, test_pids, test_paths, sorted_pids)
    res_m8["ram_kb"] = round(cleaned_ref_embs.nbytes / 1024.0, 1)
    results.append(res_m8)

    # -------------------------------------------------------------
    # Method 9: Cleaned + Augmented 1-NN + Tuned OCR Evidence (Target Architecture)
    # Tuned combination of:
    # 1. Cleaned & Balanced Reference Bank (1428 vectors)
    # 2. OCR Brand matching (+0.12 boost)
    # 3. OCR Product Name Token Overlap (+0.08 boost if 2+ product name tokens match)
    # -------------------------------------------------------------
    def pred_m9(q_emb, rel_p):
        dot_sims = np.dot(aug_ref_embs, q_emb)
        sims = np.zeros(len(sorted_pids), dtype=np.float32)
        for idx, pid in enumerate(sorted_pids):
            idxs = aug_ref_idx_map.get(pid, [])
            sims[idx] = np.max(dot_sims[idxs]) if idxs else 0.0

        ocr_info = ocr_cache.get(rel_p, {})
        brand = ocr_info.get("brand_name", "").strip().lower()
        pname = ocr_info.get("product_name", "").strip().lower()

        # Clean words
        stop_words = {"the", "and", "for", "with", "all", "day", "natural", "in", "no", "text", "detected", "unidentified", "product"}
        pname_tokens = set(pname.replace("-", " ").replace("/", " ").split()) - stop_words

        if brand and brand not in ["no text detected", "unknown brand", "unidentified product", ""]:
            for idx, pid in enumerate(sorted_pids):
                cat_brand = catalog[pid]["brand"]
                cat_pname = catalog[pid]["product_name"]
                cat_tokens = set(cat_pname.replace("-", " ").replace("/", " ").split()) - stop_words

                boost = 0.0
                if brand in cat_brand or cat_brand in brand:
                    boost += 0.12

                # Token overlap in product title
                if len(pname_tokens) > 0:
                    overlap = len(pname_tokens & cat_tokens)
                    if overlap >= 2:
                        boost += 0.08
                    elif overlap == 1 and boost > 0:
                        boost += 0.04

                if boost > 0:
                    sims[idx] = min(0.99, sims[idx] + boost)

        ranked_indices = np.argsort(sims)[::-1]
        ranked_pids = [sorted_pids[i] for i in ranked_indices]
        return ranked_pids, sims[ranked_indices]

    res_m9 = evaluate_method("Method 9: Cleaned+Augmented 1-NN + Tuned OCR Evidence", pred_m9, test_embs, test_pids, test_paths, sorted_pids)
    res_m9["ram_kb"] = round(aug_ref_embs.nbytes / 1024.0, 1)
    results.append(res_m9)

    # -------------------------------------------------------------
    # Output and Comparison Table
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("EXPERIMENTAL EVALUATION RESULTS SUMMARY (610 UNTOUCHED TEST QUERIES)")
    print("=" * 80)
    header = f"{'Method':<48} | {'Top-1 Acc':<10} | {'Top-5 Acc':<10} | {'Macro F1':<10} | {'Latency':<8} | {'Catalog RAM'}"
    print(header)
    print("-" * len(header))
    for r in results:
        line = f"{r['method_name']:<48} | {r['top1_accuracy_pct']:>6.2f}% ({r['top1_correct']}/{r['total_test']}) | {r['top5_accuracy_pct']:>6.2f}% | {r['macro_f1_pct']:>6.2f}% | {r['latency_ms_per_query']:>5.3f} ms | {r['ram_kb']} KB"
        print(line)

    # Save Comparison CSV
    with open(OUTPUT_COMPARISON_CSV, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["method_name", "top1_accuracy_pct", "top1_correct", "total_test", "top5_accuracy_pct", "top5_correct", "macro_f1_pct", "weighted_f1_pct", "latency_ms_per_query", "ram_kb"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({k: r[k] for k in fieldnames})
    print(f"\nSaved experiment comparison table to: {OUTPUT_COMPARISON_CSV}")

    # Save Baseline and Best Metrics JSON
    summary_json = {
        "evaluation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "test_benchmark": "Untouched 610 images (Seed 42 70/30 stratified split)",
        "model": "openai/clip-vit-base-patch32",
        "baseline_single_centroid": {
            "top1_pct": res_m1["top1_accuracy_pct"],
            "top5_pct": res_m1["top5_accuracy_pct"],
            "macro_f1": res_m1["macro_f1_pct"],
        },
        "cleaned_1nn_reference_bank": {
            "top1_pct": res_m4["top1_accuracy_pct"],
            "top5_pct": res_m4["top5_accuracy_pct"],
            "macro_f1": res_m4["macro_f1_pct"],
        },
        "best_method": {
            "name": res_m9["method_name"],
            "top1_pct": res_m9["top1_accuracy_pct"],
            "top5_pct": res_m9["top5_accuracy_pct"],
            "macro_f1": res_m9["macro_f1_pct"],
            "top1_correct_count": res_m9["top1_correct"],
            "total_test_queries": res_m9["total_test"],
            "exceeded_60pct_target": (res_m9["top1_accuracy_pct"] >= 60.0),
        },
        "all_methods_summary": [
            {
                "method": r["method_name"],
                "top1_acc": r["top1_accuracy_pct"],
                "top5_acc": r["top5_accuracy_pct"],
                "macro_f1": r["macro_f1_pct"],
                "latency_ms": r["latency_ms_per_query"],
            }
            for r in results
        ],
    }
    with open(OUTPUT_METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(summary_json, f, indent=2)
    print(f"Saved baseline and experiment metrics to: {OUTPUT_METRICS_JSON}")

    # Save Confusion Matrices & Per Product Breakdown
    confusion_data = {
        r["method_name"]: {
            "per_product": r["per_product"],
            "confusion_matrix": r["confusion_matrix"],
            "product_ids": sorted_pids,
        }
        for r in results
    }
    with open(OUTPUT_CONFUSION_JSON, "w", encoding="utf-8") as f:
        json.dump(confusion_data, f, indent=2)
    print(f"Saved confusion matrices and per-product accuracy to: {OUTPUT_CONFUSION_JSON}")


if __name__ == "__main__":
    main()
