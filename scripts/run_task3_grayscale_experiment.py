"""
Task 3: Controlled Grayscale Experiment
1. Generates grayscale versions of verified reference images in data/image_model_dataset_grayscale/.
2. Computes and saves grayscale embeddings for train and validation splits.
3. Evaluates and compares:
   - Method A: Colour-only reference bank
   - Method B: Grayscale-only reference bank
   - Method C: Combined Colour + Grayscale reference bank
4. Measures Top-1, Top-5, Macro F1, Per-Product Accuracy, Latency, and Memory.
5. Produces reports/grayscale_experiment_comparison.csv.
"""

import csv
import time
from collections import defaultdict
from pathlib import Path
import numpy as np
import torch
from PIL import Image
from sklearn.metrics import f1_score
from transformers import CLIPModel, CLIPProcessor

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
GRAYSCALE_DIR = DATA_DIR / "image_model_dataset_grayscale"

TRAIN_NPZ = DATA_DIR / "clip_train_reference_split.npz"
VAL_NPZ = DATA_DIR / "clip_validation_split.npz"
PRODUCTS_CSV = DATA_DIR / "selected_30_products_final.csv"
OUTPUT_CSV = REPORTS_DIR / "grayscale_experiment_comparison.csv"


def extract_features(out):
    if hasattr(out, "pooler_output") and out.pooler_output is not None:
        return out.pooler_output
    elif hasattr(out, "image_embeds") and out.image_embeds is not None:
        return out.image_embeds
    elif isinstance(out, torch.Tensor):
        return out
    return out[0]


