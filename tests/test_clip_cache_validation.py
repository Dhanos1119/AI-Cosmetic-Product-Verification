"""
Unit Tests for Genuine CLIP Centroid Cache Validation & Checksum Invalidation
"""

import sys
import json
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.resolve()
AI_SERVICE_DIR = BASE_DIR / "ai-service"
SITE_PACKAGES_DIR = AI_SERVICE_DIR / "venv" / "Lib" / "site-packages"

if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))
if SITE_PACKAGES_DIR.exists() and str(SITE_PACKAGES_DIR) not in sys.path:
    sys.path.insert(0, str(SITE_PACKAGES_DIR))

import numpy as np

import app.services.clip_service as cs
from app.services.clip_service import (
    _compute_reference_dataset_checksum,
    _validate_and_load_cache,
    CENTROIDS_NPY_FILE,
    CENTROIDS_META_FILE,
    _MODEL_ID
)

def test_deterministic_checksum_generation():
    """Test 6: Deterministic Checksum Generation"""
    print("[TEST 6] Testing Deterministic Checksum Generation...")
    hash1 = _compute_reference_dataset_checksum()
    hash2 = _compute_reference_dataset_checksum()
    assert hash1 != "", "Checksum should not be empty when dataset exists"
    assert hash1 == hash2, "Checksum generation must be 100% deterministic"
    print(f"  PASS! SHA256 Checksum: {hash1[:16]}...")

def test_valid_cache_loading():
    """Test 1: Valid Cache Loading"""
    print("[TEST 1] Testing Valid Cache Loading...")
    result = _validate_and_load_cache()
    assert result is not None, "Valid cache should load successfully"
    pids, product_catalog, centroids_mat = result
    assert len(pids) == 30
    assert centroids_mat.shape == (30, 512)
    assert np.allclose(np.linalg.norm(centroids_mat, axis=1), 1.0, atol=1e-4)
    print("  PASS! Loaded 30 valid centroids (30, 512).")

def test_cache_rejection_changed_checksum(tmp_path):
    """Test 2: Changed File List Checksum Rejection"""
    print("[TEST 2] Testing Changed File List Checksum Rejection...")
    fake_meta = tmp_path / "fake_meta.json"
    fake_npy = tmp_path / "fake_centroids.npy"

    with open(CENTROIDS_META_FILE, "r", encoding="utf-8") as f:
        meta = json.load(f)

    meta["reference_files_checksum_sha256"] = "invalid_sha256_hash_1234567890abcdef"
    with open(fake_meta, "w", encoding="utf-8") as f:
        json.dump(meta, f)

    shutil.copy(CENTROIDS_NPY_FILE, fake_npy)

    orig_meta, orig_npy = cs.CENTROIDS_META_FILE, cs.CENTROIDS_NPY_FILE
    try:
        cs.CENTROIDS_META_FILE, cs.CENTROIDS_NPY_FILE = fake_meta, fake_npy
        result = _validate_and_load_cache()
        assert result is None, "Cache with invalid dataset checksum must be rejected"
        print("  PASS! Cache rejected due to checksum mismatch.")
    finally:
        cs.CENTROIDS_META_FILE, cs.CENTROIDS_NPY_FILE = orig_meta, orig_npy

def test_cache_rejection_missing_file():
    """Test 3: Missing Cache File"""
    print("[TEST 3] Testing Missing Cache File Rejection...")
    orig_npy = cs.CENTROIDS_NPY_FILE
    try:
        cs.CENTROIDS_NPY_FILE = Path("non_existent_file.npy")
        result = _validate_and_load_cache()
        assert result is None, "Missing cache file must return None"
        print("  PASS! Missing cache file safely rejected.")
    finally:
        cs.CENTROIDS_NPY_FILE = orig_npy

def test_cache_rejection_changed_model_id(tmp_path):
    """Test 4: Changed Model ID Rejection"""
    print("[TEST 4] Testing Changed Model ID Rejection...")
    fake_meta = tmp_path / "fake_meta.json"
    fake_npy = tmp_path / "fake_centroids.npy"

    with open(CENTROIDS_META_FILE, "r", encoding="utf-8") as f:
        meta = json.load(f)

    meta["model_id"] = "different-model-checkpoint"
    with open(fake_meta, "w", encoding="utf-8") as f:
        json.dump(meta, f)

    shutil.copy(CENTROIDS_NPY_FILE, fake_npy)

    orig_meta, orig_npy = cs.CENTROIDS_META_FILE, cs.CENTROIDS_NPY_FILE
    try:
        cs.CENTROIDS_META_FILE, cs.CENTROIDS_NPY_FILE = fake_meta, fake_npy
        result = _validate_and_load_cache()
        assert result is None, "Cache with mismatched model ID must be rejected"
        print("  PASS! Cache rejected due to model ID mismatch.")
    finally:
        cs.CENTROIDS_META_FILE, cs.CENTROIDS_NPY_FILE = orig_meta, orig_npy

def test_cache_rejection_invalid_matrix_shape(tmp_path):
    """Test 5: Invalid Matrix Shape Rejection"""
    print("[TEST 5] Testing Invalid Matrix Shape Rejection...")
    fake_meta = tmp_path / "fake_meta.json"
    fake_npy = tmp_path / "fake_centroids.npy"

    with open(CENTROIDS_META_FILE, "r", encoding="utf-8") as f:
        meta = json.load(f)

    meta["matrix_shape"] = [25, 512]
    with open(fake_meta, "w", encoding="utf-8") as f:
        json.dump(meta, f)

    bad_matrix = np.random.randn(25, 512).astype(np.float32)
    np.save(fake_npy, bad_matrix)

    orig_meta, orig_npy = cs.CENTROIDS_META_FILE, cs.CENTROIDS_NPY_FILE
    try:
        cs.CENTROIDS_META_FILE, cs.CENTROIDS_NPY_FILE = fake_meta, fake_npy
        result = _validate_and_load_cache()
        assert result is None, "Cache with invalid matrix shape must be rejected"
        print("  PASS! Cache rejected due to matrix shape mismatch.")
    finally:
        cs.CENTROIDS_META_FILE, cs.CENTROIDS_NPY_FILE = orig_meta, orig_npy

def run_all_tests():
    print("=" * 70)
    print("RUNNING FOCUSED CLIP CENTROID CACHE VALIDATION TESTS")
    print("=" * 70)
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        test_deterministic_checksum_generation()
        test_valid_cache_loading()
        test_cache_rejection_changed_checksum(tmp_path)
        test_cache_rejection_missing_file()
        test_cache_rejection_changed_model_id(tmp_path)
        test_cache_rejection_invalid_matrix_shape(tmp_path)
    print("=" * 70)
    print("ALL 6 CACHE VALIDATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_all_tests()
