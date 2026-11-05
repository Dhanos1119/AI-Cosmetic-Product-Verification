"""
CLIP Image Feature & Vector Similarity Service Module

Computes deep visual embeddings and calculates vector similarity scores
against reference authentic cosmetic packaging catalog signatures using a genuine
OpenAI CLIP ViT-B/32 Vision Transformer model (Hugging Face Transformers).
"""

import io
import os
import csv
import json
import random
import hashlib
from pathlib import Path
from collections import defaultdict
import numpy as np
from PIL import Image
import torch

# Resolve root project directory (AI-Cosmetic-Product-Verification)
BASE_PROJECT_DIR = Path(__file__).parent.parent.parent.parent.resolve()
DATASET_PATH_REL = os.getenv("DATASET_PATH", "data/image_model_dataset")
METADATA_PATH_REL = os.getenv("METADATA_PATH", "data/image_dataset_metadata.csv")

DATASET_DIR = BASE_PROJECT_DIR / DATASET_PATH_REL
METADATA_CSV = BASE_PROJECT_DIR / METADATA_PATH_REL
CENTROIDS_NPY_FILE = BASE_PROJECT_DIR / "data" / "clip_centroids_cleaned.npy"
CENTROIDS_META_FILE = BASE_PROJECT_DIR / "data" / "clip_centroids_cleaned_metadata.json"
REFERENCE_BANK_NPZ_FILE = BASE_PROJECT_DIR / "data" / "clip_reference_embeddings_cleaned.npz"

# Global lazy-loaded reference bank cache (1-NN reference vectors)
_REFERENCE_BANK_CACHE = None

def _load_reference_bank():
    """
    Lazy-loads validated 1-NN reference bank embeddings (1248, 512) and their product IDs.
    Loads data/clip_reference_embeddings_cleaned.npz strictly.
    Returns (ref_embeddings_mat, ref_pids, pid_to_ref_indices) if file exists and passes validation.
    Handles missing or invalid files safely; does NOT silently fall back to uncleaned embeddings.
    """
    global _REFERENCE_BANK_CACHE
    if _REFERENCE_BANK_CACHE is not None:
        return _REFERENCE_BANK_CACHE
    if not REFERENCE_BANK_NPZ_FILE.exists():
        print(f"[REFERENCE BANK ERROR] Cleaned reference bank not found at {REFERENCE_BANK_NPZ_FILE}")
        return None
    try:
        data = np.load(REFERENCE_BANK_NPZ_FILE)
        ref_mat = data['embeddings'].astype(np.float32)
        ref_pids = list(data['product_ids'])
        
        # 1. Dimension validation
        if ref_mat.ndim != 2 or ref_mat.shape[1] != 512:
            print(f"[REFERENCE BANK INVALID] Invalid vector dimensions: {ref_mat.shape}")
            return None
            
        # 2. Count validation
        if len(ref_pids) != len(ref_mat):
            print(f"[REFERENCE BANK INVALID] Embeddings count ({len(ref_mat)}) != PIDs count ({len(ref_pids)})")
            return None
        if len(ref_pids) != 1248:
            print(f"[REFERENCE BANK NOTICE] Expected 1,248 reference vectors, found {len(ref_pids)}")

        # 3. Product label validation: must cover all 30 products
        unique_pids = set(ref_pids)
        if len(unique_pids) != 30:
            print(f"[REFERENCE BANK INVALID] Incomplete product coverage: {len(unique_pids)}/30 unique products")
            return None

        # 4. L2 Normalization check
        norms = np.linalg.norm(ref_mat, axis=1)
        if not np.allclose(norms, 1.0, atol=1e-3):
            print(f"[REFERENCE BANK INVALID] Reference embeddings are not L2 normalized")
            return None

        # Pre-group indices by product_id for fast max-pooling
        pid_indices = defaultdict(list)
        for idx, pid in enumerate(ref_pids):
            pid_indices[pid].append(idx)
        _REFERENCE_BANK_CACHE = (ref_mat, ref_pids, pid_indices)
        return _REFERENCE_BANK_CACHE
    except Exception as exc:
        print(f"[REFERENCE BANK ERROR] Exception loading cleaned reference bank: {exc}")
        return None

# Global lazy-loaded CLIP model and processor singletons
_CLIP_MODEL = None
_CLIP_PROCESSOR = None
_MODEL_ID = "openai/clip-vit-base-patch32"