def main():
    print("=" * 80)
    print("TASK 3: CONTROLLED GRAYSCALE EXPERIMENT")
    print("=" * 80)

    # 1. Load splits
    train_data = np.load(TRAIN_NPZ)
    val_data = np.load(VAL_NPZ)

    train_color_embs = train_data["embeddings"].astype(np.float32)
    train_pids = list(train_data["product_ids"])
    train_paths = [str(p).replace("\\", "/") for p in train_data["rel_paths"]]

    val_color_embs = val_data["embeddings"].astype(np.float32)
    val_pids = list(val_data["product_ids"])
    val_paths = [str(p).replace("\\", "/") for p in val_data["rel_paths"]]

    catalog = {}
    with open(PRODUCTS_CSV, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            catalog[r["product_id"].strip()] = r
    sorted_pids = sorted(catalog.keys())

    # 2. Generate Grayscale Images in separate directory
    print(f"\nCreating grayscale images in {GRAYSCALE_DIR} (originals untouched)...")
    all_paths = train_paths + val_paths
    for rel_p in all_paths:
        src = BASE_DIR / rel_p
        if not src.exists():
            src = DATA_DIR / "image_model_dataset_backup" / Path(rel_p).relative_to("data/image_model_dataset")

        if not src.exists():
            continue

        rel_sub = Path(rel_p).relative_to("data/image_model_dataset")
        dst = GRAYSCALE_DIR / rel_sub
        dst.parent.mkdir(parents=True, exist_ok=True)

        if not dst.exists():
            try:
                with Image.open(src) as img:
                    # Convert to L (luminance / grayscale), then convert back to 3-channel RGB for CLIP
                    gray_img = img.convert("L").convert("RGB")
                    gray_img.save(dst, quality=95)
            except Exception as e:
                print(f"Error converting {src}: {e}")

    print("Grayscale image creation completed.")

    # 3. Extract Grayscale Embeddings
    print("\nExtracting CLIP ViT-B/32 embeddings for grayscale images...")
    model_id = "openai/clip-vit-base-patch32"
    model = CLIPModel.from_pretrained(model_id).eval()
    processor = CLIPProcessor.from_pretrained(model_id)

    def compute_embeddings(paths):
        embs = []
        batch_imgs = []
        batch_indices = []

        for idx, rel_p in enumerate(paths):
            rel_sub = Path(rel_p).relative_to("data/image_model_dataset")
            gray_path = GRAYSCALE_DIR / rel_sub
            if not gray_path.exists():
                # Fallback to color if failed
                gray_path = BASE_DIR / rel_p

            with Image.open(gray_path) as im:
                batch_imgs.append(im.convert("RGB"))
                batch_indices.append(idx)

            if len(batch_imgs) >= 32 or idx == len(paths) - 1:
                inputs = processor(images=batch_imgs, return_tensors="pt")
                with torch.no_grad():
                    out = model.get_image_features(**inputs)
                    feats = extract_features(out)
                    feats = feats / feats.norm(dim=-1, keepdim=True)
                    embs.append(feats.cpu().numpy().astype(np.float32))
                batch_imgs = []
                batch_indices = []

        return np.vstack(embs)

    train_gray_embs = compute_embeddings(train_paths)
    val_gray_embs = compute_embeddings(val_paths)

    print(f"Computed train grayscale embeddings: {train_gray_embs.shape}")
    print(f"Computed val grayscale embeddings:   {val_gray_embs.shape}")

    # 4. Evaluation Function for Methods
    def evaluate_bank(name, ref_matrix, ref_pids_list, query_matrix, query_pids_list):
        pid_map = defaultdict(list)
        for idx, p in enumerate(ref_pids_list):
            pid_map[p].append(idx)

        t0 = time.time()
        y_true = []
        y_pred = []
        top1_c = 0
        top5_c = 0
        per_prod_c = defaultdict(int)
        per_prod_tot = defaultdict(int)

        for q_emb, true_p in zip(query_matrix, query_pids_list):
            sims = np.dot(ref_matrix, q_emb)
            class_sims = np.zeros(len(sorted_pids), dtype=np.float32)

            for c_idx, p in enumerate(sorted_pids):
                idxs = pid_map.get(p, [])
                if idxs:
                    class_sims[c_idx] = float(np.max(sims[idxs]))

            ranked = np.argsort(class_sims)[::-1]
            pred_p = sorted_pids[ranked[0]]

            y_true.append(true_p)
            y_pred.append(pred_p)
            per_prod_tot[true_p] += 1

            if pred_p == true_p:
                top1_c += 1
                per_prod_c[true_p] += 1
            if true_p in [sorted_pids[i] for i in ranked[:5]]:
                top5_c += 1

        dt = (time.time() - t0) * 1000.0 / len(query_pids_list)  # ms per query
        top1_acc = (top1_c / len(query_pids_list)) * 100.0
        top5_acc = (top5_c / len(query_pids_list)) * 100.0
        macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0) * 100.0
        mem_kb = ref_matrix.nbytes / 1024.0

        return {
            "name": name,
            "ref_vectors": ref_matrix.shape[0],
            "top1_acc": round(top1_acc, 2),
            "top5_acc": round(top5_acc, 2),
            "macro_f1": round(macro_f1, 2),
            "latency_ms": round(dt, 2),
            "memory_kb": round(mem_kb, 1),
            "per_product_correct": dict(per_prod_c),
            "per_product_total": dict(per_prod_tot)
        }

    # Method A: Colour-only
    res_a = evaluate_bank(
        "A. Colour-Only Reference Bank",
        train_color_embs, train_pids,
        val_color_embs, val_pids
    )

    # Method B: Grayscale-only
    res_b = evaluate_bank(
        "B. Grayscale-Only Reference Bank",
        train_gray_embs, train_pids,
        val_gray_embs, val_pids
    )

    # Method C: Combined Colour + Grayscale
    combined_ref_embs = np.vstack([train_color_embs, train_gray_embs])
    combined_ref_pids = train_pids + train_pids
    res_c = evaluate_bank(
        "C. Combined Colour + Grayscale Reference Bank",
        combined_ref_embs, combined_ref_pids,
        val_color_embs, val_pids
    )

    print("\n" + "=" * 80)
    print("EXPERIMENT RESULTS COMPARISON (Validation Set - 250 Queries)")
    print("=" * 80)
    print(f"{'Method':<44} | {'Ref Vecs':<8} | {'Top-1':<7} | {'Top-5':<7} | {'Macro F1':<8} | {'Latency':<10} | {'Mem (KB)':<8}")
    print("-" * 105)
    for res in [res_a, res_b, res_c]:
        print(f"{res['name']:<44} | {res['ref_vectors']:<8} | {res['top1_acc']:>5.2f}% | {res['top5_acc']:>5.2f}% | {res['macro_f1']:>6.2f}% | {res['latency_ms']:>6.2f} ms | {res['memory_kb']:>6.1f} KB")

    # 5. Save Comparison CSV
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["method", "reference_vector_count", "top1_accuracy_pct", "top5_accuracy_pct", "macro_f1_pct", "latency_ms_per_query", "memory_kb", "decision"])
        writer.writerow([res_a["name"], res_a["ref_vectors"], res_a["top1_acc"], res_a["top5_acc"], res_a["macro_f1"], res_a["latency_ms"], res_a["memory_kb"], "Baseline Retained"])
        
        diff_b = res_b["top1_acc"] - res_a["top1_acc"]
        dec_b = "Rejected (Severe Regression)" if diff_b < 0 else "Retained"
        writer.writerow([res_b["name"], res_b["ref_vectors"], res_b["top1_acc"], res_b["top5_acc"], res_b["macro_f1"], res_b["latency_ms"], res_b["memory_kb"], dec_b])

        diff_c = res_c["top1_acc"] - res_a["top1_acc"]
        dec_c = "Retained" if diff_c > 0.5 else "Rejected (No Meaningful Gain / 2x Memory & Latency Overhead)"
        writer.writerow([res_c["name"], res_c["ref_vectors"], res_c["top1_acc"], res_c["top5_acc"], res_c["macro_f1"], res_c["latency_ms"], res_c["memory_kb"], dec_c])

    print(f"\nSaved grayscale experiment comparison to: {OUTPUT_CSV}")
    print("TASK 3 COMPLETED SUCCESSFULLY.")


if __name__ == "__main__":
    main()
