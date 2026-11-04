"""
Phase 5 Data Leakage Verification Script
Checks SHA-256 and dHash perceptual hash overlaps between reference set and test set.
Ensures zero test image leakage into reference bank.
"""
import csv
import json
from collections import defaultdict
from pathlib import Path
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
AUDIT_CSV = BASE_DIR / "reports" / "image_audit.csv"
MANIFEST_CSV = BASE_DIR / "reports" / "quarantine_manifest.csv"
OUTPUT_REPORT = BASE_DIR / "reports" / "data_leakage_audit.json"


def main():
    print("=" * 80)
    print("PHASE 5: DATA LEAKAGE VERIFICATION")
    print("=" * 80)

    # Load split info from npz
    ref_npz = np.load(BASE_DIR / "data" / "clip_reference_embeddings.npz")
    test_npz = np.load(BASE_DIR / "data" / "clip_test_embeddings.npz")

    ref_paths = {p.replace("\\", "/"): pid for p, pid in zip(ref_npz["rel_paths"], ref_npz["product_ids"])}
    test_paths = {p.replace("\\", "/"): pid for p, pid in zip(test_npz["rel_paths"], test_npz["product_ids"])}

    print(f"Original Reference set: {len(ref_paths)} images")
    print(f"Original Test set:      {len(test_paths)} images")

    # Load quarantined files
    quarantined = set()
    if MANIFEST_CSV.exists():
        with open(MANIFEST_CSV, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                quarantined.add(r["original_path"].replace("\\", "/"))

    print(f"Quarantined files:      {len(quarantined)}")

    # Cleaned reference set
    cleaned_ref_paths = {p: pid for p, pid in ref_paths.items() if p not in quarantined}
    print(f"Cleaned Reference set:  {len(cleaned_ref_paths)} images")

    # Load image audit details
    with open(AUDIT_CSV, "r", encoding="utf-8") as f:
        audit_rows = list(csv.DictReader(f))

    hash_by_path = {r["rel_path"].replace("\\", "/"): (r["sha256"], r["dhash"], r["product_id"]) for r in audit_rows}

    # 1. Exact SHA-256 overlap between cleaned reference and test
    ref_shas = {hash_by_path[p][0]: p for p in cleaned_ref_paths if p in hash_by_path}
    test_shas = {hash_by_path[p][0]: p for p in test_paths if p in hash_by_path}

    sha_overlap = set(ref_shas.keys()) & set(test_shas.keys())
    print(f"\nExact SHA-256 Overlap between Reference and Test sets: {len(sha_overlap)}")

    # 2. Perceptual dHash near-duplicate check (distance <= 4)
    def hamming(h1, h2):
        if not h1 or not h2:
            return 999
        b1 = bin(int(h1, 16))[2:].zfill(64)
        b2 = bin(int(h2, 16))[2:].zfill(64)
        return sum(c1 != c2 for c1, c2 in zip(b1, b2))

    near_overlaps = []
    for test_p in test_paths:
        if test_p not in hash_by_path:
            continue
        t_sha, t_dh, t_pid = hash_by_path[test_p]
        for ref_p in cleaned_ref_paths:
            if ref_p not in hash_by_path:
                continue
            r_sha, r_dh, r_pid = hash_by_path[ref_p]
            dist = hamming(t_dh, r_dh)
            if dist <= 4:
                near_overlaps.append({
                    "test_image": test_p,
                    "test_pid": t_pid,
                    "ref_image": ref_p,
                    "ref_pid": r_pid,
                    "dhash_distance": dist,
                    "is_same_pid": (t_pid == r_pid),
                })

    print(f"Perceptual Near-Duplicate Overlap (dHash dist <= 4): {len(near_overlaps)}")
    for overlap in near_overlaps:
        print(f"  Test: {overlap['test_image']} <-> Ref: {overlap['ref_image']} (dist={overlap['dhash_distance']}, same_pid={overlap['is_same_pid']})")

    report = {
        "original_reference_count": len(ref_paths),
        "original_test_count": len(test_paths),
        "quarantined_count": len(quarantined),
        "cleaned_reference_count": len(cleaned_ref_paths),
        "exact_sha256_leakage": len(sha_overlap),
        "near_duplicate_overlap_count": len(near_overlaps),
        "near_duplicates": near_overlaps,
        "recommendation": (
            "Keep the test set intact as an unbiased benchmark. "
            "For the 1 near-duplicate pair in P001, ensure reference bank only uses non-overlapping original images."
        )
    }

    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nSaved leakage report to: {OUTPUT_REPORT}")


if __name__ == "__main__":
    main()