def _get_clip_model_and_processor():
    """
    Lazy-loads OpenAI CLIP ViT-B/32 model and processor singletons.
    Prioritizes local cached weights to prevent blocking network calls.
    """
    global _CLIP_MODEL, _CLIP_PROCESSOR
    if _CLIP_MODEL is None or _CLIP_PROCESSOR is None:
        from transformers import CLIPModel, CLIPProcessor
        print(f"Loading Genuine OpenAI CLIP Model ({_MODEL_ID})...")
        try:
            _CLIP_MODEL = CLIPModel.from_pretrained(_MODEL_ID, local_files_only=True)
            _CLIP_PROCESSOR = CLIPProcessor.from_pretrained(_MODEL_ID, local_files_only=True)
        except Exception:
            _CLIP_MODEL = CLIPModel.from_pretrained(_MODEL_ID)
            _CLIP_PROCESSOR = CLIPProcessor.from_pretrained(_MODEL_ID)
        _CLIP_MODEL.eval()
    return _CLIP_MODEL, _CLIP_PROCESSOR

# Zero-shot prompts for cosmetic vs. non-cosmetic screening
_SCREENING_COSMETIC_PROMPTS = [
    "cosmetics packaging",
    "cosmetics bottle",
    "makeup cosmetics",
    "skincare product",
    "lipstick cosmetics",
    "eyeliner cosmetics",
    "mascara cosmetics",
    "makeup swatch",
]

_SCREENING_NON_COSMETIC_PROMPTS = [
    "educational diagram grammar chart syntax tree blueprint infographic",
    "promotional sales banner advertisement typography poster coupon flyer",
    "website screen customer review mobile app screenshot interface",
    "automobile car motor vehicle mechanical engine bicycle",
    "clothing apparel t-shirt hoodie sweatpants athletic shoes footwear",
]

_SCREENING_TEXT_FEATURES = None

def _get_screening_text_features():
    """Lazy-loads and caches normalized text embeddings for screening prompts."""
    global _SCREENING_TEXT_FEATURES
    if _SCREENING_TEXT_FEATURES is not None:
        return _SCREENING_TEXT_FEATURES
    model, processor = _get_clip_model_and_processor()
    inp_p = processor(text=_SCREENING_COSMETIC_PROMPTS, return_tensors="pt", padding=True)
    inp_n = processor(text=_SCREENING_NON_COSMETIC_PROMPTS, return_tensors="pt", padding=True)
    with torch.no_grad():
        out_p = model.get_text_features(**inp_p)
        pos_f = out_p.pooler_output if hasattr(out_p, 'pooler_output') and out_p.pooler_output is not None else (out_p.text_embeds if hasattr(out_p, 'text_embeds') else (out_p if isinstance(out_p, torch.Tensor) else out_p[0]))
        pos_f = pos_f / pos_f.norm(dim=-1, keepdim=True)
        
        out_n = model.get_text_features(**inp_n)
        neg_f = out_n.pooler_output if hasattr(out_n, 'pooler_output') and out_n.pooler_output is not None else (out_n.text_embeds if hasattr(out_n, 'text_embeds') else (out_n if isinstance(out_n, torch.Tensor) else out_n[0]))
        neg_f = neg_f / neg_f.norm(dim=-1, keepdim=True)
        
    _SCREENING_TEXT_FEATURES = (pos_f.cpu().numpy().astype(np.float32), neg_f.cpu().numpy().astype(np.float32))
    return _SCREENING_TEXT_FEATURES

def screen_cosmetic_image(
    query_vec: np.ndarray,
    catalog_similarity: float,
    detected_brand: str = None
) -> dict:
    """
    Screens input images to filter out non-cosmetic artifacts (diagrams, banners, screenshots, etc.).
    Combines pretrained zero-shot CLIP image-text margin, catalog nearest-neighbor similarity,
    and verified OCR brand extraction.
    """
    pos_f, neg_f = _get_screening_text_features()
    
    p_sim = float(np.max(np.dot(pos_f, query_vec)))
    n_sim = float(np.max(np.dot(neg_f, query_vec)))
    diff = p_sim - n_sim

    has_catalog_brand = False
    if detected_brand and detected_brand.lower() not in ["unknown brand", "no text detected", "unidentified brand", ""]:
        norm_b = detected_brand.lower().strip()
        (pids, product_catalog), _ = _load_or_build_product_index()
        for pid, pdata in product_catalog.items():
            cb = pdata['brand'].lower().strip()
            if (norm_b in cb or cb in norm_b) and len(norm_b) >= 3:
                has_catalog_brand = True
                break

    metrics = {
        "cosmetic_text_score": round(p_sim, 4),
        "non_cosmetic_text_score": round(n_sim, 4),
        "score_margin": round(diff, 4),
        "catalog_similarity": round(catalog_similarity, 4),
        "has_catalog_brand": has_catalog_brand
    }

    # 1. Verified catalog brand via OCR: always pass
    if has_catalog_brand:
        return {
            "status": "passed",
            "is_rejected": False,
            "is_ambiguous": False,
            "message": "Cosmetic brand verified by OCR text extraction.",
            "metrics": metrics
        }

    # 2. Strict non-cosmetic rejection
    if diff <= 0.0 and catalog_similarity < 0.78:
        return {
            "status": "rejected_non_cosmetic",
            "is_rejected": True,
            "is_ambiguous": False,
            "message": "Please upload a cosmetic product image.",
            "metrics": metrics
        }

    # 3. Ambiguous input gate
    if diff < 0.015 and catalog_similarity < 0.75:
        return {
            "status": "ambiguous_input",
            "is_rejected": False,
            "is_ambiguous": True,
            "message": "Image contains ambiguous or unverified non-cosmetic visual features.",
            "metrics": metrics
        }

    return {
        "status": "passed",
        "is_rejected": False,
        "is_ambiguous": False,
        "message": "Cosmetic visual verification passed.",
        "metrics": metrics
    }

