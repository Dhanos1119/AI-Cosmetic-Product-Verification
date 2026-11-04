"""
Task 4: Improved OCR and Multi-Evidence Product Matching
Tests enhanced candidate ranking:
1. Multi-token evidence: Brand token match + Product title/type token overlap.
2. Confidence-weighted boost bounded by visual discrimination margin.
3. Preventing OCR from overpowering strong visual evidence.
4. Evaluates on 557 genuine cosmetic test queries with cached OCR text.
"""

import csv
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
from sklearn.metrics import f1_score

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"

TEST_NPZ = DATA_DIR / "clip_test_embeddings.npz"
CLEANED_REF_NPZ = DATA_DIR / "clip_reference_embeddings_cleaned.npz"
PRODUCTS_CSV = DATA_DIR / "selected_30_products_final.csv"
OCR_CACHE_JSON = DATA_DIR / "ocr_test_cache.json"
MANIFEST_CSV = REPORTS_DIR / "quarantine_manifest.csv"


def load_data():
    catalog = {}
    with open(PRODUCTS_CSV, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            pid = r["product_id"].strip()
            catalog[pid] = {
                "product_id": pid,
                "brand": r["brand"].strip().lower(),
                "name": r["product_name"].strip().lower(),
                "category": r["category"].strip().lower(),
                "product_type": r.get("product_type", r["category"]).strip().lower()
            }
    sorted_pids = sorted(catalog.keys())

    test_data = np.load(TEST_NPZ)
    test_embs = test_data["embeddings"].astype(np.float32)
    test_pids = [str(p) for p in test_data["product_ids"]]
    test_paths = [str(p).replace("\\", "/") for p in test_data["rel_paths"]]

    ref_data = np.load(CLEANED_REF_NPZ)
    ref_embs = ref_data["embeddings"].astype(np.float32)
    ref_pids = [str(p) for p in ref_data["product_ids"]]

    with open(OCR_CACHE_JSON, "r", encoding="utf-8") as f:
        ocr_cache = {k.replace("\\", "/"): v for k, v in json.load(f).items()}

    with open(MANIFEST_CSV, "r", encoding="utf-8") as f:
        quarantined = {r["original_path"].replace("\\", "/") for r in csv.DictReader(f)}

    valid_idx = [i for i, p in enumerate(test_paths) if p not in quarantined]

    return catalog, sorted_pids, test_embs, test_pids, test_paths, ref_embs, ref_pids, ocr_cache, valid_idx


def evaluate_ocr_policy(name, catalog, sorted_pids, test_embs, test_pids, test_paths, ref_embs, ref_pids, ocr_cache, valid_idx, boost_fn):
    pid_map = defaultdict(list)
    for idx, p in enumerate(ref_pids):
        pid_map[p].append(idx)

    y_true = []
    y_pred = []
    top1_c = 0
    top5_c = 0

    for i in valid_idx:
        q_emb = test_embs[i]
        true_pid = test_pids[i]
        rel_p = test_paths[i]

        dot_sims = np.dot(ref_embs, q_emb)
        raw_sims = np.zeros(len(sorted_pids), dtype=np.float32)
        for idx, pid in enumerate(sorted_pids):
            idxs = pid_map.get(pid, [])
            if idxs:
                raw_sims[idx] = np.max(dot_sims[idxs])

        ocr_info = ocr_cache.get(rel_p, {})
        boosted_sims = boost_fn(raw_sims, ocr_info, catalog, sorted_pids)

        ranked = np.argsort(boosted_sims)[::-1]
        pred_pid = sorted_pids[ranked[0]]

        y_true.append(true_pid)
        y_pred.append(pred_pid)
        if pred_pid == true_pid:
            top1_c += 1
        if true_pid in [sorted_pids[idx] for idx in ranked[:5]]:
            top5_c += 1

    t1 = (top1_c / len(valid_idx)) * 100.0
    t5 = (top5_c / len(valid_idx)) * 100.0
    f1 = f1_score(y_true, y_pred, average="macro", zero_division=0) * 100.0
    print(f"{name:<45} | Top-1: {t1:>5.2f}% ({top1_c}/{len(valid_idx)}) | Top-5: {t5:>5.2f}% | Macro F1: {f1:>5.2f}%")
    return t1, t5, f1


def main():
    print("=" * 80)
    print("TASK 4: IMPROVED OCR AND PRODUCT MATCHING EVALUATION")
    print("=" * 80)
    catalog, sorted_pids, test_embs, test_pids, test_paths, ref_embs, ref_pids, ocr_cache, valid_idx = load_data()

    # Policy 0: Visual-only baseline (No OCR)
    def boost_none(raw_sims, ocr_info, cat, pids):
        return raw_sims.copy()

    # Policy 1: Existing Production (Flat +0.15 Brand Boost)
    def boost_flat_015(raw_sims, ocr_info, cat, pids):
        sims = raw_sims.copy()
        brand = ocr_info.get("brand_name", "").strip().lower()
        if brand and brand not in ["no text detected", "unknown brand", "unidentified brand", ""]:
            for idx, pid in enumerate(pids):
                cb = cat[pid]["brand"]
                if brand in cb or cb in brand:
                    sims[idx] = min(0.99, sims[idx] + 0.15)
        return sims

    # Policy 2: Calibrated Supporting Evidence (Brand + Product Title Keyword Matching + Visual Margin Protection)
    # Important Keywords in cosmetic titles
    product_keywords = {
        'powder': ['powder', 'setting', 'invisible', 'mineral', 'pressed', 'mosaic'],
        'mascara': ['mascara', 'volumising', 'lash', 'brow', 'liner'],
        'liner': ['liner', 'eyeliner', 'liquid', 'pencil', 'brow'],
        'lipstick': ['lipstick', 'lippie', 'gloss', 'lip', 'shade'],
        'foundation': ['foundation', 'bb', 'cream', 'spot', 'clay', 'concealer'],
        'blush': ['blush', 'mosaic', 'cheek', 'bronzer'],
        'cleanser': ['cleanser', 'soap', 'facial', 'wash'],
        'lotion': ['lotion', 'hydrating', 'moisturizer', 'serum', 'butter', 'skin']
    }

    def boost_calibrated_multi_evidence(raw_sims, ocr_info, cat, pids, max_brand_boost=0.10, title_boost=0.04, visual_margin_cap=0.12):
        sims = raw_sims.copy()
        brand = ocr_info.get("brand_name", "").strip().lower()
        prod_text = ocr_info.get("product_name", "").strip().lower()
        full_text = f"{brand} {prod_text}"

        best_raw_sim = np.max(raw_sims)

        for idx, pid in enumerate(pids):
            cb = cat[pid]["brand"]
            cn = cat[pid]["name"]
            ct = cat[pid]["category"]

            boost = 0.0

            # 1. Brand match
            if brand and brand not in ["no text detected", "unknown brand", "unidentified brand", ""]:
                if (brand in cb or cb in brand) and len(brand) >= 3:
                    boost += max_brand_boost

            # 2. Product Name / Title Token overlap
            # Check specific product words in detected text
            name_tokens = [w for w in cn.split() if len(w) >= 4]
            matching_tokens = sum(1 for w in name_tokens if w in full_text)
            if matching_tokens > 0:
                boost += min(title_boost * matching_tokens, 0.06)

            # 3. Visual Margin Gating: prevent OCR from overriding high visual margin (> 0.12)
            # If candidate is far below the visual best match, attenuate the boost
            visual_gap = best_raw_sim - raw_sims[idx]
            if visual_gap > visual_margin_cap:
                boost *= 0.5  # Attenuate boost when visual evidence strongly disfavors

            sims[idx] = min(0.99, sims[idx] + boost)

        return sims

    # Compare policies
    evaluate_ocr_policy("1. Visual 1-NN Baseline (No OCR)", catalog, sorted_pids, test_embs, test_pids, test_paths, ref_embs, ref_pids, ocr_cache, valid_idx, boost_none)
    evaluate_ocr_policy("2. Production Policy (Flat +0.15 Brand)", catalog, sorted_pids, test_embs, test_pids, test_paths, ref_embs, ref_pids, ocr_cache, valid_idx, boost_flat_015)
    
    for mb, tb, cap in [
        (0.12, 0.04, 0.12),
        (0.10, 0.05, 0.10),
        (0.14, 0.03, 0.15),
    ]:
        fn = lambda r, o, c, p, m=mb, t=tb, cp=cap: boost_calibrated_multi_evidence(r, o, c, p, max_brand_boost=m, title_boost=t, visual_margin_cap=cp)
        evaluate_ocr_policy(f"3. Multi-Evidence (Brand={mb}, Title={tb}, Cap={cap})", catalog, sorted_pids, test_embs, test_pids, test_paths, ref_embs, ref_pids, ocr_cache, valid_idx, fn)


if __name__ == "__main__":
    main()
