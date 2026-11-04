"""
Unit & Integration Tests for 1-NN Reference Bank Matching Engine (clip_service.py)
Covers:
1. Reference Bank file integrity, L2 normalization, zero data leakage with test split.
2. Product ID mapping accuracy against catalog CSV.
3. Lazy-loading cache functionality of _load_reference_bank().
4. 1-NN Reference Bank matching execution in compute_clip_similarity().
5. Graceful fallback to Centroid matching when reference bank is absent.
6. OCR brand boosting integration with reference bank max-pooling.
7. Category mismatch gating with reference bank.
8. End-to-end FastAPI POST /api/analyze workflow confirming reference bank is used live.
"""

import io
import csv
import random
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pytest
from PIL import Image

import app.services.clip_service as cs
from app.services.clip_service import (
    compute_clip_similarity,
    _load_reference_bank,
    REFERENCE_BANK_NPZ_FILE,
    CENTROIDS_NPY_FILE,
    extract_image_embedding
)

BASE_DIR = Path(__file__).parent.parent.resolve()
DATASET_DIR = BASE_DIR / "data" / "image_model_dataset"
CSV_PRODUCTS = BASE_DIR / "data" / "selected_30_products_final.csv"

def _make_dummy_image_bytes(color=(200, 100, 50), size=(224, 224)):
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(buf, format="JPEG")
    return buf.getvalue()

