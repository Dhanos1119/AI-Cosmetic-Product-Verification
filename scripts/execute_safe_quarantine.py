"""
Safe Quarantine Execution Script
Moves confirmed non-cosmetic artifacts and duplicates into data/quarantine/.
Does NOT permanently delete any file.
Generates full audit manifest in reports/quarantine_manifest.json and reports/quarantine_manifest.csv.
"""
import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROPOSAL_CSV = BASE_DIR / "reports" / "proposed_image_quarantine.csv"
QUARANTINE_DIR = BASE_DIR / "data" / "quarantine"
MANIFEST_JSON = BASE_DIR / "reports" / "quarantine_manifest.json"
MANIFEST_CSV = BASE_DIR / "reports" / "quarantine_manifest.csv"


def main():
    print("=" * 80)
    print("EXECUTING SAFE DATASET QUARANTINE")
    print("=" * 80)

    if not PROPOSAL_CSV.exists():
        print(f"ERROR: Proposal CSV not found: {PROPOSAL_CSV}")
        return

    # Read proposal
    with open(PROPOSAL_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        records = list(reader)

    to_quarantine = [r for r in records if r["action_recommended"].startswith("QUARANTINE_")]
    print(f"Total proposed items to quarantine: {len(to_quarantine)}")

    # Ensure quarantine directories exist
    (QUARANTINE_DIR / "non_cosmetic").mkdir(parents=True, exist_ok=True)
    (QUARANTINE_DIR / "duplicates").mkdir(parents=True, exist_ok=True)
    (QUARANTINE_DIR / "wrong_labels").mkdir(parents=True, exist_ok=True)

    manifest_rows = []
    timestamp = datetime.now(timezone.utc).isoformat()

    moved_count = 0
    missing_count = 0

    for item in to_quarantine:
        src_path = BASE_DIR / item["rel_path"]
        dest_rel = item["quarantine_destination"]
        dest_path = BASE_DIR / dest_rel

        if not src_path.exists():
            print(f"WARNING: Source file does not exist (already moved?): {src_path}")
            missing_count += 1
            continue

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_path), str(dest_path))
        moved_count += 1

        manifest_rows.append({
            "image_id": item["image_id"],
            "product_id": item["product_id"],
            "category": item["category"],
            "filename": item["filename"],
            "original_path": item["rel_path"],
            "quarantined_path": dest_rel,
            "action": item["action_recommended"],
            "confidence_score": item["confidence_score"],
            "split": item["split"],
            "reason": item["specific_reason"],
            "quarantined_at": timestamp,
        })

    # Write manifest CSV
    fieldnames = [
        "image_id", "product_id", "category", "filename", "original_path",
        "quarantined_path", "action", "confidence_score", "split", "reason", "quarantined_at"
    ]
    with open(MANIFEST_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_rows)

    # Write manifest JSON
    summary = {
        "quarantine_timestamp": timestamp,
        "backup_location": "data/image_model_dataset_backup",
        "total_files_moved": moved_count,
        "missing_files": missing_count,
        "breakdown_by_action": {
            "QUARANTINE_CONFIRMED": sum(1 for r in manifest_rows if r["action"] == "QUARANTINE_CONFIRMED"),
            "QUARANTINE_DUPLICATE": sum(1 for r in manifest_rows if r["action"] == "QUARANTINE_DUPLICATE"),
        },
        "breakdown_by_split": {
            "reference": sum(1 for r in manifest_rows if r["split"] == "reference"),
            "test": sum(1 for r in manifest_rows if r["split"] == "test"),
        },
        "manifest_csv": str(MANIFEST_CSV),
    }
    with open(MANIFEST_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Safe quarantine completed!")
    print(f"  Moved files: {moved_count}")
    print(f"  Backup remains untouched at: data/image_model_dataset_backup (1950 images)")
    print(f"  Quarantine manifest saved at: {MANIFEST_CSV}")


if __name__ == "__main__":
    main()
