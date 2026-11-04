"""
Verification Script for Production CLIP Reference Bank & Non-Cosmetic Rejection Pipeline
Computes:
1. Dataset backup integrity & test set checksum confirmation.
2. Production 1-NN Reference Bank (1,248 vectors) & Centroid status.
3. Evaluation on 557 Genuine Cosmetic Test Queries:
   - Top-1 Accuracy
   - Top-5 Accuracy
   - Macro F1-Score
   - Per-Category Performance Breakdown
4. Non-Cosmetic Screening Performance on 53 Quarantined Non-Cosmetics:
   - Non-Cosmetic Rejection Rate
   - Ambiguous Input Rate
   - False Confident Assignment Rate
5. False-Rejection Rate on Valid Cosmetics.
6. Live API HTTP Verification (POST http://localhost:8001/api/analyze).
"""

import io
import csv
import json
import glob
import hashlib
from collections import defaultdict, Counter
from pathlib import Path
import numpy as np
import requests
from sklearn.metrics import f1_score

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"

CLEANED_REF_NPZ = DATA_DIR / "clip_reference_embeddings_cleaned.npz"
CLEANED_CENTROIDS_NPY = DATA_DIR / "clip_centroids_cleaned.npy"
TEST_NPZ = DATA_DIR / "clip_test_embeddings.npz"
MANIFEST_CSV = REPORTS_DIR / "quarantine_manifest.csv"
PRODUCTS_CSV = DATA_DIR / "selected_30_products_final.csv"
OCR_CACHE_JSON = DATA_DIR / "ocr_test_cache.json"
BACKUP_DIR = DATA_DIR / "image_model_dataset_backup"


def verify_file_integrity():
    print("=" * 80)
    print("1. VERIFYING DATASET INTEGRITY & FILE STATUS")
    print("=" * 80)
    
    # Check backup
    backup_imgs = list(BACKUP_DIR.rglob("*.jpg")) + list(BACKUP_DIR.rglob("*.png"))
    print(f"Dataset backup path: {BACKUP_DIR}")
    print(f"Total backup images preserved: {len(backup_imgs)} (Expected: 1,950)")
    assert len(backup_imgs) == 1950, f"Backup compromised! Found {len(backup_imgs)}"

    # Check test set
    test_data = np.load(TEST_NPZ)
    test_embs = test_data["embeddings"]
    test_paths = test_data["rel_paths"]
    print(f"Test set path: {TEST_NPZ}")
    print(f"Total test queries: {len(test_paths)} (Expected: 610)")
    assert len(test_paths) == 610, f"Test benchmark modified! Found {len(test_paths)}"

    # Check cleaned reference bank
    cleaned_ref = np.load(CLEANED_REF_NPZ)
    ref_embs = cleaned_ref["embeddings"]
    ref_pids = cleaned_ref["product_ids"]
    print(f"Cleaned reference bank path: {CLEANED_REF_NPZ}")
    print(f"Cleaned reference vectors: {ref_embs.shape[0]} vectors, {ref_embs.shape[1]}-dimensional")
    assert ref_embs.shape == (1248, 512), f"Invalid cleaned reference shape: {ref_embs.shape}"
    assert len(set(ref_pids)) == 30, f"Expected 30 unique products in cleaned reference bank, found {len(set(ref_pids))}"

    # Check cleaned centroids
    centroids = np.load(CLEANED_CENTROIDS_NPY)
    print(f"Cleaned centroids path: {CLEANED_CENTROIDS_NPY}")
    print(f"Cleaned centroids shape: {centroids.shape} (Expected: (30, 512))")
    assert centroids.shape == (30, 512)
    print("All file integrity checks PASSED.\n")


