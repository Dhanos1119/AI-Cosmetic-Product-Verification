"""
Pre-build and Validate Genuine OpenAI CLIP ViT-B/32 Catalog Centroids (70% Reference Set, seed=42)

Generates:
1. data/clip_centroids_vit_b32.npy (30 x 512 float32 matrix)
2. data/clip_centroids_metadata.json (Cache validation metadata & checksum)
"""

import os
import sys
import csv
import json
import hashlib
import random
import time
from pathlib import Path
from collections import defaultdict
import numpy as np

# Resolve project paths
BASE_DIR = Path(__file__).parent.parent.parent.resolve()
AI_SERVICE_DIR = BASE_DIR / "ai-service"
DATASET_DIR = BASE_DIR / "data" / "image_model_dataset"
CSV_PRODUCTS = BASE_DIR / "data" / "selected_30_products_final.csv"
OUTPUT_DIR = BASE_DIR / "data"

CENTROIDS_NPY = OUTPUT_DIR / "clip_centroids_vit_b32.npy"
METADATA_JSON = OUTPUT_DIR / "clip_centroids_metadata.json"

if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

from app.services.clip_service import _extract_image_file_embedding as extract_image_embedding

def build_centroids():
    print("=" * 75)
    print("PRE-BUILDING OPENAI CLIP ViT-B/32 CENTROIDS (70% Reference Split, Seed=42)")
    print("=" * 75)

    start_time = time.time()

    # 1. Load Catalog Metadata
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

    # 2. 70/30 Stratified Split with seed=42
    random.seed(42)
    reference_images_by_pid = defaultdict(list)
    found_pids = set()
    ref_paths_for_hash = []

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
            shuffled = imgs.copy()
            random.shuffle(shuffled)
            
            ref_count = max(1, int(len(imgs) * 0.70))
            ref_set = shuffled[:ref_count]
            reference_images_by_pid[pid].extend(ref_set)

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
    print(f"Active Product Classes: {len(active_pids)} (`P001` - `P030`)")
    total_ref_images = sum(len(v) for v in reference_images_by_pid.values())
    print(f"Total Reference Images (70% Split): {total_ref_images}")

    # 3. Compute 512-dim Centroid Embeddings from 70% Reference Set
    print("\nComputing centroids using OpenAI CLIP ViT-B/32...")
    centroids = []
    pid_index_map = []

    for idx, pid in enumerate(active_pids, start=1):
        ref_files = reference_images_by_pid[pid]
        for p in ref_files:
            ref_paths_for_hash.append(str(p.relative_to(BASE_DIR)).replace('\\', '/'))

        vecs = [extract_image_embedding(str(p)) for p in ref_files]
        vecs = [v for v in vecs if v is not None]
        if vecs:
            avg_vec = np.mean(vecs, axis=0)
            avg_norm = np.linalg.norm(avg_vec)
            if avg_norm > 0:
                avg_vec = avg_vec / avg_norm
            centroids.append(avg_vec)
            pid_index_map.append(pid)
            print(f"  [{idx:02d}/30] Product {pid}: {len(vecs)} reference embeddings averaged & L2-normalized")
        else:
            print(f"[ERROR] Could not extract embeddings for reference images of product {pid}")

    centroids_mat = np.array(centroids, dtype=np.float32)

    # 4. Generate Reference File Hash for Validation
    ref_paths_for_hash.sort()
    paths_blob = "\n".join(ref_paths_for_hash).encode('utf-8')
    checksum_sha256 = hashlib.sha256(paths_blob).hexdigest()

    # 5. Save .npy Centroids Matrix
    np.save(CENTROIDS_NPY, centroids_mat)
    print(f"\nSaved centroids matrix ({centroids_mat.shape}, float32) to: {CENTROIDS_NPY}")

    # 6. Save .json Cache Validation Metadata
    metadata_payload = {
        'model_id': "openai/clip-vit-base-patch32",
        'vector_dimension': 512,
        'matrix_shape': list(centroids_mat.shape),
        'random_seed': 42,
        'total_product_classes': len(pid_index_map),
        'total_reference_images': total_ref_images,
        'product_ids': pid_index_map,
        'reference_files_checksum_sha256': checksum_sha256,
        'created_timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
        'execution_seconds': round(time.time() - start_time, 2)
    }

    with open(METADATA_JSON, mode='w', encoding='utf-8') as f:
        json.dump(metadata_payload, f, indent=2)
    print(f"Saved cache validation metadata to: {METADATA_JSON}")

    # 7. Self-Validation Check
    assert CENTROIDS_NPY.exists() and METADATA_JSON.exists()
    loaded_mat = np.load(CENTROIDS_NPY)
    assert loaded_mat.shape == (30, 512)
    print("Self-validation PASSED: Persistent centroid cache is verified and ready.\n")

if __name__ == "__main__":
    build_centroids()