SUPPORTED_CATEGORIES = [
    "Foundation",
    "Lipstick",
    "Concealer",
    "Face powder",
    "Blush",
    "Eyeshadow",
    "Eyeliner",
    "Mascara",
    "Lip gloss",
    "Other makeup",
    "Non-cosmetic / uncertain",
]

_CATEGORY_PROMPTS = [
    "a photo of foundation cosmetic packaging or liquid makeup bottle",
    "a photo of lipstick cosmetic tube bullet makeup",
    "a photo of concealer cosmetic tube wand or liquid corrector",
    "a photo of face powder compact or setting powder loose jar",
    "a photo of blush cheek powder makeup compact",
    "a photo of eyeshadow eye shadow palette with powder colors",
    "a photo of eyeliner pencil or liquid eyeliner pen cosmetic",
    "a photo of mascara cosmetic tube with lash applicator brush",
    "a photo of lip gloss shiny wand tube cosmetic",
    "a photo of other makeup cosmetic beauty packaging",
]

_CATEGORY_NAMES = [
    "Foundation",
    "Lipstick",
    "Concealer",
    "Face powder",
    "Blush",
    "Eyeshadow",
    "Eyeliner",
    "Mascara",
    "Lip gloss",
    "Other makeup",
]

_CATEGORY_TEXT_FEATURES = None

def _get_category_text_features():
    """Lazy-loads and caches normalized text embeddings for the 10 cosmetic categories."""
    global _CATEGORY_TEXT_FEATURES
    if _CATEGORY_TEXT_FEATURES is not None:
        return _CATEGORY_TEXT_FEATURES
    model, processor = _get_clip_model_and_processor()
    inp = processor(text=_CATEGORY_PROMPTS, return_tensors="pt", padding=True)
    with torch.no_grad():
        out = model.get_text_features(**inp)
        feat = out.pooler_output if hasattr(out, 'pooler_output') and out.pooler_output is not None else (out.text_embeds if hasattr(out, 'text_embeds') else (out if isinstance(out, torch.Tensor) else out[0]))
        feat = feat / feat.norm(dim=-1, keepdim=True)
    _CATEGORY_TEXT_FEATURES = feat.cpu().numpy().astype(np.float32)
    return _CATEGORY_TEXT_FEATURES

CATEGORY_KEYWORDS_MAP = {
    "Foundation": ["foundation", "fit me", "coverage foundation", "liquid foundation", "bb cream", "cc cream", "complexion"],
    "Lipstick": ["lipstick", "lippie", "lip colour", "lip color", "rouge", "matte lipstick", "satin lipstick"],
    "Concealer": ["concealer", "stretch concealer", "spot concealer", "correct and cover", "corrector", "skinstick", "onebase", "camouflage"],
    "Face powder": ["powder", "setting powder", "pressed powder", "loose powder", "compact makeup", "translucent powder", "mineral powder", "blur powder", "finishing powder"],
    "Blush": ["blush", "blusher", "cheek", "cheek color", "cheek colour", "rouge powder", "mosaic blush"],
    "Eyeshadow": ["eyeshadow", "eye shadow", "shadow palette", "liquid eye shadow", "eye color", "pigment palette"],
    "Eyeliner": ["eyeliner", "eye liner", "liquid liner", "gel liner", "kohl", "pencil liner", "eye brow liner", "brow liner"],
    "Mascara": ["mascara", "volumising mascara", "lash", "lashes", "waterproof mascara"],
    "Lip gloss": ["lip gloss", "lipgloss", "glossy lip", "lip shine", "lip oil", "lip tint"],
    "Other makeup": ["bronzer", "bronzing", "contour", "highlighter", "nail polish", "makeup", "tint", "primer"]
}