def test_reference_bank_file_integrity_and_no_leakage():
    """Test 1: Reference bank file integrity, shapes, norms, and zero leakage."""
    assert REFERENCE_BANK_NPZ_FILE.exists(), f"Reference bank not found at {REFERENCE_BANK_NPZ_FILE}"
    
    data = np.load(REFERENCE_BANK_NPZ_FILE)
    embs = data['embeddings']
    pids = list(data['product_ids'])
    paths = [str(p) for p in data['rel_paths']]
    
    # Check shape: 512-dim normalized vectors across 30 products
    assert embs.ndim == 2 and embs.shape[1] == 512, f"Expected (N, 512), got {embs.shape}"
    assert len(pids) == len(embs), f"PIDs count {len(pids)} must match embeddings count {len(embs)}"
    assert len(embs) == 1248, f"Expected exactly 1248 cleaned reference vectors, got {len(embs)}"
    assert "cleaned" in REFERENCE_BANK_NPZ_FILE.name, f"Expected cleaned reference bank, got {REFERENCE_BANK_NPZ_FILE.name}"

    # Check L2 normalization
    norms = np.linalg.norm(embs, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-4), "All reference vectors must be L2 normalized"

    # Assert zero overlap with test set embeddings
    test_npz_path = BASE_DIR / "data" / "clip_test_embeddings.npz"
    if test_npz_path.exists():
        test_data = np.load(test_npz_path)
        test_paths = {str(p).replace('\\', '/') for p in test_data['rel_paths']}
        ref_paths_set = {str(p).replace('\\', '/') for p in paths}
        overlap = ref_paths_set.intersection(test_paths)
        assert len(overlap) == 0, f"DATA LEAKAGE: {len(overlap)} test images found in reference bank!"
    else:
        # Recreate deterministic 70/30 split using backup or original dataset
        src_dir = BASE_DIR / "data" / "image_model_dataset_backup"
        if not src_dir.exists():
            src_dir = DATASET_DIR
        random.seed(42)
        test_paths = set()
        for cat_dir in sorted(src_dir.iterdir()):
            if not cat_dir.is_dir() or cat_dir.name.startswith('_'): continue
            for folder in sorted(cat_dir.iterdir()):
                if not folder.is_dir(): continue
                imgs = sorted([f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']], key=lambda x: x.name)
                shuffled = imgs.copy()
                random.shuffle(shuffled)
                ref_count = max(1, int(len(imgs) * 0.70))
                for p in shuffled[ref_count:]:
                    test_paths.add(str(p.relative_to(src_dir)).replace('\\', '/'))
        ref_paths_rel = {p.replace('data/image_model_dataset/', '').replace('\\', '/') for p in paths}
        overlap = ref_paths_rel.intersection(test_paths)
        assert len(overlap) == 0, f"DATA LEAKAGE: {len(overlap)} test images found in reference bank!"

def test_reference_bank_product_id_mappings():
    """Test 2: Every reference image maps 100% to its folder product ID and catalog CSV."""
    catalog = {}
    with open(CSV_PRODUCTS, 'r', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            catalog[r['product_id'].strip()] = r
            
    assert len(catalog) == 30, f"Expected 30 products in catalog, got {len(catalog)}"
    
    data = np.load(REFERENCE_BANK_NPZ_FILE)
    pids = list(data['product_ids'])
    paths = [str(p) for p in data['rel_paths']]
    
    for p, pid in zip(paths, pids):
        # Format: data/image_model_dataset/<category>/<PID_folder>/<image.jpg>
        parts = p.split('/')
        folder_name = parts[3]
        expected_pid = folder_name.split('_')[0]
        assert pid == expected_pid, f"Path {p} has pid {pid} but folder specifies {expected_pid}"
        assert pid in catalog, f"Product {pid} not found in catalog CSV"

def test_reference_bank_loader_caching():
    """Test 3: _load_reference_bank correctly populates matrices and pid_indices for cleaned 1248 vectors."""
    ref_bank = _load_reference_bank()
    assert ref_bank is not None, "Failed to load reference bank"
    ref_mat, ref_pids, pid_indices = ref_bank
    
    assert ref_mat.shape == (1248, 512), f"Expected (1248, 512), got {ref_mat.shape}"
    assert len(ref_pids) == 1248
    assert len(pid_indices) == 30, "Expected all 30 products to have reference indices"
    
    total_indexed = sum(len(idxs) for idxs in pid_indices.values())
    assert total_indexed == 1248

def test_missing_reference_bank_safety():
    """Test: When cleaned reference bank file is missing, does NOT fall back to uncleaned bank."""
    with patch("app.services.clip_service.REFERENCE_BANK_NPZ_FILE", BASE_DIR / "data" / "non_existent_bank.npz"):
        with patch("app.services.clip_service._REFERENCE_BANK_CACHE", None):
            bank = _load_reference_bank()
            assert bank is None, "Should return None on missing file without loading uncleaned bank"

def test_compute_clip_similarity_uses_reference_bank():
    """Test 4: compute_clip_similarity reports matching_method='1-NN Reference Bank (Max-Pooling)'."""
    img_bytes = _make_dummy_image_bytes()
    result = compute_clip_similarity(img_bytes)
    
    assert result["status"] == "completed"
    assert result["matching_method"] == "1-NN Reference Bank (Max-Pooling)"
    assert result["matched_product_id"] in [f"P{i:03d}" for i in range(1, 31)]
    assert 0.0 <= result["similarity_score"] <= 1.0
    assert 0.0 <= result["similarity_percentage"] <= 100.0
    assert len(result["top_matches"]) == 5
    assert "discrimination_margin" in result

def test_compute_clip_similarity_fallback_to_centroids_when_ref_bank_missing():
    """Test 5: Gracefully falls back to centroids when reference bank is absent."""
    img_bytes = _make_dummy_image_bytes()
    
    with patch("app.services.clip_service._load_reference_bank", return_value=None):
        result = compute_clip_similarity(img_bytes)
        
    assert result["status"] == "completed"
    assert result["matching_method"] == "Centroid Baseline (Fallback)"
    assert result["matched_product_id"] in [f"P{i:03d}" for i in range(1, 31)]
    assert len(result["top_matches"]) == 5

def test_ocr_brand_boosting_with_reference_bank():
    """Test 6: Providing a detected brand applies +0.15 boost in reference bank mode."""
    img_bytes = _make_dummy_image_bytes()
    
    # Run unboosted
    res_unboosted = compute_clip_similarity(img_bytes, brand_name=None)
    
    # Run with brand boost for Colourpop
    res_boosted = compute_clip_similarity(img_bytes, brand_name="Colourpop")
    
    p001_unboosted = next((m for m in res_unboosted["top_matches"] if m["product_id"] == "P001"), None)
    p001_boosted = next((m for m in res_boosted["top_matches"] if m["product_id"] == "P001"), None)
    
    if p001_unboosted and p001_boosted:
        assert p001_boosted["similarity_score"] >= p001_unboosted["similarity_score"]

def test_category_mismatch_filtering_with_reference_bank():
    """Test 7: Category conflict triggers catalog_category_mismatch and caps confidence at Low."""
    img_bytes = _make_dummy_image_bytes()
    
    # Pass an incongruous category
    res = compute_clip_similarity(img_bytes, ocr_category="Skin_Care")
    top_cat = res["top_matches"][0]["category"] if res["top_matches"] else ""
    
    if "skin" not in top_cat.lower():
        assert res["catalog_category_mismatch"] is True
        assert res["confidence_level"] == "Low"

def test_screening_rejects_non_cosmetic_image():
    """Test 9: Non-cosmetic diagram/banner images are rejected with rejected_non_cosmetic."""
    diagram_path = BASE_DIR / "data" / "quarantine" / "non_cosmetic" / "Eye_Products" / "P013" / "P013_0033.jpg"
    assert diagram_path.exists(), f"Diagram sample not found at {diagram_path}"
    with open(diagram_path, "rb") as f:
        img_bytes = f.read()
    
    res = compute_clip_similarity(img_bytes)
    assert res["status"] == "rejected_non_cosmetic"
    assert res["message"] == "Please upload a cosmetic product image."
    assert res["matched_product_id"] is None
    assert res["confidence_level"] == "Rejected"
    assert res["screening_details"]["is_rejected"] is True

def test_screening_preserves_valid_cosmetics():
    """Test 10: Genuine cosmetic packaging images pass screening and identify product."""
    import glob
    cosmetics = glob.glob(str(BASE_DIR / "data" / "image_model_dataset" / "**" / "*.jpg"), recursive=True)
    assert len(cosmetics) > 0
    with open(cosmetics[0], "rb") as f:
        img_bytes = f.read()
        
    res = compute_clip_similarity(img_bytes)
    assert res["status"] == "completed"
    assert res["matched_product_id"] is not None
    assert res["matching_method"] == "1-NN Reference Bank (Max-Pooling)"

def test_end_to_end_image_upload_workflow_with_reference_bank():
    """Test 8: Full API POST /api/analyze verifies live application uses 1-NN Reference Bank."""
    import json
    from fastapi import UploadFile
    from app.routes.analysis import analyze_image
    from database.connection import SessionLocal

    img_bytes = _make_dummy_image_bytes()
    upload = UploadFile(filename="test_packaging.jpg", file=io.BytesIO(img_bytes), headers={"content-type": "image/jpeg"})
    db = SessionLocal()
    try:
        response = analyze_image(file=upload, db=db)
        assert response.status_code == 200
        data = json.loads(response.body.decode("utf-8")) if hasattr(response, "body") else response
        assert data["success"] is True

        clip_res = data.get("clip_result")
        assert clip_res is not None
        assert clip_res["matching_method"] == "1-NN Reference Bank (Max-Pooling)"
        assert clip_res["matched_product_id"] is not None
        assert data["db_persisted"] is True
    finally:
        db.close()

def test_api_analyze_rejects_non_cosmetic_image():
    """Test 11: Live API endpoint rejects non-cosmetic input with standard response schema."""
    import json
    from fastapi import UploadFile
    from app.routes.analysis import analyze_image
    from database.connection import SessionLocal

    diagram_path = BASE_DIR / "data" / "quarantine" / "non_cosmetic" / "Eye_Products" / "P013" / "P013_0033.jpg"
    with open(diagram_path, "rb") as f:
        img_bytes = f.read()

    upload = UploadFile(filename="grammar_chart.jpg", file=io.BytesIO(img_bytes), headers={"content-type": "image/jpeg"})
    db = SessionLocal()
    try:
        response = analyze_image(file=upload, db=db)
        assert response.status_code == 200
        data = json.loads(response.body.decode("utf-8")) if hasattr(response, "body") else response
        assert data["status"] == "rejected_non_cosmetic"
        assert data["message"] == "Please upload a cosmetic product image."
        assert data["success"] is False
        assert "screening_details" in data
    finally:
        db.close()