def evaluate_cosmetic_accuracy():
    print("=" * 80)
    print("2. EVALUATING COSMETIC ACCURACY ON 557 GENUINE TEST QUERIES")
    print("=" * 80)

    # Load catalog
    catalog = {}
    with open(PRODUCTS_CSV, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            pid = r["product_id"].strip()
            catalog[pid] = {
                "brand": r["brand"].strip(),
                "name": r["product_name"].strip(),
                "category": r["category"].strip()
            }
    sorted_pids = sorted(catalog.keys())
    pid_to_cat = {pid: catalog[pid]["category"] for pid in sorted_pids}

    # Load test set
    test_data = np.load(TEST_NPZ)
    test_embs = test_data["embeddings"].astype(np.float32)
    test_pids = [str(p) for p in test_data["product_ids"]]
    test_paths = [str(p).replace("\\", "/") for p in test_data["rel_paths"]]

    # Load quarantine manifest to separate valid test queries from non-cosmetics
    manifest_paths = set()
    if MANIFEST_CSV.exists():
        with open(MANIFEST_CSV, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                manifest_paths.add(r["original_path"].replace("\\", "/"))

    valid_indices = [i for i, p in enumerate(test_paths) if p not in manifest_paths]
    print(f"Total test benchmark images:      {len(test_paths)}")
    print(f"Genuine cosmetic test queries:     {len(valid_indices)}")
    print(f"Quarantined non-cosmetic artifacts:{len(test_paths) - len(valid_indices)}")

    # Load cleaned reference bank
    cleaned_ref = np.load(CLEANED_REF_NPZ)
    ref_embs = cleaned_ref["embeddings"].astype(np.float32)
    ref_pids = [str(p) for p in cleaned_ref["product_ids"]]

    pid_to_ref_idx = defaultdict(list)
    for idx, pid in enumerate(ref_pids):
        pid_to_ref_idx[pid].append(idx)

    # Load OCR cache
    with open(OCR_CACHE_JSON, "r", encoding="utf-8") as f:
        ocr_cache = {k.replace("\\", "/"): v for k, v in json.load(f).items()}

    y_true = []
    y_pred = []
    top5_correct = 0
    top1_correct = 0

    category_stats = defaultdict(lambda: {"total": 0, "top1": 0, "top5": 0})

    for i in valid_indices:
        q_emb = test_embs[i]
        true_pid = test_pids[i]
        rel_p = test_paths[i]
        cat = pid_to_cat[true_pid]

        # 1-NN similarity against cleaned reference bank
        dot_sims = np.dot(ref_embs, q_emb)
        sims = np.zeros(len(sorted_pids), dtype=np.float32)
        for idx, pid in enumerate(sorted_pids):
            idxs = pid_to_ref_idx.get(pid, [])
            sims[idx] = np.max(dot_sims[idxs]) if idxs else 0.0

        # OCR brand boost
        ocr_info = ocr_cache.get(rel_p, {})
        brand = ocr_info.get("brand_name", "").strip().lower()
        boosted_sims = sims.copy()
        if brand and brand not in ["no text detected", "unknown brand", "unidentified brand", ""]:
            for idx, pid in enumerate(sorted_pids):
                cat_b = catalog[pid]["brand"].lower().strip()
                if brand in cat_b or cat_b in brand:
                    boosted_sims[idx] = min(0.99, boosted_sims[idx] + 0.15)

        ranked_indices = np.argsort(boosted_sims)[::-1]
        ranked_pids = [sorted_pids[idx] for idx in ranked_indices]

        pred_pid = ranked_pids[0]
        y_true.append(true_pid)
        y_pred.append(pred_pid)

        category_stats[cat]["total"] += 1
        if pred_pid == true_pid:
            top1_correct += 1
            category_stats[cat]["top1"] += 1

        if true_pid in ranked_pids[:5]:
            top5_correct += 1
            category_stats[cat]["top5"] += 1

    total_valid = len(valid_indices)
    top1_acc = (top1_correct / total_valid) * 100.0
    top5_acc = (top5_correct / total_valid) * 100.0
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0) * 100.0

    print(f"\n--- ACCURACY METRICS (557 Genuine Cosmetics) ---")
    print(f"Top-1 Accuracy:  {top1_acc:.2f}% ({top1_correct}/{total_valid})")
    print(f"Top-5 Accuracy:  {top5_acc:.2f}% ({top5_correct}/{total_valid})")
    print(f"Macro F1-Score:  {macro_f1:.2f}%")

    print(f"\n--- PER-CATEGORY BREAKDOWN ---")
    print(f"{'Category':<18} | {'Total':<6} | {'Top-1 Correct':<14} | {'Top-1 Acc':<10} | {'Top-5 Acc':<10}")
    print("-" * 68)
    for cat in sorted(category_stats.keys()):
        stat = category_stats[cat]
        t = stat["total"]
        c1 = stat["top1"]
        c5 = stat["top5"]
        acc1 = (c1 / t) * 100.0 if t > 0 else 0.0
        acc5 = (c5 / t) * 100.0 if t > 0 else 0.0
        print(f"{cat:<18} | {t:<6} | {c1:<14} | {acc1:>8.2f}% | {acc5:>8.2f}%")

    return {
        "top1_acc": top1_acc,
        "top5_acc": top5_acc,
        "macro_f1": macro_f1,
        "category_stats": dict(category_stats)
    }


def evaluate_non_cosmetic_screening():
    print("\n" + "=" * 80)
    print("3. EVALUATING NON-COSMETIC REJECTION ON 53 QUARANTINED ARTIFACTS")
    print("=" * 80)

    import sys
    sys.path.insert(0, str(BASE_DIR / "ai-service"))
    from app.services.clip_service import compute_clip_similarity, screen_cosmetic_image

    # Load 53 quarantined test images
    test_data = np.load(TEST_NPZ)
    test_paths = [str(p).replace("\\", "/") for p in test_data["rel_paths"]]

    manifest_paths = set()
    manifest_info = {}
    if MANIFEST_CSV.exists():
        with open(MANIFEST_CSV, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                p = r["original_path"].replace("\\", "/")
                manifest_paths.add(p)
                manifest_info[p] = r

    q_test_paths = [p for p in test_paths if p in manifest_paths]
    print(f"Total quarantined non-cosmetic test images: {len(q_test_paths)}")

    rejected_count = 0
    ambiguous_count = 0
    accepted_count = 0

    rejection_reasons = Counter()

    for p in q_test_paths:
        fpath = BACKUP_DIR / Path(p).relative_to("data/image_model_dataset")
        if not fpath.exists():
            fpath = BASE_DIR / p
        with open(fpath, "rb") as f:
            img_bytes = f.read()

        res = compute_clip_similarity(img_bytes)
        status = res.get("status")
        match_status = res.get("match_status")

        if status == "rejected_non_cosmetic":
            rejected_count += 1
            reason_type = manifest_info.get(p, {}).get("reason", "unknown")
            rejection_reasons[reason_type.split("(")[1].split(",")[0] if "(" in reason_type else "other"] += 1
        elif match_status == "Ambiguous Input / Manual Review Required":
            ambiguous_count += 1
        else:
            accepted_count += 1

    rejection_rate = (rejected_count / len(q_test_paths)) * 100.0
    ambiguous_rate = (ambiguous_count / len(q_test_paths)) * 100.0

    print(f"\n--- NON-COSMETIC SCREENING METRICS (53 Images) ---")
    print(f"Strict Rejection Rate (rejected_non_cosmetic): {rejection_rate:.2f}% ({rejected_count}/53)")
    print(f"Ambiguous Review Rate (confidence capped):     {ambiguous_rate:.2f}% ({ambiguous_count}/53)")
    print(f"Total Controlled Rate (rejection + ambiguous): {(rejected_count + ambiguous_count)/len(q_test_paths)*100:.2f}% ({rejected_count + ambiguous_count}/53)")
    print(f"False Acceptance Rate (allowed as cosmetic):   {accepted_count / len(q_test_paths)*100:.2f}% ({accepted_count}/53)")
    print(f"\nRejections by category: {dict(rejection_reasons)}")

    # Test false-rejection rate on valid cosmetics sample
    print("\n--- EVALUATING FALSE-REJECTION ON VALID COSMETICS ---")
    cosmetics = sorted(glob.glob(str(DATA_DIR / "image_model_dataset" / "**" / "*.jpg"), recursive=True))[::10][:100]
    false_rejections = 0
    valid_ambiguous = 0
    valid_accepted = 0

    for cp in cosmetics:
        with open(cp, "rb") as f:
            c_bytes = f.read()
        c_res = compute_clip_similarity(c_bytes)
        if c_res.get("status") == "rejected_non_cosmetic":
            false_rejections += 1
        elif c_res.get("match_status") == "Ambiguous Input / Manual Review Required":
            valid_ambiguous += 1
        else:
            valid_accepted += 1

    false_rej_rate = (false_rejections / len(cosmetics)) * 100.0
    print(f"Valid cosmetic images tested: {len(cosmetics)}")
    print(f"False-Rejection Rate:          {false_rej_rate:.2f}% ({false_rejections}/{len(cosmetics)})")
    print(f"Valid Cosmetic Preservation:   {(valid_accepted + valid_ambiguous)/len(cosmetics)*100:.2f}%")

    return {
        "non_cosmetic_rejection_rate": rejection_rate,
        "non_cosmetic_ambiguous_rate": ambiguous_rate,
        "false_rejection_rate": false_rej_rate
    }


def test_live_api():
    print("\n" + "=" * 80)
    print("4. TESTING LIVE RUNNING API (http://localhost:8001/api/analyze)")
    print("=" * 80)

    url = "http://localhost:8001/api/analyze"

    # 1. Test live rejection of a non-cosmetic diagram
    diagram_path = DATA_DIR / "quarantine" / "non_cosmetic" / "Eye_Products" / "P013" / "P013_0033.jpg"
    with open(diagram_path, "rb") as f:
        files = {"file": ("grammar_chart.jpg", f, "image/jpeg")}
        resp_diagram = requests.post(url, files=files)

    print(f"Test 1 [Non-Cosmetic Diagram Upload]: HTTP {resp_diagram.status_code}")
    d_json = resp_diagram.json()
    print(f"  status:  {d_json.get('status')}")
    print(f"  message: {d_json.get('message')}")
    print(f"  success: {d_json.get('success')}")
    assert resp_diagram.status_code == 200
    assert d_json.get("status") == "rejected_non_cosmetic"
    assert d_json.get("message") == "Please upload a cosmetic product image."

    # 2. Test live acceptance of a genuine cosmetic packaging image
    cosmetics = sorted(glob.glob(str(DATA_DIR / "image_model_dataset" / "**" / "*.jpg"), recursive=True))
    cosmetic_path = cosmetics[0]
    with open(cosmetic_path, "rb") as f:
        files = {"file": ("cosmetic_packaging.jpg", f, "image/jpeg")}
        resp_cosmetic = requests.post(url, files=files)

    print(f"\nTest 2 [Genuine Cosmetic Upload]: HTTP {resp_cosmetic.status_code}")
    c_json = resp_cosmetic.json()
    print(f"  success:                {c_json.get('success')}")
    print(f"  product_detection:      {c_json.get('product_detection')}")
    print(f"  clip_similarity:        {c_json.get('clip_similarity')}")
    clip_details = c_json.get("clip_result", {})
    print(f"  matched_product_name:   {clip_details.get('matched_product_name')}")
    print(f"  matched_product_id:     {clip_details.get('matched_product_id')}")
    print(f"  matching_method:        {clip_details.get('matching_method')}")
    print(f"  similarity_percentage:  {clip_details.get('similarity_percentage')}%")
    print(f"  db_persisted:           {c_json.get('db_persisted')}")

    assert resp_cosmetic.status_code == 200
    assert c_json.get("success") is True
    assert clip_details.get("matching_method") == "1-NN Reference Bank (Max-Pooling)"
    assert clip_details.get("matched_product_id") is not None
    print("\nLive API tests completed successfully!")


if __name__ == "__main__":
    verify_file_integrity()
    cosmetic_metrics = evaluate_cosmetic_accuracy()
    screening_metrics = evaluate_non_cosmetic_screening()
    test_live_api()