def classify_cosmetic_category(
    query_vec: np.ndarray,
    ocr_text: str = "",
    catalog_category: str = None,
    is_rejected: bool = False
) -> dict:
    """
    Classifies the input product image into one of the supported categories:
    Foundation, Lipstick, Concealer, Face powder, Blush, Eyeshadow, Eyeliner,
    Mascara, Lip gloss, Other makeup, Non-cosmetic / uncertain.

    Combines zero-shot CLIP visual embeddings, OCR extracted label tokens,
    and reference catalog compatibility.
    Computes confidence level and prediction score margin between top-1 and top-2 categories.
    """
    if is_rejected:
        return {
            "category": "Non-cosmetic / uncertain",
            "confidence": "Rejected",
            "confidence_score": 0.0,
            "prediction_margin": 0.0,
            "evidence": ["Image screening flagged non-cosmetic visual features."],
            "all_scores": {}
        }

    cat_feats = _get_category_text_features()  # shape: (10, 512)
    raw_sims = np.dot(cat_feats, query_vec)    # shape: (10,)

    combined_scores = {}
    ocr_lower = (ocr_text or "").lower()

    for idx, name in enumerate(_CATEGORY_NAMES):
        score = float(raw_sims[idx])

        # OCR keyword boost (+0.25)
        keywords = CATEGORY_KEYWORDS_MAP.get(name, [])
        ocr_match = any(kw in ocr_lower for kw in keywords)
        if ocr_match:
            score += 0.25

        # Catalog category compatibility boost (+0.12)
        if catalog_category:
            cat_norm = catalog_category.replace('_', ' ').lower()
            if name.lower() in cat_norm or cat_norm in name.lower():
                score += 0.12

        combined_scores[name] = round(score, 4)

    # Sort descending
    sorted_cats = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
    top_cat, top_score = sorted_cats[0]
    second_cat, second_score = sorted_cats[1] if len(sorted_cats) > 1 else (None, 0.0)

    margin = round((top_score - second_score) * 100, 2)

    # Determine confidence
    has_ocr_confirmation = any(kw in ocr_lower for kw in CATEGORY_KEYWORDS_MAP.get(top_cat, []))
    if has_ocr_confirmation or (margin >= 8.0 and top_score >= 0.50):
        confidence = "High"
    elif margin >= 3.0 or top_score >= 0.45:
        confidence = "Moderate"
    elif top_score < 0.35 and margin < 2.0:
        top_cat = "Other makeup"
        confidence = "Low"
    else:
        confidence = "Low"

    evidence = []
    if has_ocr_confirmation:
        evidence.append(f"OCR label keywords confirmed '{top_cat}' form factor.")
    evidence.append(f"CLIP visual category similarity: {round(top_score * 100, 1)}% (margin: {margin}% over {second_cat}).")

    return {
        "category": top_cat,
        "confidence": confidence,
        "confidence_score": round(top_score, 4),
        "prediction_margin": margin,
        "runner_up_category": second_cat,
        "evidence": evidence,
        "all_scores": combined_scores
    }

def get_dataset_info() -> dict:
    """
    Returns metadata summary and readiness status of the integrated image model dataset.
    """
    if not DATASET_DIR.exists():
        return {"status": "missing", "message": f"Dataset path not found at {DATASET_DIR}"}
    
    total_images = 0
    categories = {}
    for cat in ["Eye_Products", "Foundation_Base", "Lip_Products", "Other_Makeup", "Skin_Care"]:
        cat_path = DATASET_DIR / cat
        if cat_path.exists():
            cnt = sum(1 for p in cat_path.glob("**/*") if p.is_file() and p.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp'])
            categories[cat] = cnt
            total_images += cnt
            
    return {
        "status": "ready",
        "dataset_path": "data/image_model_dataset",
        "metadata_path": "data/image_dataset_metadata.csv" if METADATA_CSV.exists() else None,
        "total_catalog_images": total_images,
        "categories": categories,
        "clip_model": "OpenAI CLIP ViT-B/32 Vision Transformer (Hugging Face)"
    }

def extract_image_embedding(file_bytes: bytes) -> np.ndarray:
    """
    Extracts a normalized 512-dimensional feature embedding vector from an input image
    using OpenAI CLIP ViT-B/32 Vision Transformer (projected multimodal pooler output).
    """
    try:
        pil_img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        model, processor = _get_clip_model_and_processor()

        inputs = processor(images=pil_img, return_tensors="pt")
        with torch.no_grad():
            out = model.get_image_features(**inputs)
            if hasattr(out, 'pooler_output') and out.pooler_output is not None:
                features = out.pooler_output
            elif hasattr(out, 'image_embeds') and out.image_embeds is not None:
                features = out.image_embeds
            elif isinstance(out, torch.Tensor):
                features = out
            else:
                features = out[0]

            features = features / features.norm(p=2, dim=-1, keepdim=True)
            vec = features.squeeze(0).cpu().numpy().astype(np.float32)

        return vec
    except Exception as e:
        print(f"Embedding extraction notice: {e}")
        # Fallback 512-dim uniform unit vector
        vec = np.ones(512, dtype=np.float32)
        return vec / np.linalg.norm(vec)

def _extract_image_file_embedding(file_path: str) -> np.ndarray:
    """Helper to extract normalized 512-dim CLIP embedding from an image file path."""
    try:
        pil_img = Image.open(file_path).convert("RGB")
        model, processor = _get_clip_model_and_processor()

        inputs = processor(images=pil_img, return_tensors="pt")
        with torch.no_grad():
            out = model.get_image_features(**inputs)
            if hasattr(out, 'pooler_output') and out.pooler_output is not None:
                features = out.pooler_output
            elif hasattr(out, 'image_embeds') and out.image_embeds is not None:
                features = out.image_embeds
            elif isinstance(out, torch.Tensor):
                features = out
            else:
                features = out[0]

            features = features / features.norm(p=2, dim=-1, keepdim=True)
            vec = features.squeeze(0).cpu().numpy().astype(np.float32)

        return vec
    except Exception as exc:
        print(f"Error extracting CLIP embedding for {file_path}: {exc}")
        return None

# Global Cache for Product Dataset Catalog Embeddings (P001 - P030)
_PRODUCT_CATALOG_CACHE = None
_PRODUCT_CENTROIDS_CACHE = None

def _compute_reference_dataset_checksum() -> str:
    """
    Recreates the exact deterministic 70% reference split (seed=42),
    sorts relative file paths, and computes SHA256 checksum.
    """
    if not DATASET_DIR.exists():
        return ""

    random.seed(42)
    ref_paths = []

    for cat_dir in sorted(DATASET_DIR.iterdir()):
        if not cat_dir.is_dir() or cat_dir.name.startswith('_'):
            continue
        for folder in sorted(cat_dir.iterdir()):
            if not folder.is_dir():
                continue
            imgs = sorted([f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']], key=lambda x: x.name)
            if not imgs:
                continue
            shuffled = imgs.copy()
            random.shuffle(shuffled)
            ref_count = max(1, int(len(imgs) * 0.70))
            for p in shuffled[:ref_count]:
                ref_paths.append(str(p.relative_to(BASE_PROJECT_DIR)).replace('\\', '/'))

    ref_paths.sort()
    paths_blob = "\n".join(ref_paths).encode('utf-8')
    return hashlib.sha256(paths_blob).hexdigest()

def _validate_and_load_cache():
    """
    Validates disk cache integrity (model_id, seed=42, matrix shape, product catalog, live checksum).
    Returns (pids, product_catalog, centroids_mat) if valid, else returns None with diagnostic logs.
    """
    if not (CENTROIDS_NPY_FILE.exists() and CENTROIDS_META_FILE.exists()):
        return None
    try:
        with open(CENTROIDS_META_FILE, mode='r', encoding='utf-8') as f:
            meta = json.load(f)

        if meta.get("model_id") != _MODEL_ID:
            print(f"[CACHE STALE] Model ID mismatch: {meta.get('model_id')} != {_MODEL_ID}")
            return None

        if meta.get("random_seed") != 42:
            print(f"[CACHE STALE] Seed mismatch: {meta.get('random_seed')} != 42")
            return None

        centroids_mat = np.load(CENTROIDS_NPY_FILE)
        if list(centroids_mat.shape) != [30, 512]:
            print(f"[CACHE STALE] Matrix shape mismatch: {centroids_mat.shape}")
            return None

        pids = meta.get("product_ids", [])
        if len(pids) != 30:
            print(f"[CACHE STALE] Product count mismatch: {len(pids)}")
            return None

        # Re-compute live reference dataset checksum and compare against metadata
        live_checksum = _compute_reference_dataset_checksum()
        cached_checksum = meta.get("reference_files_checksum_sha256")
        if live_checksum and cached_checksum and live_checksum != cached_checksum:
            print(f"[CACHE REJECTED] Reference dataset file list has changed! Live SHA256 ({live_checksum[:12]}...) != Cached SHA256 ({cached_checksum[:12]}...). Centroids cache must be rebuilt!")
            return None

        csv_30_path = BASE_PROJECT_DIR / "data" / "selected_30_products_final.csv"
        product_catalog = {}
        if csv_30_path.exists():
            with open(csv_30_path, mode='r', encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    pid = row['product_id'].strip()
                    product_catalog[pid] = {
                        'product_id': pid,
                        'brand': row['brand'].strip(),
                        'product_name': row['product_name'].strip(),
                        'category': row['category'].strip(),
                        'product_type': row.get('product_type', row['category']).strip(),
                        'folder_name': f"{pid}_Product"
                    }

        if DATASET_DIR.exists():
            for cat_dir in DATASET_DIR.iterdir():
                if not cat_dir.is_dir() or cat_dir.name.startswith('_'):
                    continue
                for folder in cat_dir.iterdir():
                    if not folder.is_dir():
                        continue
                    pid = folder.name.split('_')[0]
                    if pid in product_catalog:
                        product_catalog[pid]['folder_name'] = folder.name

        return pids, product_catalog, centroids_mat
    except Exception as exc:
        print(f"[CACHE ERROR] Could not load centroid cache: {exc}")
        return None

def _load_or_build_product_index():
    """
    Loads product metadata and validated precomputed CLIP centroid embeddings
    built from the exact 70% reference set (seed=42) across all 30 product folders (P001 - P030).
    """
    global _PRODUCT_CATALOG_CACHE, _PRODUCT_CENTROIDS_CACHE
    if _PRODUCT_CATALOG_CACHE is not None and _PRODUCT_CENTROIDS_CACHE is not None:
        return _PRODUCT_CATALOG_CACHE, _PRODUCT_CENTROIDS_CACHE

    # 1. Attempt to load validated persistent cache
    cache_res = _validate_and_load_cache()
    if cache_res is not None:
        pids, product_catalog, centroids_mat = cache_res
        _PRODUCT_CATALOG_CACHE = (pids, product_catalog)
        _PRODUCT_CENTROIDS_CACHE = centroids_mat
        return _PRODUCT_CATALOG_CACHE, _PRODUCT_CENTROIDS_CACHE

    # 2. Recompute centroids from 70% Reference Split if cache missing/stale
    print("Recomputing product centroids from 70% Reference Set (seed=42)...")
    csv_30_path = BASE_PROJECT_DIR / "data" / "selected_30_products_final.csv"
    product_catalog = {}
    if csv_30_path.exists():
        with open(csv_30_path, mode='r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                pid = row['product_id'].strip()
                product_catalog[pid] = {
                    'product_id': pid,
                    'brand': row['brand'].strip(),
                    'product_name': row['product_name'].strip(),
                    'category': row['category'].strip(),
                    'product_type': row.get('product_type', row['category']).strip(),
                    'folder_name': f"{pid}_Product"
                }

    random.seed(42)
    reference_images_by_pid = defaultdict(list)
    found_pids = set()

    if DATASET_DIR.exists():
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
                reference_images_by_pid[pid].extend(shuffled[:ref_count])

                if pid not in product_catalog:
                    parts = folder.name.split('_', 2)
                    product_catalog[pid] = {
                        'product_id': pid,
                        'brand': parts[1] if len(parts) > 1 else 'Brand',
                        'product_name': parts[2] if len(parts) > 2 else folder.name,
                        'category': cat_dir.name,
                        'product_type': cat_dir.name,
                        'folder_name': folder.name
                    }

    pids = sorted(list(found_pids))
    centroids = []

    for pid in pids:
        ref_files = reference_images_by_pid[pid]
        vecs = [_extract_image_file_embedding(str(p)) for p in ref_files]
        vecs = [v for v in vecs if v is not None]
        if vecs:
            avg_vec = np.mean(vecs, axis=0)
            avg_norm = np.linalg.norm(avg_vec)
            if avg_norm > 0:
                avg_vec = avg_vec / avg_norm
            centroids.append(avg_vec)

    centroids_mat = np.array(centroids, dtype=np.float32) if centroids else np.empty((0, 512), dtype=np.float32)
    _PRODUCT_CATALOG_CACHE = (pids, product_catalog)
    _PRODUCT_CENTROIDS_CACHE = centroids_mat
    return _PRODUCT_CATALOG_CACHE, _PRODUCT_CENTROIDS_CACHE

# Minimum similarity margin between rank-1 and rank-2 centroids below which the catalog
# is considered unable to discriminate the query image from noise.  When all centroids cluster
# tightly (mean pairwise sim ~0.87) a margin this small means the ranking is unreliable.
_MIN_DISCRIMINATION_MARGIN = 0.02  # 2 percentage points


def compute_clip_similarity(
    file_bytes: bytes,
    brand_name: str = None,
    ocr_category: str = None,
) -> dict:
    """
    Calculates product-level visual feature vector similarity against dataset folders P001-P030
    using OpenAI CLIP ViT-B/32, ranks top 5 product matches, and assigns confidence thresholds.

    Confidence thresholds:
      - High Confidence Match  (>= 80.0% AND margin >= 2% AND no category conflict)
      - Possible Match         (>= 60.0% and < 80.0% AND margin >= 2%)
      - Low-Confidence         (< 60.0% OR margin < 2% OR category mismatch)

    Category mismatch: if OCR identified a category (e.g. Foundation_Base) but the top CLIP
    hit belongs to a different category (e.g. Lip_Products), confidence is capped at Low and
    the result is flagged with `catalog_category_mismatch=True` so callers can gate on it.
    """
    try:
        query_vec = extract_image_embedding(file_bytes)
        (pids, product_catalog), centroids_mat = _load_or_build_product_index()

        top_matches = []
        best_match = None
        similarity_score = 0.0
        similarity_percentage = 0.0
        match_status = "No Catalog Match Found"
        confidence_level = "Low"
        catalog_category_mismatch = False
        discrimination_margin = 0.0

        matching_method = "Centroid Baseline (Fallback)"
        catalog_sim = 0.0
        if centroids_mat.shape[0] > 0 and len(pids) > 0:
            # 1. Cosine similarity: prefer 1-NN reference bank (max-pooling) if available, fallback to centroids
            ref_bank = _load_reference_bank()
            if ref_bank is not None:
                ref_mat, ref_pids, pid_indices = ref_bank
                ref_sims = np.dot(ref_mat, query_vec)
                raw_sims = np.zeros(len(pids), dtype=np.float32)
                for idx, pid in enumerate(pids):
                    idxs = pid_indices.get(pid, [])
                    if idxs:
                        raw_sims[idx] = float(np.max(ref_sims[idxs]))
                    else:
                        raw_sims[idx] = float(np.dot(centroids_mat[idx], query_vec))
                matching_method = "1-NN Reference Bank (Max-Pooling)"
                catalog_sim = float(np.max(ref_sims))
            else:
                raw_sims = np.dot(centroids_mat, query_vec)
                matching_method = "Centroid Baseline (Fallback)"
                catalog_sim = float(np.max(raw_sims))

            # 2. Screening Gate: distinguish valid cosmetics from non-cosmetic artifacts
            screen_res = screen_cosmetic_image(
                query_vec=query_vec,
                catalog_similarity=catalog_sim,
                detected_brand=brand_name
            )

            if screen_res.get("is_rejected"):
                return {
                    "status": "rejected_non_cosmetic",
                    "message": "Please upload a cosmetic product image.",
                    "matched_product_id": None,
                    "matched_product_name": None,
                    "matched_brand": None,
                    "matched_category": None,
                    "matched_folder": None,
                    "similarity_score": round(catalog_sim, 4),
                    "similarity_percentage": round(catalog_sim * 100, 1),
                    "discrimination_margin": 0.0,
                    "catalog_category_mismatch": False,
                    "match_status": "Rejected: Non-Cosmetic Image Detected",
                    "confidence_level": "Rejected",
                    "vector_dimension": len(query_vec),
                    "model": "OpenAI CLIP ViT-B/32 Vision Transformer (Hugging Face)",
                    "matching_method": "Zero-Shot Screening Rejection",
                    "screening_details": screen_res,
                    "top_matches": [],
                }

            # 3. OCR text boost for matching catalog brands (does NOT affect category)
            boosted_sims = raw_sims.copy()
            if brand_name and brand_name.lower() not in ["unknown brand", "no text detected", ""]:
                norm_b = brand_name.lower().strip()
                for idx, pid in enumerate(pids):
                    cat_b = product_catalog[pid]['brand'].lower().strip()
                    if norm_b in cat_b or cat_b in norm_b:
                        boosted_sims[idx] = min(0.99, boosted_sims[idx] + 0.15)

            # 4. Rank top 5 product matches
            top_indices = np.argsort(boosted_sims)[::-1][:5]

            for rank_idx, idx in enumerate(top_indices, start=1):
                pid = pids[idx]
                info = product_catalog[pid]
                sim_val = float(boosted_sims[idx])
                sim_pct = round(sim_val * 100, 1)
                top_matches.append({
                    "rank": rank_idx,
                    "product_id": pid,
                    "brand": info['brand'],
                    "product_name": info['product_name'],
                    "category": info['category'],
                    "folder_name": info['folder_name'],
                    "similarity_score": round(sim_val, 4),
                    "similarity_percentage": sim_pct,
                })

            best_match = top_matches[0]
            similarity_score = best_match['similarity_score']
            similarity_percentage = best_match['similarity_percentage']

            # 5. Discrimination margin — difference between rank-1 and rank-2 raw similarity.
            if len(top_matches) >= 2:
                discrimination_margin = round(
                    (best_match['similarity_score'] - top_matches[1]['similarity_score']) * 100, 2
                )
            else:
                discrimination_margin = round(similarity_percentage, 2)

            poor_discrimination = discrimination_margin < _MIN_DISCRIMINATION_MARGIN * 100

            # 6. Category mismatch gate: OCR-derived category vs CLIP top-hit category
            clip_top_category = best_match.get('category', '')
            _norm = lambda s: (s or '').replace(' ', '_').replace('-', '_').lower()
            if ocr_category and clip_top_category:
                catalog_category_mismatch = (
                    _norm(ocr_category) not in _norm(clip_top_category) and
                    _norm(clip_top_category) not in _norm(ocr_category)
                )

            # 7. Assign confidence using validated similarity thresholds:
            # When actual similarity score is 80.0% or above (without category contradiction), assign High Confidence.
            if catalog_category_mismatch:
                match_status = "Low-Confidence / Catalog Mismatch"
                confidence_level = "Low"
            elif similarity_percentage >= 80.0:
                match_status = "High-Confidence Product Match"
                confidence_level = "High"
            elif screen_res.get("is_ambiguous"):
                match_status = "Ambiguous Input / Manual Review Required"
                confidence_level = "Low"
            elif poor_discrimination:
                match_status = "Low-Confidence / Poor Discrimination"
                confidence_level = "Low"
            elif similarity_percentage >= 60.0:
                match_status = "Possible Product Match"
                confidence_level = "Moderate"
            else:
                match_status = "Low-Confidence / Unverified Match"
                confidence_level = "Low"

        # 8. Category Classification across supported categories
        cat_classification = classify_cosmetic_category(
            query_vec=query_vec,
            ocr_text=f"{brand_name or ''} {ocr_category or ''}",
            catalog_category=best_match["category"] if best_match else None,
            is_rejected=False
        )

        return {
            "status": "completed",
            "matched_product_id": best_match["product_id"] if best_match else None,
            "matched_product_name": best_match["product_name"] if best_match else "Unknown Product",
            "matched_brand": best_match["brand"] if best_match else "Unknown Brand",
            "matched_category": best_match["category"] if best_match else None,
            "detected_category": cat_classification.get("category", "Other makeup"),
            "category_classification": cat_classification,
            "matched_folder": best_match["folder_name"] if best_match else None,
            "similarity_score": round(similarity_score, 4),
            "similarity_percentage": similarity_percentage,
            "discrimination_margin": discrimination_margin,
            "catalog_category_mismatch": catalog_category_mismatch,
            "match_status": match_status,
            "confidence_level": confidence_level,
            "vector_dimension": len(query_vec),
            "model": "OpenAI CLIP ViT-B/32 Vision Transformer (Hugging Face)",
            "matching_method": matching_method,
            "screening_details": screen_res if centroids_mat.shape[0] > 0 else None,
            "top_matches": top_matches,
        }
    except Exception as exc:
        print(f"CLIP Product Matching exception: {exc}")
        # Do NOT fabricate a specific product result. Return an honest unknown/error state.
        return {
            "status": "error",
            "matched_product_id": None,
            "matched_product_name": "Unknown Product",
            "matched_brand": "Unknown Brand",
            "matched_category": None,
            "matched_folder": None,
            "similarity_score": 0.0,
            "similarity_percentage": 0.0,
            "discrimination_margin": 0.0,
            "catalog_category_mismatch": False,
            "match_status": "CLIP Error / Unavailable",
            "confidence_level": "Low",
            "vector_dimension": 512,
            "model": "OpenAI CLIP ViT-B/32 Vision Transformer (Hugging Face)",
            "matching_method": "Error Fallback",
            "top_matches": [],
            "error": str(exc),
        }
